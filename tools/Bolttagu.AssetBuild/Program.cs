using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Bolttagu.Assets;

namespace Bolttagu.AssetBuild;

internal static class Program
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        PropertyNameCaseInsensitive = true,
        WriteIndented = true
    };

    [STAThread]
    public static int Main(string[] args)
    {
        try
        {
            var command = args.FirstOrDefault()?.ToLowerInvariant() ?? "all";
            var root = FindRepositoryRoot(args.Skip(1).FirstOrDefault() ?? Environment.CurrentDirectory);
            return command switch
            {
                "verify" => Verify(root),
                "generate" => Generate(root),
                "compile" => Compile(root),
                "all" => RunAll(root),
                _ => Usage(command)
            };
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine($"asset-build: {exception.Message}");
            return 1;
        }
    }

    private static int RunAll(string root)
    {
        var verifyResult = Verify(root);
        if (verifyResult != 0)
        {
            return verifyResult;
        }
        Generate(root);
        return Compile(root);
    }

    private static int Verify(string root)
    {
        var inventoryPath = Path.Combine(root, "asset", "bolttagu", "inventory.json");
        var inventory = AssetInventoryVerifier.Load(inventoryPath);
        var issues = AssetInventoryVerifier.Verify(root, inventory);
        if (issues.Count > 0)
        {
            foreach (var issue in issues)
            {
                Console.Error.WriteLine($"{issue.Path}: {issue.Message}");
            }
            return 1;
        }

        Console.WriteLine($"verified {inventory.Files.Count} immutable upstream files");
        return 0;
    }

    private static int Generate(string root)
    {
        var modelRoot = Path.Combine(root, "asset", "bolttagu", "derived", "model");
        var recipePath = Path.Combine(modelRoot, "animation-recipes.json");
        var recipe = ReadJson<ModelRecipe>(recipePath);
        if (recipe.SchemaVersion != 1)
        {
            throw new InvalidDataException($"Unsupported recipe schema {recipe.SchemaVersion}.");
        }

        var sourcePath = ResolveContained(modelRoot, recipe.Source);
        var source = LoadBitmap(sourcePath);
        ValidateRect(recipe.SourceRect, source.PixelWidth, source.PixelHeight);
        var crop = new CroppedBitmap(source, new Int32Rect(
            recipe.SourceRect.X,
            recipe.SourceRect.Y,
            recipe.SourceRect.Width,
            recipe.SourceRect.Height));

        var animationRoot = Path.Combine(root, "asset", "bolttagu", "derived", "animations");
        var written = 0;
        foreach (var clip in recipe.Clips.OrderBy(clip => clip.Id, StringComparer.Ordinal))
        {
            if (!IsSnakeCase(clip.Id))
            {
                throw new InvalidDataException($"Invalid clip id '{clip.Id}'.");
            }

            var outputDirectory = Path.Combine(animationRoot, clip.Id, "frames");
            Directory.CreateDirectory(outputDirectory);
            for (var index = 0; index < clip.Frames.Count; index++)
            {
                var outputPath = Path.Combine(outputDirectory, $"{index:D3}.png");
                RenderFrame(crop, recipe.Canvas, recipe.Padding, clip.Frames[index], outputPath);
                written++;
            }
        }

        Console.WriteLine($"generated {written} deterministic preview frames from {recipe.Source}");
        return 0;
    }

    private static int Compile(string root)
    {
        var animationRoot = Path.Combine(root, "asset", "bolttagu", "derived", "animations");
        var packPath = Path.Combine(animationRoot, "pack.json");
        var pack = AnimationPackLoader.Load(packPath);
        var issues = AnimationPackValidator.Validate(packPath, pack);
        if (issues.Count > 0)
        {
            foreach (var issue in issues)
            {
                Console.Error.WriteLine($"{issue.Path}: {issue.Message}");
            }
            return 1;
        }

        var orderedFrames = pack.Clips
            .SelectMany(clip => clip.Frames.Select((frame, index) => new FrameWorkItem(clip.Id, index, frame)))
            .ToArray();
        var columns = Math.Min(4, orderedFrames.Length);
        var rows = (int)Math.Ceiling(orderedFrames.Length / (double)columns);
        var atlas = new RenderTargetBitmap(
            columns * pack.Canvas.Width,
            rows * pack.Canvas.Height,
            96,
            96,
            PixelFormats.Pbgra32);
        var visual = new DrawingVisual();
        var catalogFrames = new List<CatalogFrame>();
        using (var context = visual.RenderOpen())
        {
            for (var index = 0; index < orderedFrames.Length; index++)
            {
                var item = orderedFrames[index];
                var column = index % columns;
                var row = index / columns;
                var x = column * pack.Canvas.Width;
                var y = row * pack.Canvas.Height;
                var framePath = ResolveContained(animationRoot, item.Frame.Path);
                context.DrawImage(LoadBitmap(framePath), new Rect(x, y, pack.Canvas.Width, pack.Canvas.Height));
                catalogFrames.Add(new(
                    item.ClipId,
                    item.FrameIndex,
                    new(x, y, pack.Canvas.Width, pack.Canvas.Height),
                    item.Frame.DurationMs,
                    item.Frame.Pivot));
            }
        }
        atlas.Render(visual);

        var buildRoot = Path.Combine(root, "asset", "bolttagu", "build");
        Directory.CreateDirectory(buildRoot);
        var atlasPath = Path.Combine(buildRoot, "atlas.png");
        SavePng(atlas, atlasPath);

        var catalog = new RuntimeCatalog(
            1,
            pack.Id,
            "atlas.png",
            new(columns * pack.Canvas.Width, rows * pack.Canvas.Height),
            pack.Clips.Select(clip => new CatalogClip(clip.Id, clip.Loop)).ToArray(),
            catalogFrames);
        var catalogPath = Path.Combine(buildRoot, "catalog.json");
        WriteJson(catalogPath, catalog);

        var inputs = new List<BuildArtifact>
        {
            HashArtifact(root, Path.Combine(root, "asset", "bolttagu", "derived", "model", "turnaround-v1.png")),
            HashArtifact(root, Path.Combine(root, "asset", "bolttagu", "derived", "model", "animation-recipes.json")),
            HashArtifact(root, packPath)
        };
        inputs.AddRange(orderedFrames.Select(item => HashArtifact(root, ResolveContained(animationRoot, item.Frame.Path))));
        inputs = inputs.DistinctBy(item => item.Path, StringComparer.Ordinal).OrderBy(item => item.Path, StringComparer.Ordinal).ToList();
        var outputs = new[] { HashArtifact(root, atlasPath), HashArtifact(root, catalogPath) };
        var buildHash = ComputeBuildHash(inputs.Concat(outputs));
        WriteJson(Path.Combine(buildRoot, "build-manifest.json"), new BuildManifest(1, buildHash, inputs, outputs));

        Console.WriteLine($"compiled {orderedFrames.Length} frames; build hash {buildHash}");
        return 0;
    }

    private static void RenderFrame(
        BitmapSource source,
        CanvasSize canvas,
        int padding,
        FrameTransform transform,
        string outputPath)
    {
        var availableWidth = canvas.Width - (padding * 2);
        var availableHeight = canvas.Height - (padding * 2);
        if (availableWidth <= 0 || availableHeight <= 0)
        {
            throw new InvalidDataException("Padding leaves no drawable canvas.");
        }

        var fit = Math.Min(availableWidth / (double)source.PixelWidth, availableHeight / (double)source.PixelHeight);
        var width = Math.Round(source.PixelWidth * fit * transform.ScaleX);
        var height = Math.Round(source.PixelHeight * fit * transform.ScaleY);
        var x = Math.Round((canvas.Width - width) / 2d + transform.OffsetX);
        var y = Math.Round(canvas.Height - padding - height + transform.OffsetY);

        var target = new RenderTargetBitmap(canvas.Width, canvas.Height, 96, 96, PixelFormats.Pbgra32);
        var visual = new DrawingVisual();
        using (var context = visual.RenderOpen())
        {
            context.DrawImage(source, new Rect(x, y, width, height));
        }
        target.Render(visual);
        SavePng(target, outputPath);
    }

    private static BitmapSource LoadBitmap(string path)
    {
        using var stream = File.OpenRead(path);
        var decoder = BitmapDecoder.Create(stream, BitmapCreateOptions.PreservePixelFormat, BitmapCacheOption.OnLoad);
        var frame = decoder.Frames[0];
        frame.Freeze();
        return frame;
    }

    private static void SavePng(BitmapSource bitmap, string path)
    {
        var encoder = new PngBitmapEncoder();
        encoder.Frames.Add(BitmapFrame.Create(bitmap));
        using var stream = new FileStream(path, FileMode.Create, FileAccess.Write, FileShare.None);
        encoder.Save(stream);
    }

    private static T ReadJson<T>(string path) where T : class =>
        JsonSerializer.Deserialize<T>(File.ReadAllText(path), JsonOptions)
        ?? throw new InvalidDataException($"{path} is empty.");

    private static void WriteJson<T>(string path, T value) =>
        File.WriteAllText(path, JsonSerializer.Serialize(value, JsonOptions) + Environment.NewLine, new UTF8Encoding(false));

    private static BuildArtifact HashArtifact(string root, string path)
    {
        using var stream = File.OpenRead(path);
        return new(
            Path.GetRelativePath(root, path).Replace('\\', '/'),
            new FileInfo(path).Length,
            Convert.ToHexString(SHA256.HashData(stream)));
    }

    private static string ComputeBuildHash(IEnumerable<BuildArtifact> artifacts)
    {
        var canonical = string.Join('\n', artifacts
            .OrderBy(item => item.Path, StringComparer.Ordinal)
            .Select(item => $"{item.Path}:{item.Bytes}:{item.Sha256}"));
        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(canonical)));
    }

    private static string ResolveContained(string root, string relativePath)
    {
        var normalizedRoot = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        var candidate = Path.GetFullPath(Path.Combine(normalizedRoot, relativePath.Replace('/', Path.DirectorySeparatorChar)));
        if (!candidate.StartsWith(normalizedRoot, StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidDataException($"Path escapes its root: {relativePath}");
        }
        return candidate;
    }

    private static string FindRepositoryRoot(string start)
    {
        var directory = new DirectoryInfo(Path.GetFullPath(start));
        while (directory is not null)
        {
            if (File.Exists(Path.Combine(directory.FullName, "Bolttagu.slnx")))
            {
                return directory.FullName;
            }
            directory = directory.Parent;
        }
        throw new DirectoryNotFoundException("Could not find Bolttagu.slnx.");
    }

    private static void ValidateRect(SourceRect rect, int width, int height)
    {
        if (rect.X < 0 || rect.Y < 0 || rect.Width <= 0 || rect.Height <= 0 ||
            rect.X + rect.Width > width || rect.Y + rect.Height > height)
        {
            throw new InvalidDataException("Source rectangle is outside the model sheet.");
        }
    }

    private static bool IsSnakeCase(string value) => value.Length > 0 && value.All(character =>
        character is >= 'a' and <= 'z' or >= '0' and <= '9' or '_');

    private static int Usage(string command)
    {
        Console.Error.WriteLine($"Unknown command '{command}'. Use verify, generate, compile, or all.");
        return 2;
    }
}

internal sealed record ModelRecipe(
    int SchemaVersion,
    string Source,
    SourceRect SourceRect,
    CanvasSize Canvas,
    int Padding,
    IReadOnlyList<ClipRecipe> Clips);

internal sealed record SourceRect(int X, int Y, int Width, int Height);
internal sealed record ClipRecipe(string Id, IReadOnlyList<FrameTransform> Frames);
internal sealed record FrameTransform(double ScaleX, double ScaleY, int OffsetX, int OffsetY);
internal sealed record FrameWorkItem(string ClipId, int FrameIndex, AnimationFrame Frame);
internal sealed record AtlasRect(int X, int Y, int Width, int Height);
internal sealed record CatalogFrame(string ClipId, int Index, AtlasRect Rect, int DurationMs, PivotPoint Pivot);
internal sealed record CatalogClip(string Id, bool Loop);
internal sealed record RuntimeCatalog(
    int SchemaVersion,
    string PackId,
    string Atlas,
    CanvasSize AtlasSize,
    IReadOnlyList<CatalogClip> Clips,
    IReadOnlyList<CatalogFrame> Frames);
internal sealed record BuildArtifact(string Path, long Bytes, string Sha256);
internal sealed record BuildManifest(
    int SchemaVersion,
    string BuildHash,
    IReadOnlyList<BuildArtifact> Inputs,
    IReadOnlyList<BuildArtifact> Outputs);

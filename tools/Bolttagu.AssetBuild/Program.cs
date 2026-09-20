using System.IO;
using System.Globalization;
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

        var animationRoot = Path.Combine(root, "asset", "bolttagu", "derived", "animations");
        var sourceCache = new Dictionary<string, BitmapSource>(StringComparer.OrdinalIgnoreCase);
        var written = 0;
        foreach (var clip in recipe.Clips.OrderBy(clip => clip.Id, StringComparer.Ordinal))
        {
            if (!IsSnakeCase(clip.Id))
            {
                throw new InvalidDataException($"Invalid clip id '{clip.Id}'.");
            }

            var outputDirectory = Path.Combine(animationRoot, clip.Id, "frames");
            Directory.CreateDirectory(outputDirectory);
            var sourceName = clip.Source ?? recipe.Source;
            var sourcePath = ResolveContained(modelRoot, sourceName);
            if (!sourceCache.TryGetValue(sourcePath, out var source))
            {
                source = LoadBitmap(sourcePath);
                sourceCache.Add(sourcePath, source);
            }
            var sourceRects = clip.SourceRects ?? [recipe.SourceRect];
            if (sourceRects.Count != 1 && sourceRects.Count != clip.Frames.Count)
            {
                throw new InvalidDataException($"Clip '{clip.Id}' must declare one source rect or one per frame.");
            }
            var frameSources = new List<(BitmapSource Source, Int32Rect Bounds)>();
            for (var index = 0; index < clip.Frames.Count; index++)
            {
                var sourceRect = sourceRects.Count == 1 ? sourceRects[0] : sourceRects[index];
                ValidateRect(sourceRect, source.PixelWidth, source.PixelHeight);
                var crop = new CroppedBitmap(source, new Int32Rect(
                    sourceRect.X,
                    sourceRect.Y,
                    sourceRect.Width,
                    sourceRect.Height));
                frameSources.Add((crop, GetAlphaBounds(crop)));
            }

            var referenceIndex = Math.Clamp(clip.ReferenceFrame, 0, frameSources.Count - 1);
            var referenceBounds = frameSources[referenceIndex].Bounds;
            var targetHeight = clip.TargetVisibleHeight > 0
                ? clip.TargetVisibleHeight
                : recipe.Canvas.Height - (recipe.Padding * 2);
            var maxWidth = clip.MaxVisibleWidth > 0
                ? clip.MaxVisibleWidth
                : recipe.Canvas.Width - (recipe.Padding * 2);
            var commonScale = Math.Min(
                targetHeight / (double)referenceBounds.Height,
                maxWidth / (double)referenceBounds.Width);

            for (var index = 0; index < clip.Frames.Count; index++)
            {
                var outputPath = Path.Combine(outputDirectory, $"{index:D3}.png");
                RenderFrame(
                    frameSources[index].Source,
                    frameSources[index].Bounds,
                    recipe.Canvas,
                    commonScale,
                    clip.AnchorY,
                    clip.Align,
                    clip.Frames[index],
                    outputPath);
                written++;
            }
        }

        var sourceCount = recipe.Clips.Select(clip => clip.Source ?? recipe.Source)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .Count();
        Console.WriteLine($"generated {written} deterministic preview frames from {sourceCount} model sources");
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
        var reviewOutputs = WriteReviewArtifacts(buildRoot, animationRoot, pack, orderedFrames);

        var modelRoot = Path.Combine(root, "asset", "bolttagu", "derived", "model");
        var inputs = Directory.EnumerateFiles(modelRoot, "*.png", SearchOption.TopDirectoryOnly)
            .Select(path => HashArtifact(root, path))
            .ToList();
        inputs.Add(HashArtifact(root, Path.Combine(modelRoot, "animation-recipes.json")));
        inputs.Add(HashArtifact(root, packPath));
        inputs.AddRange(orderedFrames.Select(item => HashArtifact(root, ResolveContained(animationRoot, item.Frame.Path))));
        inputs = inputs.DistinctBy(item => item.Path, StringComparer.Ordinal).OrderBy(item => item.Path, StringComparer.Ordinal).ToList();
        var outputs = new[] { HashArtifact(root, atlasPath), HashArtifact(root, catalogPath) }
            .Concat(reviewOutputs.Select(path => HashArtifact(root, path)))
            .ToArray();
        var buildHash = ComputeBuildHash(inputs.Concat(outputs));
        WriteJson(Path.Combine(buildRoot, "build-manifest.json"), new BuildManifest(1, buildHash, inputs, outputs));

        Console.WriteLine($"compiled {orderedFrames.Length} frames; build hash {buildHash}");
        return 0;
    }

    private static void RenderFrame(
        BitmapSource source,
        Int32Rect alphaBounds,
        CanvasSize canvas,
        double commonScale,
        int anchorY,
        string align,
        FrameTransform transform,
        string outputPath)
    {
        var trimmed = new CroppedBitmap(source, alphaBounds);
        var width = Math.Round(alphaBounds.Width * commonScale * transform.ScaleX);
        var height = Math.Round(alphaBounds.Height * commonScale * transform.ScaleY);
        var x = Math.Round((canvas.Width - width) / 2d + transform.OffsetX);
        var y = align.Equals("top", StringComparison.OrdinalIgnoreCase)
            ? anchorY + transform.OffsetY
            : anchorY - height + transform.OffsetY;

        var target = new RenderTargetBitmap(canvas.Width, canvas.Height, 96, 96, PixelFormats.Pbgra32);
        var visual = new DrawingVisual();
        using (var context = visual.RenderOpen())
        {
            context.DrawImage(trimmed, new Rect(x, y, width, height));
        }
        target.Render(visual);
        SavePng(target, outputPath);
    }

    private static Int32Rect GetAlphaBounds(BitmapSource source)
    {
        var converted = new FormatConvertedBitmap(source, PixelFormats.Bgra32, null, 0);
        var stride = converted.PixelWidth * 4;
        var pixels = new byte[stride * converted.PixelHeight];
        converted.CopyPixels(pixels, stride, 0);
        var minX = converted.PixelWidth;
        var minY = converted.PixelHeight;
        var maxX = -1;
        var maxY = -1;
        for (var y = 0; y < converted.PixelHeight; y++)
        {
            for (var x = 0; x < converted.PixelWidth; x++)
            {
                if (pixels[(y * stride) + (x * 4) + 3] <= 8) continue;
                minX = Math.Min(minX, x);
                minY = Math.Min(minY, y);
                maxX = Math.Max(maxX, x);
                maxY = Math.Max(maxY, y);
            }
        }
        if (maxX < minX || maxY < minY)
            throw new InvalidDataException("Sprite source contains no visible pixels.");
        return new(minX, minY, maxX - minX + 1, maxY - minY + 1);
    }

    private static string[] WriteReviewArtifacts(
        string buildRoot,
        string animationRoot,
        AnimationPack pack,
        IReadOnlyList<FrameWorkItem> frames)
    {
        const int preview = 256;
        const int labelHeight = 24;
        const int columns = 4;
        var rows = (int)Math.Ceiling(frames.Count / (double)columns);
        var target = new RenderTargetBitmap(
            columns * preview,
            rows * (preview + labelHeight),
            96,
            96,
            PixelFormats.Pbgra32);
        var visual = new DrawingVisual();
        var metrics = new List<FrameMetric>();
        using (var context = visual.RenderOpen())
        {
            for (var index = 0; index < frames.Count; index++)
            {
                var item = frames[index];
                var column = index % columns;
                var row = index / columns;
                var x = column * preview;
                var y = row * (preview + labelHeight);
                context.DrawRectangle(
                    new SolidColorBrush(Color.FromRgb(34, 31, 42)),
                    null,
                    new Rect(x, y, preview, preview));
                var frame = LoadBitmap(ResolveContained(animationRoot, item.Frame.Path));
                context.DrawImage(frame, new Rect(x, y, preview, preview));
                var bounds = GetAlphaBounds(frame);
                metrics.Add(new(
                    item.ClipId,
                    item.FrameIndex,
                    bounds.X,
                    bounds.Y,
                    bounds.Width,
                    bounds.Height,
                    bounds.Y + bounds.Height - 1));
                var label = new FormattedText(
                    $"{item.ClipId}/{item.FrameIndex:D3}",
                    CultureInfo.InvariantCulture,
                    FlowDirection.LeftToRight,
                    new Typeface("Consolas"),
                    12,
                    Brushes.White,
                    1);
                context.DrawText(label, new Point(x + 4, y + preview + 4));
            }
        }
        target.Render(visual);
        var reviewRoot = Path.Combine(buildRoot, "review");
        Directory.CreateDirectory(reviewRoot);
        var sheetPath = Path.Combine(reviewRoot, "contact-sheet.png");
        var metricsPath = Path.Combine(reviewRoot, "frame-metrics.json");
        SavePng(target, sheetPath);
        WriteJson(metricsPath, new ReviewMetrics(1, pack.Canvas, metrics));
        return [sheetPath, metricsPath];
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
internal sealed record ClipRecipe(
    string Id,
    IReadOnlyList<FrameTransform> Frames,
    string? Source = null,
    IReadOnlyList<SourceRect>? SourceRects = null,
    int TargetVisibleHeight = 420,
    int MaxVisibleWidth = 480,
    int AnchorY = 480,
    string Align = "bottom",
    int ReferenceFrame = 0);
internal sealed record FrameTransform(double ScaleX, double ScaleY, int OffsetX, int OffsetY);
internal sealed record FrameWorkItem(string ClipId, int FrameIndex, AnimationFrame Frame);
internal sealed record FrameMetric(string ClipId, int Index, int X, int Y, int Width, int Height, int Bottom);
internal sealed record ReviewMetrics(int SchemaVersion, CanvasSize Canvas, IReadOnlyList<FrameMetric> Frames);
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

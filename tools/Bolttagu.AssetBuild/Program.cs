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

public static class Program
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
            Console.Error.WriteLine($"asset-build: {exception}");
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
        var animationRoot = Path.Combine(root, "asset", "bolttagu", "derived", "animations");
        var rigFrames = IdleRigComposer.ComposeIfPresent(modelRoot, animationRoot);
        var recipePath = Path.Combine(modelRoot, "animation-recipes.json");
        var recipe = ReadJson<ModelRecipe>(recipePath);
        if (recipe.SchemaVersion != 1)
        {
            throw new InvalidDataException($"Unsupported recipe schema {recipe.SchemaVersion}.");
        }

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

            // A calibration frame is deliberately independent from the emitted animation frames.
            // New sheets should reserve their final cell for a canonical idle pose; legacy sheets
            // may instead point at the shared turnaround idle through Calibration.Source.
            var calibration = LoadCalibrationFrame(
                clip,
                sourceName,
                frameSources,
                modelRoot,
                sourceCache);
            var referenceBounds = calibration.Bounds;
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

            if (clip.Calibration?.Emit == true)
            {
                var outputPath = Path.Combine(outputDirectory, $"{clip.Frames.Count:D3}.png");
                RenderFrame(
                    calibration.Source,
                    calibration.Bounds,
                    recipe.Canvas,
                    commonScale,
                    clip.AnchorY,
                    clip.Align,
                    clip.Calibration.Transform ?? FrameTransform.Identity,
                    outputPath);
                written++;
            }
        }

        var sourceCount = recipe.Clips.Select(clip => clip.Source ?? recipe.Source)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .Count();
        Console.WriteLine($"generated {written + rigFrames} deterministic preview frames from {sourceCount} model sources ({rigFrames} rig-composited)");
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
                    item.Frame.Pivot,
                    item.Frame.Contacts));
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
        var inputs = Directory.EnumerateFiles(modelRoot, "*.png", SearchOption.AllDirectories)
            .Select(path => HashArtifact(root, path))
            .ToList();
        inputs.Add(HashArtifact(root, Path.Combine(modelRoot, "animation-recipes.json")));
        inputs.Add(HashArtifact(root, Path.Combine(modelRoot, "model.json")));
        var rigPath = Path.Combine(modelRoot, "idle-rig.json");
        if (File.Exists(rigPath))
        {
            inputs.Add(HashArtifact(root, rigPath));
        }
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

    private static (BitmapSource Source, Int32Rect Bounds) LoadCalibrationFrame(
        ClipRecipe clip,
        string clipSourceName,
        IReadOnlyList<(BitmapSource Source, Int32Rect Bounds)> frameSources,
        string modelRoot,
        IDictionary<string, BitmapSource> sourceCache)
    {
        if (clip.Calibration is null)
        {
            var referenceIndex = Math.Clamp(clip.ReferenceFrame, 0, frameSources.Count - 1);
            return frameSources[referenceIndex];
        }

        var calibrationSourceName = clip.Calibration.Source ?? clipSourceName;
        var calibrationSourcePath = ResolveContained(modelRoot, calibrationSourceName);
        if (!sourceCache.TryGetValue(calibrationSourcePath, out var calibrationSource))
        {
            calibrationSource = LoadBitmap(calibrationSourcePath);
            sourceCache.Add(calibrationSourcePath, calibrationSource);
        }

        ValidateRect(
            clip.Calibration.SourceRect,
            calibrationSource.PixelWidth,
            calibrationSource.PixelHeight);
        var crop = new CroppedBitmap(calibrationSource, new Int32Rect(
            clip.Calibration.SourceRect.X,
            clip.Calibration.SourceRect.Y,
            clip.Calibration.SourceRect.Width,
            clip.Calibration.SourceRect.Height));
        return (crop, GetAlphaBounds(crop));
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
        var scaleAuditPath = Path.Combine(reviewRoot, "scale-audit-sheet.png");
        var showcasePath = Path.Combine(reviewRoot, "animation-showcase.gif");
        SavePng(target, sheetPath);
        WriteJson(metricsPath, new ReviewMetrics(1, pack.Canvas, metrics));
        WriteScaleAuditSheet(scaleAuditPath, animationRoot, frames);
        WriteAnimationShowcaseGif(showcasePath, animationRoot, frames);
        return [sheetPath, metricsPath, scaleAuditPath, showcasePath];
    }

    private static void WriteAnimationShowcaseGif(
        string outputPath,
        string animationRoot,
        IReadOnlyList<FrameWorkItem> frames)
    {
        const int preview = 256;
        const int labelHeight = 32;
        var encoder = new GifBitmapEncoder();
        foreach (var item in frames)
        {
            var target = new RenderTargetBitmap(preview, preview + labelHeight, 96, 96, PixelFormats.Pbgra32);
            var visual = new DrawingVisual();
            using (var context = visual.RenderOpen())
            {
                context.DrawRectangle(
                    new SolidColorBrush(Color.FromRgb(15, 17, 22)),
                    null,
                    new Rect(0, 0, preview, preview + labelHeight));
                context.DrawImage(
                    LoadBitmap(ResolveContained(animationRoot, item.Frame.Path)),
                    new Rect(0, 0, preview, preview));
                var label = new FormattedText(
                    item.ClipId,
                    CultureInfo.InvariantCulture,
                    FlowDirection.LeftToRight,
                    new Typeface("Consolas"),
                    15,
                    Brushes.White,
                    1);
                context.DrawText(label, new Point(10, preview + 6));
            }
            target.Render(visual);

            var metadata = new BitmapMetadata("gif");
            metadata.SetQuery("/grctlext/Delay", (ushort)Math.Max(6, item.Frame.DurationMs / 10));
            encoder.Frames.Add(BitmapFrame.Create(target, null, metadata, null));
        }

        using var encodedStream = new MemoryStream();
        encoder.Save(encodedStream);
        var encoded = encodedStream.ToArray();
        var globalColorTableBytes = (encoded[10] & 0x80) == 0
            ? 0
            : 3 * (1 << ((encoded[10] & 0x07) + 1));
        var extensionOffset = 13 + globalColorTableBytes;
        byte[] loopForeverExtension =
        [
            0x21, 0xFF, 0x0B,
            (byte)'N', (byte)'E', (byte)'T', (byte)'S', (byte)'C', (byte)'A', (byte)'P', (byte)'E',
            (byte)'2', (byte)'.', (byte)'0',
            0x03, 0x01, 0x00, 0x00, 0x00,
        ];
        using var stream = new FileStream(outputPath, FileMode.Create, FileAccess.Write, FileShare.None);
        stream.Write(encoded, 0, extensionOffset);
        stream.Write(loopForeverExtension);
        stream.Write(encoded, extensionOffset, encoded.Length - extensionOffset);
    }

    private static void WriteScaleAuditSheet(
        string outputPath,
        string animationRoot,
        IReadOnlyList<FrameWorkItem> frames)
    {
        var requested = new (string ClipId, int Index)[]
        {
            ("idle_breathe", 0),
            ("walk", 0),
            ("click", 0),
            ("click_huff", 0),
            ("turn", 0),
            ("drag_held_idle", 0),
            ("drag_pulled", 0),
            ("spawn_in", 5),
            ("despawn_out", 0),
            ("fall", 0),
            ("drop_land", 3),
            ("sit_down", 5),
            ("doze_loop", 0),
            ("wake_up", 5),
            ("look_around", 0),
            ("stretch", 3),
            ("land_recover", 0),
            ("rope_climb_prepare", 0),
            ("rope_climb_loop", 0),
            ("rope_climb_finish", 1),
            ("free_climb_prepare", 0),
            ("free_climb_loop", 0),
            ("free_climb_finish", 1),
        };
        var selected = requested.Select(key => frames.Single(
            item => item.ClipId == key.ClipId && item.FrameIndex == key.Index)).ToArray();
        const int preview = 256;
        const int labelHeight = 36;
        const int columns = 4;
        var rows = (int)Math.Ceiling(selected.Length / (double)columns);
        var target = new RenderTargetBitmap(
            columns * preview,
            rows * (preview + labelHeight),
            96,
            96,
            PixelFormats.Pbgra32);
        var visual = new DrawingVisual();
        using (var context = visual.RenderOpen())
        {
            for (var index = 0; index < selected.Length; index++)
            {
                var item = selected[index];
                var column = index % columns;
                var row = index / columns;
                var x = column * preview;
                var y = row * (preview + labelHeight);
                context.DrawRectangle(
                    new SolidColorBrush(Color.FromRgb(34, 31, 42)),
                    null,
                    new Rect(x, y, preview, preview));
                var frame = LoadBitmap(ResolveContained(animationRoot, item.Frame.Path));
                var bounds = GetAlphaBounds(frame);
                context.DrawImage(frame, new Rect(x, y, preview, preview));
                var guide = new Pen(new SolidColorBrush(Color.FromArgb(110, 78, 142, 136)), 1)
                {
                    DashStyle = DashStyles.Dash
                };
                context.DrawLine(guide, new Point(x + 128, y), new Point(x + 128, y + preview));
                context.DrawLine(
                    guide,
                    new Point(x, y + (item.Frame.Pivot.Y / 2d)),
                    new Point(x + preview, y + (item.Frame.Pivot.Y / 2d)));
                var label = new FormattedText(
                    $"{item.ClipId}/{item.FrameIndex:D3}\n{bounds.Width}x{bounds.Height} px",
                    CultureInfo.InvariantCulture,
                    FlowDirection.LeftToRight,
                    new Typeface("Consolas"),
                    11,
                    Brushes.White,
                    1);
                context.DrawText(label, new Point(x + 4, y + preview + 2));
            }
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
internal sealed record ClipRecipe(
    string Id,
    IReadOnlyList<FrameTransform> Frames,
    string? Source = null,
    IReadOnlyList<SourceRect>? SourceRects = null,
    int TargetVisibleHeight = 420,
    int MaxVisibleWidth = 480,
    int AnchorY = 480,
    string Align = "bottom",
    int ReferenceFrame = 0,
    CalibrationFrame? Calibration = null);
internal sealed record CalibrationFrame(
    SourceRect SourceRect,
    string? Source = null,
    bool Emit = false,
    FrameTransform? Transform = null);
internal sealed record FrameTransform(double ScaleX, double ScaleY, int OffsetX, int OffsetY)
{
    public static FrameTransform Identity { get; } = new(1.0, 1.0, 0, 0);
}
internal sealed record FrameWorkItem(string ClipId, int FrameIndex, AnimationFrame Frame);
internal sealed record FrameMetric(string ClipId, int Index, int X, int Y, int Width, int Height, int Bottom);
internal sealed record ReviewMetrics(int SchemaVersion, CanvasSize Canvas, IReadOnlyList<FrameMetric> Frames);
internal sealed record AtlasRect(int X, int Y, int Width, int Height);
internal sealed record CatalogFrame(
    string ClipId,
    int Index,
    AtlasRect Rect,
    int DurationMs,
    PivotPoint Pivot,
    IReadOnlyList<FrameContact>? Contacts);
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

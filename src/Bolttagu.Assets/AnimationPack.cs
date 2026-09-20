using System.Text.Json;

namespace Bolttagu.Assets;

public sealed record AnimationPack(
    int SchemaVersion,
    string Id,
    CanvasSize Canvas,
    IReadOnlyList<AnimationClip> Clips);

public sealed record CanvasSize(int Width, int Height);

public sealed record AnimationClip(
    string Id,
    bool Loop,
    IReadOnlyList<AnimationFrame> Frames);

public sealed record AnimationFrame(
    string Path,
    int DurationMs,
    PivotPoint Pivot);

public sealed record PivotPoint(int X, int Y);

public sealed record PngMetadata(int Width, int Height, byte BitDepth, byte ColorType)
{
    public bool HasAlpha => ColorType is 4 or 6;
}

public static class AnimationPackLoader
{
    private static readonly JsonSerializerOptions Options = new() { PropertyNameCaseInsensitive = true };

    public static AnimationPack Load(string path)
    {
        var pack = JsonSerializer.Deserialize<AnimationPack>(File.ReadAllText(path), Options);
        return pack ?? throw new InvalidDataException("Animation pack JSON is empty.");
    }
}

public static class AnimationPackValidator
{
    public static IReadOnlyList<VerificationIssue> Validate(string packPath, AnimationPack pack)
    {
        var issues = new List<VerificationIssue>();
        var packRoot = Path.GetDirectoryName(Path.GetFullPath(packPath))
            ?? throw new InvalidDataException("Pack path has no parent directory.");

        if (pack.SchemaVersion != 1)
        {
            issues.Add(new(packPath, $"Unsupported schema version {pack.SchemaVersion}."));
        }

        if (pack.Canvas.Width <= 0 || pack.Canvas.Height <= 0)
        {
            issues.Add(new(packPath, "Canvas dimensions must be positive."));
        }

        var clipIds = new HashSet<string>(StringComparer.Ordinal);
        foreach (var clip in pack.Clips)
        {
            if (!IsSnakeCase(clip.Id))
            {
                issues.Add(new(clip.Id, "Clip id must be lower_snake_case."));
            }
            if (!clipIds.Add(clip.Id))
            {
                issues.Add(new(clip.Id, "Clip id is duplicated."));
            }
            if (clip.Frames.Count == 0)
            {
                issues.Add(new(clip.Id, "Clip must contain at least one frame."));
            }

            foreach (var frame in clip.Frames)
            {
                ValidateFrame(packRoot, pack.Canvas, clip.Id, frame, issues);
            }
        }

        return issues;
    }

    private static void ValidateFrame(
        string packRoot,
        CanvasSize canvas,
        string clipId,
        AnimationFrame frame,
        List<VerificationIssue> issues)
    {
        if (frame.DurationMs is < 40 or > 10_000)
        {
            issues.Add(new(frame.Path, "Frame duration must be between 40 and 10000 ms."));
        }
        if (frame.Pivot.X < 0 || frame.Pivot.X > canvas.Width || frame.Pivot.Y < 0 || frame.Pivot.Y > canvas.Height)
        {
            issues.Add(new(frame.Path, "Pivot must be inside the canvas."));
        }

        string path;
        try
        {
            path = AssetInventoryVerifier.ResolveContainedPath(packRoot, frame.Path);
        }
        catch (InvalidDataException exception)
        {
            issues.Add(new(frame.Path, exception.Message));
            return;
        }

        if (!File.Exists(path))
        {
            issues.Add(new(frame.Path, $"Frame for {clipId} is missing."));
            return;
        }

        try
        {
            var png = PngInspector.Read(path);
            if (png.Width != canvas.Width || png.Height != canvas.Height)
            {
                issues.Add(new(frame.Path, $"Expected {canvas.Width}x{canvas.Height}, got {png.Width}x{png.Height}."));
            }
            if (!png.HasAlpha)
            {
                issues.Add(new(frame.Path, "Frame must be an RGBA or grayscale-alpha PNG."));
            }
        }
        catch (InvalidDataException exception)
        {
            issues.Add(new(frame.Path, exception.Message));
        }
    }

    private static bool IsSnakeCase(string value) =>
        value.Length > 0 && value.All(character =>
            character is >= 'a' and <= 'z' or >= '0' and <= '9' or '_');
}

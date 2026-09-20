using System.Text.Json;
using Bolttagu.Contracts;

namespace Bolttagu.Assets;

public sealed class RuntimeAnimationCatalog : IAnimationCatalog
{
    private static readonly JsonSerializerOptions JsonOptions = new() { PropertyNameCaseInsensitive = true };
    private readonly IReadOnlyDictionary<string, SpriteClip> _clips;

    private RuntimeAnimationCatalog(
        IReadOnlyDictionary<string, SpriteClip> clips,
        bool isFallback,
        string diagnostic)
    {
        _clips = clips;
        IsFallback = isFallback;
        Diagnostic = diagnostic;
    }

    public bool IsFallback { get; }
    public string Diagnostic { get; }

    public SpriteClip GetClip(string clipId) =>
        _clips.TryGetValue(clipId, out var clip)
            ? clip
            : throw new KeyNotFoundException($"Animation clip '{clipId}' does not exist.");

    public static RuntimeAnimationCatalog Load(string buildRoot)
    {
        var root = Path.GetFullPath(buildRoot);
        var catalogPath = Path.Combine(root, "catalog.json");
        var document = JsonSerializer.Deserialize<CatalogDocument>(File.ReadAllText(catalogPath), JsonOptions)
            ?? throw new InvalidDataException("Runtime catalog is empty.");
        if (document.SchemaVersion != 1)
        {
            throw new InvalidDataException($"Unsupported runtime catalog schema {document.SchemaVersion}.");
        }
        if (string.IsNullOrWhiteSpace(document.Atlas) || document.AtlasSize is null ||
            document.Clips is null || document.Frames is null)
        {
            throw new InvalidDataException("Runtime catalog is missing required fields.");
        }

        var atlasPath = ResolveContained(root, document.Atlas);
        var atlas = PngInspector.Read(atlasPath);
        if (atlas.Width != document.AtlasSize.Width || atlas.Height != document.AtlasSize.Height)
        {
            throw new InvalidDataException("Atlas dimensions do not match catalog metadata.");
        }

        var framesByClip = document.Frames
            .GroupBy(frame => frame.ClipId, StringComparer.Ordinal)
            .ToDictionary(
                group => group.Key,
                group => group.OrderBy(frame => frame.Index).ToArray(),
                StringComparer.Ordinal);
        var clips = new Dictionary<string, SpriteClip>(StringComparer.Ordinal);
        foreach (var clip in document.Clips)
        {
            if (clips.ContainsKey(clip.Id))
            {
                throw new InvalidDataException($"Clip '{clip.Id}' is duplicated.");
            }
            if (!framesByClip.TryGetValue(clip.Id, out var frames) || frames.Length == 0)
            {
                throw new InvalidDataException($"Clip '{clip.Id}' has no frames.");
            }

            for (var index = 0; index < frames.Length; index++)
            {
                if (frames[index].Index != index)
                {
                    throw new InvalidDataException($"Clip '{clip.Id}' frame indices must be contiguous from zero.");
                }
            }

            clips.Add(clip.Id, new(
                clip.Id,
                clip.Loop,
                frames.Select(frame => ToFrame(atlasPath, atlas, frame)).ToArray()));
        }

        return new(clips, false, $"Loaded {clips.Count} clips from {Path.GetFileName(catalogPath)}.");
    }

    public static RuntimeAnimationCatalog LoadOrFallback(string buildRoot, string fallbackImagePath)
    {
        try
        {
            return Load(buildRoot);
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or JsonException or InvalidDataException)
        {
            var fallback = Path.GetFullPath(fallbackImagePath);
            var image = PngInspector.Read(fallback);
            var frame = new SpriteFrame(
                fallback,
                new(0, 0, image.Width, image.Height),
                TimeSpan.FromMilliseconds(500),
                new(image.Width / 2, image.Height));
            var clips = PetActionClips.All.Values.ToDictionary(
                clipId => clipId,
                clipId => new SpriteClip(clipId, clipId is "idle_breathe" or "walk", [frame]),
                StringComparer.Ordinal);
            return new(clips, true, $"Runtime pack failed validation; static fallback active: {exception.Message}");
        }
    }

    private static SpriteFrame ToFrame(string atlasPath, PngMetadata atlas, CatalogFrame frame)
    {
        if (frame.DurationMs <= 0)
        {
            throw new InvalidDataException($"Frame {frame.ClipId}/{frame.Index} has an invalid duration.");
        }
        if (frame.Rect.X < 0 || frame.Rect.Y < 0 || frame.Rect.Width <= 0 || frame.Rect.Height <= 0 ||
            frame.Rect.X + frame.Rect.Width > atlas.Width || frame.Rect.Y + frame.Rect.Height > atlas.Height)
        {
            throw new InvalidDataException($"Frame {frame.ClipId}/{frame.Index} is outside the atlas.");
        }
        if (frame.Pivot.X < 0 || frame.Pivot.X > frame.Rect.Width ||
            frame.Pivot.Y < 0 || frame.Pivot.Y > frame.Rect.Height)
        {
            throw new InvalidDataException($"Frame {frame.ClipId}/{frame.Index} has an invalid pivot.");
        }

        return new(
            atlasPath,
            new(frame.Rect.X, frame.Rect.Y, frame.Rect.Width, frame.Rect.Height),
            TimeSpan.FromMilliseconds(frame.DurationMs),
            new(frame.Pivot.X, frame.Pivot.Y));
    }

    private static string ResolveContained(string root, string relativePath)
    {
        if (Path.IsPathRooted(relativePath))
        {
            throw new InvalidDataException("Catalog atlas path must be relative.");
        }
        var normalizedRoot = root.TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        var candidate = Path.GetFullPath(Path.Combine(normalizedRoot, relativePath));
        if (!candidate.StartsWith(normalizedRoot, StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidDataException("Catalog atlas path escapes the build root.");
        }
        return candidate;
    }

    private sealed record CatalogDocument(
        int SchemaVersion,
        string PackId,
        string Atlas,
        CatalogSize AtlasSize,
        IReadOnlyList<CatalogClip> Clips,
        IReadOnlyList<CatalogFrame> Frames);
    private sealed record CatalogSize(int Width, int Height);
    private sealed record CatalogClip(string Id, bool Loop);
    private sealed record CatalogFrame(
        string ClipId,
        int Index,
        CatalogRect Rect,
        int DurationMs,
        CatalogPoint Pivot);
    private sealed record CatalogRect(int X, int Y, int Width, int Height);
    private sealed record CatalogPoint(int X, int Y);
}

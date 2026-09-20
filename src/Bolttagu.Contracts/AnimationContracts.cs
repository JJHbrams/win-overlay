namespace Bolttagu.Contracts;

public readonly record struct PixelRect(int X, int Y, int Width, int Height);
public readonly record struct PixelPoint(int X, int Y);

public sealed record SpriteFrame(
    string AtlasPath,
    PixelRect SourceRect,
    TimeSpan Duration,
    PixelPoint Pivot);

public sealed record SpriteClip(
    string Id,
    bool Loop,
    IReadOnlyList<SpriteFrame> Frames);

public interface IAnimationCatalog
{
    bool IsFallback { get; }
    string Diagnostic { get; }
    SpriteClip GetClip(string clipId);
}

public sealed class AnimationPlaybackCompletedEventArgs(string clipId) : EventArgs
{
    public string ClipId { get; } = clipId;
}

public interface IAnimationPlayer : IDisposable
{
    string? CurrentClipId { get; }
    event EventHandler<AnimationPlaybackCompletedEventArgs>? PlaybackCompleted;
    void Play(string clipId);
    void Stop();
}

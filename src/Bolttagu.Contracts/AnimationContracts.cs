namespace Bolttagu.Contracts;

public readonly record struct PixelRect(int X, int Y, int Width, int Height);
public readonly record struct PixelPoint(int X, int Y);

public enum FacingDirection { Left, Right }
public enum PetAction { Idle, Click, Turn, Walk, DragDangle, Fall, DropLand }

public static class PetActionClips
{
    public const string Idle = "idle_breathe";
    public const string Click = "click";
    public const string Turn = "turn";
    public const string Walk = "walk";
    public const string DragDangle = "drag_dangle";
    public const string Fall = "fall";
    public const string DropLand = "drop_land";
    public const string TurnToIdle = "turn_to_idle";

    public static IReadOnlyDictionary<PetAction, string> All { get; } =
        new Dictionary<PetAction, string>
        {
            [PetAction.Idle] = Idle,
            [PetAction.Click] = Click,
            [PetAction.Turn] = Turn,
            [PetAction.Walk] = Walk,
            [PetAction.DragDangle] = DragDangle,
            [PetAction.Fall] = Fall,
            [PetAction.DropLand] = DropLand,
        };
}

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
    FacingDirection Facing { get; }
    event EventHandler<AnimationPlaybackCompletedEventArgs>? PlaybackCompleted;
    void Play(string clipId);
    void SetFacing(FacingDirection facing);
    void Stop();
}

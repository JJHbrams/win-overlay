namespace Bolttagu.Contracts;

public readonly record struct PixelRect(int X, int Y, int Width, int Height);
public readonly record struct PixelPoint(int X, int Y);
public enum SpriteContactKind { Hand, Foot }
public sealed record SpriteContactAnchor(SpriteContactKind Kind, PixelPoint Point);
public sealed record RenderedSpriteContact(SpriteContactKind Kind, ScreenPoint LocalPosition);

public enum FacingDirection { Left, Right }
public enum PetAction
{
    Idle,
    Click,
    ClickHuff,
    Turn,
    Walk,
    Run,
    DragHeldIdle,
    DragPulled,
    SpawnIn,
    DespawnOut,
    Fall,
    DropLand,
    SitDown,
    SitSettle,
    DozeEnter,
    DozeLoop,
    WakeUp,
    StandUp,
    DozeStartle,
    LookAround,
    Stretch,
    LandRecover,
    RopeClimbPrepare,
    RopeClimbLoop,
    RopeClimbFinish,
    FreeClimbPrepare,
    FreeClimbLoop,
    FreeClimbFinish,
    RopeClimbDownPrepare,
    RopeClimbDownLoop,
    RopeClimbDownFinish,
    FreeClimbDownPrepare,
    FreeClimbDownLoop,
    FreeClimbDownFinish,
}

public static class PetActionClips
{
    public const string Idle = "idle_breathe";
    public const string Click = "click";
    public const string ClickHuff = "click_huff";
    public const string Turn = "turn";
    public const string Walk = "walk";
    public const string Run = "run";
    public const string DragHeldIdle = "drag_held_idle";
    public const string DragPulled = "drag_pulled";
    public const string SpawnIn = "spawn_in";
    public const string DespawnOut = "despawn_out";
    public const string Fall = "fall";
    public const string DropLand = "drop_land";
    public const string TurnToIdle = "turn_to_idle";
    public const string SitDown = "sit_down";
    public const string SitSettle = "sit_settle";
    public const string DozeEnter = "doze_enter";
    public const string DozeLoop = "doze_loop";
    public const string WakeUp = "wake_up";
    public const string StandUp = "stand_up";
    public const string DozeStartle = "doze_startle";
    public const string LookAround = "look_around";
    public const string Stretch = "stretch";
    public const string LandRecover = "land_recover";
    public const string RopeClimbPrepare = "rope_climb_prepare";
    public const string RopeClimbLoop = "rope_climb_loop";
    public const string RopeClimbFinish = "rope_climb_finish";
    public const string FreeClimbPrepare = "free_climb_prepare";
    public const string FreeClimbLoop = "free_climb_loop";
    public const string FreeClimbFinish = "free_climb_finish";
    public const string RopeClimbDownPrepare = "rope_climb_down_prepare";
    public const string RopeClimbDownLoop = "rope_climb_down_loop";
    public const string RopeClimbDownFinish = "rope_climb_down_finish";
    public const string FreeClimbDownPrepare = "free_climb_down_prepare";
    public const string FreeClimbDownLoop = "free_climb_down_loop";
    public const string FreeClimbDownFinish = "free_climb_down_finish";

    public static IReadOnlyDictionary<PetAction, string> All { get; } =
        new Dictionary<PetAction, string>
        {
            [PetAction.Idle] = Idle,
            [PetAction.Click] = Click,
            [PetAction.ClickHuff] = ClickHuff,
            [PetAction.Turn] = Turn,
            [PetAction.Walk] = Walk,
            [PetAction.Run] = Run,
            [PetAction.DragHeldIdle] = DragHeldIdle,
            [PetAction.DragPulled] = DragPulled,
            [PetAction.SpawnIn] = SpawnIn,
            [PetAction.DespawnOut] = DespawnOut,
            [PetAction.Fall] = Fall,
            [PetAction.DropLand] = DropLand,
            [PetAction.SitDown] = SitDown,
            [PetAction.SitSettle] = SitSettle,
            [PetAction.DozeEnter] = DozeEnter,
            [PetAction.DozeLoop] = DozeLoop,
            [PetAction.WakeUp] = WakeUp,
            [PetAction.StandUp] = StandUp,
            [PetAction.DozeStartle] = DozeStartle,
            [PetAction.LookAround] = LookAround,
            [PetAction.Stretch] = Stretch,
            [PetAction.LandRecover] = LandRecover,
            [PetAction.RopeClimbPrepare] = RopeClimbPrepare,
            [PetAction.RopeClimbLoop] = RopeClimbLoop,
            [PetAction.RopeClimbFinish] = RopeClimbFinish,
            [PetAction.FreeClimbPrepare] = FreeClimbPrepare,
            [PetAction.FreeClimbLoop] = FreeClimbLoop,
            [PetAction.FreeClimbFinish] = FreeClimbFinish,
            [PetAction.RopeClimbDownPrepare] = RopeClimbDownPrepare,
            [PetAction.RopeClimbDownLoop] = RopeClimbDownLoop,
            [PetAction.RopeClimbDownFinish] = RopeClimbDownFinish,
            [PetAction.FreeClimbDownPrepare] = FreeClimbDownPrepare,
            [PetAction.FreeClimbDownLoop] = FreeClimbDownLoop,
            [PetAction.FreeClimbDownFinish] = FreeClimbDownFinish,
        };
}

public sealed record SpriteFrame(
    string AtlasPath,
    PixelRect SourceRect,
    TimeSpan Duration,
    PixelPoint Pivot,
    IReadOnlyList<SpriteContactAnchor>? Contacts = null)
{
    public IReadOnlyList<SpriteContactAnchor> ContactAnchors => Contacts ?? [];
}

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

public sealed class AnimationFramePresentedEventArgs(
    string clipId,
    int frameIndex,
    IReadOnlyList<RenderedSpriteContact> contacts) : EventArgs
{
    public string ClipId { get; } = clipId;
    public int FrameIndex { get; } = frameIndex;
    public IReadOnlyList<RenderedSpriteContact> Contacts { get; } = contacts;
}

public interface IAnimationFrameSource
{
    event EventHandler<AnimationFramePresentedEventArgs>? FramePresented;
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

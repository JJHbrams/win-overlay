using Bolttagu.Contracts;
using Bolttagu.Core;

namespace Bolttagu.Runtime;

public enum PetRuntimeState { Idle, Turning, Walking, TurningToIdle, Reacting, Dragging, Falling, Landing }

public sealed class PetAnimationController : IDisposable
{
    private readonly IAnimationPlayer _player;
    private readonly IOverlayWindow _window;
    private readonly BehaviorPlanner _planner;
    private readonly IMonotonicClock _clock;
    private readonly IDesktopSurfaceProvider _surfaces;
    private PlannedWalk? _walk;
    private ScreenPoint _walkOrigin;
    private TimeSpan _walkStartedAt;
    private TimeSpan _nextActionAt;
    private ScreenPoint _fallOrigin;
    private double _fallTargetY;
    private TimeSpan _fallStartedAt;
    private bool _disposed;

    public PetAnimationController(
        IAnimationPlayer player,
        IOverlayWindow window,
        BehaviorPlanner planner,
        IMonotonicClock clock,
        IDesktopSurfaceProvider surfaces)
    {
        _player = player ?? throw new ArgumentNullException(nameof(player));
        _window = window ?? throw new ArgumentNullException(nameof(window));
        _planner = planner ?? throw new ArgumentNullException(nameof(planner));
        _clock = clock ?? throw new ArgumentNullException(nameof(clock));
        _surfaces = surfaces ?? throw new ArgumentNullException(nameof(surfaces));
        _player.PlaybackCompleted += OnPlaybackCompleted;
    }

    public PetRuntimeState State { get; private set; }

    public void Start()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        SnapToSurface();
        EnterIdle(_clock.Elapsed);
    }

    public void Tick()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        var now = _clock.Elapsed;
        if (State == PetRuntimeState.Idle && now >= _nextActionAt)
        {
            var surface = CurrentSurface();
            var standingPosition = new ScreenPoint(_window.Position.X, surface.Top - _window.Size.Height);
            _window.MoveTo(standingPosition);
            var movementArea = new ScreenArea(
                new(surface.Left, _window.WorkArea.Origin.Y),
                new(surface.Bounds.Size.Width, _window.WorkArea.Size.Height));
            _walk = _planner.PlanWalk(standingPosition, _window.Size, movementArea, _player.Facing);
            _player.SetFacing(_walk.Facing);
            State = PetRuntimeState.Turning;
            _player.Play(PetActionClips.Turn);
        }
        else if (State == PetRuntimeState.Walking)
        {
            AdvanceWalk(now);
        }
        else if (State == PetRuntimeState.Falling)
        {
            AdvanceFall(now);
        }
    }

    public void ReactToClick()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        _walk = null;
        State = PetRuntimeState.Reacting;
        _player.Play(PetActionClips.Click);
    }

    public void BeginDrag()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        _walk = null;
        State = PetRuntimeState.Dragging;
        _player.Play(PetActionClips.DragDangle);
    }

    public void CompleteDrag()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        if (State != PetRuntimeState.Dragging) return;
        _fallOrigin = _window.Position;
        _fallTargetY = Math.Max(_fallOrigin.Y, CurrentSurface().Top - _window.Size.Height);
        _fallStartedAt = _clock.Elapsed;
        if (_fallTargetY - _fallOrigin.Y <= 1)
        {
            StartLanding();
            return;
        }
        State = PetRuntimeState.Falling;
        _player.Play(PetActionClips.Fall);
    }

    public void CancelDrag()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        if (State is PetRuntimeState.Dragging or PetRuntimeState.Falling or PetRuntimeState.Landing)
        {
            EnterIdle(_clock.Elapsed);
        }
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        _player.PlaybackCompleted -= OnPlaybackCompleted;
        _player.Stop();
    }

    private void StartWalk(TimeSpan now)
    {
        if (_walk is null)
        {
            EnterIdle(now);
            return;
        }
        _walkOrigin = _window.Position;
        _walkStartedAt = now;
        State = PetRuntimeState.Walking;
        _player.Play(PetActionClips.Walk);
    }

    private void AdvanceWalk(TimeSpan now)
    {
        var walk = _walk;
        if (walk is null)
        {
            EnterIdle(now);
            return;
        }
        var distance = walk.TargetX - _walkOrigin.X;
        var durationSeconds = Math.Abs(distance) / walk.SpeedPixelsPerSecond;
        var elapsedSeconds = Math.Max(0, (now - _walkStartedAt).TotalSeconds);
        var progress = durationSeconds <= 0 ? 1 : Math.Min(1, elapsedSeconds / durationSeconds);
        _window.MoveTo(new(_walkOrigin.X + (distance * progress), _walkOrigin.Y));
        if (progress >= 1)
        {
            _walk = null;
            State = PetRuntimeState.TurningToIdle;
            _player.Play(PetActionClips.TurnToIdle);
        }
    }

    private void AdvanceFall(TimeSpan now)
    {
        const double gravity = 1200;
        var elapsed = Math.Max(0, (now - _fallStartedAt).TotalSeconds);
        var nextY = Math.Min(_fallTargetY, _fallOrigin.Y + (0.5 * gravity * elapsed * elapsed));
        _window.MoveTo(new(_fallOrigin.X, nextY));
        if (nextY >= _fallTargetY)
        {
            StartLanding();
        }
    }

    private void StartLanding()
    {
        _window.MoveTo(new(_window.Position.X, _fallTargetY));
        State = PetRuntimeState.Landing;
        _player.Play(PetActionClips.DropLand);
    }

    private DesktopSurface CurrentSurface()
    {
        var position = _window.Position;
        return _surfaces.FindFirstBelow(
            position.X + (_window.Size.Width / 2d),
            position.Y + _window.Size.Height - 8,
            _window.WorkArea);
    }

    private void SnapToSurface()
    {
        var surface = CurrentSurface();
        _window.MoveTo(new(_window.Position.X, surface.Top - _window.Size.Height));
    }

    private void EnterIdle(TimeSpan now)
    {
        State = PetRuntimeState.Idle;
        _nextActionAt = now + _planner.NextIdleDelay();
        _player.Play(PetActionClips.Idle);
    }

    private void OnPlaybackCompleted(object? sender, AnimationPlaybackCompletedEventArgs e)
    {
        if (_disposed) return;
        if (State == PetRuntimeState.Turning && e.ClipId == PetActionClips.Turn)
        {
            StartWalk(_clock.Elapsed);
        }
        else if (State == PetRuntimeState.Reacting && e.ClipId == PetActionClips.Click)
        {
            EnterIdle(_clock.Elapsed);
        }
        else if (State == PetRuntimeState.TurningToIdle && e.ClipId == PetActionClips.TurnToIdle)
        {
            EnterIdle(_clock.Elapsed);
        }
        else if (State == PetRuntimeState.Landing && e.ClipId == PetActionClips.DropLand)
        {
            EnterIdle(_clock.Elapsed);
        }
    }
}

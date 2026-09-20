using Bolttagu.Contracts;
using Bolttagu.Core;

namespace Bolttagu.Runtime;

public enum PetRuntimeState
{
    Launching,
    Idle,
    Turning,
    Walking,
    TurningToIdle,
    Reacting,
    Huffing,
    DraggingIdle,
    DraggingPulled,
    Falling,
    Landing,
    Exiting,
}

public sealed class PetAnimationController : IDisposable
{
    private static readonly TimeSpan DragSettleDuration = TimeSpan.FromMilliseconds(180);
    private static readonly TimeSpan ExitTimeout = TimeSpan.FromMilliseconds(1500);
    private const double DragPulledThreshold = 80;
    private const double DragHeldThreshold = 40;
    private const double DragFilterSeconds = 0.08;
    private readonly IAnimationPlayer _player;
    private readonly IOverlayWindow _window;
    private readonly BehaviorPlanner _planner;
    private readonly IMonotonicClock _clock;
    private readonly IDesktopSurfaceProvider _surfaces;
    private PlannedWalk? _walk;
    private ScreenPoint _walkOrigin;
    private TimeSpan _walkStartedAt;
    private TimeSpan _nextActionAt;
    private DesktopSurface? _support;
    private ScreenPoint _dragLastPosition;
    private TimeSpan _dragLastSampleAt;
    private TimeSpan? _dragSettledAt;
    private double _dragVelocityX;
    private double _dragVelocityY;
    private ScreenPoint _fallOrigin;
    private TimeSpan _fallStartedAt;
    private TimeSpan _exitDeadline;
    private bool _exitReadyRaised;
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
    public event EventHandler? ExitReady;

    public void Start()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        SnapToSurface();
        State = PetRuntimeState.Launching;
        _player.Play(PetActionClips.SpawnIn);
    }

    public void Tick()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        var now = _clock.Elapsed;
        if (State == PetRuntimeState.Exiting)
        {
            if (now >= _exitDeadline) SignalExitReady();
            return;
        }
        if (IsGrounded(State) && !RefreshSupport())
        {
            StartFalling(now);
            return;
        }
        if (State == PetRuntimeState.Idle && now >= _nextActionAt)
        {
            var surface = _support ?? CurrentSurface();
            var standingPosition = new ScreenPoint(_window.Position.X, surface.Top - _window.Size.Height);
            _window.MoveTo(standingPosition);
            _walk = _planner.PlanWalk(standingPosition, _window.Size, _window.WorkArea, _player.Facing);
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
        else if (State is PetRuntimeState.DraggingIdle or PetRuntimeState.DraggingPulled)
        {
            AdvanceDrag(now);
        }
    }

    public void ReactToClick()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        if (State == PetRuntimeState.Exiting) return;
        _walk = null;
        State = PetRuntimeState.Reacting;
        _player.Play(PetActionClips.Click);
    }

    public void BeginDrag()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        if (State == PetRuntimeState.Exiting) return;
        _walk = null;
        _dragLastPosition = _window.Position;
        _dragLastSampleAt = _clock.Elapsed;
        _dragSettledAt = null;
        _dragVelocityX = 0;
        _dragVelocityY = 0;
        State = PetRuntimeState.DraggingIdle;
        _player.Play(PetActionClips.DragHeldIdle);
    }

    public void CompleteDrag()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        if (State is not (PetRuntimeState.DraggingIdle or PetRuntimeState.DraggingPulled)) return;
        var position = _window.Position;
        var footY = position.Y + _window.Size.Height;
        var destination = CurrentSurface();
        if (Math.Abs(destination.Top - footY) <= 3)
        {
            StartLanding(destination);
            return;
        }
        StartFalling(_clock.Elapsed);
    }

    public void CancelDrag()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        if (State is PetRuntimeState.DraggingIdle or PetRuntimeState.DraggingPulled or
            PetRuntimeState.Falling or PetRuntimeState.Landing)
        {
            EnterIdle(_clock.Elapsed);
        }
    }

    public void RequestExit()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        if (State == PetRuntimeState.Exiting || _exitReadyRaised) return;
        _walk = null;
        State = PetRuntimeState.Exiting;
        _exitDeadline = _clock.Elapsed + ExitTimeout;
        _player.Play(PetActionClips.DespawnOut);
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

    private void AdvanceDrag(TimeSpan now)
    {
        var position = _window.Position;
        var elapsedSeconds = (now - _dragLastSampleAt).TotalSeconds;
        if (elapsedSeconds <= 0) return;

        var instantX = (position.X - _dragLastPosition.X) / elapsedSeconds;
        var instantY = (position.Y - _dragLastPosition.Y) / elapsedSeconds;
        var alpha = 1 - Math.Exp(-elapsedSeconds / DragFilterSeconds);
        _dragVelocityX += alpha * (instantX - _dragVelocityX);
        _dragVelocityY += alpha * (instantY - _dragVelocityY);
        _dragLastPosition = position;
        _dragLastSampleAt = now;

        var speed = Math.Sqrt((_dragVelocityX * _dragVelocityX) + (_dragVelocityY * _dragVelocityY));
        if (speed >= DragPulledThreshold)
        {
            _dragSettledAt = null;
            if (Math.Abs(_dragVelocityX) >= 10)
            {
                _player.SetFacing(_dragVelocityX >= 0 ? FacingDirection.Right : FacingDirection.Left);
            }
            if (State != PetRuntimeState.DraggingPulled)
            {
                State = PetRuntimeState.DraggingPulled;
                _player.Play(PetActionClips.DragPulled);
            }
            return;
        }

        if (speed > DragHeldThreshold)
        {
            _dragSettledAt = null;
            return;
        }

        _dragSettledAt ??= now;
        if (State == PetRuntimeState.DraggingPulled && now - _dragSettledAt >= DragSettleDuration)
        {
            State = PetRuntimeState.DraggingIdle;
            _player.Play(PetActionClips.DragHeldIdle);
        }
    }

    private void AdvanceFall(TimeSpan now)
    {
        const double gravity = 1200;
        var destination = FindLandingSurface();
        var targetY = Math.Max(_window.Position.Y, destination.Top - _window.Size.Height);
        var elapsed = Math.Max(0, (now - _fallStartedAt).TotalSeconds);
        var nextY = Math.Min(targetY, _fallOrigin.Y + (0.5 * gravity * elapsed * elapsed));
        _window.MoveTo(new(_fallOrigin.X, nextY));
        if (nextY >= targetY)
        {
            StartLanding(destination);
        }
    }

    private void StartFalling(TimeSpan now)
    {
        _walk = null;
        _support = null;
        _fallOrigin = _window.Position;
        _fallStartedAt = now;
        State = PetRuntimeState.Falling;
        _player.Play(PetActionClips.Fall);
    }

    private void StartLanding(DesktopSurface surface)
    {
        _support = surface;
        _window.MoveTo(new(_window.Position.X, surface.Top - _window.Size.Height));
        State = PetRuntimeState.Landing;
        _player.Play(PetActionClips.DropLand);
    }

    private DesktopSurface FindLandingSurface()
    {
        var position = _window.Position;
        return _surfaces.FindFirstBelow(
            position.X + (_window.Size.Width / 2d),
            position.Y + _window.Size.Height + 4,
            _window.WorkArea);
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
        _support = surface;
        _window.MoveTo(new(_window.Position.X, surface.Top - _window.Size.Height));
    }

    private bool RefreshSupport()
    {
        if (_support is not { } expected) return false;
        var position = _window.Position;
        var valid = _surfaces.TryRefreshSupport(
            expected,
            position.X + (_window.Size.Width / 2d),
            position.Y + _window.Size.Height,
            _window.WorkArea,
            out var current);
        if (valid) _support = current;
        return valid;
    }

    private static bool IsGrounded(PetRuntimeState state) => state is
        PetRuntimeState.Idle or
        PetRuntimeState.Turning or
        PetRuntimeState.Walking or
        PetRuntimeState.TurningToIdle or
        PetRuntimeState.Reacting or
        PetRuntimeState.Huffing or
        PetRuntimeState.Landing;

    private void EnterIdle(TimeSpan now)
    {
        State = PetRuntimeState.Idle;
        _nextActionAt = now + _planner.NextIdleDelay();
        _player.Play(PetActionClips.Idle);
    }

    private void SignalExitReady()
    {
        if (_exitReadyRaised) return;
        _exitReadyRaised = true;
        ExitReady?.Invoke(this, EventArgs.Empty);
    }

    private void OnPlaybackCompleted(object? sender, AnimationPlaybackCompletedEventArgs e)
    {
        if (_disposed) return;
        if (State == PetRuntimeState.Launching && e.ClipId == PetActionClips.SpawnIn)
        {
            EnterIdle(_clock.Elapsed);
        }
        else if (State == PetRuntimeState.Exiting && e.ClipId == PetActionClips.DespawnOut)
        {
            SignalExitReady();
        }
        else if (State == PetRuntimeState.Turning && e.ClipId == PetActionClips.Turn)
        {
            StartWalk(_clock.Elapsed);
        }
        else if (State == PetRuntimeState.Reacting && e.ClipId == PetActionClips.Click)
        {
            State = PetRuntimeState.Huffing;
            _player.Play(PetActionClips.ClickHuff);
        }
        else if (State == PetRuntimeState.Huffing && e.ClipId == PetActionClips.ClickHuff)
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

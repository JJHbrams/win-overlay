using Bolttagu.Contracts;
using Bolttagu.Core;

namespace Bolttagu.Runtime;

public enum PetRuntimeState
{
    Launching,
    Idle,
    Turning,
    Walking,
    Running,
    TurningToIdle,
    Reacting,
    Huffing,
    DraggingIdle,
    DraggingPulled,
    Falling,
    Landing,
    Recovering,
    Dozing,
    RopeClimbPreparing,
    RopeClimbing,
    FreeClimbPreparing,
    FreeClimbing,
    RopeDescendingPreparing,
    RopeDescending,
    FreeDescendingPreparing,
    FreeDescending,
    ClimbFinishing,
    Exiting,
}

public sealed class PetAnimationController : IDisposable
{
    private static readonly TimeSpan DragSettleDuration = TimeSpan.FromMilliseconds(180);
    private static readonly TimeSpan ExitTimeout = TimeSpan.FromMilliseconds(1500);
    private const double DragPulledThreshold = 80;
    private const double DragHeldThreshold = 40;
    private const double DragFilterSeconds = 0.08;
    private const double DizzyRecoveryFallHeight = 260;
    private readonly IAnimationPlayer _player;
    private readonly IOverlayWindow _window;
    private readonly BehaviorPlanner _planner;
    private readonly IMonotonicClock _clock;
    private readonly IDesktopSurfaceProvider _surfaces;
    private readonly bool _startWithFall;
    private readonly BehaviorSequenceRunner _sequence;
    private PlannedWalk? _walk;
    private PlannedWalk? _walkInterruptedByFall;
    private bool _interruptedWalkWasRunning;
    private bool _isRunning;
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
    private DesktopSurface? _climbAnchor;
    private ScreenPoint _climbOrigin;
    private double _climbTargetY;
    private double _climbFixedX;
    private TimeSpan _climbStartedAt;
    private double _climbSpeedPixelsPerSecond;
    private bool _climbIsRope;
    private int _climbDirection = -1;
    private RopeEdgeEncounter? _lastRopeEdgeEncounter;
    private bool _exitReadyRaised;
    private bool _disposed;

    public PetAnimationController(
        IAnimationPlayer player,
        IOverlayWindow window,
        BehaviorPlanner planner,
        IMonotonicClock clock,
        IDesktopSurfaceProvider surfaces,
        bool startWithFall = false)
    {
        _player = player ?? throw new ArgumentNullException(nameof(player));
        _window = window ?? throw new ArgumentNullException(nameof(window));
        _planner = planner ?? throw new ArgumentNullException(nameof(planner));
        _clock = clock ?? throw new ArgumentNullException(nameof(clock));
        _surfaces = surfaces ?? throw new ArgumentNullException(nameof(surfaces));
        _startWithFall = startWithFall;
        _sequence = new BehaviorSequenceRunner(_player);
        _sequence.Completed += OnSequenceCompleted;
        _sequence.StepStarted += OnSequenceStepStarted;
        _player.PlaybackCompleted += OnPlaybackCompleted;
    }

    public PetRuntimeState State { get; private set; }
    public bool HasActiveBehavior => _sequence.IsRunning;
    public PetPose Pose => _sequence.IsRunning ? _sequence.Pose : State switch
    {
        PetRuntimeState.DraggingIdle or PetRuntimeState.DraggingPulled => PetPose.Hanging,
        PetRuntimeState.Falling => PetPose.Airborne,
        PetRuntimeState.Landing => PetPose.GroundedCompressed,
        PetRuntimeState.RopeClimbPreparing or PetRuntimeState.RopeClimbing or
            PetRuntimeState.FreeClimbPreparing or PetRuntimeState.FreeClimbing or
            PetRuntimeState.RopeDescendingPreparing or PetRuntimeState.RopeDescending or
            PetRuntimeState.FreeDescendingPreparing or PetRuntimeState.FreeDescending or
            PetRuntimeState.ClimbFinishing => PetPose.Climbing,
        PetRuntimeState.Dozing => PetPose.Seated,
        _ => PetPose.Standing,
    };
    public event EventHandler? ExitReady;

    public void Start()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        if (_startWithFall)
        {
            var workArea = _window.WorkArea;
            _window.MoveTo(new(_window.Position.X, workArea.Origin.Y));
        }
        else
        {
            SnapToSurface();
        }
        State = PetRuntimeState.Launching;
        _player.Play(PetActionClips.SpawnIn);
    }

    public void Tick()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        var now = _clock.Elapsed;
        _planner.AdvanceMood(now, _sequence.Current?.Id == BehaviorDefinitions.SitDoze
            ? PetActivity.Dozing
            : State switch
            {
                PetRuntimeState.Walking => PetActivity.Walking,
                PetRuntimeState.Running => PetActivity.Running,
                PetRuntimeState.RopeClimbing or PetRuntimeState.FreeClimbing or
                    PetRuntimeState.RopeDescending or PetRuntimeState.FreeDescending => PetActivity.Climbing,
                _ => PetActivity.Resting,
            });
        if (State == PetRuntimeState.Exiting)
        {
            if (now >= _exitDeadline) SignalExitReady();
            return;
        }
        if (IsGrounded(State) && !RefreshSupport())
        {
            // At a walking edge, the support can disappear in the same tick that
            // the leading edge reaches a climbable foreground window. Preserve the
            // previous support long enough to give that encounter its one chance.
            if (State is PetRuntimeState.Walking or PetRuntimeState.Running && TryStartRopeClimbBeforeFalling(now)) return;
            StartFalling(now);
            return;
        }
        if (_sequence.Tick(now)) return;
        if (State == PetRuntimeState.Idle && now >= _nextActionAt)
        {
            var behavior = _planner.ChooseAutonomousBehavior(now);
            if (behavior is null)
            {
                _nextActionAt = now + _planner.NextIdleDelay();
                return;
            }
            if (behavior.Id == BehaviorDefinitions.FreeClimb)
            {
                StartFreeClimb(now);
                return;
            }
            if (behavior.Id == BehaviorDefinitions.FreeDescend)
            {
                StartFreeDescend(now);
                return;
            }
            if (behavior.Id is not (BehaviorDefinitions.Walk or BehaviorDefinitions.Run))
            {
                StartAutonomousBehavior(behavior);
                return;
            }
            var surface = _support ?? CurrentSurface();
            var standingPosition = new ScreenPoint(_window.Position.X, surface.Top - _window.Size.Height);
            _window.MoveTo(standingPosition);
            _isRunning = behavior.Id == BehaviorDefinitions.Run;
            _walk = _isRunning
                ? _planner.PlanRun(standingPosition, _window.Size, _window.WorkArea, _player.Facing)
                : _planner.PlanWalk(standingPosition, _window.Size, _window.WorkArea, _player.Facing);
            _player.SetFacing(_walk.Facing);
            _sequence.Start(_isRunning
                ? BehaviorDefinitions.CreateRun(_walk.RequiresTurn)
                : BehaviorDefinitions.CreateWalk(_walk.RequiresTurn), now);
        }
        else if (State is PetRuntimeState.Walking or PetRuntimeState.Running)
        {
            AdvanceWalk(now);
        }
        else if (State == PetRuntimeState.Falling)
        {
            AdvanceFall(now);
        }
        else if (State is PetRuntimeState.RopeClimbPreparing or PetRuntimeState.RopeClimbing or
                 PetRuntimeState.FreeClimbPreparing or PetRuntimeState.FreeClimbing or
                 PetRuntimeState.RopeDescendingPreparing or PetRuntimeState.RopeDescending or
                 PetRuntimeState.FreeDescendingPreparing or PetRuntimeState.FreeDescending)
        {
            AdvanceClimb(now);
        }
        else if (State is PetRuntimeState.DraggingIdle or PetRuntimeState.DraggingPulled)
        {
            AdvanceDrag(now);
        }
    }

    public void ReactToClick()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        if (State == PetRuntimeState.Exiting || Pose is PetPose.Hanging or PetPose.Airborne or PetPose.GroundedCompressed) return;
        _planner.RecordUserInput(_clock.Elapsed);
        if (Pose == PetPose.Seated)
        {
            _sequence.Cancel();
            State = PetRuntimeState.Dozing;
            _player.Play(PetActionClips.DozeStartle);
            return;
        }
        if (Pose != PetPose.Standing) return;
        _walk = null;
        ClearClimb();
        _sequence.Cancel();
        State = PetRuntimeState.Reacting;
        _player.Play(PetActionClips.Click);
    }

    public void BeginDrag()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        if (State == PetRuntimeState.Exiting) return;
        _planner.RecordUserInput(_clock.Elapsed);
        _walk = null;
        ClearClimb();
        _sequence.Cancel();
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
        ClearClimb();
        _sequence.Cancel();
        State = PetRuntimeState.Exiting;
        _exitDeadline = _clock.Elapsed + ExitTimeout;
        _player.Play(PetActionClips.DespawnOut);
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        _player.PlaybackCompleted -= OnPlaybackCompleted;
        _sequence.Completed -= OnSequenceCompleted;
        _sequence.StepStarted -= OnSequenceStepStarted;
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
        _planner.RecordLocomotion(now);
        State = _isRunning ? PetRuntimeState.Running : PetRuntimeState.Walking;
        _player.Play(_isRunning ? PetActionClips.Run : PetActionClips.Walk);
    }

    private void AdvanceWalk(TimeSpan now)
    {
        var walk = _walk;
        if (walk is null)
        {
            EnterIdle(now);
            return;
        }
        var (nextPosition, progress) = GetWalkPosition(walk, now);
        var support = _support;
        if (support is { } descendSupport && TryStartRopeDescend(
                descendSupport, _window.Position, nextPosition, walk.Facing, now))
        {
            return;
        }
        if (support is { } currentSupport && TryStartRopeClimb(currentSupport, _window.Position, nextPosition, walk.Facing, now))
        {
            return;
        }
        _window.MoveTo(nextPosition);
        if (progress >= 1)
        {
            _walk = null;
            if (!_sequence.AdvanceExternal(now))
            {
                State = PetRuntimeState.TurningToIdle;
                _player.Play(PetActionClips.TurnToIdle);
            }
        }
    }

    private bool TryStartRopeClimbBeforeFalling(TimeSpan now)
    {
        var walk = _walk;
        var support = _support;
        if (walk is null || support is not { } currentSupport) return false;

        var (nextPosition, _) = GetWalkPosition(walk, now);
        return TryStartRopeDescend(currentSupport, _window.Position, nextPosition, walk.Facing, now) ||
            TryStartRopeClimb(currentSupport, _window.Position, nextPosition, walk.Facing, now);
    }

    private (ScreenPoint Position, double Progress) GetWalkPosition(PlannedWalk walk, TimeSpan now)
    {
        var distance = walk.TargetX - _walkOrigin.X;
        var durationSeconds = Math.Abs(distance) / walk.SpeedPixelsPerSecond;
        var elapsedSeconds = Math.Max(0, (now - _walkStartedAt).TotalSeconds);
        var progress = durationSeconds <= 0 ? 1 : Math.Min(1, elapsedSeconds / durationSeconds);
        return (new ScreenPoint(_walkOrigin.X + (distance * progress), _walkOrigin.Y), progress);
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
        _walkInterruptedByFall = State is PetRuntimeState.Walking or PetRuntimeState.Running
            ? _walk
            : null;
        _interruptedWalkWasRunning = State == PetRuntimeState.Running;
        _walk = null;
        ClearClimb();
        _sequence.Cancel();
        _support = null;
        _fallOrigin = _window.Position;
        _fallStartedAt = now;
        State = PetRuntimeState.Falling;
        _player.Play(PetActionClips.Fall);
    }

    private void StartLanding(DesktopSurface surface)
    {
        _support = surface;
        var landingY = surface.Top - _window.Size.Height;
        _window.MoveTo(new(_window.Position.X, landingY));
        if (landingY - _fallOrigin.Y >= DizzyRecoveryFallHeight)
        {
            _walkInterruptedByFall = null;
            State = PetRuntimeState.Recovering;
            _player.Play(PetActionClips.LandRecover);
        }
        else
        {
            State = PetRuntimeState.Landing;
            _player.Play(PetActionClips.DropLand);
        }
    }

    private bool TryStartRopeDescend(
        DesktopSurface support,
        ScreenPoint currentPosition,
        ScreenPoint nextPosition,
        FacingDirection facing,
        TimeSpan now)
    {
        var currentLeadingX = facing == FacingDirection.Right
            ? currentPosition.X + _window.Size.Width
            : currentPosition.X;
        var nextLeadingX = facing == FacingDirection.Right
            ? nextPosition.X + _window.Size.Width
            : nextPosition.X;
        if (!_surfaces.TryFindRopeDescendObstacle(
                support,
                currentPosition.Y + _window.Size.Height,
                currentLeadingX,
                nextLeadingX,
                facing,
                _window.Size,
                _window.WorkArea,
                out var obstacle)) return false;

        _walk = null;
        _sequence.Cancel();
        _climbAnchor = obstacle;
        _climbIsRope = true;
        _climbDirection = 1;
        _climbFixedX = facing == FacingDirection.Right ? obstacle.Left - _window.Size.Width : obstacle.Right;
        _climbOrigin = new(_climbFixedX, currentPosition.Y);
        _climbTargetY = Math.Min(
            _window.WorkArea.Bottom - _window.Size.Height,
            obstacle.Bottom - _window.Size.Height);
        _climbStartedAt = now;
        _climbSpeedPixelsPerSecond = 84;
        _window.MoveTo(_climbOrigin);
        State = PetRuntimeState.RopeDescendingPreparing;
        _player.Play(PetActionClips.RopeClimbDownPrepare);
        return true;
    }

    private bool TryStartRopeClimb(
        DesktopSurface support,
        ScreenPoint currentPosition,
        ScreenPoint nextPosition,
        FacingDirection facing,
        TimeSpan now)
    {
        var currentLeadingX = facing == FacingDirection.Right
            ? currentPosition.X + _window.Size.Width
            : currentPosition.X;
        var nextLeadingX = facing == FacingDirection.Right
            ? nextPosition.X + _window.Size.Width
            : nextPosition.X;
        if (!_surfaces.TryFindRopeClimbObstacle(
                support,
                currentPosition.Y + _window.Size.Height,
                currentLeadingX,
                nextLeadingX,
                facing,
                _window.Size,
                _window.WorkArea,
                out var obstacle))
        {
            _lastRopeEdgeEncounter = null;
            return false;
        }

        var encounter = new RopeEdgeEncounter(obstacle.Id, facing);
        if (_lastRopeEdgeEncounter == encounter) return false;
        _lastRopeEdgeEncounter = encounter;
        if (obstacle.Kind != DesktopSurfaceKind.VerticalLine && !_planner.ShouldStartRopeClimb()) return false;

        _walk = null;
        _sequence.Cancel();
        _climbAnchor = obstacle;
        _climbIsRope = true;
        _climbDirection = -1;
        _climbFixedX = facing == FacingDirection.Right ? obstacle.Left - _window.Size.Width : obstacle.Right;
        _climbOrigin = new ScreenPoint(_climbFixedX, currentPosition.Y);
        _climbTargetY = Math.Max(
            _window.WorkArea.Origin.Y,
            obstacle.Top - _window.Size.Height);
        _climbStartedAt = now;
        _climbSpeedPixelsPerSecond = 84;
        _window.MoveTo(_climbOrigin);
        State = PetRuntimeState.RopeClimbPreparing;
        _player.Play(PetActionClips.RopeClimbPrepare);
        return true;
    }

    private void StartFreeClimb(TimeSpan now)
    {
        var plan = _planner.PlanFreeClimb(_window.Size);
        _walk = null;
        _sequence.Cancel();
        _climbAnchor = null;
        _climbIsRope = false;
        _climbDirection = -1;
        _climbFixedX = _window.Position.X;
        _climbOrigin = _window.Position;
        _climbTargetY = Math.Max(
            _window.WorkArea.Origin.Y,
            _climbOrigin.Y - plan.TargetHeight);
        _climbStartedAt = now;
        _climbSpeedPixelsPerSecond = plan.SpeedPixelsPerSecond;
        State = PetRuntimeState.FreeClimbPreparing;
        _player.Play(PetActionClips.FreeClimbPrepare);
    }

    private void StartFreeDescend(TimeSpan now)
    {
        var plan = _planner.PlanFreeDescend(_window.Size);
        _walk = null;
        _sequence.Cancel();
        _climbAnchor = null;
        _climbIsRope = false;
        _climbDirection = 1;
        _climbFixedX = _window.Position.X;
        _climbOrigin = _window.Position;
        _climbTargetY = Math.Min(
            _window.WorkArea.Bottom - _window.Size.Height,
            _climbOrigin.Y + plan.TargetHeight);
        _climbStartedAt = now;
        _climbSpeedPixelsPerSecond = plan.SpeedPixelsPerSecond;
        State = PetRuntimeState.FreeDescendingPreparing;
        _player.Play(PetActionClips.FreeClimbDownPrepare);
    }

    private void AdvanceClimb(TimeSpan now)
    {
        if (_climbIsRope)
        {
            var contactEdgeX = _player.Facing == FacingDirection.Right
                ? _climbFixedX + _window.Size.Width
                : _climbFixedX;
            if (_climbAnchor is not { } climbAnchor || !_surfaces.TryRefreshClimbAnchor(climbAnchor, contactEdgeX, _window.WorkArea, out var refreshed))
            {
                StartFalling(now);
                return;
            }
            _climbAnchor = refreshed;
        }

        if (State is PetRuntimeState.RopeClimbPreparing or PetRuntimeState.FreeClimbPreparing or
            PetRuntimeState.RopeDescendingPreparing or PetRuntimeState.FreeDescendingPreparing) return;

        var elapsedSeconds = Math.Max(0, (now - _climbStartedAt).TotalSeconds);
        var nextY = _climbDirection < 0
            ? Math.Max(_climbTargetY, _climbOrigin.Y - (_climbSpeedPixelsPerSecond * elapsedSeconds))
            : Math.Min(_climbTargetY, _climbOrigin.Y + (_climbSpeedPixelsPerSecond * elapsedSeconds));
        var fromFootY = _window.Position.Y + _window.Size.Height;
        if (_climbDirection > 0)
        {
            var nextFootY = nextY + _window.Size.Height;
            var intercept = _surfaces.FindDescendIntercept(
                _climbFixedX + (_window.Size.Width / 2d), fromFootY, nextFootY, _window.WorkArea);
            if (intercept is { } surface)
            {
                StartClimbFinish(surface);
                return;
            }
        }
        else if (!_climbIsRope)
        {
            var nextFootY = nextY + _window.Size.Height;
            // A second estimate of the takeoff platform must not finish a climb
            // before the pet has visibly cleared that platform.
            const double takeoffClearance = 24;
            var probeFromFootY = Math.Min(
                fromFootY,
                _climbOrigin.Y + _window.Size.Height - takeoffClearance + 3);
            var intercept = _surfaces.FindClimbIntercept(
                _climbFixedX + (_window.Size.Width / 2d), probeFromFootY, nextFootY, _window.WorkArea);
            if (intercept is { } surface)
            {
                StartClimbFinish(surface);
                return;
            }
        }

        _window.MoveTo(new(_climbFixedX, nextY));
        var reachedTarget = _climbDirection < 0
            ? nextY <= _climbTargetY
            : nextY >= _climbTargetY;
        if (!reachedTarget) return;
        if (_climbDirection > 0)
        {
            StartFalling(now);
            return;
        }
        if (_climbIsRope && _climbAnchor is { } anchor)
        {
            if (anchor.Kind == DesktopSurfaceKind.VerticalLine)
            {
                var topSupport = _surfaces.FindClimbIntercept(
                    (anchor.Left + anchor.Right) / 2d,
                    fromFootY,
                    anchor.Top - 3,
                    _window.WorkArea);
                if (topSupport is { } visualTop)
                {
                    StartClimbFinish(visualTop);
                    return;
                }
                StartFalling(now);
                return;
            }
            StartClimbFinish(anchor);
            return;
        }
        StartFalling(now);
    }

    private void StartClimbFinish(DesktopSurface surface)
    {
        _support = surface;
        var halfWidth = _window.Size.Width / 2d;
        var centerX = Math.Clamp(
            _climbFixedX + halfWidth,
            surface.Left + 2,
            Math.Max(surface.Left + 2, surface.Right - 2));
        var landingX = Math.Clamp(
            centerX - halfWidth,
            _window.WorkArea.Origin.X,
            Math.Max(_window.WorkArea.Origin.X, _window.WorkArea.Right - _window.Size.Width));
        _window.MoveTo(new(landingX, surface.Top - _window.Size.Height));
        State = PetRuntimeState.ClimbFinishing;
        _player.Play((_climbIsRope, _climbDirection) switch
        {
            (true, > 0) => PetActionClips.RopeClimbDownFinish,
            (false, > 0) => PetActionClips.FreeClimbDownFinish,
            (true, _) => PetActionClips.RopeClimbFinish,
            _ => PetActionClips.FreeClimbFinish,
        });
    }

    private void ClearClimb()
    {
        _climbAnchor = null;
        _climbOrigin = default;
        _climbTargetY = 0;
        _climbFixedX = 0;
        _climbStartedAt = default;
        _climbSpeedPixelsPerSecond = 0;
        _climbIsRope = false;
        _climbDirection = -1;
        _lastRopeEdgeEncounter = null;
    }

    private readonly record struct RopeEdgeEncounter(long WindowId, FacingDirection ApproachedFrom);

    private DesktopSurface FindLandingSurface()
    {
        var position = _window.Position;
        return _surfaces.FindFirstBelow(
            position.X + (_window.Size.Width / 2d),
            position.Y + _window.Size.Height - 4,
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
        PetRuntimeState.Running or
        PetRuntimeState.TurningToIdle or
        PetRuntimeState.Reacting or
        PetRuntimeState.Huffing or
        PetRuntimeState.Landing or
        PetRuntimeState.Recovering or
        PetRuntimeState.ClimbFinishing or
        PetRuntimeState.Dozing;

    private void EnterIdle(TimeSpan now)
    {
        _walkInterruptedByFall = null;
        ClearClimb();
        State = PetRuntimeState.Idle;
        _planner.EnterIdleHub(now);
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
        if (_sequence.HandleCompletion(e.ClipId, _clock.Elapsed)) return;
        if (State == PetRuntimeState.Launching && e.ClipId == PetActionClips.SpawnIn)
        {
            if (_startWithFall) StartFalling(_clock.Elapsed);
            else EnterIdle(_clock.Elapsed);
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
            var interrupted = _walkInterruptedByFall;
            _walkInterruptedByFall = null;
            if (interrupted is { } walk && Math.Abs(walk.TargetX - _window.Position.X) > 1)
            {
                _walk = walk;
                _isRunning = _interruptedWalkWasRunning;
                _player.SetFacing(walk.Facing);
                _sequence.Start(_isRunning
                    ? BehaviorDefinitions.CreateRun(false)
                    : BehaviorDefinitions.CreateWalk(false), _clock.Elapsed);
            }
            else EnterIdle(_clock.Elapsed);
        }
        else if (State == PetRuntimeState.Recovering && e.ClipId == PetActionClips.LandRecover)
        {
            EnterIdle(_clock.Elapsed);
        }
        else if (State == PetRuntimeState.RopeClimbPreparing && e.ClipId == PetActionClips.RopeClimbPrepare)
        {
            State = PetRuntimeState.RopeClimbing;
            _climbStartedAt = _clock.Elapsed;
            _player.Play(PetActionClips.RopeClimbLoop);
        }
        else if (State == PetRuntimeState.FreeClimbPreparing && e.ClipId == PetActionClips.FreeClimbPrepare)
        {
            State = PetRuntimeState.FreeClimbing;
            _climbStartedAt = _clock.Elapsed;
            _player.Play(PetActionClips.FreeClimbLoop);
        }
        else if (State == PetRuntimeState.RopeDescendingPreparing && e.ClipId == PetActionClips.RopeClimbDownPrepare)
        {
            State = PetRuntimeState.RopeDescending;
            _climbStartedAt = _clock.Elapsed;
            _player.Play(PetActionClips.RopeClimbDownLoop);
        }
        else if (State == PetRuntimeState.FreeDescendingPreparing && e.ClipId == PetActionClips.FreeClimbDownPrepare)
        {
            State = PetRuntimeState.FreeDescending;
            _climbStartedAt = _clock.Elapsed;
            _player.Play(PetActionClips.FreeClimbDownLoop);
        }
        else if (State == PetRuntimeState.ClimbFinishing &&
                 e.ClipId is PetActionClips.RopeClimbFinish or PetActionClips.FreeClimbFinish or
                     PetActionClips.RopeClimbDownFinish or PetActionClips.FreeClimbDownFinish)
        {
            EnterIdle(_clock.Elapsed);
        }
        else if (State == PetRuntimeState.Dozing && e.ClipId == PetActionClips.DozeStartle)
        {
            _player.Play(PetActionClips.StandUp);
        }
        else if (State == PetRuntimeState.Dozing && e.ClipId == PetActionClips.StandUp)
        {
            EnterIdle(_clock.Elapsed);
        }
    }

    public bool StartAutonomousBehavior(BehaviorDefinition definition)
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        if (State != PetRuntimeState.Idle || definition.InterruptPolicy != BehaviorInterruptPolicy.AutonomousOnly) return false;
        if (definition.Id == BehaviorDefinitions.FreeClimb)
        {
            StartFreeClimb(_clock.Elapsed);
            return true;
        }
        if (definition.Id == BehaviorDefinitions.FreeDescend)
        {
            StartFreeDescend(_clock.Elapsed);
            return true;
        }
        if (definition.Id is BehaviorDefinitions.Walk or BehaviorDefinitions.Run)
        {
            var surface = _support ?? CurrentSurface();
            var standingPosition = new ScreenPoint(_window.Position.X, surface.Top - _window.Size.Height);
            _window.MoveTo(standingPosition);
            _isRunning = definition.Id == BehaviorDefinitions.Run;
            _walk = _isRunning
                ? _planner.PlanRun(standingPosition, _window.Size, _window.WorkArea, _player.Facing)
                : _planner.PlanWalk(standingPosition, _window.Size, _window.WorkArea, _player.Facing);
            _player.SetFacing(_walk.Facing);
            _sequence.Start(_isRunning
                ? BehaviorDefinitions.CreateRun(_walk.RequiresTurn)
                : BehaviorDefinitions.CreateWalk(_walk.RequiresTurn), _clock.Elapsed);
            return true;
        }
        _walk = null;
        _sequence.Start(definition, _clock.Elapsed);
        State = definition.ExitPose == PetPose.Seated ? PetRuntimeState.Dozing : PetRuntimeState.Reacting;
        return true;
    }

    private void OnSequenceCompleted(object? sender, BehaviorDefinition definition)
    {
        if (_disposed) return;
        EnterIdle(_clock.Elapsed);
    }

    private void OnSequenceStepStarted(object? sender, string clipId)
    {
        if (_sequence.Current?.Id is not (BehaviorDefinitions.Walk or BehaviorDefinitions.Run)) return;
        if (clipId == PetActionClips.Turn) State = PetRuntimeState.Turning;
        else if (clipId is PetActionClips.Walk or PetActionClips.Run)
        {
            _isRunning = clipId == PetActionClips.Run;
            _walkOrigin = _window.Position;
            _walkStartedAt = _clock.Elapsed;
            _planner.RecordLocomotion(_walkStartedAt);
            State = _isRunning ? PetRuntimeState.Running : PetRuntimeState.Walking;
        }
        else if (clipId == PetActionClips.TurnToIdle) State = PetRuntimeState.TurningToIdle;
    }

}

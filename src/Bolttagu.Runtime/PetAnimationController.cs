using Bolttagu.Contracts;
using Bolttagu.Core;

namespace Bolttagu.Runtime;

public enum PetRuntimeState { Idle, Turning, Walking, Reacting }

public sealed class PetAnimationController : IDisposable
{
    private readonly IAnimationPlayer _player;
    private readonly IOverlayWindow _window;
    private readonly BehaviorPlanner _planner;
    private readonly IMonotonicClock _clock;
    private PlannedWalk? _walk;
    private ScreenPoint _walkOrigin;
    private TimeSpan _walkStartedAt;
    private TimeSpan _nextActionAt;
    private bool _disposed;

    public PetAnimationController(
        IAnimationPlayer player,
        IOverlayWindow window,
        BehaviorPlanner planner,
        IMonotonicClock clock)
    {
        _player = player ?? throw new ArgumentNullException(nameof(player));
        _window = window ?? throw new ArgumentNullException(nameof(window));
        _planner = planner ?? throw new ArgumentNullException(nameof(planner));
        _clock = clock ?? throw new ArgumentNullException(nameof(clock));
        _player.PlaybackCompleted += OnPlaybackCompleted;
    }

    public PetRuntimeState State { get; private set; }

    public void Start()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        EnterIdle(_clock.Elapsed);
    }

    public void Tick()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        var now = _clock.Elapsed;
        if (State == PetRuntimeState.Idle && now >= _nextActionAt)
        {
            _walk = _planner.PlanWalk(_window.Position, _window.Size, _window.WorkArea, _player.Facing);
            _player.SetFacing(_walk.Facing);
            if (_walk.RequiresTurn)
            {
                State = PetRuntimeState.Turning;
                _player.Play(PetActionClips.Turn);
            }
            else
            {
                StartWalk(now);
            }
        }
        else if (State == PetRuntimeState.Walking)
        {
            AdvanceWalk(now);
        }
    }

    public void ReactToClick()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        _walk = null;
        State = PetRuntimeState.Reacting;
        _player.Play(PetActionClips.Click);
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
            EnterIdle(now);
        }
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
    }
}

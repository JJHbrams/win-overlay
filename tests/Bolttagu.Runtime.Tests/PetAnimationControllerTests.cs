using Bolttagu.Contracts;
using Bolttagu.Core;

namespace Bolttagu.Runtime.Tests;

[TestClass]
public sealed class PetAnimationControllerTests
{
    [TestMethod]
    public void ClickCompletion_ReturnsToIdle()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.Controller.Start();
        fixture.Controller.ReactToClick();
        fixture.Player.Complete(PetActionClips.Click);
        CollectionAssert.AreEqual(
            new[] { PetActionClips.Idle, PetActionClips.Click, PetActionClips.Idle },
            fixture.Player.PlayedClips.ToArray());
    }

    [TestMethod]
    public void ScheduledTurn_CompletesIntoWalkAndMovesWindow()
    {
        using var fixture = new Fixture(2000, 1, 120, 2000);
        fixture.Controller.Start();
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(2);
        fixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.Walking, fixture.Controller.State);
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(3);
        fixture.Controller.Tick();
        Assert.IsGreaterThan(100, fixture.Window.Position.X);
        CollectionAssert.AreEqual(
            new[] { PetActionClips.Idle, PetActionClips.Walk },
            fixture.Player.PlayedClips.ToArray());
    }

    [TestMethod]
    public void ScheduledDirectionChange_PlaysTurnBeforeWalk()
    {
        using var fixture = new Fixture(2000, 0, 120, 2000);
        fixture.Controller.Start();
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(2);
        fixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.Turning, fixture.Controller.State);
        fixture.Player.Complete(PetActionClips.Turn);
        Assert.AreEqual(PetRuntimeState.Walking, fixture.Controller.State);
        CollectionAssert.AreEqual(
            new[] { PetActionClips.Idle, PetActionClips.Turn, PetActionClips.Walk },
            fixture.Player.PlayedClips.ToArray());
    }

    [TestMethod]
    public void BehaviorPlanner_ReplaysIdenticallyForSameRandomStream()
    {
        static string Replay()
        {
            var planner = new BehaviorPlanner(new SequenceRandom(2500, 0, 180));
            var delay = planner.NextIdleDelay();
            var walk = planner.PlanWalk(
                new(400, 500), new(220, 220), new(new(0, 0), new(1920, 1080)),
                FacingDirection.Right);
            return $"{delay.TotalMilliseconds}|{walk.Facing}|{walk.TargetX}|{walk.SpeedPixelsPerSecond}|{walk.RequiresTurn}";
        }
        Assert.AreEqual(Replay(), Replay());
    }

    private sealed class Fixture : IDisposable
    {
        public Fixture(params int[] randomValues) =>
            Controller = new(Player, Window, new(new SequenceRandom(randomValues)), Clock);
        public FakeAnimationPlayer Player { get; } = new();
        public FakeWindow Window { get; } = new();
        public FakeClock Clock { get; } = new();
        public PetAnimationController Controller { get; }
        public void Dispose() => Controller.Dispose();
    }

    private sealed class SequenceRandom(params int[] values) : IRandomSource
    {
        private int _index;
        public int NextInt(int minimumInclusive, int maximumExclusive)
        {
            var value = values[_index++ % values.Length];
            return Math.Clamp(value, minimumInclusive, maximumExclusive - 1);
        }
    }

    private sealed class FakeClock : IMonotonicClock
    {
        public TimeSpan Elapsed { get; set; }
    }

    private sealed class FakeAnimationPlayer : IAnimationPlayer
    {
        public List<string> PlayedClips { get; } = [];
        public string? CurrentClipId { get; private set; }
        public FacingDirection Facing { get; private set; } = FacingDirection.Right;
        public event EventHandler<AnimationPlaybackCompletedEventArgs>? PlaybackCompleted;
        public void Play(string clipId) { CurrentClipId = clipId; PlayedClips.Add(clipId); }
        public void SetFacing(FacingDirection facing) => Facing = facing;
        public void Complete(string clipId) => PlaybackCompleted?.Invoke(this, new(clipId));
        public void Stop() => CurrentClipId = null;
        public void Dispose() { }
    }

    private sealed class FakeWindow : IOverlayWindow
    {
        public bool IsVisible => true;
        public ScreenPoint Position { get; private set; } = new(100, 500);
        public ScreenSize Size => new(220, 220);
        public ScreenArea WorkArea => new(new(0, 0), new(1920, 1080));
        public event EventHandler? ClickObserved { add { } remove { } }
        public event EventHandler? ExitRequested { add { } remove { } }
        public event EventHandler<double>? DpiScaleChanged { add { } remove { } }
        public void MoveTo(ScreenPoint position) => Position = position;
        public void ShowOverlay() { }
        public void HideOverlay() { }
        public void PlaceAtBottomRight(double margin) { }
        public void CloseOverlay() { }
    }
}

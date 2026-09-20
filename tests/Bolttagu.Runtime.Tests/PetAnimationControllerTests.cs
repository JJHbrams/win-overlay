using Bolttagu.Contracts;
using Bolttagu.Core;

namespace Bolttagu.Runtime.Tests;

[TestClass]
public sealed class PetAnimationControllerTests
{
    [TestMethod]
    public void ClickCompletion_PlaysHuffBeforeReturningToIdle()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.Controller.Start();
        fixture.Controller.ReactToClick();
        fixture.Player.Complete(PetActionClips.Click);
        Assert.AreEqual(PetRuntimeState.Huffing, fixture.Controller.State);
        fixture.Player.Complete(PetActionClips.ClickHuff);
        CollectionAssert.AreEqual(
            new[] { PetActionClips.Idle, PetActionClips.Click, PetActionClips.ClickHuff, PetActionClips.Idle },
            fixture.Player.PlayedClips.ToArray());
    }

    [TestMethod]
    public void ScheduledTurn_CompletesIntoWalkAndMovesWindow()
    {
        using var fixture = new Fixture(2000, 1, 120, 2000);
        fixture.Controller.Start();
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(2);
        fixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.Turning, fixture.Controller.State);
        fixture.Player.Complete(PetActionClips.Turn);
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(3);
        fixture.Controller.Tick();
        Assert.IsGreaterThan(100, fixture.Window.Position.X);
        CollectionAssert.AreEqual(
            new[] { PetActionClips.Idle, PetActionClips.Turn, PetActionClips.Walk },
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
    public void WalkCompletion_ReversesTurnBeforeIdle()
    {
        using var fixture = new Fixture(2000, 1, 120, 2000);
        fixture.Controller.Start();
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(2);
        fixture.Controller.Tick();
        fixture.Player.Complete(PetActionClips.Turn);
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(4);
        fixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.TurningToIdle, fixture.Controller.State);
        fixture.Player.Complete(PetActionClips.TurnToIdle);
        Assert.AreEqual(PetRuntimeState.Idle, fixture.Controller.State);
        CollectionAssert.AreEqual(
            new[] { PetActionClips.Idle, PetActionClips.Turn, PetActionClips.Walk, PetActionClips.TurnToIdle, PetActionClips.Idle },
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

    [TestMethod]
    public void DragRelease_PlaysDangleThenLandingThenIdle()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.Controller.Start();
        fixture.Window.MoveTo(new(100, 100));
        fixture.Controller.BeginDrag();
        Assert.AreEqual(PetRuntimeState.Dragging, fixture.Controller.State);
        fixture.Controller.CompleteDrag();
        Assert.AreEqual(PetRuntimeState.Falling, fixture.Controller.State);
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(1);
        fixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.Landing, fixture.Controller.State);
        fixture.Player.Complete(PetActionClips.DropLand);
        Assert.AreEqual(PetRuntimeState.Idle, fixture.Controller.State);
        CollectionAssert.AreEqual(
            new[] { PetActionClips.Idle, PetActionClips.DragDangle, PetActionClips.Fall, PetActionClips.DropLand, PetActionClips.Idle },
            fixture.Player.PlayedClips.ToArray());
    }

    [TestMethod]
    public void CaptureLoss_DuringDragReturnsDirectlyToIdle()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.Controller.Start();
        fixture.Controller.BeginDrag();
        fixture.Controller.CancelDrag();
        Assert.AreEqual(PetRuntimeState.Idle, fixture.Controller.State);
        CollectionAssert.AreEqual(
            new[] { PetActionClips.Idle, PetActionClips.DragDangle, PetActionClips.Idle },
            fixture.Player.PlayedClips.ToArray());
    }

    [TestMethod]
    public void GroundedWindowBecomingUnavailable_StartsFallOnNextTick()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.Controller.Start();
        fixture.Surfaces.SupportValid = false;

        fixture.Controller.Tick();

        Assert.AreEqual(PetRuntimeState.Falling, fixture.Controller.State);
        Assert.AreEqual(PetActionClips.Fall, fixture.Player.CurrentClipId);
    }

    [TestMethod]
    public void EveryGroundedRuntimeState_RevalidatesItsSupport()
    {
        var groundedStates = new[]
        {
            PetRuntimeState.Idle,
            PetRuntimeState.Turning,
            PetRuntimeState.Walking,
            PetRuntimeState.TurningToIdle,
            PetRuntimeState.Reacting,
            PetRuntimeState.Huffing,
            PetRuntimeState.Landing,
        };

        foreach (var target in groundedStates)
        {
            using var fixture = new Fixture(2000, 1, 320, 2000);
            fixture.Controller.Start();
            EnterState(fixture, target);
            Assert.AreEqual(target, fixture.Controller.State, $"Failed to arrange {target}.");
            fixture.Surfaces.SupportValid = false;

            fixture.Controller.Tick();

            Assert.AreEqual(PetRuntimeState.Falling, fixture.Controller.State, $"{target} did not fall.");
            Assert.AreEqual(PetActionClips.Fall, fixture.Player.CurrentClipId);
        }
    }

    [TestMethod]
    public void WalkLeavingSupportBounds_StartsFall()
    {
        using var fixture = new Fixture(2000, 1, 320, 2000);
        fixture.Surfaces.Current = new(
            new(new(0, 720), new(260, 300)), DesktopSurfaceKind.Window, 1);
        fixture.Controller.Start();
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(2);
        fixture.Controller.Tick();
        fixture.Player.Complete(PetActionClips.Turn);
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(4);
        fixture.Controller.Tick();
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(4.01);

        fixture.Controller.Tick();

        Assert.AreEqual(PetRuntimeState.Falling, fixture.Controller.State);
        Assert.AreEqual(PetActionClips.Fall, fixture.Player.CurrentClipId);
    }

    [TestMethod]
    public void FallingRetargetsWhenDestinationSurfaceDisappears()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.Controller.Start();
        fixture.Window.MoveTo(new(100, 100));
        fixture.Controller.BeginDrag();
        fixture.Controller.CompleteDrag();
        fixture.Surfaces.Below = new(
            new(new(0, 500), new(1200, 300)), DesktopSurfaceKind.Window, 2);
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(0.3);
        fixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.Falling, fixture.Controller.State);

        fixture.Surfaces.Below = new(
            new(new(0, 900), new(1200, 200)), DesktopSurfaceKind.Window, 3);
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(1.2);
        fixture.Controller.Tick();

        Assert.AreEqual(PetRuntimeState.Landing, fixture.Controller.State);
        Assert.AreEqual(680, fixture.Window.Position.Y);
    }

    private static void EnterState(Fixture fixture, PetRuntimeState target)
    {
        if (target == PetRuntimeState.Idle) return;
        if (target is PetRuntimeState.Reacting or PetRuntimeState.Huffing)
        {
            fixture.Controller.ReactToClick();
            if (target == PetRuntimeState.Huffing) fixture.Player.Complete(PetActionClips.Click);
            return;
        }
        if (target == PetRuntimeState.Landing)
        {
            fixture.Window.MoveTo(new(100, 100));
            fixture.Controller.BeginDrag();
            fixture.Controller.CompleteDrag();
            fixture.Clock.Elapsed = TimeSpan.FromSeconds(1);
            fixture.Controller.Tick();
            return;
        }

        fixture.Clock.Elapsed = TimeSpan.FromSeconds(2);
        fixture.Controller.Tick();
        if (target == PetRuntimeState.Turning) return;
        fixture.Player.Complete(PetActionClips.Turn);
        if (target == PetRuntimeState.Walking) return;
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(20);
        fixture.Controller.Tick();
    }

    private sealed class Fixture : IDisposable
    {
        public Fixture(params int[] randomValues) =>
            Controller = new(Player, Window, new(new SequenceRandom(randomValues)), Clock, Surfaces);
        public FakeAnimationPlayer Player { get; } = new();
        public FakeWindow Window { get; } = new();
        public FakeClock Clock { get; } = new();
        public FakeSurfaceProvider Surfaces { get; } = new();
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
        public event EventHandler? DragStarted { add { } remove { } }
        public event EventHandler? DragCompleted { add { } remove { } }
        public event EventHandler? DragCanceled { add { } remove { } }
        public event EventHandler? ExitRequested { add { } remove { } }
        public event EventHandler<double>? DpiScaleChanged { add { } remove { } }
        public void MoveTo(ScreenPoint position) => Position = position;
        public void ShowOverlay() { }
        public void HideOverlay() { }
        public void PlaceAtBottomRight(double margin) { }
        public void CloseOverlay() { }
    }

    private sealed class FakeSurfaceProvider : IDesktopSurfaceProvider
    {
        public DesktopSurface Current { get; set; } =
            new(new(new(0, 720), new(1200, 400)), DesktopSurfaceKind.Window, 1);
        public DesktopSurface? Below { get; set; }
        public bool SupportValid { get; set; } = true;

        public DesktopSurface FindFirstBelow(double centerX, double fromY, ScreenArea workArea) =>
            Below ?? Current;

        public bool TryRefreshSupport(
            DesktopSurface expected,
            double centerX,
            double footY,
            ScreenArea workArea,
            out DesktopSurface current)
        {
            current = Current;
            return SupportValid && expected.Id == current.Id &&
                   centerX >= current.Left && centerX <= current.Right &&
                   Math.Abs(current.Top - footY) <= 3;
        }
    }
}

using Bolttagu.Contracts;
using Bolttagu.Core;

namespace Bolttagu.Runtime.Tests;

[TestClass]
public sealed class PetAnimationControllerTests
{
    [TestMethod]
    public void StartupFall_BeginsAtWorkAreaTopAfterSpawn()
    {
        var player = new FakeAnimationPlayer();
        var window = new FakeWindow();
        var clock = new FakeClock();
        var surfaces = new FakeSurfaceProvider();
        using var controller = new PetAnimationController(
            player, window, new(new SequenceRandom([0])), clock, surfaces, startWithFall: true);

        controller.Start();
        Assert.AreEqual(window.WorkArea.Origin.Y, window.Position.Y);
        player.Complete(PetActionClips.SpawnIn);

        Assert.AreEqual(PetRuntimeState.Falling, controller.State);
        Assert.AreEqual(PetActionClips.Fall, player.CurrentClipId);
    }

    [TestMethod]
    public void Start_PlaysSpawnBeforeEnteringIdle()
    {
        using var fixture = new Fixture(2000, 2000);

        fixture.Controller.Start();

        Assert.AreEqual(PetRuntimeState.Launching, fixture.Controller.State);
        CollectionAssert.AreEqual(new[] { PetActionClips.SpawnIn }, fixture.Player.PlayedClips.ToArray());
        fixture.Player.Complete(PetActionClips.SpawnIn);
        Assert.AreEqual(PetRuntimeState.Idle, fixture.Controller.State);
        CollectionAssert.AreEqual(
            new[] { PetActionClips.SpawnIn, PetActionClips.Idle },
            fixture.Player.PlayedClips.ToArray());
    }

    [TestMethod]
    public void ClickCompletion_PlaysHuffBeforeReturningToIdle()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.StartToIdle();
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
        using var fixture = new Fixture(2000, 0, 0, 120, 2000);
        fixture.StartToIdle();
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(2);
        fixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.Turning, fixture.Controller.State);
        fixture.Player.Complete(PetActionClips.Turn);
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(3);
        fixture.Controller.Tick();
        Assert.IsLessThan(100, fixture.Window.Position.X);
        CollectionAssert.AreEqual(
            new[] { PetActionClips.Idle, PetActionClips.Turn, PetActionClips.Walk },
            fixture.Player.PlayedClips.ToArray());
    }

    [TestMethod]
    public void ScheduledDirectionChange_PlaysTurnBeforeWalk()
    {
        using var fixture = new Fixture(2000, 0, 0, 120, 2000);
        fixture.StartToIdle();
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
        using var fixture = new Fixture(2000, 0, 0, 120, 2000);
        fixture.StartToIdle();
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
    public void BehaviorPlanner_RopeClimbChanceUsesThirtyFivePercentBoundary()
    {
        Assert.IsTrue(new BehaviorPlanner(new SequenceRandom(34)).ShouldStartRopeClimb());
        Assert.IsFalse(new BehaviorPlanner(new SequenceRandom(35)).ShouldStartRopeClimb());
    }

    [TestMethod]
    public void HighDragRelease_UsesSingleDizzyRecoveryInsteadOfStandingTwice()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.StartToIdle();
        fixture.Window.MoveTo(new(100, 100));
        fixture.Controller.BeginDrag();
        Assert.AreEqual(PetRuntimeState.DraggingIdle, fixture.Controller.State);
        fixture.Controller.CompleteDrag();
        Assert.AreEqual(PetRuntimeState.Falling, fixture.Controller.State);
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(1);
        fixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.Recovering, fixture.Controller.State);
        Assert.AreEqual(PetActionClips.LandRecover, fixture.Player.CurrentClipId);
        fixture.Player.Complete(PetActionClips.LandRecover);
        Assert.AreEqual(PetRuntimeState.Idle, fixture.Controller.State);
        CollectionAssert.AreEqual(
            new[] { PetActionClips.Idle, PetActionClips.DragHeldIdle, PetActionClips.Fall, PetActionClips.LandRecover, PetActionClips.Idle },
            fixture.Player.PlayedClips.ToArray());
    }

    [TestMethod]
    public void LowDragRelease_UsesExistingFallAndLandingWithoutDizzyRecovery()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.StartToIdle();
        fixture.Controller.BeginDrag();
        fixture.Controller.CompleteDrag();
        Assert.AreEqual(PetRuntimeState.Falling, fixture.Controller.State);

        fixture.Clock.Elapsed = TimeSpan.FromMilliseconds(10);
        fixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.Landing, fixture.Controller.State);
        fixture.Player.Complete(PetActionClips.DropLand);

        Assert.AreEqual(PetRuntimeState.Idle, fixture.Controller.State);
        CollectionAssert.AreEqual(
            new[] { PetActionClips.Idle, PetActionClips.DragHeldIdle, PetActionClips.Fall, PetActionClips.DropLand, PetActionClips.Idle },
            fixture.Player.PlayedClips.ToArray());
    }

    [TestMethod]
    public void DragRelease_ProbesAboveTheFeetSoExactTextContactCanLand()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.StartToIdle();
        fixture.Surfaces.Below = new(
            new(new(0, 720), new(1200, 24)), DesktopSurfaceKind.TextLine, 77, 0, true);

        fixture.Controller.BeginDrag();
        fixture.Controller.CompleteDrag();
        fixture.Clock.Elapsed = TimeSpan.FromMilliseconds(10);
        fixture.Controller.Tick();

        Assert.IsLessThanOrEqualTo(720, fixture.Surfaces.LastFindFromY,
            "Landing search must include a thin surface touching the pet's feet.");
        Assert.AreEqual(PetRuntimeState.Landing, fixture.Controller.State);
    }

    [TestMethod]
    public void CaptureLoss_DuringDragReturnsDirectlyToIdle()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.StartToIdle();
        fixture.Controller.BeginDrag();
        fixture.Controller.CancelDrag();
        Assert.AreEqual(PetRuntimeState.Idle, fixture.Controller.State);
        CollectionAssert.AreEqual(
            new[] { PetActionClips.Idle, PetActionClips.DragHeldIdle, PetActionClips.Idle },
            fixture.Player.PlayedClips.ToArray());
    }

    [TestMethod]
    public void ClickTransitionTable_DoesNotUseStandingClickForCompressedLanding()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.StartToIdle();
        fixture.Controller.BeginDrag();
        fixture.Controller.CompleteDrag();
        fixture.Clock.Elapsed = TimeSpan.FromMilliseconds(10);
        fixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.Landing, fixture.Controller.State);

        fixture.Controller.ReactToClick();
        Assert.AreEqual(PetRuntimeState.Landing, fixture.Controller.State);
        Assert.AreEqual(PetActionClips.DropLand, fixture.Player.CurrentClipId);
    }

    [TestMethod]
    public void DozeBehavior_UsesProductionControllerTraceAndTwoPackCycles()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.StartToIdle();
        Assert.IsTrue(fixture.Controller.StartAutonomousBehavior(
            BehaviorDefinitions.Autonomous.Single(definition => definition.Id == BehaviorDefinitions.SitDoze)));
        fixture.Player.Complete(PetActionClips.SitDown);
        fixture.Clock.Elapsed = TimeSpan.FromMilliseconds(750);
        fixture.Controller.Tick();
        fixture.Player.Complete(PetActionClips.DozeEnter);
        Assert.AreEqual(PetActionClips.DozeLoop, fixture.Player.CurrentClipId);

        fixture.Clock.Elapsed = TimeSpan.FromMilliseconds(5550);
        fixture.Controller.Tick();
        Assert.AreEqual(PetActionClips.WakeUp, fixture.Player.CurrentClipId);
        fixture.Player.Complete(PetActionClips.WakeUp);
        fixture.Player.Complete(PetActionClips.StandUp);
        CollectionAssert.AreEqual(new[]
        {
            PetActionClips.Idle, PetActionClips.SitDown, PetActionClips.SitSettle,
            PetActionClips.DozeEnter, PetActionClips.DozeLoop, PetActionClips.WakeUp,
            PetActionClips.StandUp, PetActionClips.Idle,
        }, fixture.Player.PlayedClips.ToArray());
    }

    [TestMethod]
    public void GroundedWindowBecomingUnavailable_StartsFallOnNextTick()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.StartToIdle();
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
            PetRuntimeState.Recovering,
        };

        foreach (var target in groundedStates)
        {
            using var fixture = new Fixture(2000, 0, 0, 320, 2000);
            fixture.StartToIdle();
            EnterState(fixture, target);
            Assert.AreEqual(target, fixture.Controller.State, $"Failed to arrange {target}.");
            fixture.Surfaces.SupportValid = false;

            fixture.Controller.Tick();

            Assert.AreEqual(PetRuntimeState.Falling, fixture.Controller.State, $"{target} did not fall.");
            Assert.AreEqual(PetActionClips.Fall, fixture.Player.CurrentClipId);
        }
    }

    [TestMethod]
    public void RopeClimb_SupportLossWithoutEligibleObstacleFalls()
    {
        using var fixture = new Fixture(2000, 0, 0, 320, 2000);
        fixture.Surfaces.Current = new(
            new(new(0, 720), new(260, 300)), DesktopSurfaceKind.Window, 1);
        fixture.StartToIdle();
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(2);
        fixture.Controller.Tick();
        fixture.Player.Complete(PetActionClips.Turn);
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(4);
        fixture.Controller.Tick();
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(4.01);
        fixture.Surfaces.SupportValid = false;

        fixture.Controller.Tick();

        Assert.AreEqual(PetRuntimeState.Falling, fixture.Controller.State);
        Assert.AreEqual(PetActionClips.Fall, fixture.Player.CurrentClipId);
    }

    [TestMethod]
    public void FallingRetargetsWhenDestinationSurfaceDisappears()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.StartToIdle();
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

        Assert.AreEqual(PetRuntimeState.Recovering, fixture.Controller.State);
        Assert.AreEqual(PetActionClips.LandRecover, fixture.Player.CurrentClipId);
        Assert.AreEqual(680, fixture.Window.Position.Y);
    }

    [TestMethod]
    public void MovingDrag_PlaysPulledAndFacesMovementSoArtTrailsBehind()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.StartToIdle();
        fixture.Controller.BeginDrag();

        fixture.Window.MoveTo(new(180, 500));
        fixture.Clock.Elapsed = TimeSpan.FromMilliseconds(100);
        fixture.Controller.Tick();

        Assert.AreEqual(PetRuntimeState.DraggingPulled, fixture.Controller.State);
        Assert.AreEqual(PetActionClips.DragPulled, fixture.Player.CurrentClipId);
        Assert.AreEqual(FacingDirection.Right, fixture.Player.Facing);
    }

    [TestMethod]
    public void MovingDragLeft_MirrorsPulledArtSoLimbsTrailRight()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.StartToIdle();
        fixture.Controller.BeginDrag();

        fixture.Window.MoveTo(new(20, 500));
        fixture.Clock.Elapsed = TimeSpan.FromMilliseconds(100);
        fixture.Controller.Tick();

        Assert.AreEqual(PetRuntimeState.DraggingPulled, fixture.Controller.State);
        Assert.AreEqual(FacingDirection.Left, fixture.Player.Facing);
    }

    [TestMethod]
    public void PulledDrag_ReturnsToHeldOnlyAfterSettling()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.StartToIdle();
        fixture.Controller.BeginDrag();
        fixture.Window.MoveTo(new(180, 500));
        fixture.Clock.Elapsed = TimeSpan.FromMilliseconds(100);
        fixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.DraggingPulled, fixture.Controller.State);

        foreach (var milliseconds in new[] { 200, 300, 400, 550 })
        {
            fixture.Clock.Elapsed = TimeSpan.FromMilliseconds(milliseconds);
            fixture.Controller.Tick();
        }
        Assert.AreEqual(PetRuntimeState.DraggingPulled, fixture.Controller.State);

        fixture.Clock.Elapsed = TimeSpan.FromMilliseconds(600);
        fixture.Controller.Tick();

        Assert.AreEqual(PetRuntimeState.DraggingIdle, fixture.Controller.State);
        Assert.AreEqual(PetActionClips.DragHeldIdle, fixture.Player.CurrentClipId);
    }

    [TestMethod]
    public void ExitCompletion_RaisesExitReadyExactlyOnce()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.StartToIdle();
        var readyCount = 0;
        fixture.Controller.ExitReady += (_, _) => readyCount++;

        fixture.Controller.RequestExit();
        fixture.Controller.RequestExit();
        fixture.Player.Complete(PetActionClips.DespawnOut);
        fixture.Player.Complete(PetActionClips.DespawnOut);

        Assert.AreEqual(PetRuntimeState.Exiting, fixture.Controller.State);
        Assert.AreEqual(1, readyCount);
        Assert.AreEqual(PetActionClips.DespawnOut, fixture.Player.CurrentClipId);
    }

    [TestMethod]
    public void ExitTimeout_RaisesExitReadyExactlyOnce()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.StartToIdle();
        var readyCount = 0;
        fixture.Controller.ExitReady += (_, _) => readyCount++;
        fixture.Controller.RequestExit();

        fixture.Clock.Elapsed = TimeSpan.FromMilliseconds(1499);
        fixture.Controller.Tick();
        Assert.AreEqual(0, readyCount);
        fixture.Clock.Elapsed = TimeSpan.FromMilliseconds(1500);
        fixture.Controller.Tick();
        fixture.Controller.Tick();

        Assert.AreEqual(1, readyCount);
    }

    [TestMethod]
    public void PriorityTable_ExitBeatsDragAndClick()
    {
        using var fixture = new Fixture(2000, 2000);
        fixture.StartToIdle();
        fixture.Controller.RequestExit();
        fixture.Controller.BeginDrag();
        fixture.Controller.ReactToClick();
        fixture.Surfaces.SupportValid = false;
        fixture.Controller.Tick();

        Assert.AreEqual(PetRuntimeState.Exiting, fixture.Controller.State);
        CollectionAssert.AreEqual(new[] { PetActionClips.Idle, PetActionClips.DespawnOut }, fixture.Player.PlayedClips.ToArray());
    }

    [TestMethod]
    public void PriorityTable_DragAndSupportLossPreemptPendingBehavior()
    {
        using var fixture = new Fixture(2000, 0, 0, 120);
        fixture.StartToIdle();
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(2);
        fixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.Turning, fixture.Controller.State);

        fixture.Controller.BeginDrag();
        fixture.Player.Complete(PetActionClips.Turn);
        Assert.AreEqual(PetRuntimeState.DraggingIdle, fixture.Controller.State);
        Assert.AreEqual(PetActionClips.DragHeldIdle, fixture.Player.CurrentClipId);
        Assert.IsFalse(fixture.Controller.HasActiveBehavior, "Drag must clear pending turn/walk sequence state.");

        fixture.Controller.CancelDrag();
        fixture.Controller.ReactToClick();
        fixture.Surfaces.SupportValid = false;
        fixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.Falling, fixture.Controller.State);
        Assert.AreEqual(PetActionClips.Fall, fixture.Player.CurrentClipId);
        Assert.IsFalse(fixture.Controller.HasActiveBehavior, "Support loss must clear the interrupted click sequence.");
    }

    [TestMethod]
    public void RopeClimb_RightObstacle_UsesPrepareLoopFinishAndLandsOnObstacleTop()
    {
        using var fixture = new Fixture(0, 1, 220);
        fixture.Surfaces.Obstacle = new(
            new(new(400, 300), new(500, 600)), DesktopSurfaceKind.Window, 2);
        fixture.StartToIdle();

        fixture.Clock.Elapsed = TimeSpan.FromSeconds(2);
        fixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.Walking, fixture.Controller.State);
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(5);
        fixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.RopeClimbPreparing, fixture.Controller.State);
        Assert.AreEqual(PetActionClips.RopeClimbPrepare, fixture.Player.CurrentClipId);

        fixture.Player.Complete(PetActionClips.RopeClimbPrepare);
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(10);
        fixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.ClimbFinishing, fixture.Controller.State);
        Assert.AreEqual(80, fixture.Window.Position.Y);
        fixture.Player.Complete(PetActionClips.RopeClimbFinish);

        Assert.AreEqual(PetRuntimeState.Idle, fixture.Controller.State);
        CollectionAssert.AreEqual(new[]
        {
            PetActionClips.Idle, PetActionClips.Walk, PetActionClips.RopeClimbPrepare,
            PetActionClips.RopeClimbLoop, PetActionClips.RopeClimbFinish, PetActionClips.Idle,
        }, fixture.Player.PlayedClips.ToArray());
    }

    [TestMethod]
    public void RopeClimb_LeftObstacle_ClimbsAtItsRightEdge()
    {
        using var fixture = new Fixture(0, 0, 0, 220);
        fixture.Window.MoveTo(new(400, 500));
        fixture.Surfaces.Obstacle = new(
            new(new(0, 300), new(300, 600)), DesktopSurfaceKind.Window, 2);
        fixture.StartToIdle();

        fixture.Clock.Elapsed = TimeSpan.FromSeconds(2);
        fixture.Controller.Tick();
        fixture.Player.Complete(PetActionClips.Turn);
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(5);
        fixture.Controller.Tick();

        Assert.AreEqual(PetRuntimeState.RopeClimbPreparing, fixture.Controller.State);
        fixture.Player.Complete(PetActionClips.RopeClimbPrepare);
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(10);
        fixture.Controller.Tick();
        Assert.AreEqual(300, fixture.Window.Position.X);
        Assert.AreEqual(PetRuntimeState.ClimbFinishing, fixture.Controller.State);
    }

    [TestMethod]
    public void RopeClimb_FailedChanceRollsOnlyOnceForTheSameEdgeEncounter()
    {
        using var fixture = new Fixture(0, 1, 220, 220, 99, 0);
        fixture.Surfaces.Obstacle = new(
            new(new(400, 100), new(500, 180)), DesktopSurfaceKind.Window, 2);
        fixture.StartToIdle();

        fixture.Clock.Elapsed = TimeSpan.FromSeconds(2);
        fixture.Controller.Tick();
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(3.08);
        fixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.Walking, fixture.Controller.State);

        fixture.Clock.Elapsed = TimeSpan.FromSeconds(3.10);
        fixture.Controller.Tick();

        Assert.AreEqual(PetRuntimeState.Walking, fixture.Controller.State,
            "The same edge contact must not reroll after its first failed chance.");
        Assert.AreEqual(PetActionClips.Walk, fixture.Player.CurrentClipId);
    }

    [TestMethod]
    public void RopeClimb_ForegroundEdgeExtensionStartsBeforeWalkingOffSupportCanFall()
    {
        using var fixture = new Fixture(0, 1, 220, 220, 0);
        fixture.Surfaces.Current = new(
            new(new(0, 720), new(400, 300)), DesktopSurfaceKind.Window, 1);
        fixture.Surfaces.Obstacle = new(
            new(new(400, 100), new(500, 180)), DesktopSurfaceKind.Window, 2);
        fixture.StartToIdle();

        fixture.Clock.Elapsed = TimeSpan.FromSeconds(2);
        fixture.Controller.Tick();
        fixture.Surfaces.SupportValid = false;
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(5);
        fixture.Controller.Tick();

        Assert.AreEqual(PetRuntimeState.RopeClimbPreparing, fixture.Controller.State);
        Assert.AreEqual(PetActionClips.RopeClimbPrepare, fixture.Player.CurrentClipId);
    }

    [TestMethod]
    public void FreeClimb_InterceptsExposedTopThenReturnsIdle()
    {
        using var fixture = new Fixture(125);
        fixture.Surfaces.Intercept = new(
            new(new(0, 600), new(1200, 300)), DesktopSurfaceKind.Window, 3);
        fixture.StartToIdle();

        Assert.IsTrue(fixture.Controller.StartAutonomousBehavior(
            BehaviorDefinitions.Autonomous.Single(definition => definition.Id == BehaviorDefinitions.FreeClimb)));
        fixture.Player.Complete(PetActionClips.FreeClimbPrepare);
        fixture.Controller.Tick();

        Assert.AreEqual(PetRuntimeState.ClimbFinishing, fixture.Controller.State);
        Assert.AreEqual(380, fixture.Window.Position.Y);
        fixture.Player.Complete(PetActionClips.FreeClimbFinish);
        Assert.AreEqual(PetRuntimeState.Idle, fixture.Controller.State);
    }

    [TestMethod]
    public void FreeClimb_WithoutInterceptFallsAtSampledTargetHeight()
    {
        using var fixture = new Fixture(125);
        fixture.StartToIdle();
        fixture.Controller.StartAutonomousBehavior(
            BehaviorDefinitions.Autonomous.Single(definition => definition.Id == BehaviorDefinitions.FreeClimb));
        fixture.Player.Complete(PetActionClips.FreeClimbPrepare);

        fixture.Clock.Elapsed = TimeSpan.FromSeconds(5);
        fixture.Controller.Tick();

        Assert.AreEqual(PetRuntimeState.Falling, fixture.Controller.State);
        Assert.AreEqual(PetActionClips.Fall, fixture.Player.CurrentClipId);
        Assert.AreEqual(225, fixture.Window.Position.Y);
    }

    [TestMethod]
    public void RopeClimb_AnchorLossFalls()
    {
        using var fixture = new Fixture(0, 1, 220);
        fixture.Surfaces.Obstacle = new(
            new(new(400, 300), new(500, 600)), DesktopSurfaceKind.Window, 2);
        fixture.StartToIdle();
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(2);
        fixture.Controller.Tick();
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(5);
        fixture.Controller.Tick();
        fixture.Surfaces.ClimbAnchorValid = false;
        fixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.Falling, fixture.Controller.State);
    }

    [TestMethod]
    public void TextLineEndDropsAndVerticalLineClimbBypassesChance()
    {
        using var textFixture = new Fixture(0, 1, 220);
        textFixture.Surfaces.Current = new(
            new(new(0, 720), new(250, 24)), DesktopSurfaceKind.TextLine, 10, 0, true);
        textFixture.StartToIdle();
        textFixture.Clock.Elapsed = TimeSpan.FromSeconds(2);
        textFixture.Controller.Tick();
        textFixture.Clock.Elapsed = TimeSpan.FromSeconds(5);
        textFixture.Controller.Tick();
        textFixture.Clock.Elapsed = TimeSpan.FromSeconds(5.1);
        textFixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.Falling, textFixture.Controller.State);

        using var lineFixture = new Fixture(0, 1, 220, 220, 99);
        lineFixture.Surfaces.Obstacle = new(
            new(new(400, 200), new(4, 320)), DesktopSurfaceKind.VerticalLine, 11, 0, true);
        lineFixture.Surfaces.Intercept = new(
            new(new(360, 200), new(120, 20)), DesktopSurfaceKind.TextLine, 12, 0, true);
        lineFixture.StartToIdle();
        lineFixture.Clock.Elapsed = TimeSpan.FromSeconds(2);
        lineFixture.Controller.Tick();
        lineFixture.Clock.Elapsed = TimeSpan.FromSeconds(5);
        lineFixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.RopeClimbPreparing, lineFixture.Controller.State,
            "Visual lines must bypass the window-edge chance roll.");
        lineFixture.Player.Complete(PetActionClips.RopeClimbPrepare);
        lineFixture.Clock.Elapsed = TimeSpan.FromSeconds(12);
        lineFixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.ClimbFinishing, lineFixture.Controller.State);
        Assert.AreEqual(DesktopSurfaceKind.TextLine, lineFixture.Surfaces.Intercept.Value.Kind);
    }

    [TestMethod]
    public void VerticalLineWithoutTopSupportFallsAtItsEnd()
    {
        using var fixture = new Fixture(0, 1, 220, 220, 99);
        fixture.Surfaces.Obstacle = new(
            new(new(400, 200), new(4, 320)), DesktopSurfaceKind.VerticalLine, 11, 0, true);
        fixture.StartToIdle();
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(2);
        fixture.Controller.Tick();
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(5);
        fixture.Controller.Tick();
        fixture.Player.Complete(PetActionClips.RopeClimbPrepare);
        fixture.Clock.Elapsed = TimeSpan.FromSeconds(12);
        fixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.Falling, fixture.Controller.State);
    }

    [TestMethod]
    public void DragAndExit_PreemptClimbPrepareAndClearItsTransientState()
    {
        using var dragFixture = new Fixture(125);
        dragFixture.StartToIdle();
        dragFixture.Controller.StartAutonomousBehavior(
            BehaviorDefinitions.Autonomous.Single(definition => definition.Id == BehaviorDefinitions.FreeClimb));
        Assert.AreEqual(PetRuntimeState.FreeClimbPreparing, dragFixture.Controller.State);
        dragFixture.Controller.BeginDrag();
        dragFixture.Player.Complete(PetActionClips.FreeClimbPrepare);
        Assert.AreEqual(PetRuntimeState.DraggingIdle, dragFixture.Controller.State);

        using var loopFixture = new Fixture(125);
        loopFixture.StartToIdle();
        loopFixture.Controller.StartAutonomousBehavior(
            BehaviorDefinitions.Autonomous.Single(definition => definition.Id == BehaviorDefinitions.FreeClimb));
        loopFixture.Player.Complete(PetActionClips.FreeClimbPrepare);
        loopFixture.Controller.BeginDrag();
        loopFixture.Player.Complete(PetActionClips.FreeClimbLoop);
        Assert.AreEqual(PetRuntimeState.DraggingIdle, loopFixture.Controller.State);

        using var exitFixture = new Fixture(125);
        exitFixture.Surfaces.Intercept = new(
            new(new(0, 600), new(1200, 300)), DesktopSurfaceKind.Window, 3);
        exitFixture.StartToIdle();
        exitFixture.Controller.StartAutonomousBehavior(
            BehaviorDefinitions.Autonomous.Single(definition => definition.Id == BehaviorDefinitions.FreeClimb));
        exitFixture.Player.Complete(PetActionClips.FreeClimbPrepare);
        exitFixture.Controller.Tick();
        Assert.AreEqual(PetRuntimeState.ClimbFinishing, exitFixture.Controller.State);
        exitFixture.Controller.RequestExit();
        exitFixture.Player.Complete(PetActionClips.FreeClimbFinish);
        Assert.AreEqual(PetRuntimeState.Exiting, exitFixture.Controller.State);
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
        if (target is PetRuntimeState.Landing or PetRuntimeState.Recovering)
        {
            if (target == PetRuntimeState.Recovering) fixture.Window.MoveTo(new(100, 100));
            fixture.Controller.BeginDrag();
            fixture.Controller.CompleteDrag();
            fixture.Clock.Elapsed = target == PetRuntimeState.Landing
                ? TimeSpan.FromMilliseconds(10)
                : TimeSpan.FromSeconds(1);
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
        public void StartToIdle()
        {
            Controller.Start();
            Player.Complete(PetActionClips.SpawnIn);
            Player.PlayedClips.Clear();
            Player.PlayedClips.Add(PetActionClips.Idle);
        }
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
        public DesktopSurface? Obstacle { get; set; }
        public DesktopSurface? Intercept { get; set; }
        public bool SupportValid { get; set; } = true;
        public bool ClimbAnchorValid { get; set; } = true;
        public double LastFindFromY { get; private set; }

        public DesktopSurface FindFirstBelow(double centerX, double fromY, ScreenArea workArea)
        {
            LastFindFromY = fromY;
            return Below ?? Current;
        }

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

        public bool TryFindRopeClimbObstacle(
            DesktopSurface support,
            double footY,
            double currentLeadingX,
            double nextLeadingX,
            FacingDirection facing,
            ScreenSize petSize,
            ScreenArea workArea,
            out DesktopSurface obstacle)
        {
            obstacle = Obstacle.GetValueOrDefault();
            if (Obstacle is not { } candidate || !ClimbAnchorValid) return false;
            return facing == FacingDirection.Right
                ? candidate.Left >= currentLeadingX - 3 && candidate.Left <= nextLeadingX + 3
                : candidate.Right <= currentLeadingX + 3 && candidate.Right >= nextLeadingX - 3;
        }

        public DesktopSurface? FindClimbIntercept(
            double centerX,
            double fromFootY,
            double targetFootY,
            ScreenArea workArea) =>
            Intercept is { } candidate && candidate.Top < fromFootY && candidate.Top >= targetFootY
                ? candidate
                : null;

        public bool TryRefreshClimbAnchor(
            DesktopSurface expected,
            double edgeX,
            ScreenArea workArea,
            out DesktopSurface current)
        {
            current = Obstacle.GetValueOrDefault();
            return ClimbAnchorValid && Obstacle is { } candidate && candidate.Id == expected.Id;
        }
    }
}

using Bolttagu.Contracts;
using Bolttagu.Core;
using Bolttagu.Runtime;

namespace Bolttagu.Runtime.Tests;

[TestClass]
public sealed class BehaviorGrammarTests
{
    [TestMethod]
    public void Validator_RejectsPoseMismatchAndUnboundedLoop()
    {
        var mismatch = new BehaviorDefinition("bad", PetPose.Standing,
            [new("first", PetPose.Seated, PetPose.Seated)], PetPose.Seated, BehaviorInterruptPolicy.AutonomousOnly);
        AssertInvalid(() => BehaviorDefinitionValidator.Validate(mismatch));

        var loop = new BehaviorDefinition("loop", PetPose.Standing,
            [new("loop", PetPose.Standing, PetPose.Standing, BehaviorCompletionPolicy.TimedLoop)], PetPose.Standing, BehaviorInterruptPolicy.AutonomousOnly);
        AssertInvalid(() => BehaviorDefinitionValidator.Validate(loop));

        var orphan = new BehaviorDefinition("orphan", PetPose.Standing,
            [new("not-in-pack", PetPose.Standing, PetPose.Standing)], PetPose.Standing, BehaviorInterruptPolicy.AutonomousOnly);
        AssertInvalid(() => BehaviorDefinitionValidator.Validate(orphan, new HashSet<string>(StringComparer.Ordinal) { PetActionClips.Idle }));
    }

    [TestMethod]
    public void Registry_DefinitionsReferenceOnlyContractClipIds()
    {
        var known = PetActionClips.All.Values.Append(PetActionClips.TurnToIdle).ToHashSet(StringComparer.Ordinal);
        BehaviorDefinitionValidator.ValidateAll(BehaviorDefinitions.Autonomous, known);
        BehaviorDefinitionValidator.Validate(BehaviorDefinitions.CreateWalk(false), known);
    }

    [TestMethod]
    public void Registry_FavorsWalkingOverDozing()
    {
        var walk = BehaviorDefinitions.Autonomous.Single(x => x.Id == BehaviorDefinitions.Walk);
        var doze = BehaviorDefinitions.Autonomous.Single(x => x.Id == BehaviorDefinitions.SitDoze);

        Assert.AreEqual(50, walk.Weight);
        Assert.AreEqual(10, doze.Weight);
        Assert.IsGreaterThan(doze.Weight, walk.Weight);
    }

    [TestMethod]
    public void SequenceRunner_ProducesExactDozeTrace()
    {
        using var player = new FakePlayer();
        var runner = new BehaviorSequenceRunner(player);
        runner.Start(BehaviorDefinitions.Autonomous.Single(x => x.Id == BehaviorDefinitions.SitDoze), TimeSpan.Zero);
        Assert.IsTrue(runner.HandleCompletion(PetActionClips.SitDown, TimeSpan.Zero));
        Assert.IsTrue(runner.Tick(TimeSpan.FromMilliseconds(750)));
        Assert.IsTrue(runner.HandleCompletion(PetActionClips.DozeEnter, TimeSpan.FromMilliseconds(750)));
        Assert.IsTrue(runner.Tick(TimeSpan.FromMilliseconds(5550)));
        Assert.IsTrue(runner.HandleCompletion(PetActionClips.WakeUp, TimeSpan.FromMilliseconds(5550)));
        Assert.IsTrue(runner.HandleCompletion(PetActionClips.StandUp, TimeSpan.FromMilliseconds(5550)));
        CollectionAssert.AreEqual(new[] { PetActionClips.SitDown, PetActionClips.SitSettle, PetActionClips.DozeEnter,
            PetActionClips.DozeLoop, PetActionClips.WakeUp, PetActionClips.StandUp }, player.Played);
        Assert.IsFalse(runner.IsRunning);
        Assert.AreEqual(PetPose.Standing, runner.Pose);
    }

    [TestMethod]
    public void Scheduler_RespectsIdleDwellAndRecentHistory()
    {
        var planner = new BehaviorPlanner(new FixedRandom(0));
        var definitions = new[]
        {
            new BehaviorDefinition("a", PetPose.Standing, [new("a", PetPose.Standing, PetPose.Standing)], PetPose.Standing, BehaviorInterruptPolicy.AutonomousOnly, 1),
            new BehaviorDefinition("b", PetPose.Standing, [new("b", PetPose.Standing, PetPose.Standing)], PetPose.Standing, BehaviorInterruptPolicy.AutonomousOnly, 1),
            new BehaviorDefinition("c", PetPose.Standing, [new("c", PetPose.Standing, PetPose.Standing)], PetPose.Standing, BehaviorInterruptPolicy.AutonomousOnly, 1),
        };
        planner.EnterIdleHub(TimeSpan.Zero);
        Assert.IsNull(planner.ChooseAutonomousBehavior(TimeSpan.FromMilliseconds(1499), definitions));
        Assert.AreEqual("a", planner.ChooseAutonomousBehavior(TimeSpan.FromMilliseconds(1500), definitions)!.Id);
        Assert.AreEqual("b", planner.ChooseAutonomousBehavior(TimeSpan.FromMilliseconds(1500), definitions)!.Id);
        Assert.AreEqual("c", planner.ChooseAutonomousBehavior(TimeSpan.FromMilliseconds(1500), definitions)!.Id);
    }

    [TestMethod]
    public void Scheduler_HoldsDozeUntilCalmWindowsExpire()
    {
        var planner = new BehaviorPlanner(new FixedRandom(0));
        var doze = BehaviorDefinitions.Autonomous.Single(x => x.Id == BehaviorDefinitions.SitDoze);
        planner.EnterIdleHub(TimeSpan.Zero);
        planner.RecordLocomotion(TimeSpan.Zero);
        planner.RecordUserInput(TimeSpan.Zero);
        Assert.IsNull(planner.ChooseAutonomousBehavior(TimeSpan.FromSeconds(7), [doze]));
        Assert.IsNull(planner.ChooseAutonomousBehavior(TimeSpan.FromSeconds(9), [doze]));
        Assert.AreEqual(BehaviorDefinitions.SitDoze, planner.ChooseAutonomousBehavior(TimeSpan.FromSeconds(10), [doze])!.Id);
    }

    [TestMethod]
    public void Scheduler_ReplaysAndHonorsCooldown()
    {
        static string Replay()
        {
            var planner = new BehaviorPlanner(new CyclingRandom(0, 80, 20));
            planner.EnterIdleHub(TimeSpan.Zero);
            var selected = Enumerable.Range(0, 3)
                .Select(index => planner.ChooseAutonomousBehavior(TimeSpan.FromSeconds(2 + index * 5))?.Id ?? "idle")
                .ToArray();
            return string.Join(',', selected);
        }
        Assert.AreEqual(Replay(), Replay());

        var only = new BehaviorDefinition("only", PetPose.Standing, [new("only", PetPose.Standing, PetPose.Standing)], PetPose.Standing, BehaviorInterruptPolicy.AutonomousOnly, 1, TimeSpan.FromSeconds(10));
        var planner = new BehaviorPlanner(new FixedRandom(0));
        planner.EnterIdleHub(TimeSpan.Zero);
        Assert.IsNotNull(planner.ChooseAutonomousBehavior(TimeSpan.FromSeconds(2), [only]));
        Assert.IsNull(planner.ChooseAutonomousBehavior(TimeSpan.FromSeconds(5), [only]));
    }

    private sealed class FixedRandom(int value) : IRandomSource
    {
        public int NextInt(int minimumInclusive, int maximumExclusive) => Math.Clamp(value, minimumInclusive, maximumExclusive - 1);
    }

    private sealed class CyclingRandom(params int[] values) : IRandomSource
    {
        private int _index;
        public int NextInt(int minimumInclusive, int maximumExclusive) => Math.Clamp(values[_index++ % values.Length], minimumInclusive, maximumExclusive - 1);
    }

    private static void AssertInvalid(Action action)
    {
        try { action(); Assert.Fail("Expected validation to fail."); }
        catch (InvalidDataException) { }
    }

    private sealed class FakePlayer : IAnimationPlayer
    {
        public List<string> Played { get; } = [];
        public string? CurrentClipId { get; private set; }
        public FacingDirection Facing { get; private set; }
        public event EventHandler<AnimationPlaybackCompletedEventArgs>? PlaybackCompleted { add { } remove { } }
        public void Play(string clipId) { CurrentClipId = clipId; Played.Add(clipId); }
        public void SetFacing(FacingDirection facing) => Facing = facing;
        public void Stop() { }
        public void Dispose() { }
    }
}

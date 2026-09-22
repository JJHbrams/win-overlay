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
        BehaviorDefinitionValidator.Validate(BehaviorDefinitions.CreateRun(false), known);
    }

    [TestMethod]
    public void Registry_FavorsWalkingOverDozing()
    {
        var walk = BehaviorDefinitions.Autonomous.Single(x => x.Id == BehaviorDefinitions.Walk);
        var doze = BehaviorDefinitions.Autonomous.Single(x => x.Id == BehaviorDefinitions.SitDoze);

        var run = BehaviorDefinitions.Autonomous.Single(x => x.Id == BehaviorDefinitions.Run);

        Assert.AreEqual(80, walk.Weight);
        Assert.AreEqual(55, run.Weight);
        Assert.AreEqual(5, doze.Weight);
        Assert.IsGreaterThan(doze.Weight, walk.Weight);
        Assert.IsGreaterThan(doze.Weight, run.Weight);
        Assert.IsGreaterThanOrEqualTo(
            0.70,
            (walk.Weight + run.Weight) / (double)BehaviorDefinitions.Autonomous.Sum(x => x.Weight));
    }

    [TestMethod]
    public void Registry_IdleExpressionsAreStandingNonLoopingAndLowWeight()
    {
        var expressions = new[]
        {
            (BehaviorDefinitions.IdleDazed, PetActionClips.IdleDazed),
            (BehaviorDefinitions.IdleProud, PetActionClips.IdleProud),
            (BehaviorDefinitions.IdlePout, PetActionClips.IdlePout),
        };

        foreach (var (id, clipId) in expressions)
        {
            var expression = BehaviorDefinitions.Autonomous.Single(x => x.Id == id);
            Assert.AreEqual(PetPose.Standing, expression.EntryPose);
            Assert.AreEqual(PetPose.Standing, expression.ExitPose);
            Assert.AreEqual(BehaviorInterruptPolicy.AutonomousOnly, expression.InterruptPolicy);
            Assert.AreEqual(1, expression.Weight);
            Assert.AreEqual(TimeSpan.FromSeconds(15), expression.Cooldown);
            Assert.HasCount(1, expression.Steps);
            Assert.AreEqual(clipId, expression.Steps[0].ClipId);
            Assert.AreEqual(BehaviorCompletionPolicy.AdvanceOnClipComplete, expression.Steps[0].Completion);
        }

        Assert.AreEqual(3, expressions.Select(x => x.Item2).Distinct(StringComparer.Ordinal).Count());
        var locomotionWeight = BehaviorDefinitions.Autonomous
            .Where(x => x.Id is BehaviorDefinitions.Walk or BehaviorDefinitions.Run)
            .Sum(x => x.Weight);
        Assert.IsGreaterThanOrEqualTo(
            0.70,
            locomotionWeight / (double)BehaviorDefinitions.Autonomous.Sum(x => x.Weight));
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
        Assert.IsNull(planner.ChooseAutonomousBehavior(TimeSpan.FromSeconds(10), [doze]), "A fresh pet is not sleepy.");
        planner.AdvanceMood(TimeSpan.Zero, PetActivity.Running);
        for (var second = 1; second <= 60; second++) planner.AdvanceMood(TimeSpan.FromSeconds(second), PetActivity.Running);
        planner.EnterIdleHub(TimeSpan.FromSeconds(60));
        planner.RecordUserInput(TimeSpan.FromSeconds(60));
        Assert.IsNull(planner.ChooseAutonomousBehavior(TimeSpan.FromSeconds(67), [doze]));
        Assert.IsNull(planner.ChooseAutonomousBehavior(TimeSpan.FromSeconds(69), [doze]));
        Assert.AreEqual(BehaviorDefinitions.SitDoze, planner.ChooseAutonomousBehavior(TimeSpan.FromSeconds(70), [doze])!.Id);
    }

    [TestMethod]
    public void Mood_EnergyTracksActivityIntensityAndCapsLongTick()
    {
        var planner = new BehaviorPlanner(new FixedRandom(0));
        planner.AdvanceMood(TimeSpan.Zero, PetActivity.Resting);
        for (var second = 1; second <= 10; second++) planner.AdvanceMood(TimeSpan.FromSeconds(second), PetActivity.Walking);
        var afterWalk = planner.Energy;
        for (var second = 11; second <= 20; second++) planner.AdvanceMood(TimeSpan.FromSeconds(second), PetActivity.Running);
        var afterRun = planner.Energy;
        for (var second = 21; second <= 30; second++) planner.AdvanceMood(TimeSpan.FromSeconds(second), PetActivity.Climbing);
        var afterClimb = planner.Energy;
        Assert.AreEqual(95, afterWalk, 0.001);
        Assert.AreEqual(80, afterRun, 0.001);
        Assert.AreEqual(68, afterClimb, 0.001);
        planner.AdvanceMood(TimeSpan.FromHours(1), PetActivity.Running);
        Assert.AreEqual(66.5, planner.Energy, 0.001, "A suspended app must not consume an hour of energy in one tick.");
        for (var second = 1; second <= 10; second++) planner.AdvanceMood(TimeSpan.FromHours(1) + TimeSpan.FromSeconds(second), PetActivity.Dozing);
        Assert.AreEqual(100, planner.Energy, 0.001);
    }

    [TestMethod]
    public void Scheduler_LowEnergySuppressesVoluntaryRunAndClimb()
    {
        var planner = new BehaviorPlanner(new FixedRandom(0));
        planner.AdvanceMood(TimeSpan.Zero, PetActivity.Running);
        for (var second = 1; second <= 60; second++) planner.AdvanceMood(TimeSpan.FromSeconds(second), PetActivity.Running);
        planner.EnterIdleHub(TimeSpan.FromSeconds(60));
        var vigorous = BehaviorDefinitions.Autonomous.Where(x => x.Id is
            BehaviorDefinitions.Run or BehaviorDefinitions.FreeClimb or BehaviorDefinitions.FreeDescend).ToArray();
        Assert.IsNull(planner.ChooseAutonomousBehavior(TimeSpan.FromSeconds(70), vigorous));
    }

    [TestMethod]
    public void Scheduler_CuriosityAndEventGatedExpressions()
    {
        var random = new RecordingRandom();
        var planner = new BehaviorPlanner(random);
        planner.EnterIdleHub(TimeSpan.Zero);
        var look = BehaviorDefinitions.Autonomous.Single(x => x.Id == BehaviorDefinitions.LookAround);
        var walk = BehaviorDefinitions.Autonomous.Single(x => x.Id == BehaviorDefinitions.Walk);
        var run = BehaviorDefinitions.Autonomous.Single(x => x.Id == BehaviorDefinitions.Run);
        Assert.AreEqual(BehaviorDefinitions.LookAround, planner.ChooseAutonomousBehavior(TimeSpan.FromSeconds(2), [look])!.Id);
        Assert.AreEqual(25, planner.Curiosity, 0.001, "Selecting a clip is not a completion event.");
        planner.RecordLookAroundCompleted();
        Assert.AreEqual(BehaviorDefinitions.Run, planner.ChooseAutonomousBehavior(TimeSpan.FromSeconds(4), [run, walk])!.Id);
        Assert.AreEqual(179, random.LastMaximum, "Completed exploration should raise running weight.");
        var climb = BehaviorDefinitions.Autonomous.Single(x => x.Id == BehaviorDefinitions.FreeClimb);
        planner.ChooseAutonomousBehavior(TimeSpan.FromSeconds(6), [climb]);
        Assert.AreEqual(14, random.LastMaximum, "Curiosity should raise reachable climbing weight without crowding out movement.");

        var emotions = new BehaviorPlanner(new FixedRandom(0));
        emotions.EnterIdleHub(TimeSpan.Zero);
        var pout = BehaviorDefinitions.Autonomous.Single(x => x.Id == BehaviorDefinitions.IdlePout);
        var proud = BehaviorDefinitions.Autonomous.Single(x => x.Id == BehaviorDefinitions.IdleProud);
        Assert.IsNull(emotions.ChooseAutonomousBehavior(TimeSpan.FromSeconds(2), [pout, proud]));
        emotions.RecordValidClick(TimeSpan.FromSeconds(2));
        emotions.RecordValidClick(TimeSpan.FromSeconds(3));
        Assert.AreEqual(BehaviorDefinitions.IdlePout, emotions.ChooseAutonomousBehavior(TimeSpan.FromSeconds(4), [pout])!.Id);
        emotions.RecordPoutCompleted();
        Assert.IsNull(emotions.ChooseAutonomousBehavior(TimeSpan.FromSeconds(5), [proud]));
        Assert.AreEqual(BehaviorDefinitions.LookAround, emotions.ChooseAutonomousBehavior(TimeSpan.FromSeconds(6), [look])!.Id);
        emotions.RecordClimbCompleted(TimeSpan.FromSeconds(6));
        Assert.AreEqual(BehaviorDefinitions.IdleProud, emotions.ChooseAutonomousBehavior(TimeSpan.FromSeconds(7), [proud])!.Id);
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

    [TestMethod]
    public void Scheduler_IdleExpressionsAvoidRecentRepeatsAndHonorCooldown()
    {
        var planner = new BehaviorPlanner(new FixedRandom(0));
        var dazed = BehaviorDefinitions.Autonomous.Single(x => x.Id == BehaviorDefinitions.IdleDazed);
        planner.EnterIdleHub(TimeSpan.Zero);
        Assert.IsNull(planner.ChooseAutonomousBehavior(TimeSpan.FromSeconds(2), [dazed]));
        planner.AdvanceMood(TimeSpan.Zero, PetActivity.Running);
        for (var second = 1; second <= 50; second++) planner.AdvanceMood(TimeSpan.FromSeconds(second), PetActivity.Running);
        Assert.AreEqual(BehaviorDefinitions.IdleDazed, planner.ChooseAutonomousBehavior(TimeSpan.FromSeconds(51), [dazed])!.Id);
        Assert.IsNull(planner.ChooseAutonomousBehavior(TimeSpan.FromSeconds(52), [dazed]));
        var look = BehaviorDefinitions.Autonomous.Single(x => x.Id == BehaviorDefinitions.LookAround);
        var walk = BehaviorDefinitions.Autonomous.Single(x => x.Id == BehaviorDefinitions.Walk);
        Assert.AreEqual(BehaviorDefinitions.LookAround, planner.ChooseAutonomousBehavior(TimeSpan.FromSeconds(53), [look])!.Id);
        Assert.AreEqual(BehaviorDefinitions.Walk, planner.ChooseAutonomousBehavior(TimeSpan.FromSeconds(54), [walk])!.Id);
        Assert.AreEqual(BehaviorDefinitions.IdleDazed, planner.ChooseAutonomousBehavior(TimeSpan.FromSeconds(66), [dazed])!.Id);
    }

    private sealed class FixedRandom(int value) : IRandomSource
    {
        public int NextInt(int minimumInclusive, int maximumExclusive) => Math.Clamp(value, minimumInclusive, maximumExclusive - 1);
    }

    private sealed class RecordingRandom : IRandomSource
    {
        public int LastMaximum { get; private set; }
        public int NextInt(int minimumInclusive, int maximumExclusive)
        {
            LastMaximum = maximumExclusive;
            return minimumInclusive;
        }
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

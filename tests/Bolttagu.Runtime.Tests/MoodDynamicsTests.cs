using Bolttagu.Core;

namespace Bolttagu.Runtime.Tests;

[TestClass]
public sealed class MoodDynamicsTests
{
    [TestMethod]
    public void ThreeAxes_UseElapsedTimeAndBoundLongSuspension()
    {
        var mood = new PetMoodState();
        mood.Advance(TimeSpan.Zero, PetActivity.Neutral);
        for (var second = 1; second <= 10; second++) mood.Advance(TimeSpan.FromSeconds(second), PetActivity.Running);
        Assert.AreEqual(85, mood.Energy, 0.001);
        Assert.AreEqual(0, mood.Curiosity, 0.001);
        mood.Advance(TimeSpan.FromHours(1), PetActivity.Running);
        Assert.AreEqual(83.5, mood.Energy, 0.001, "One resumed tick cannot consume an hour of energy.");
        mood.RecordLookAroundCompleted();
        Assert.AreEqual(55, mood.Curiosity, 0.001);
        for (var second = 1; second <= 10; second++)
            mood.Advance(TimeSpan.FromHours(1) + TimeSpan.FromSeconds(second), PetActivity.Dozing);
        Assert.AreEqual(100, mood.Energy, 0.001);
        Assert.AreEqual(35, mood.Curiosity, 0.001);
        mood.RecordStretchCompleted();
        Assert.AreEqual(100, mood.Energy, 0.001);
    }

    [TestMethod]
    public void ClickBurstAndSuccessToken_HaveExplicitCausesAndExpiry()
    {
        var mood = new PetMoodState();
        Assert.IsFalse(mood.CanPout(TimeSpan.Zero));
        Assert.IsFalse(mood.HasPrideOpportunity(TimeSpan.Zero));
        mood.RecordValidClick(TimeSpan.Zero);
        mood.RecordValidClick(TimeSpan.FromSeconds(1));
        Assert.AreEqual(60, mood.Irritation, 0.001);
        Assert.IsTrue(mood.CanPout(TimeSpan.FromSeconds(2)));
        mood.RecordValidClick(TimeSpan.FromSeconds(2));
        Assert.AreEqual(100, mood.Irritation, 0.001);
        mood.RecordPoutCompleted();
        Assert.AreEqual(60, mood.Irritation, 0.001);
        Assert.IsFalse(mood.CanPout(TimeSpan.FromSeconds(11)), "Old input cannot trigger a delayed pout.");

        mood.RecordClimbCompleted(TimeSpan.FromSeconds(12));
        Assert.IsTrue(mood.HasPrideOpportunity(TimeSpan.FromSeconds(24)));
        Assert.IsFalse(mood.HasPrideOpportunity(TimeSpan.FromSeconds(25)));
        mood.RecordClimbCompleted(TimeSpan.FromSeconds(26));
        mood.RecordValidClick(TimeSpan.FromSeconds(27));
        Assert.IsFalse(mood.HasPrideOpportunity(TimeSpan.FromSeconds(27)), "Input invalidates an unplayed victory expression.");
    }

    [TestMethod]
    public void TenMinuteSeededTrace_IsDeterministicAndRespectsDriveGates()
    {
        var first = Simulate(719);
        var second = Simulate(719);
        CollectionAssert.AreEqual(first, second);
        Console.WriteLine("Seed 719 / 600 s: " + string.Join(", ", first
            .GroupBy(item => item.Id, StringComparer.Ordinal)
            .OrderBy(group => group.Key, StringComparer.Ordinal)
            .Select(group => $"{group.Key}={group.Count()}")));
        Assert.IsGreaterThan(20, first.Count);
        Assert.IsTrue(first.Any(item => item.Id == BehaviorDefinitions.Walk));
        Assert.IsTrue(first.Any(item => item.Id == BehaviorDefinitions.Run));
        Assert.IsTrue(first.All(item => item.Id != BehaviorDefinitions.Run || item.Energy > BehaviorPlanner.DozeEnergyThreshold));
        Assert.IsTrue(first.All(item => item.Id != BehaviorDefinitions.IdlePout || item.Irritation >= 55));
        Assert.IsTrue(first.All(item => item.Id != BehaviorDefinitions.SitDoze || item.Energy <= BehaviorPlanner.DozeEnergyThreshold));
        Assert.IsTrue(first.All(item => (item.Reason is "weighted" or "exhaustion") && item.Candidates.Length > 0));
        Assert.IsFalse(first.Zip(first.Skip(1)).Any(pair =>
            pair.First.Id == BehaviorDefinitions.SitDoze && pair.Second.Id == BehaviorDefinitions.SitDoze));
        Assert.IsFalse(first.Zip(first.Skip(1)).Any(pair =>
            pair.First.Id == BehaviorDefinitions.Run && pair.Second.Id == BehaviorDefinitions.SitDoze));

        foreach (var seed in Enumerable.Range(720, 9))
        {
            var sample = Simulate(seed);
            var dozes = sample.Count(item => item.Id == BehaviorDefinitions.SitDoze);
            var walks = sample.Count(item => item.Id == BehaviorDefinitions.Walk);
            var runs = sample.Count(item => item.Id == BehaviorDefinitions.Run);
            Assert.IsGreaterThanOrEqualTo(18, walks, $"Seed {seed} should keep walking.");
            Assert.IsGreaterThanOrEqualTo(18, runs, $"Seed {seed} should keep running.");
            Assert.IsLessThanOrEqualTo(3, dozes, $"Seed {seed} should not overdoze.");
            Console.WriteLine($"Seed {seed} / 600 s: walk={walks}, run={runs}, doze={dozes}");
        }
    }

    private static List<TraceEntry> Simulate(int seed)
    {
        var planner = new BehaviorPlanner(new SystemRandomSource(new Random(seed)));
        var trace = new List<TraceEntry>();
        planner.EnterIdleHub(TimeSpan.Zero);
        var activity = PetActivity.Resting;
        BehaviorDefinition? active = null;
        var activeUntil = 0;
        var idleEnteredAt = 0;

        for (var second = 0; second <= 600; second++)
        {
            var now = TimeSpan.FromSeconds(second);
            planner.AdvanceMood(now, activity);
            if (second is 100 or 101) planner.RecordValidClick(now);
            if (active is not null && second >= activeUntil)
            {
                switch (active.Id)
                {
                    case BehaviorDefinitions.LookAround: planner.RecordLookAroundCompleted(); break;
                    case BehaviorDefinitions.Stretch: planner.RecordStretchCompleted(); break;
                    case BehaviorDefinitions.IdlePout: planner.RecordPoutCompleted(); break;
                    case BehaviorDefinitions.FreeClimb: planner.RecordClimbCompleted(now); break;
                }
                active = null;
                activity = PetActivity.Resting;
                idleEnteredAt = second;
                planner.EnterIdleHub(now);
            }
            if (active is not null || second - idleEnteredAt < 2) continue;

            var chosen = planner.ChooseAutonomousBehavior(now);
            if (chosen is null) continue;
            var decision = planner.LastDecision!;
            trace.Add(new(second, chosen.Id, planner.Energy, planner.Curiosity, planner.Irritation,
                decision.Reason, string.Join(',', decision.Eligible.Select(candidate => $"{candidate.Id}:{candidate.Weight}"))));
            active = chosen;
            activity = chosen.Id switch
            {
                BehaviorDefinitions.Walk => PetActivity.Walking,
                BehaviorDefinitions.Run => PetActivity.Running,
                BehaviorDefinitions.FreeClimb or BehaviorDefinitions.FreeDescend => PetActivity.Climbing,
                BehaviorDefinitions.SitDoze => PetActivity.Dozing,
                _ => PetActivity.Resting,
            };
            activeUntil = second + (chosen.Id == BehaviorDefinitions.SitDoze ? 6 :
                chosen.Id is BehaviorDefinitions.Walk or BehaviorDefinitions.Run or
                    BehaviorDefinitions.FreeClimb or BehaviorDefinitions.FreeDescend ? 4 : 2);
        }
        return trace;
    }

    private sealed record TraceEntry(
        int Second, string Id, double Energy, double Curiosity, double Irritation, string Reason, string Candidates);
}

using Bolttagu.Contracts;

namespace Bolttagu.Core;

public interface IRandomSource
{
    int NextInt(int minimumInclusive, int maximumExclusive);
}

public sealed class SystemRandomSource(Random random) : IRandomSource
{
    public int NextInt(int minimumInclusive, int maximumExclusive) =>
        random.Next(minimumInclusive, maximumExclusive);
}

public interface IMonotonicClock
{
    TimeSpan Elapsed { get; }
}

public sealed class StopwatchClock : IMonotonicClock
{
    private readonly System.Diagnostics.Stopwatch _stopwatch = System.Diagnostics.Stopwatch.StartNew();
    public TimeSpan Elapsed => _stopwatch.Elapsed;
}

public sealed record PlannedWalk(
    FacingDirection Facing,
    double TargetX,
    double SpeedPixelsPerSecond,
    bool RequiresTurn);

public sealed record PlannedClimb(
    double TargetHeight,
    double SpeedPixelsPerSecond);

public readonly record struct AutonomousAffordances(bool CanClimb, bool CanDescend)
{
    public static AutonomousAffordances All { get; } = new(true, true);
}

public sealed record BehaviorCandidateWeight(string Id, int Weight);
public sealed record BehaviorDecisionTrace(
    TimeSpan At,
    double Energy,
    double Curiosity,
    double Irritation,
    IReadOnlyList<BehaviorCandidateWeight> Eligible,
    string? SelectedId,
    string Reason);

public sealed class BehaviorPlanner(IRandomSource random)
{
    public const double DozeEnergyThreshold = 20;
    public const double ExhaustedEnergyThreshold = 8;
    private readonly Queue<string> _recent = new();
    private readonly Dictionary<string, TimeSpan> _lastSelected = new(StringComparer.Ordinal);
    private TimeSpan _idleHubEnteredAt;
    private TimeSpan? _lastLocomotionAt;
    private TimeSpan? _lastUserInputAt;
    private string? _lastBehaviorId;
    public PetMoodState Mood { get; } = new();
    public double Energy => Mood.Energy;
    public double Curiosity => Mood.Curiosity;
    public double Irritation => Mood.Irritation;
    public BehaviorDecisionTrace? LastDecision { get; private set; }

    public void AdvanceMood(TimeSpan now, PetActivity activity)
    {
        if (activity is PetActivity.Walking or PetActivity.Running or PetActivity.Climbing)
            _lastLocomotionAt = now;
        Mood.Advance(now, activity);
    }

    public TimeSpan NextIdleDelay() =>
        TimeSpan.FromMilliseconds(random.NextInt(800, 2501));

    public PlannedWalk PlanWalk(
        ScreenPoint position,
        ScreenSize petSize,
        ScreenArea workArea,
        FacingDirection currentFacing)
    {
        var facing = random.NextInt(0, 2) == 0 ? FacingDirection.Left : FacingDirection.Right;
        var distance = Energy <= DozeEnergyThreshold ? random.NextInt(80, 181) : random.NextInt(180, 481);
        var minimumX = workArea.Origin.X;
        var maximumX = Math.Max(minimumX, workArea.Right - petSize.Width);
        var signedDistance = facing == FacingDirection.Left ? -distance : distance;
        var targetX = Math.Clamp(position.X + signedDistance, minimumX, maximumX);

        if (Math.Abs(targetX - position.X) < 24)
        {
            facing = facing == FacingDirection.Left ? FacingDirection.Right : FacingDirection.Left;
            signedDistance = facing == FacingDirection.Left ? -distance : distance;
            targetX = Math.Clamp(position.X + signedDistance, minimumX, maximumX);
        }

        return new(facing, targetX, Energy <= DozeEnergyThreshold ? 56 : 72, facing != currentFacing);
    }

    public PlannedClimb PlanFreeClimb(ScreenSize petSize)
    {
        var hundredthsOfPetHeight = random.NextInt(125, 301);
        return new(petSize.Height * hundredthsOfPetHeight / 100d, 84);
    }

    public PlannedWalk PlanRun(
        ScreenPoint position,
        ScreenSize petSize,
        ScreenArea workArea,
        FacingDirection currentFacing)
    {
        var facing = random.NextInt(0, 2) == 0 ? FacingDirection.Left : FacingDirection.Right;
        var distance = random.NextInt(300, 701);
        var minimumX = workArea.Origin.X;
        var maximumX = Math.Max(minimumX, workArea.Right - petSize.Width);
        var signedDistance = facing == FacingDirection.Left ? -distance : distance;
        var targetX = Math.Clamp(position.X + signedDistance, minimumX, maximumX);
        if (Math.Abs(targetX - position.X) < 48)
        {
            facing = facing == FacingDirection.Left ? FacingDirection.Right : FacingDirection.Left;
            signedDistance = facing == FacingDirection.Left ? -distance : distance;
            targetX = Math.Clamp(position.X + signedDistance, minimumX, maximumX);
        }
        return new(facing, targetX, 132, facing != currentFacing);
    }

    public PlannedClimb PlanFreeDescend(ScreenSize petSize)
    {
        var hundredthsOfPetHeight = random.NextInt(125, 301);
        return new(petSize.Height * hundredthsOfPetHeight / 100d, 84);
    }

    public bool ShouldStartRopeClimb() => Energy > DozeEnergyThreshold &&
        random.NextInt(0, 100) < Math.Clamp(20 + (int)(Curiosity * 0.4), 20, 60);

    public void EnterIdleHub(TimeSpan now) => _idleHubEnteredAt = now;
    public void RecordLocomotion(TimeSpan now) => _lastLocomotionAt = now;
    public void RecordUserInput(TimeSpan now) => _lastUserInputAt = now;
    public void RecordValidClick(TimeSpan now)
    {
        RecordUserInput(now);
        Mood.RecordValidClick(now);
    }
    public void RecordLookAroundCompleted() => Mood.RecordLookAroundCompleted();
    public void RecordStretchCompleted() => Mood.RecordStretchCompleted();
    public void RecordPoutCompleted() => Mood.RecordPoutCompleted();
    public void RecordClimbCompleted(TimeSpan now) => Mood.RecordClimbCompleted(now);
    public void InvalidatePride() => Mood.InvalidatePride();

    public BehaviorDefinition? ChooseAutonomousBehavior(
        TimeSpan now,
        IEnumerable<BehaviorDefinition>? definitions = null,
        AutonomousAffordances? affordances = null)
    {
        if (now - _idleHubEnteredAt < TimeSpan.FromMilliseconds(1500))
        {
            RecordDecision(now, [], null, "idle-dwell");
            return null;
        }
        var available = affordances ?? AutonomousAffordances.All;
        var candidates = (definitions ?? BehaviorDefinitions.Autonomous)
            .Where(definition => IsEligible(definition, now, available))
            .ToArray();
        if (candidates.Length == 0)
        {
            RecordDecision(now, [], null, "no-eligible-action");
            return null;
        }
        var weights = candidates.Select(definition => new BehaviorCandidateWeight(
            definition.Id, EffectiveWeight(definition, now))).ToArray();
        var doze = candidates.FirstOrDefault(definition => definition.Id == BehaviorDefinitions.SitDoze);
        if (Energy <= ExhaustedEnergyThreshold && doze is not null)
        {
            RecordDecision(now, weights, doze.Id, "exhaustion");
            return RecordSelection(doze, now);
        }
        var totalWeight = weights.Sum(candidate => candidate.Weight);
        if (totalWeight <= 0)
        {
            RecordDecision(now, weights, null, "no-positive-weight");
            return null;
        }
        var pick = random.NextInt(0, totalWeight);
        BehaviorDefinition selected = candidates[^1];
        for (var index = 0; index < candidates.Length; index++)
        {
            pick -= weights[index].Weight;
            if (pick < 0) { selected = candidates[index]; break; }
        }
        RecordDecision(now, weights, selected.Id, "weighted");
        return RecordSelection(selected, now);
    }

    private void RecordDecision(TimeSpan now, IReadOnlyList<BehaviorCandidateWeight> weights, string? selectedId, string reason) =>
        LastDecision = new(now, Energy, Curiosity, Irritation, weights, selectedId, reason);

    private BehaviorDefinition RecordSelection(BehaviorDefinition selected, TimeSpan now)
    {
        _lastSelected[selected.Id] = now;
        _recent.Enqueue(selected.Id);
        while (_recent.Count > 2) _recent.Dequeue();
        _lastBehaviorId = selected.Id;
        if (selected.Id == BehaviorDefinitions.IdleProud) Mood.ConsumePride(now);
        return selected;
    }

    private int EffectiveWeight(BehaviorDefinition definition, TimeSpan now)
    {
        var weight = Math.Max(0, definition.Weight);
        return definition.Id switch
        {
            BehaviorDefinitions.Run => 35 + (int)(Curiosity * 0.8),
            BehaviorDefinitions.LookAround => weight + (int)(Curiosity / 5),
            BehaviorDefinitions.Stretch => Energy <= 60 ? weight * 2 : weight,
            BehaviorDefinitions.IdleDazed => 5,
            BehaviorDefinitions.IdleProud => 60,
            BehaviorDefinitions.IdlePout => 45,
            BehaviorDefinitions.SitDoze => weight * 15,
            BehaviorDefinitions.FreeClimb => weight / 2 + (Curiosity >= 55 ? (int)(Curiosity / 8) : 0),
            BehaviorDefinitions.FreeDescend => weight / 2 + (int)(Curiosity / 16),
            _ => weight,
        };
    }

    private bool IsEligible(BehaviorDefinition definition, TimeSpan now, AutonomousAffordances affordances)
    {
        if (_recent.Contains(definition.Id, StringComparer.Ordinal)) return false;
        if (_lastSelected.TryGetValue(definition.Id, out var last) && definition.Cooldown is { } cooldown && now - last < cooldown) return false;
        if (Energy <= DozeEnergyThreshold && definition.Id is BehaviorDefinitions.Run or BehaviorDefinitions.FreeClimb or BehaviorDefinitions.FreeDescend) return false;
        if (definition.Id == BehaviorDefinitions.Walk && Energy <= 0) return false;
        if (definition.Id == BehaviorDefinitions.FreeClimb && !affordances.CanClimb) return false;
        if (definition.Id == BehaviorDefinitions.FreeDescend && !affordances.CanDescend) return false;
        if (definition.Id == BehaviorDefinitions.IdleDazed && Energy > 35) return false;
        if (definition.Id == BehaviorDefinitions.IdleProud && (!Mood.HasPrideOpportunity(now) || Irritation >= 55)) return false;
        if (definition.Id == BehaviorDefinitions.IdlePout && !Mood.CanPout(now)) return false;
        if (definition.Id == BehaviorDefinitions.SitDoze && Energy > DozeEnergyThreshold) return false;
        if (_lastBehaviorId is BehaviorDefinitions.IdlePout or BehaviorDefinitions.IdleProud &&
            definition.Id is BehaviorDefinitions.IdlePout or BehaviorDefinitions.IdleProud &&
            definition.Id != _lastBehaviorId) return false;
        if (definition.Id == BehaviorDefinitions.SitDoze &&
            ((_lastLocomotionAt is { } locomotion && now - locomotion < TimeSpan.FromSeconds(8)) ||
             (_lastUserInputAt is { } input && now - input < TimeSpan.FromSeconds(10)))) return false;
        return true;
    }
}

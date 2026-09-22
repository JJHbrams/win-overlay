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

public enum PetActivity { Resting, Walking, Running, Climbing, Dozing }

public sealed class BehaviorPlanner(IRandomSource random)
{
    public const int RopeClimbChancePercent = 35;
    public const double DozeEnergyThreshold = 20;
    public const double ExhaustedEnergyThreshold = 8;
    private const double ActivityTickLimitSeconds = 1;
    private readonly Queue<string> _recent = new();
    private readonly Dictionary<string, TimeSpan> _lastSelected = new(StringComparer.Ordinal);
    private TimeSpan _idleHubEnteredAt;
    private TimeSpan? _lastLocomotionAt;
    private TimeSpan? _lastUserInputAt;
    private TimeSpan? _lastMoodUpdateAt;
    private string? _lastBehaviorId;
    private TimeSpan? _curiousUntil;

    public double Energy { get; private set; } = 100;

    public void AdvanceMood(TimeSpan now, PetActivity activity)
    {
        if (activity is PetActivity.Walking or PetActivity.Running or PetActivity.Climbing)
            _lastLocomotionAt = now;
        if (_lastMoodUpdateAt is not { } previous)
        {
            _lastMoodUpdateAt = now;
            return;
        }
        var seconds = Math.Clamp((now - previous).TotalSeconds, 0, ActivityTickLimitSeconds);
        _lastMoodUpdateAt = now;
        var rate = activity switch
        {
            PetActivity.Walking => -0.9,
            PetActivity.Running => -2.5,
            PetActivity.Climbing => -2.0,
            PetActivity.Dozing => 7.0,
            _ => 0.25,
        };
        Energy = Math.Clamp(Energy + seconds * rate, 0, 100);
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
        var distance = random.NextInt(180, 481);
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

        return new(facing, targetX, 72, facing != currentFacing);
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

    public bool ShouldStartRopeClimb() =>
        random.NextInt(0, 100) < RopeClimbChancePercent;

    public void EnterIdleHub(TimeSpan now) => _idleHubEnteredAt = now;
    public void RecordLocomotion(TimeSpan now) => _lastLocomotionAt = now;
    public void RecordUserInput(TimeSpan now) => _lastUserInputAt = now;

    public BehaviorDefinition? ChooseAutonomousBehavior(TimeSpan now, IEnumerable<BehaviorDefinition>? definitions = null)
    {
        if (now - _idleHubEnteredAt < TimeSpan.FromMilliseconds(1500)) return null;
        var candidates = (definitions ?? BehaviorDefinitions.Autonomous)
            .Where(definition => IsEligible(definition, now))
            .ToArray();
        if (candidates.Length == 0) return null;
        var doze = candidates.FirstOrDefault(definition => definition.Id == BehaviorDefinitions.SitDoze);
        if (Energy <= ExhaustedEnergyThreshold && doze is not null) return RecordSelection(doze, now);
        var totalWeight = candidates.Sum(definition => EffectiveWeight(definition, now));
        if (totalWeight <= 0) return null;
        var pick = random.NextInt(0, totalWeight);
        BehaviorDefinition selected = candidates[^1];
        foreach (var candidate in candidates)
        {
            pick -= EffectiveWeight(candidate, now);
            if (pick < 0) { selected = candidate; break; }
        }
        return RecordSelection(selected, now);
    }

    private BehaviorDefinition RecordSelection(BehaviorDefinition selected, TimeSpan now)
    {
        _lastSelected[selected.Id] = now;
        _recent.Enqueue(selected.Id);
        while (_recent.Count > 2) _recent.Dequeue();
        _lastBehaviorId = selected.Id;
        if (selected.Id == BehaviorDefinitions.LookAround) _curiousUntil = now + TimeSpan.FromSeconds(12);
        return selected;
    }

    private int EffectiveWeight(BehaviorDefinition definition, TimeSpan now)
    {
        var weight = Math.Max(0, definition.Weight);
        if (definition.Id == BehaviorDefinitions.SitDoze) return Energy <= DozeEnergyThreshold ? weight * 15 : 0;
        if (_curiousUntil is { } curiousUntil && now <= curiousUntil)
        {
            if (definition.Id == BehaviorDefinitions.Walk) return weight * 2;
            if (definition.Id is BehaviorDefinitions.Run or BehaviorDefinitions.FreeClimb) return weight * 3;
        }
        return weight;
    }

    private bool IsEligible(BehaviorDefinition definition, TimeSpan now)
    {
        if (_recent.Contains(definition.Id, StringComparer.Ordinal)) return false;
        if (_lastSelected.TryGetValue(definition.Id, out var last) && definition.Cooldown is { } cooldown && now - last < cooldown) return false;
        if (Energy <= DozeEnergyThreshold && definition.Id is BehaviorDefinitions.Run or BehaviorDefinitions.FreeClimb or BehaviorDefinitions.FreeDescend) return false;
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

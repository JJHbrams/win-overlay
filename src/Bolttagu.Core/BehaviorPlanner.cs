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

public sealed class BehaviorPlanner(IRandomSource random)
{
    public const int RopeClimbChancePercent = 35;
    private readonly Queue<string> _recent = new();
    private readonly Dictionary<string, TimeSpan> _lastSelected = new(StringComparer.Ordinal);
    private TimeSpan _idleHubEnteredAt;
    private TimeSpan? _lastLocomotionAt;
    private TimeSpan? _lastUserInputAt;

    public TimeSpan NextIdleDelay() =>
        TimeSpan.FromMilliseconds(random.NextInt(2000, 5001));

    public PlannedWalk PlanWalk(
        ScreenPoint position,
        ScreenSize petSize,
        ScreenArea workArea,
        FacingDirection currentFacing)
    {
        var facing = random.NextInt(0, 2) == 0 ? FacingDirection.Left : FacingDirection.Right;
        var distance = random.NextInt(120, 321);
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
        var totalWeight = candidates.Sum(definition => Math.Max(0, definition.Weight));
        if (totalWeight <= 0) return null;
        var pick = random.NextInt(0, totalWeight);
        BehaviorDefinition selected = candidates[^1];
        foreach (var candidate in candidates)
        {
            pick -= Math.Max(0, candidate.Weight);
            if (pick < 0) { selected = candidate; break; }
        }
        _lastSelected[selected.Id] = now;
        _recent.Enqueue(selected.Id);
        while (_recent.Count > 2) _recent.Dequeue();
        return selected;
    }

    private bool IsEligible(BehaviorDefinition definition, TimeSpan now)
    {
        if (_recent.Contains(definition.Id, StringComparer.Ordinal)) return false;
        if (_lastSelected.TryGetValue(definition.Id, out var last) && definition.Cooldown is { } cooldown && now - last < cooldown) return false;
        if (definition.Id == BehaviorDefinitions.SitDoze &&
            ((_lastLocomotionAt is { } locomotion && now - locomotion < TimeSpan.FromSeconds(8)) ||
             (_lastUserInputAt is { } input && now - input < TimeSpan.FromSeconds(10)))) return false;
        return true;
    }
}

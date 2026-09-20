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

public sealed class BehaviorPlanner(IRandomSource random)
{
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

        return new(facing, targetX, 90, facing != currentFacing);
    }
}

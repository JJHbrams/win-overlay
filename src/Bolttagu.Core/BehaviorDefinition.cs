using Bolttagu.Contracts;

namespace Bolttagu.Core;

public enum PetPose
{
    Standing,
    Seated,
    Hanging,
    Airborne,
    GroundedCompressed,
    Climbing,
}

public enum BehaviorCompletionPolicy { AdvanceOnClipComplete, TimedLoop, External }
public enum BehaviorInterruptPolicy { AutonomousOnly, Click, Drag, SupportLost, Exit }

public sealed record BehaviorStep(
    string ClipId,
    PetPose EntryPose,
    PetPose ExitPose,
    BehaviorCompletionPolicy Completion = BehaviorCompletionPolicy.AdvanceOnClipComplete,
    int LoopCount = 0,
    TimeSpan? LoopDuration = null)
{
    public bool IsLoop => Completion == BehaviorCompletionPolicy.TimedLoop;
}

public sealed record BehaviorDefinition(
    string Id,
    PetPose EntryPose,
    IReadOnlyList<BehaviorStep> Steps,
    PetPose ExitPose,
    BehaviorInterruptPolicy InterruptPolicy,
    int Weight = 1,
    TimeSpan? Cooldown = null);

public static class BehaviorDefinitionValidator
{
    public static void Validate(BehaviorDefinition definition, ISet<string>? knownClipIds = null)
    {
        if (string.IsNullOrWhiteSpace(definition.Id)) throw new InvalidDataException("Behavior id is required.");
        if (definition.Steps.Count == 0) throw new InvalidDataException($"Behavior '{definition.Id}' has no steps.");
        var pose = definition.EntryPose;
        foreach (var step in definition.Steps)
        {
            if (string.IsNullOrWhiteSpace(step.ClipId)) throw new InvalidDataException($"Behavior '{definition.Id}' has an orphan step.");
            if (knownClipIds is not null && !knownClipIds.Contains(step.ClipId)) throw new InvalidDataException($"Behavior '{definition.Id}' references unknown clip '{step.ClipId}'.");
            if (step.EntryPose != pose) throw new InvalidDataException($"Behavior '{definition.Id}' has a pose mismatch at '{step.ClipId}'.");
            if (step.IsLoop && (step.LoopCount <= 0 || step.LoopDuration is not { } duration || duration <= TimeSpan.Zero)) throw new InvalidDataException($"Behavior '{definition.Id}' has a loop without termination.");
            pose = step.ExitPose;
        }
        if (pose != definition.ExitPose) throw new InvalidDataException($"Behavior '{definition.Id}' exit pose does not match its final step.");
    }

    public static void ValidateAll(IEnumerable<BehaviorDefinition> definitions, ISet<string>? knownClipIds = null)
    {
        var ids = new HashSet<string>(StringComparer.Ordinal);
        foreach (var definition in definitions)
        {
            Validate(definition, knownClipIds);
            if (!ids.Add(definition.Id)) throw new InvalidDataException($"Behavior '{definition.Id}' is duplicated.");
        }
    }
}

public static class BehaviorDefinitions
{
    public static readonly TimeSpan DozeLoopCycleDuration = TimeSpan.FromMilliseconds(2400);
    public const int WalkWeight = 80;
    public const int RunWeight = 55;
    public const int SitDozeWeight = 5;
    public const string Walk = "walk";
    public const string Run = "run";
    public const string LookAround = "look-around";
    public const string Stretch = "stretch";
    public const string SitDoze = "sit-doze";
    public const string IdleDazed = "idle-dazed";
    public const string IdleProud = "idle-proud";
    public const string IdlePout = "idle-pout";
    public const string FreeClimb = "free-climb";
    public const string FreeDescend = "free-descend";

    public static IReadOnlyList<BehaviorDefinition> Autonomous { get; } =
    [
        new(Walk, PetPose.Standing,
            [new(PetActionClips.Turn, PetPose.Standing, PetPose.Standing), new(PetActionClips.Walk, PetPose.Standing, PetPose.Standing, BehaviorCompletionPolicy.External), new(PetActionClips.TurnToIdle, PetPose.Standing, PetPose.Standing)],
            PetPose.Standing, BehaviorInterruptPolicy.AutonomousOnly, WalkWeight, TimeSpan.FromSeconds(3)),
        new(Run, PetPose.Standing,
            [new(PetActionClips.Turn, PetPose.Standing, PetPose.Standing), new(PetActionClips.Run, PetPose.Standing, PetPose.Standing, BehaviorCompletionPolicy.External), new(PetActionClips.TurnToIdle, PetPose.Standing, PetPose.Standing)],
            PetPose.Standing, BehaviorInterruptPolicy.AutonomousOnly, RunWeight, TimeSpan.FromSeconds(3)),
        new(LookAround, PetPose.Standing,
            [new(PetActionClips.LookAround, PetPose.Standing, PetPose.Standing)],
            PetPose.Standing, BehaviorInterruptPolicy.AutonomousOnly, 19, TimeSpan.FromSeconds(3)),
        new(Stretch, PetPose.Standing,
            [new(PetActionClips.Stretch, PetPose.Standing, PetPose.Standing)],
            PetPose.Standing, BehaviorInterruptPolicy.AutonomousOnly, 14, TimeSpan.FromSeconds(4)),
        new(IdleDazed, PetPose.Standing,
            [new(PetActionClips.IdleDazed, PetPose.Standing, PetPose.Standing)],
            PetPose.Standing, BehaviorInterruptPolicy.AutonomousOnly, 1, TimeSpan.FromSeconds(15)),
        new(IdleProud, PetPose.Standing,
            [new(PetActionClips.IdleProud, PetPose.Standing, PetPose.Standing)],
            PetPose.Standing, BehaviorInterruptPolicy.AutonomousOnly, 1, TimeSpan.FromSeconds(15)),
        new(IdlePout, PetPose.Standing,
            [new(PetActionClips.IdlePout, PetPose.Standing, PetPose.Standing)],
            PetPose.Standing, BehaviorInterruptPolicy.AutonomousOnly, 1, TimeSpan.FromSeconds(15)),
        new(SitDoze, PetPose.Standing,
            [new(PetActionClips.SitDown, PetPose.Standing, PetPose.Seated), new(PetActionClips.SitSettle, PetPose.Seated, PetPose.Seated, BehaviorCompletionPolicy.TimedLoop, 1, TimeSpan.FromMilliseconds(750)), new(PetActionClips.DozeEnter, PetPose.Seated, PetPose.Seated), new(PetActionClips.DozeLoop, PetPose.Seated, PetPose.Seated, BehaviorCompletionPolicy.TimedLoop, 2, DozeLoopCycleDuration), new(PetActionClips.WakeUp, PetPose.Seated, PetPose.Seated), new(PetActionClips.StandUp, PetPose.Seated, PetPose.Standing)],
            PetPose.Standing, BehaviorInterruptPolicy.AutonomousOnly, SitDozeWeight, TimeSpan.FromSeconds(10)),
        new(FreeClimb, PetPose.Standing,
            [new(PetActionClips.FreeClimbPrepare, PetPose.Standing, PetPose.Climbing)],
            PetPose.Climbing, BehaviorInterruptPolicy.AutonomousOnly, 8, TimeSpan.FromSeconds(8)),
        new(FreeDescend, PetPose.Standing,
            [new(PetActionClips.FreeClimbDownPrepare, PetPose.Standing, PetPose.Climbing)],
            PetPose.Climbing, BehaviorInterruptPolicy.AutonomousOnly, 8, TimeSpan.FromSeconds(8)),
    ];

    public static BehaviorDefinition CreateWalk(bool requiresTurn)
    {
        var steps = new List<BehaviorStep>();
        if (requiresTurn) steps.Add(new(PetActionClips.Turn, PetPose.Standing, PetPose.Standing));
        steps.Add(new(PetActionClips.Walk, PetPose.Standing, PetPose.Standing, BehaviorCompletionPolicy.External));
        steps.Add(new(PetActionClips.TurnToIdle, PetPose.Standing, PetPose.Standing));
        return new(Walk, PetPose.Standing, steps, PetPose.Standing, BehaviorInterruptPolicy.AutonomousOnly);
    }

    public static BehaviorDefinition CreateRun(bool requiresTurn)
    {
        var steps = new List<BehaviorStep>();
        if (requiresTurn) steps.Add(new(PetActionClips.Turn, PetPose.Standing, PetPose.Standing));
        steps.Add(new(PetActionClips.Run, PetPose.Standing, PetPose.Standing, BehaviorCompletionPolicy.External));
        steps.Add(new(PetActionClips.TurnToIdle, PetPose.Standing, PetPose.Standing));
        return new(Run, PetPose.Standing, steps, PetPose.Standing, BehaviorInterruptPolicy.AutonomousOnly);
    }
}

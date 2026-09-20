using Bolttagu.Contracts;
using Bolttagu.Core;

namespace Bolttagu.Runtime;

/// <summary>Owns clip-by-clip progression for one declarative behavior sequence.</summary>
public sealed class BehaviorSequenceRunner
{
    private readonly IAnimationPlayer _player;
    private BehaviorDefinition? _definition;
    private int _stepIndex;
    private int _loopsRemaining;
    private TimeSpan _loopDeadline;

    public BehaviorSequenceRunner(IAnimationPlayer player) => _player = player;
    public BehaviorDefinition? Current => _definition;
    public PetPose Pose { get; private set; } = PetPose.Standing;
    public bool IsRunning => _definition is not null;
    public event EventHandler<BehaviorDefinition>? Completed;
    public event EventHandler<string>? StepStarted;

    public void Start(BehaviorDefinition definition, TimeSpan now)
    {
        BehaviorDefinitionValidator.Validate(definition);
        Cancel();
        _definition = definition;
        Pose = definition.EntryPose;
        _stepIndex = 0;
        PlayCurrent(now);
    }

    public void Cancel()
    {
        _definition = null;
        _stepIndex = 0;
        _loopsRemaining = 0;
        _loopDeadline = TimeSpan.Zero;
    }

    public bool HandleCompletion(string clipId, TimeSpan now)
    {
        if (_definition is null || _stepIndex >= _definition.Steps.Count) return false;
        var step = _definition.Steps[_stepIndex];
        if (!string.Equals(step.ClipId, clipId, StringComparison.Ordinal) || step.Completion == BehaviorCompletionPolicy.External) return false;
        if (step.IsLoop)
        {
            if (_loopsRemaining <= 0) _loopsRemaining = step.LoopCount;
            return true;
        }
        Pose = step.ExitPose;
        _stepIndex++;
        if (_stepIndex < _definition.Steps.Count)
        {
            PlayCurrent(now);
            return true;
        }
        var completed = _definition;
        _definition = null;
        Pose = completed.ExitPose;
        Completed?.Invoke(this, completed);
        return true;
    }

    public bool AdvanceExternal(TimeSpan now)
    {
        if (_definition is null || _stepIndex >= _definition.Steps.Count ||
            _definition.Steps[_stepIndex].Completion != BehaviorCompletionPolicy.External) return false;
        Pose = _definition.Steps[_stepIndex].ExitPose;
        _stepIndex++;
        if (_stepIndex < _definition.Steps.Count) { PlayCurrent(now); return true; }
        var completed = _definition;
        _definition = null;
        Pose = completed.ExitPose;
        Completed?.Invoke(this, completed);
        return true;
    }

    public bool Tick(TimeSpan now)
    {
        if (_definition is null || _stepIndex >= _definition.Steps.Count) return false;
        var step = _definition.Steps[_stepIndex];
        if (!step.IsLoop || now < _loopDeadline) return false;
        Pose = step.ExitPose;
        _stepIndex++;
        if (_stepIndex < _definition.Steps.Count)
        {
            PlayCurrent(now);
            return true;
        }
        var completed = _definition;
        _definition = null;
        Pose = completed.ExitPose;
        Completed?.Invoke(this, completed);
        return true;
    }

    private void PlayCurrent(TimeSpan now)
    {
        var step = _definition!.Steps[_stepIndex];
        _loopsRemaining = step.IsLoop ? step.LoopCount : 0;
        _loopDeadline = step.IsLoop ? now + TimeSpan.FromTicks(step.LoopDuration!.Value.Ticks * step.LoopCount) : TimeSpan.Zero;
        _player.Play(step.ClipId);
        StepStarted?.Invoke(this, step.ClipId);
    }
}

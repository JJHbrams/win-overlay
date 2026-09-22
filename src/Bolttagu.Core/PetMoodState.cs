namespace Bolttagu.Core;

public enum PetActivity { Resting, Walking, Running, Climbing, Dozing, Neutral }

/// <summary>Bounded, deterministic drives. Physical state and animation ownership stay in the runtime.</summary>
public sealed class PetMoodState
{
    private static readonly TimeSpan ClickBurstWindow = TimeSpan.FromSeconds(6);
    private static readonly TimeSpan PrideWindow = TimeSpan.FromSeconds(12);
    private readonly Queue<TimeSpan> _validClicks = new();
    private TimeSpan? _lastUpdateAt;
    private TimeSpan? _lastValidClickAt;
    private TimeSpan? _prideUntil;

    public double Energy { get; private set; } = 100;
    public double Curiosity { get; private set; } = 25;
    public double Irritation { get; private set; }
    public TimeSpan? LastValidClickAt => _lastValidClickAt;

    public bool HasPrideOpportunity(TimeSpan now) => _prideUntil is { } until && now <= until;

    public void Advance(TimeSpan now, PetActivity activity)
    {
        if (_lastUpdateAt is not { } previous)
        {
            _lastUpdateAt = now;
            return;
        }

        var seconds = Math.Clamp((now - previous).TotalSeconds, 0, 1);
        _lastUpdateAt = now;
        var (energyRate, curiosityRate) = activity switch
        {
            PetActivity.Resting => (0.25, 0.20),
            PetActivity.Walking => (-0.5, -1.0),
            PetActivity.Running => (-1.5, -3.0),
            PetActivity.Climbing => (-1.2, -3.0),
            PetActivity.Dozing => (8.0, -2.0),
            _ => (0.0, 0.0),
        };
        Energy = Math.Clamp(Energy + seconds * energyRate, 0, 100);
        Curiosity = Math.Clamp(Curiosity + seconds * curiosityRate, 0, 100);
        Irritation = Math.Clamp(Irritation - seconds * 2, 0, 100);
    }

    public void RecordValidClick(TimeSpan now)
    {
        while (_validClicks.TryPeek(out var oldest) && now - oldest > ClickBurstWindow) _validClicks.Dequeue();
        _validClicks.Enqueue(now);
        _lastValidClickAt = now;
        Irritation = Math.Clamp(Irritation + 30 + (_validClicks.Count == 3 ? 20 : 0), 0, 100);
        InvalidatePride();
    }

    public bool CanPout(TimeSpan now) =>
        Irritation >= 55 && _lastValidClickAt is { } last && now - last <= TimeSpan.FromSeconds(8);

    public void RecordLookAroundCompleted() => Curiosity = Math.Clamp(Curiosity + 55, 0, 100);
    public void RecordStretchCompleted() => Energy = Math.Clamp(Energy + 3, 0, 100);
    public void RecordPoutCompleted() => Irritation = Math.Clamp(Irritation - 40, 0, 100);
    public void RecordClimbCompleted(TimeSpan now) => _prideUntil = now + PrideWindow;
    public void InvalidatePride() => _prideUntil = null;

    public bool ConsumePride(TimeSpan now)
    {
        if (!HasPrideOpportunity(now)) return false;
        _prideUntil = null;
        return true;
    }
}

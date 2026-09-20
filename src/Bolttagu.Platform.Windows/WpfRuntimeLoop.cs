using System.Windows.Threading;

namespace Bolttagu.Platform.Windows;

public sealed class WpfRuntimeLoop : IDisposable
{
    private readonly DispatcherTimer _timer;

    public WpfRuntimeLoop(Dispatcher dispatcher, Action tick)
    {
        ArgumentNullException.ThrowIfNull(dispatcher);
        ArgumentNullException.ThrowIfNull(tick);
        _timer = new(DispatcherPriority.Background, dispatcher)
        {
            Interval = TimeSpan.FromMilliseconds(33),
        };
        _timer.Tick += (_, _) => tick();
    }

    public void Start() => _timer.Start();
    public void Dispose() => _timer.Stop();
}

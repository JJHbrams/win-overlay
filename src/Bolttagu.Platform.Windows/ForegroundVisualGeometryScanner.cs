using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
using Bolttagu.Contracts;

namespace Bolttagu.Platform.Windows;

public interface IVisualGeometrySnapshotSource
{
    VisualGeometrySnapshot? GetLatest(DateTimeOffset now, TimeSpan maximumAge);
}

public readonly record struct ForegroundCaptureResult(long ForegroundWindowId, CapturedWindowFrame? Frame);

public interface IForegroundWindowFrameCapture
{
    ForegroundCaptureResult Capture(DateTimeOffset now);
}

public sealed class VisualScanScheduler(TimeSpan interval)
{
    private readonly object _gate = new();
    private DateTimeOffset _lastStarted = DateTimeOffset.MinValue;
    private bool _running;

    public bool TryStart(DateTimeOffset now)
    {
        lock (_gate)
        {
            if (_running || (_lastStarted != DateTimeOffset.MinValue && now - _lastStarted < interval)) return false;
            _running = true;
            _lastStarted = now;
            return true;
        }
    }

    public void Complete()
    {
        lock (_gate) _running = false;
    }
}

public sealed class VisualGeometrySnapshotTracker : IVisualGeometrySnapshotSource
{
    private readonly object _gate = new();
    private VisualGeometrySnapshot? _latest;
    private int _consecutiveMisses;

    public void Observe(long foregroundWindowId, DateTimeOffset capturedAt, IReadOnlyList<VisualGeometry>? geometry)
    {
        lock (_gate)
        {
            if (_latest is { } previous && previous.ForegroundWindowId != foregroundWindowId)
            {
                _latest = geometry is null ? null : new(foregroundWindowId, capturedAt, geometry);
                _consecutiveMisses = geometry is { Count: > 0 } ? 0 : 1;
                return;
            }

            if (geometry is { Count: > 0 })
            {
                _latest = new(foregroundWindowId, capturedAt, geometry);
                _consecutiveMisses = 0;
                return;
            }

            _consecutiveMisses++;
            if (_consecutiveMisses < 2 && _latest is not null) return;
            _latest = geometry is null ? null : new(foregroundWindowId, capturedAt, geometry);
        }
    }

    public VisualGeometrySnapshot? GetLatest(DateTimeOffset now, TimeSpan maximumAge)
    {
        lock (_gate)
        {
            return _latest is { } snapshot && now - snapshot.CapturedAt <= maximumAge
                ? snapshot
                : null;
        }
    }
}

public sealed class ForegroundVisualGeometryScanner : IVisualGeometrySnapshotSource, IDisposable
{
    public static readonly TimeSpan ScanInterval = TimeSpan.FromMilliseconds(250);
    public static readonly TimeSpan MaximumSnapshotAge = TimeSpan.FromMilliseconds(750);
    private readonly IForegroundWindowFrameCapture _capture;
    private readonly VisualGeometryDetector _detector;
    private readonly VisualGeometrySnapshotTracker _tracker = new();
    private readonly VisualScanScheduler _scheduler = new(ScanInterval);
    private readonly TimeProvider _timeProvider;
    private readonly System.Threading.Timer _timer;
    private bool _disposed;

    public ForegroundVisualGeometryScanner(
        IForegroundWindowFrameCapture capture,
        VisualGeometryDetector? detector = null,
        TimeProvider? timeProvider = null)
    {
        _capture = capture;
        _detector = detector ?? new();
        _timeProvider = timeProvider ?? TimeProvider.System;
        _timer = new(_ => QueueScan(), null, Timeout.InfiniteTimeSpan, Timeout.InfiniteTimeSpan);
    }

    public void Start() => _timer.Change(TimeSpan.Zero, ScanInterval);

    public VisualGeometrySnapshot? GetLatest(DateTimeOffset now, TimeSpan maximumAge) =>
        _tracker.GetLatest(now, maximumAge);

    private void QueueScan()
    {
        if (_disposed) return;
        var now = _timeProvider.GetUtcNow();
        if (!_scheduler.TryStart(now)) return;
        _ = Task.Run(() => Scan(now));
    }

    private void Scan(DateTimeOffset now)
    {
        try
        {
            var result = _capture.Capture(now);
            var geometry = result.Frame is { } frame ? _detector.Detect(frame) : null;
            _tracker.Observe(result.ForegroundWindowId, now, geometry);
        }
        catch (Exception exception) when (exception is ExternalException or InvalidOperationException or ArgumentException)
        {
            _tracker.Observe(0, now, null);
        }
        finally
        {
            _scheduler.Complete();
        }
    }

    public void Dispose()
    {
        _disposed = true;
        _timer.Dispose();
    }
}

public sealed class GdiForegroundWindowFrameCapture(nint coordinateWindowHandle) : IForegroundWindowFrameCapture
{
    private const uint PrintWindowRenderFullContent = 2;

    public ForegroundCaptureResult Capture(DateTimeOffset now)
    {
        var foreground = GetForegroundWindow();
        if (foreground == IntPtr.Zero || foreground == coordinateWindowHandle || !GetWindowRect(foreground, out var rect))
            return new(foreground.ToInt64(), null);
        var width = rect.Right - rect.Left;
        var height = rect.Bottom - rect.Top;
        if (width < 48 || height < 24) return new(foreground.ToInt64(), null);

        using var bitmap = new Bitmap(width, height, PixelFormat.Format32bppArgb);
        using (var graphics = Graphics.FromImage(bitmap))
        {
            var deviceContext = graphics.GetHdc();
            try
            {
                if (!PrintWindow(foreground, deviceContext, PrintWindowRenderFullContent))
                    return new(foreground.ToInt64(), null);
            }
            finally
            {
                graphics.ReleaseHdc(deviceContext);
            }
        }

        var data = bitmap.LockBits(new(0, 0, width, height), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
        try
        {
            var stride = Math.Abs(data.Stride);
            var bytes = new byte[stride * height];
            Marshal.Copy(data.Scan0, bytes, 0, bytes.Length);
            var dpi = Math.Max(1d, GetDpiForWindow(coordinateWindowHandle) / 96d);
            return new(foreground.ToInt64(), new(
                foreground.ToInt64(), now, new(rect.Left / dpi, rect.Top / dpi), dpi,
                width, height, stride, bytes));
        }
        finally
        {
            bitmap.UnlockBits(data);
        }
    }

    [DllImport("user32.dll")]
    private static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetWindowRect(IntPtr handle, out NativeRect rect);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool PrintWindow(IntPtr handle, IntPtr deviceContext, uint flags);

    [DllImport("user32.dll")]
    private static extern uint GetDpiForWindow(IntPtr handle);

    [StructLayout(LayoutKind.Sequential)]
    private struct NativeRect
    {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }
}

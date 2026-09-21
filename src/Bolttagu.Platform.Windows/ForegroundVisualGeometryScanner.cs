using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
using Bolttagu.Contracts;

namespace Bolttagu.Platform.Windows;

public interface IVisualGeometrySnapshotSource
{
    VisualGeometrySnapshot? GetLatest(DateTimeOffset now, TimeSpan maximumAge);
}

public readonly record struct VisualCaptureResult(long CaptureScopeId, CapturedWindowFrame? Frame);

public interface IVisualFrameCapture
{
    VisualCaptureResult Capture(DateTimeOffset now);
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

    public void Observe(
        long captureScopeId,
        DateTimeOffset capturedAt,
        IReadOnlyList<VisualGeometry>? geometry,
        VisualCollisionMask? collisionMask = null)
    {
        lock (_gate)
        {
            if (_latest is { } previous && previous.CaptureScopeId != captureScopeId)
            {
                _latest = geometry is null ? null : new(captureScopeId, capturedAt, geometry, collisionMask);
                _consecutiveMisses = geometry is { Count: > 0 } ? 0 : 1;
                return;
            }

            if (geometry is { Count: > 0 })
            {
                _latest = new(captureScopeId, capturedAt, geometry, collisionMask);
                _consecutiveMisses = 0;
                return;
            }

            _consecutiveMisses++;
            if (_consecutiveMisses < 2 && _latest is not null) return;
            _latest = geometry is null ? null : new(captureScopeId, capturedAt, geometry, collisionMask);
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

public sealed class VisualGeometryScanner : IVisualGeometrySnapshotSource, IDisposable
{
    public static readonly TimeSpan ScanInterval = TimeSpan.FromMilliseconds(500);
    public static readonly TimeSpan MaximumSnapshotAge = TimeSpan.FromSeconds(3);
    private readonly IVisualFrameCapture _capture;
    private readonly VisualGeometryDetector _detector;
    private readonly VisualGeometrySnapshotTracker _tracker = new();
    private readonly VisualScanScheduler _scheduler = new(ScanInterval);
    private readonly TimeProvider _timeProvider;
    private readonly System.Threading.Timer _timer;
    private bool _disposed;

    public VisualGeometryScanner(
        IVisualFrameCapture capture,
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
            var analysis = result.Frame is { } frame ? _detector.Analyze(frame) : null;
            var geometry = analysis?.Geometry;
            if (result.Frame is { Exclusions.Count: > 0 } occludedFrame && geometry is not null)
            {
                geometry = VisualGeometryOcclusionMerger.Merge(
                    geometry,
                    _tracker.GetLatest(now, MaximumSnapshotAge),
                    occludedFrame);
            }
            _tracker.Observe(
                result.CaptureScopeId,
                _timeProvider.GetUtcNow(),
                geometry,
                analysis?.CollisionMask);
        }
        catch (Exception exception) when (exception is ExternalException or InvalidOperationException or ArgumentException)
        {
            _tracker.Observe(0, _timeProvider.GetUtcNow(), null);
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

public static class VisualGeometryOcclusionMerger
{
    public static IReadOnlyList<VisualGeometry> Merge(
        IReadOnlyList<VisualGeometry> detected,
        VisualGeometrySnapshot? previous,
        CapturedWindowFrame frame)
    {
        if (previous is null || previous.CaptureScopeId != frame.CaptureScopeId ||
            frame.Exclusions is not { Count: > 0 }) return detected;

        var occludedAreas = frame.Exclusions.Select(exclusion => new ScreenArea(
            new(
                frame.ScreenOrigin.X + exclusion.Left / frame.CoordinateScale,
                frame.ScreenOrigin.Y + exclusion.Top / frame.CoordinateScale),
            new(
                Math.Max(0, exclusion.Right - exclusion.Left) / frame.CoordinateScale,
                Math.Max(0, exclusion.Bottom - exclusion.Top) / frame.CoordinateScale)))
            .ToArray();
        var ids = detected.Select(item => item.Id).ToHashSet();
        var merged = detected.ToList();
        merged.AddRange(previous.Geometry.Where(item =>
            !ids.Contains(item.Id) && occludedAreas.Any(area => Intersects(item.Bounds, area))));
        return merged;
    }

    private static bool Intersects(ScreenArea left, ScreenArea right) =>
        left.Origin.X < right.Right && left.Right > right.Origin.X &&
        left.Origin.Y < right.Bottom && left.Bottom > right.Origin.Y;
}

public sealed class GdiVisibleDisplayFrameCapture(nint coordinateWindowHandle) : IVisualFrameCapture
{
    private const uint MonitorDefaultToNearest = 2;
    private const double CaptureScale = 0.25;
    private const int ExclusionPaddingPixels = 8;
    private const int StretchHalftone = 4;
    private const uint SourceCopy = 0x00CC0020;

    public VisualCaptureResult Capture(DateTimeOffset now)
    {
        var monitor = MonitorFromWindow(coordinateWindowHandle, MonitorDefaultToNearest);
        var info = new MonitorInfo { Size = Marshal.SizeOf<MonitorInfo>() };
        if (monitor == IntPtr.Zero || !GetMonitorInfo(monitor, ref info))
            return new(monitor.ToInt64(), null);
        var rect = info.Monitor;
        var width = rect.Right - rect.Left;
        var height = rect.Bottom - rect.Top;
        if (width < 48 || height < 24) return new(monitor.ToInt64(), null);
        var captureWidth = Math.Max(1, (int)Math.Round(width * CaptureScale));
        var captureHeight = Math.Max(1, (int)Math.Round(height * CaptureScale));

        using var bitmap = new Bitmap(captureWidth, captureHeight, PixelFormat.Format32bppArgb);
        using (var graphics = Graphics.FromImage(bitmap))
        {
            var destination = graphics.GetHdc();
            var desktop = GetDC(IntPtr.Zero);
            try
            {
                _ = SetStretchBltMode(destination, StretchHalftone);
                if (!StretchBlt(destination, 0, 0, captureWidth, captureHeight,
                        desktop, rect.Left, rect.Top, width, height, SourceCopy))
                    return new(monitor.ToInt64(), null);
            }
            finally
            {
                _ = ReleaseDC(IntPtr.Zero, desktop);
                graphics.ReleaseHdc(destination);
            }
        }

        var data = bitmap.LockBits(new(0, 0, captureWidth, captureHeight), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
        try
        {
            var stride = Math.Abs(data.Stride);
            var bytes = new byte[stride * captureHeight];
            Marshal.Copy(data.Scan0, bytes, 0, bytes.Length);
            var dpi = Math.Max(1d, GetDpiForWindow(coordinateWindowHandle) / 96d);
            IReadOnlyList<PixelExclusion> exclusions = GetWindowRect(coordinateWindowHandle, out var ownerRect)
                ? [ToCaptureExclusion(ownerRect, rect)]
                : [];
            return new(monitor.ToInt64(), new(
                monitor.ToInt64(), now, new(rect.Left / dpi, rect.Top / dpi), dpi * CaptureScale,
                captureWidth, captureHeight, stride, bytes, exclusions));
        }
        finally
        {
            bitmap.UnlockBits(data);
        }
    }

    private static PixelExclusion ToCaptureExclusion(NativeRect window, NativeRect monitor) => new(
        (int)Math.Floor((window.Left - monitor.Left) * CaptureScale) - ExclusionPaddingPixels,
        (int)Math.Floor((window.Top - monitor.Top) * CaptureScale) - ExclusionPaddingPixels,
        (int)Math.Ceiling((window.Right - monitor.Left) * CaptureScale) + ExclusionPaddingPixels,
        (int)Math.Ceiling((window.Bottom - monitor.Top) * CaptureScale) + ExclusionPaddingPixels);

    [DllImport("user32.dll")]
    private static extern IntPtr MonitorFromWindow(IntPtr handle, uint flags);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetMonitorInfo(IntPtr monitor, ref MonitorInfo info);

    [DllImport("user32.dll")]
    private static extern uint GetDpiForWindow(IntPtr handle);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetWindowRect(IntPtr handle, out NativeRect rect);

    [DllImport("user32.dll")]
    private static extern IntPtr GetDC(IntPtr handle);

    [DllImport("user32.dll")]
    private static extern int ReleaseDC(IntPtr handle, IntPtr deviceContext);

    [DllImport("gdi32.dll")]
    private static extern int SetStretchBltMode(IntPtr deviceContext, int mode);

    [DllImport("gdi32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool StretchBlt(
        IntPtr destination,
        int destinationX,
        int destinationY,
        int destinationWidth,
        int destinationHeight,
        IntPtr source,
        int sourceX,
        int sourceY,
        int sourceWidth,
        int sourceHeight,
        uint operation);

    [StructLayout(LayoutKind.Sequential)]
    private struct NativeRect
    {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct MonitorInfo
    {
        public int Size;
        public NativeRect Monitor;
        public NativeRect WorkArea;
        public uint Flags;
    }
}

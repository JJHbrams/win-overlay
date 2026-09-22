using Bolttagu.Contracts;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Interop;
using System.Windows.Media;

namespace Bolttagu.Platform.Windows;

public readonly record struct SurfaceProbeDebug(
    string Operation,
    bool Valid,
    ScreenPoint Probe,
    DesktopSurface Surface,
    int TextSurfaceCount,
    int VerticalSurfaceCount,
    long CaptureScopeId);

public sealed class DesktopSurfaceProvider(
    Window owner,
    IVisualGeometrySnapshotSource? visualGeometry = null,
    IReadOnlyList<Window>? excludedWindows = null) : IDesktopSurfaceProvider
{
    private const int DwmExtendedFrameBounds = 9;
    private const long TaskbarId = long.MinValue;
    private const long WorkAreaFallbackId = long.MinValue + 1;
    private readonly object _debugGate = new();
    private SurfaceProbeDebug _debugSnapshot;

    public SurfaceProbeDebug DebugSnapshot
    {
        get { lock (_debugGate) return _debugSnapshot; }
    }

    public DesktopSurface FindFirstBelow(double centerX, double fromY, ScreenArea workArea)
    {
        try
        {
            var candidates = Snapshot(workArea);
            var selected = DesktopSurfaceSelector.FindFirstBelow(candidates, centerX, fromY, workArea);
            PublishDebug("landing", true, centerX, fromY, selected, candidates);
            return selected;
        }
        catch (Exception exception) when (exception is InvalidOperationException or ExternalException)
        {
            var fallback = WorkAreaFallback(workArea);
            PublishDebug("landing-error", false, centerX, fromY, fallback, []);
            return fallback;
        }
    }

    public bool TryRefreshSupport(
        DesktopSurface expected,
        double centerX,
        double footY,
        ScreenArea workArea,
        out DesktopSurface current)
    {
        try
        {
            var candidates = Snapshot(workArea);
            if (expected.Kind is DesktopSurfaceKind.Taskbar or DesktopSurfaceKind.WorkAreaFallback)
            {
                current = candidates.First(candidate => candidate.Kind == DesktopSurfaceKind.Taskbar);
                var valid = centerX >= current.Left && centerX <= current.Right &&
                            Math.Abs(current.Top - footY) <= 3;
                PublishDebug("refresh", valid, centerX, footY, current, candidates);
                return valid;
            }

            if (expected.Kind == DesktopSurfaceKind.TextLine)
            {
                current = candidates
                    .Where(candidate => candidate.Kind == DesktopSurfaceKind.TextLine)
                    .Where(candidate => centerX >= candidate.Left && centerX <= candidate.Right)
                    .Where(candidate => Math.Abs(candidate.Top - footY) <= 6)
                    .OrderBy(candidate => Math.Abs(candidate.Top - expected.Top))
                    .FirstOrDefault();
                var valid = current.Bounds.Size.Width > 0;
                PublishDebug("refresh-text", valid, centerX, footY, current, candidates);
                return valid;
            }

            current = candidates.FirstOrDefault(candidate =>
                candidate.Kind == expected.Kind && candidate.Id == expected.Id);
            var refreshed = current.Bounds.Size.Width > 0 &&
                            centerX >= current.Left && centerX <= current.Right &&
                            Math.Abs(current.Top - footY) <= 3 &&
                            DesktopSurfaceSelector.IsTopExposed(candidates, current, centerX);
            PublishDebug("refresh", refreshed, centerX, footY, current, candidates);
            return refreshed;
        }
        catch (Exception exception) when (exception is InvalidOperationException or ExternalException)
        {
            current = default;
            return false;
        }
    }

    public bool TryFindRopeClimbObstacle(
        DesktopSurface support,
        double footY,
        double currentLeadingX,
        double nextLeadingX,
        FacingDirection facing,
        ScreenSize petSize,
        ScreenArea workArea,
        out DesktopSurface obstacle)
    {
        try
        {
            var candidates = Snapshot(workArea);
            return DesktopSurfaceSelector.TryFindRopeClimbObstacle(
                candidates, support, footY, currentLeadingX, nextLeadingX, facing, petSize, out obstacle);
        }
        catch (Exception exception) when (exception is InvalidOperationException or ExternalException)
        {
            obstacle = default;
            return false;
        }
    }

    public DesktopSurface? FindClimbIntercept(
        double centerX,
        double fromFootY,
        double targetFootY,
        ScreenArea workArea)
    {
        try
        {
            return DesktopSurfaceSelector.FindClimbIntercept(
                Snapshot(workArea), centerX, fromFootY, targetFootY);
        }
        catch (Exception exception) when (exception is InvalidOperationException or ExternalException)
        {
            return null;
        }
    }

    public bool TryFindRopeDescendObstacle(
        DesktopSurface support,
        double footY,
        double currentLeadingX,
        double nextLeadingX,
        FacingDirection facing,
        ScreenSize petSize,
        ScreenArea workArea,
        out DesktopSurface obstacle)
    {
        try
        {
            return DesktopSurfaceSelector.TryFindRopeDescendObstacle(
                Snapshot(workArea), support, footY, currentLeadingX, nextLeadingX, facing, petSize,
                out obstacle);
        }
        catch (Exception exception) when (exception is InvalidOperationException or ExternalException)
        {
            obstacle = default;
            return false;
        }
    }

    public DesktopSurface? FindDescendIntercept(
        double centerX,
        double fromFootY,
        double targetFootY,
        ScreenArea workArea)
    {
        try
        {
            return DesktopSurfaceSelector.FindDescendIntercept(
                Snapshot(workArea), centerX, fromFootY, targetFootY);
        }
        catch (Exception exception) when (exception is InvalidOperationException or ExternalException)
        {
            return null;
        }
    }

    public bool TryRefreshClimbAnchor(
        DesktopSurface expected,
        double edgeX,
        ScreenArea workArea,
        out DesktopSurface current)
    {
        try
        {
            return DesktopSurfaceSelector.TryRefreshClimbAnchor(
                Snapshot(workArea), expected, edgeX, out current);
        }
        catch (Exception exception) when (exception is InvalidOperationException or ExternalException)
        {
            current = default;
            return false;
        }
    }

    private IReadOnlyList<DesktopSurface> Snapshot(ScreenArea workArea)
    {
        var ownerHandle = new WindowInteropHelper(owner).Handle;
        var excludedHandles = excludedWindows?
            .Select(window => new WindowInteropHelper(window).Handle)
            .Where(handle => handle != IntPtr.Zero)
            .ToHashSet() ?? [];
        var dpi = VisualTreeHelper.GetDpi(owner);
        var candidates = new List<DesktopSurface>();
        var zOrder = 0;
        var foregroundHandle = GetForegroundWindow();
        EnumWindows((handle, _) =>
        {
            var currentZOrder = zOrder++;
            if (handle == ownerHandle || excludedHandles.Contains(handle) ||
                !IsWindowVisible(handle) || IsIconic(handle)) return true;
            if (!TryGetBounds(handle, out var rect)) return true;
            var left = rect.Left / dpi.DpiScaleX;
            var right = rect.Right / dpi.DpiScaleX;
            var top = rect.Top / dpi.DpiScaleY;
            var bottom = rect.Bottom / dpi.DpiScaleY;
            if (right - left < 48 || bottom - top < 24) return true;
            candidates.Add(new(
                new(new(left, top), new(right - left, bottom - top)),
                DesktopSurfaceKind.Window,
                handle.ToInt64(),
                currentZOrder,
                handle == foregroundHandle,
                IsZoomed(handle)));
            return true;
        }, IntPtr.Zero);

        var visualSnapshot = visualGeometry?.GetLatest(DateTimeOffset.UtcNow,
            VisualGeometryScanner.MaximumSnapshotAge);
        if (visualSnapshot is { } snapshot)
        {
            candidates.AddRange(snapshot.Geometry.Select(ToDesktopSurface));
        }

        candidates.Add(new(
            new(new(workArea.Origin.X, workArea.Bottom), new(workArea.Size.Width, 1)),
            DesktopSurfaceKind.Taskbar,
            TaskbarId));
        return candidates;
    }

    private static DesktopSurface ToDesktopSurface(VisualGeometry geometry) => new(
        geometry.Bounds,
        geometry.Kind is VisualGeometryKind.TextLine or VisualGeometryKind.HorizontalLine
            ? DesktopSurfaceKind.TextLine
            : DesktopSurfaceKind.VerticalLine,
        geometry.Id,
        0,
        true,
        false);

    private void PublishDebug(
        string operation,
        bool valid,
        double probeX,
        double probeY,
        DesktopSurface surface,
        IReadOnlyList<DesktopSurface> candidates)
    {
        var snapshot = new SurfaceProbeDebug(
            operation,
            valid,
            new(probeX, probeY),
            surface,
            candidates.Count(item => item.Kind == DesktopSurfaceKind.TextLine),
            candidates.Count(item => item.Kind == DesktopSurfaceKind.VerticalLine),
            visualGeometry?.GetLatest(DateTimeOffset.UtcNow, VisualGeometryScanner.MaximumSnapshotAge)
                ?.CaptureScopeId ?? 0);
        lock (_debugGate) _debugSnapshot = snapshot;
    }

    private static DesktopSurface WorkAreaFallback(ScreenArea workArea) => new(
        new(new(workArea.Origin.X, workArea.Bottom), new(workArea.Size.Width, 1)),
        DesktopSurfaceKind.WorkAreaFallback,
        WorkAreaFallbackId);

    private static bool TryGetBounds(IntPtr handle, out NativeRect rect)
    {
        if (DwmGetWindowAttribute(
                handle,
                DwmExtendedFrameBounds,
                out rect,
                Marshal.SizeOf<NativeRect>()) == 0)
        {
            return true;
        }
        return GetWindowRect(handle, out rect);
    }

    private delegate bool EnumWindowsCallback(IntPtr handle, IntPtr parameter);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool EnumWindows(EnumWindowsCallback callback, IntPtr parameter);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool IsWindowVisible(IntPtr handle);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool IsIconic(IntPtr handle);

    [DllImport("user32.dll")]
    private static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool IsZoomed(IntPtr handle);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetWindowRect(IntPtr handle, out NativeRect rect);

    [DllImport("dwmapi.dll")]
    private static extern int DwmGetWindowAttribute(
        IntPtr handle,
        int attribute,
        out NativeRect value,
        int size);

    [StructLayout(LayoutKind.Sequential)]
    private struct NativeRect
    {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }
}

public static class DesktopSurfaceSelector
{
    public static bool TryRefreshClimbAnchor(
        IEnumerable<DesktopSurface> candidates,
        DesktopSurface expected,
        double edgeX,
        out DesktopSurface current)
    {
        var all = candidates.ToArray();
        current = all
            .Where(candidate => candidate.Kind == expected.Kind)
            .Where(candidate => candidate.Id == expected.Id ||
                (expected.Kind == DesktopSurfaceKind.VerticalLine &&
                 Math.Abs(candidate.Left - expected.Left) <= 8 &&
                 Math.Abs(candidate.Top - expected.Top) <= 16 &&
                 Math.Abs(candidate.Bottom - expected.Bottom) <= 16))
            .Where(candidate => Math.Abs(candidate.Left - expected.Left) <= 8 &&
                Math.Abs(candidate.Right - expected.Right) <= 8)
            .Where(candidate => IsClimbEligible(all, candidate) &&
                edgeX >= candidate.Left - 8 && edgeX <= candidate.Right + 8)
            .OrderBy(candidate => candidate.Id == expected.Id ? 0 : 1)
            .ThenBy(candidate => Math.Abs(candidate.Left - expected.Left))
            .FirstOrDefault();
        return current.Bounds.Size.Width > 0;
    }

    public static DesktopSurface FindFirstBelow(
        IEnumerable<DesktopSurface> candidates,
        double centerX,
        double fromY,
        ScreenArea workArea)
    {
        var surface = candidates
            .Where(candidate => candidate.Kind != DesktopSurfaceKind.VerticalLine)
            .Where(candidate => centerX >= candidate.Left && centerX <= candidate.Right)
            .Where(candidate => candidate.Top >= fromY - 3)
            .Where(candidate => IsTopExposed(candidates, candidate, centerX))
            .OrderBy(candidate => candidate.Top)
            .FirstOrDefault();
        return surface.Bounds.Size.Width > 0
            ? surface
            : new(
                new(new(workArea.Origin.X, workArea.Bottom), new(workArea.Size.Width, 1)),
                DesktopSurfaceKind.WorkAreaFallback);
    }

    public static bool IsTopExposed(
        IEnumerable<DesktopSurface> candidates,
        DesktopSurface candidate,
        double centerX)
    {
        if (candidate.Kind != DesktopSurfaceKind.Window) return true;
        var probeY = candidate.Top + 1;
        return !candidates.Any(front =>
            front.Kind == DesktopSurfaceKind.Window &&
            front.Id != candidate.Id &&
            front.ZOrder < candidate.ZOrder &&
            centerX >= front.Left && centerX <= front.Right &&
            probeY >= front.Top && probeY <= front.Bounds.Bottom);
    }

    public static bool IsClimbEligible(IEnumerable<DesktopSurface> candidates, DesktopSurface candidate)
    {
        if (candidate.Kind == DesktopSurfaceKind.VerticalLine) return candidate.IsForeground;
        if (candidate.Kind != DesktopSurfaceKind.Window || candidate.IsMaximized || !candidate.IsForeground) return false;
        if (!IsTopExposed(candidates, candidate, (candidate.Left + candidate.Right) / 2d)) return false;
        return true;
    }

    public static bool TryFindRopeClimbObstacle(
        IEnumerable<DesktopSurface> candidates,
        DesktopSurface support,
        double footY,
        double currentLeadingX,
        double nextLeadingX,
        FacingDirection facing,
        ScreenSize petSize,
        out DesktopSurface obstacle)
    {
        var all = candidates.ToArray();
        var ascending = facing == FacingDirection.Right;
        obstacle = all
            .Where(candidate => candidate.Id != support.Id)
            .Where(candidate => IsClimbEligible(all, candidate))
            .Where(candidate => candidate.Top <= support.Top - petSize.Height)
            .Where(candidate => ascending
                ? candidate.Left >= currentLeadingX - 3 && candidate.Left <= nextLeadingX + 3
                : candidate.Right <= currentLeadingX + 3 && candidate.Right >= nextLeadingX - 3)
            .OrderBy(candidate => ascending ? candidate.Left : -candidate.Right)
            .FirstOrDefault();
        return obstacle.Bounds.Size.Width > 0;
    }

    public static DesktopSurface? FindClimbIntercept(
        IEnumerable<DesktopSurface> candidates,
        double centerX,
        double fromFootY,
        double targetFootY)
    {
        var all = candidates.ToArray();
        var intercept = all
            .Where(candidate => candidate.Kind == DesktopSurfaceKind.TextLine
                ? candidate.IsForeground
                : IsClimbEligible(all, candidate))
            .Where(candidate => candidate.Kind != DesktopSurfaceKind.VerticalLine)
            .Where(candidate => centerX >= candidate.Left && centerX <= candidate.Right)
            .Where(candidate => candidate.Top < fromFootY - 3 && candidate.Top >= targetFootY - 3)
            .OrderByDescending(candidate => candidate.Top)
            .FirstOrDefault();
        return intercept.Bounds.Size.Width > 0 ? intercept : null;
    }

    public static bool TryFindRopeDescendObstacle(
        IEnumerable<DesktopSurface> candidates,
        DesktopSurface support,
        double footY,
        double currentLeadingX,
        double nextLeadingX,
        FacingDirection facing,
        ScreenSize petSize,
        out DesktopSurface obstacle)
    {
        var ascending = facing == FacingDirection.Right;
        obstacle = candidates
            .Where(candidate => candidate.Kind == DesktopSurfaceKind.VerticalLine && candidate.IsForeground)
            .Where(candidate => candidate.Id != support.Id)
            .Where(candidate => candidate.Top >= support.Top - 6 && candidate.Top <= footY + 6)
            .Where(candidate => candidate.Bottom >= footY + Math.Min(48, petSize.Height / 2d))
            .Where(candidate => ascending
                ? candidate.Left >= currentLeadingX - 3 && candidate.Left <= nextLeadingX + 3
                : candidate.Right <= currentLeadingX + 3 && candidate.Right >= nextLeadingX - 3)
            .OrderBy(candidate => ascending ? candidate.Left : -candidate.Right)
            .FirstOrDefault();
        return obstacle.Bounds.Size.Width > 0;
    }

    public static DesktopSurface? FindDescendIntercept(
        IEnumerable<DesktopSurface> candidates,
        double centerX,
        double fromFootY,
        double targetFootY)
    {
        if (targetFootY < fromFootY) return null;
        var all = candidates.ToArray();
        var intercept = all
            .Where(candidate => candidate.Kind != DesktopSurfaceKind.VerticalLine)
            .Where(candidate => centerX >= candidate.Left && centerX <= candidate.Right)
            .Where(candidate => candidate.Top > fromFootY + 3 && candidate.Top <= targetFootY + 3)
            .Where(candidate => IsTopExposed(all, candidate, centerX))
            .OrderBy(candidate => candidate.Top)
            .FirstOrDefault();
        return intercept.Bounds.Size.Width > 0 ? intercept : null;
    }
}

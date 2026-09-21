using Bolttagu.Contracts;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Interop;
using System.Windows.Media;

namespace Bolttagu.Platform.Windows;

public sealed class DesktopSurfaceProvider(
    Window owner,
    IVisualGeometrySnapshotSource? visualGeometry = null) : IDesktopSurfaceProvider
{
    private const int DwmExtendedFrameBounds = 9;
    private const long TaskbarId = long.MinValue;
    private const long WorkAreaFallbackId = long.MinValue + 1;

    public DesktopSurface FindFirstBelow(double centerX, double fromY, ScreenArea workArea)
    {
        try
        {
            var candidates = Snapshot(workArea);
            return DesktopSurfaceSelector.FindFirstBelow(candidates, centerX, fromY, workArea);
        }
        catch (Exception exception) when (exception is InvalidOperationException or ExternalException)
        {
            return WorkAreaFallback(workArea);
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
                return centerX >= current.Left && centerX <= current.Right &&
                       Math.Abs(current.Top - footY) <= 3;
            }

            current = candidates.FirstOrDefault(candidate =>
                candidate.Kind == expected.Kind && candidate.Id == expected.Id);
            return current.Bounds.Size.Width > 0 &&
                   centerX >= current.Left && centerX <= current.Right &&
                   Math.Abs(current.Top - footY) <= 3 &&
                   DesktopSurfaceSelector.IsTopExposed(candidates, current, centerX);
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

    public bool TryRefreshClimbAnchor(
        DesktopSurface expected,
        double edgeX,
        ScreenArea workArea,
        out DesktopSurface current)
    {
        try
        {
            var candidates = Snapshot(workArea);
            current = candidates.FirstOrDefault(candidate =>
                candidate.Kind == expected.Kind && candidate.Id == expected.Id);
            return current.Bounds.Size.Width > 0 &&
                   Math.Abs(current.Left - expected.Left) <= 3 &&
                   Math.Abs(current.Right - expected.Right) <= 3 &&
                   DesktopSurfaceSelector.IsClimbEligible(candidates, current) &&
                   edgeX >= current.Left - 3 && edgeX <= current.Right + 3;
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
        var dpi = VisualTreeHelper.GetDpi(owner);
        var candidates = new List<DesktopSurface>();
        var zOrder = 0;
        var foregroundHandle = GetForegroundWindow();
        EnumWindows((handle, _) =>
        {
            var currentZOrder = zOrder++;
            if (handle == ownerHandle || !IsWindowVisible(handle) || IsIconic(handle)) return true;
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

        var visualSnapshot = visualGeometry?.GetLatest(
            DateTimeOffset.UtcNow,
            ForegroundVisualGeometryScanner.MaximumSnapshotAge);
        if (visualSnapshot is { } snapshot && snapshot.ForegroundWindowId == foregroundHandle.ToInt64())
        {
            candidates.AddRange(snapshot.Geometry.Select(geometry => new DesktopSurface(
                geometry.Bounds,
                geometry.Kind == VisualGeometryKind.TextLine
                    ? DesktopSurfaceKind.TextLine
                    : DesktopSurfaceKind.VerticalLine,
                geometry.Id,
                0,
                true,
                false)));
        }

        candidates.Add(new(
            new(new(workArea.Origin.X, workArea.Bottom), new(workArea.Size.Width, 1)),
            DesktopSurfaceKind.Taskbar,
            TaskbarId));
        return candidates;
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
}

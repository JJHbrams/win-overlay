using Bolttagu.Contracts;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Interop;
using System.Windows.Media;

namespace Bolttagu.Platform.Windows;

public sealed class DesktopSurfaceProvider(Window owner) : IDesktopSurfaceProvider
{
    private const int DwmExtendedFrameBounds = 9;

    public DesktopSurface FindFirstBelow(double centerX, double fromY, ScreenArea workArea)
    {
        try
        {
            var ownerHandle = new WindowInteropHelper(owner).Handle;
            var dpi = VisualTreeHelper.GetDpi(owner);
            var candidates = new List<DesktopSurface>();
            EnumWindows((handle, _) =>
            {
                if (handle == ownerHandle || !IsWindowVisible(handle) || IsIconic(handle)) return true;
                if (!TryGetBounds(handle, out var rect)) return true;
                var left = rect.Left / dpi.DpiScaleX;
                var right = rect.Right / dpi.DpiScaleX;
                var top = rect.Top / dpi.DpiScaleY;
                var bottom = rect.Bottom / dpi.DpiScaleY;
                if (right - left < 48 || bottom - top < 24) return true;
                if (centerX < left || centerX > right || top < fromY - 3) return true;
                candidates.Add(new(
                    new(new(left, top), new(right - left, bottom - top)),
                    DesktopSurfaceKind.Window));
                return true;
            }, IntPtr.Zero);

            candidates.Add(new(
                new(new(workArea.Origin.X, workArea.Bottom), new(workArea.Size.Width, 1)),
                DesktopSurfaceKind.Taskbar));
            return DesktopSurfaceSelector.FindFirstBelow(candidates, centerX, fromY, workArea);
        }
        catch (Exception exception) when (exception is InvalidOperationException or ExternalException)
        {
            return WorkAreaFallback(workArea);
        }
    }

    private static DesktopSurface WorkAreaFallback(ScreenArea workArea) => new(
        new(new(workArea.Origin.X, workArea.Bottom), new(workArea.Size.Width, 1)),
        DesktopSurfaceKind.WorkAreaFallback);

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
            .Where(candidate => centerX >= candidate.Left && centerX <= candidate.Right)
            .Where(candidate => candidate.Top >= fromY - 3)
            .OrderBy(candidate => candidate.Top)
            .FirstOrDefault();
        return surface.Bounds.Size.Width > 0
            ? surface
            : new(
                new(new(workArea.Origin.X, workArea.Bottom), new(workArea.Size.Width, 1)),
                DesktopSurfaceKind.WorkAreaFallback);
    }
}

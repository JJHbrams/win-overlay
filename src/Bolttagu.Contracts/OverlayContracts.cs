namespace Bolttagu.Contracts;

public readonly record struct ScreenPoint(double X, double Y);
public readonly record struct ScreenSize(double Width, double Height);
public readonly record struct ScreenArea(ScreenPoint Origin, ScreenSize Size)
{
    public double Right => Origin.X + Size.Width;
    public double Bottom => Origin.Y + Size.Height;
}

public enum DesktopSurfaceKind { Window, Taskbar, WorkAreaFallback }

public readonly record struct DesktopSurface(
    ScreenArea Bounds,
    DesktopSurfaceKind Kind,
    long Id = 0,
    int ZOrder = int.MaxValue)
{
    public double Top => Bounds.Origin.Y;
    public double Left => Bounds.Origin.X;
    public double Right => Bounds.Right;
}

public interface IDesktopSurfaceProvider
{
    DesktopSurface FindFirstBelow(double centerX, double fromY, ScreenArea workArea);
    bool TryRefreshSupport(
        DesktopSurface expected,
        double centerX,
        double footY,
        ScreenArea workArea,
        out DesktopSurface current);
}

public interface IOverlayWindow
{
    bool IsVisible { get; }
    ScreenPoint Position { get; }
    ScreenSize Size { get; }
    ScreenArea WorkArea { get; }
    event EventHandler? ClickObserved;
    event EventHandler? DragStarted;
    event EventHandler? DragCompleted;
    event EventHandler? DragCanceled;
    event EventHandler? ExitRequested;
    event EventHandler<double>? DpiScaleChanged;
    void ShowOverlay();
    void HideOverlay();
    void PlaceAtBottomRight(double margin);
    void MoveTo(ScreenPoint position);
    void CloseOverlay();
}

public interface ITrayController : IDisposable
{
    event EventHandler? ShowRequested;
    event EventHandler? HideRequested;
    event EventHandler? ExitRequested;
    void SetStatus(string status);
}

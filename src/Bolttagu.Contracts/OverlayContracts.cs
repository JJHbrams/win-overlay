namespace Bolttagu.Contracts;

public readonly record struct ScreenPoint(double X, double Y);
public readonly record struct ScreenSize(double Width, double Height);
public readonly record struct ScreenArea(ScreenPoint Origin, ScreenSize Size)
{
    public double Right => Origin.X + Size.Width;
    public double Bottom => Origin.Y + Size.Height;
}

public interface IOverlayWindow
{
    bool IsVisible { get; }
    ScreenPoint Position { get; }
    ScreenSize Size { get; }
    event EventHandler? ClickObserved;
    event EventHandler? ExitRequested;
    event EventHandler<double>? DpiScaleChanged;
    void ShowOverlay();
    void HideOverlay();
    void PlaceAtBottomRight(double margin);
    void CloseOverlay();
}

public interface ITrayController : IDisposable
{
    event EventHandler? ShowRequested;
    event EventHandler? HideRequested;
    event EventHandler? ExitRequested;
    void SetStatus(string status);
}


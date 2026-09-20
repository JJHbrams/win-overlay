using Bolttagu.Contracts;
using Bolttagu.Platform.Windows;
using Bolttagu.Presentation;
using System.Windows;

namespace Bolttagu.App;

public partial class App : System.Windows.Application
{
    private IOverlayWindow? _overlay;
    private ITrayController? _tray;

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        var view = new PetPlaceholderView();
        var overlay = new OverlayWindow(view);
        var tray = new TrayController();

        overlay.ClickObserved += (_, _) => view.ReactToClick();
        overlay.DpiScaleChanged += (_, scale) =>
        {
            view.SetDpiScale(scale);
            tray.SetStatus($"Bolttagu P0 · {scale:P0} DPI");
        };
        overlay.ExitRequested += (_, _) => ExitApplication();
        tray.ShowRequested += (_, _) => overlay.ShowOverlay();
        tray.HideRequested += (_, _) => overlay.HideOverlay();
        tray.ExitRequested += (_, _) => ExitApplication();

        _overlay = overlay;
        _tray = tray;
        overlay.PlaceAtBottomRight(24);
        overlay.ShowOverlay();
    }

    protected override void OnExit(ExitEventArgs e)
    {
        _tray?.Dispose();
        base.OnExit(e);
    }

    private void ExitApplication()
    {
        _overlay?.CloseOverlay();
        Shutdown();
    }
}

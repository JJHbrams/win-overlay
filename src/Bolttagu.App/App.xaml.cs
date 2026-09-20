using Bolttagu.Contracts;
using Bolttagu.Assets;
using Bolttagu.Platform.Windows;
using Bolttagu.Presentation;
using Bolttagu.Runtime;
using Bolttagu.Core;
using System.IO;
using System.Windows;

namespace Bolttagu.App;

public partial class App : System.Windows.Application
{
    private IOverlayWindow? _overlay;
    private ITrayController? _tray;
    private IAnimationPlayer? _animationPlayer;
    private PetAnimationController? _animationController;
    private WpfRuntimeLoop? _runtimeLoop;

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        var tray = new TrayController();
        var (view, player, setDpiScale, assetStatus) = CreatePetView();
        var overlay = new OverlayWindow(view);
        var animationController = new PetAnimationController(
            player,
            overlay,
            new BehaviorPlanner(new SystemRandomSource(Random.Shared)),
            new StopwatchClock(),
            new DesktopSurfaceProvider(overlay));
        var runtimeLoop = new WpfRuntimeLoop(Dispatcher, animationController.Tick);

        overlay.ClickObserved += (_, _) => animationController.ReactToClick();
        overlay.DragStarted += (_, _) => animationController.BeginDrag();
        overlay.DragCompleted += (_, _) => animationController.CompleteDrag();
        overlay.DragCanceled += (_, _) => animationController.CancelDrag();
        overlay.DpiScaleChanged += (_, scale) =>
        {
            setDpiScale(scale);
            tray.SetStatus($"Bolttagu P3 · {scale:P0} DPI · {assetStatus}");
        };
        overlay.ExitRequested += (_, _) => ExitApplication();
        tray.ShowRequested += (_, _) => overlay.ShowOverlay();
        tray.HideRequested += (_, _) => overlay.HideOverlay();
        tray.ExitRequested += (_, _) => ExitApplication();
        animationController.ExitReady += (_, _) => CompleteShutdown();

        _overlay = overlay;
        _tray = tray;
        _animationPlayer = player;
        _animationController = animationController;
        _runtimeLoop = runtimeLoop;
        overlay.PlaceAtBottomRight(24);
        overlay.ShowOverlay();
        animationController.Start();
        runtimeLoop.Start();
    }

    protected override void OnExit(ExitEventArgs e)
    {
        _runtimeLoop?.Dispose();
        _animationController?.Dispose();
        _animationPlayer?.Dispose();
        _tray?.Dispose();
        base.OnExit(e);
    }

    private void ExitApplication()
    {
        if (_overlay is { IsVisible: false }) _overlay.ShowOverlay();
        _animationController?.RequestExit();
    }

    private void CompleteShutdown()
    {
        _overlay?.CloseOverlay();
        Shutdown();
    }

    private static (FrameworkElement View, IAnimationPlayer Player, Action<double> SetDpiScale, string Status) CreatePetView()
    {
        try
        {
            var assetRoot = Path.Combine(AppContext.BaseDirectory, "Assets", "Bolttagu");
            var catalog = RuntimeAnimationCatalog.LoadOrFallback(
                Path.Combine(assetRoot, "build"),
                Path.Combine(assetRoot, "fallback", "character.png"));
            var view = new PetSpriteView(catalog);
            return (view, view, view.SetDpiScale, catalog.IsFallback ? "fallback" : "atlas");
        }
        catch (Exception)
        {
            var fallback = new PetPlaceholderView();
            return (fallback, fallback, fallback.SetDpiScale, "vector fallback");
        }
    }
}

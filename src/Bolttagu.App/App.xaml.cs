using Bolttagu.Contracts;
using Bolttagu.Assets;
using Bolttagu.Platform.Windows;
using Bolttagu.Presentation;
using Bolttagu.Runtime;
using Bolttagu.Core;
using System.IO;
using System.Windows;
using System.Windows.Interop;

namespace Bolttagu.App;

public partial class App : System.Windows.Application
{
    private IOverlayWindow? _overlay;
    private ITrayController? _tray;
    private IAnimationPlayer? _animationPlayer;
    private PetAnimationController? _animationController;
    private WpfRuntimeLoop? _runtimeLoop;
    private ForegroundVisualGeometryScanner? _visualGeometryScanner;
    private ContactVfxWindow? _contactVfx;

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);
        var tray = new TrayController();
        var (view, player, setDpiScale, assetStatus) = CreatePetView();
        var overlay = new OverlayWindow(view);
        var contactVfx = new ContactVfxWindow();
        var visualGeometryScanner = new ForegroundVisualGeometryScanner(
            new GdiForegroundWindowFrameCapture(() => new WindowInteropHelper(overlay).Handle));
        var animationController = new PetAnimationController(
            player,
            overlay,
            new BehaviorPlanner(new SystemRandomSource(Random.Shared)),
            new StopwatchClock(),
            new DesktopSurfaceProvider(overlay, visualGeometryScanner));
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
        tray.ShowRequested += (_, _) =>
        {
            contactVfx.ShowLayer();
            overlay.ShowOverlay();
        };
        tray.HideRequested += (_, _) =>
        {
            contactVfx.HideLayer();
            overlay.HideOverlay();
        };
        tray.ExitRequested += (_, _) => ExitApplication();
        animationController.ExitReady += (_, _) => CompleteShutdown();

        _overlay = overlay;
        _tray = tray;
        _animationPlayer = player;
        _animationController = animationController;
        _runtimeLoop = runtimeLoop;
        _visualGeometryScanner = visualGeometryScanner;
        _contactVfx = contactVfx;
        if (player is IAnimationFrameSource frameSource)
        {
            frameSource.FramePresented += (_, args) =>
            {
                if (args.ClipId is not (PetActionClips.RopeClimbLoop or PetActionClips.FreeClimbLoop))
                {
                    contactVfx.Clear();
                    return;
                }
                var origin = overlay.Position;
                contactVfx.UpdateContacts(args.Contacts.Select(contact => new VfxContact(
                    contact.Kind,
                    new(origin.X + contact.LocalPosition.X, origin.Y + contact.LocalPosition.Y))).ToArray());
            };
        }
        overlay.PlaceAtBottomRight(24);
        contactVfx.ShowLayer();
        overlay.ShowOverlay();
        visualGeometryScanner.Start();
        animationController.Start();
        runtimeLoop.Start();
    }

    protected override void OnExit(ExitEventArgs e)
    {
        _runtimeLoop?.Dispose();
        _visualGeometryScanner?.Dispose();
        _animationController?.Dispose();
        _animationPlayer?.Dispose();
        _contactVfx?.Dispose();
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

using Bolttagu.Platform.Windows;
using System.Threading;
using System.Windows.Controls;
using System.Windows.Interop;
using System.Windows.Threading;

namespace Bolttagu.Architecture.Tests;

[TestClass]
public sealed class OverlayWindowSmokeTests
{
    [TestMethod]
    public void OverlayWindow_CreatesARealTransparentTopmostHwnd()
    {
        Exception? failure = null;
        var thread = new Thread(() =>
        {
            try
            {
                var window = new OverlayWindow(new Border());
                window.Show();

                var handle = new WindowInteropHelper(window).Handle;
                Assert.AreNotEqual(IntPtr.Zero, handle);
                Assert.IsTrue(window.AllowsTransparency);
                Assert.IsTrue(window.Topmost);
                Assert.IsFalse(window.ShowInTaskbar);

                var overlay = (Bolttagu.Contracts.IOverlayWindow)window;
                var surfaces = new DesktopSurfaceProvider(window);
                var surface = surfaces.FindFirstBelow(
                    overlay.Position.X + (overlay.Size.Width / 2d),
                    overlay.Position.Y + overlay.Size.Height - 8,
                    overlay.WorkArea);
                Assert.IsGreaterThanOrEqualTo(
                    overlay.Position.Y + overlay.Size.Height - 11,
                    surface.Top,
                    "Desktop surface must be at or below the pet's foot probe.");
                _ = surfaces.TryRefreshSupport(
                    surface,
                    overlay.Position.X + (overlay.Size.Width / 2d),
                    surface.Top,
                    overlay.WorkArea,
                    out _);

                window.Close();
            }
            catch (Exception exception)
            {
                failure = exception;
            }
            finally
            {
                Dispatcher.CurrentDispatcher.InvokeShutdown();
            }
        });
        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();

        Assert.IsTrue(thread.Join(TimeSpan.FromSeconds(5)), "WPF smoke thread did not exit.");
        if (failure is not null)
        {
            Assert.Fail(failure.ToString());
        }
    }

    [TestMethod]
    public void TrayController_CanBeCreatedAndDisposed()
    {
        Exception? failure = null;
        var thread = new Thread(() =>
        {
            try
            {
                using var tray = new TrayController();
                tray.SetStatus("Bolttagu P0 test");
            }
            catch (Exception exception)
            {
                failure = exception;
            }
            finally
            {
                Dispatcher.CurrentDispatcher.InvokeShutdown();
            }
        });
        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();

        Assert.IsTrue(thread.Join(TimeSpan.FromSeconds(5)), "Tray smoke thread did not exit.");
        if (failure is not null)
        {
            Assert.Fail(failure.ToString());
        }
    }
}

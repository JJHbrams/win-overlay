using Bolttagu.Assets;
using Bolttagu.Contracts;
using Bolttagu.Core;
using Bolttagu.Runtime;
using System.IO;
using System.Threading;
using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;

namespace Bolttagu.Presentation.Tests;

[TestClass]
public sealed class AnimationPlaybackTests
{
    [TestMethod]
    public void Cursor_LoopsOrCompletesAccordingToClipPolicy()
    {
        var frame = new SpriteFrame("atlas.png", new(0, 0, 1, 1), TimeSpan.FromMilliseconds(100), new(0, 1));
        var looping = new AnimationPlaybackCursor(new("idle_breathe", true, [frame, frame]));
        var oneShot = new AnimationPlaybackCursor(new("click", false, [frame, frame]));

        Assert.IsFalse(looping.Advance());
        Assert.IsFalse(looping.Advance());
        Assert.AreEqual(0, looping.FrameIndex);
        Assert.IsFalse(oneShot.Advance());
        Assert.IsTrue(oneShot.Advance());
        Assert.AreEqual(1, oneShot.FrameIndex);
    }

    [TestMethod]
    public void RealSpriteView_LoopingDozeAdvancesByRunnerDeadlineWithoutCompletionEvent()
    {
        Exception? failure = null;
        var thread = new Thread(() =>
        {
            try
            {
                var catalog = RuntimeAnimationCatalog.Load(Path.Combine(FindRepositoryRoot(), "asset", "bolttagu", "build"));
                using var view = new PetSpriteView(catalog);
                var runner = new BehaviorSequenceRunner(view);
                runner.Start(BehaviorDefinitions.Autonomous.Single(x => x.Id == BehaviorDefinitions.SitDoze), TimeSpan.Zero);
                runner.HandleCompletion(PetActionClips.SitDown, TimeSpan.Zero);
                runner.Tick(TimeSpan.FromMilliseconds(750));
                runner.HandleCompletion(PetActionClips.DozeEnter, TimeSpan.FromMilliseconds(750));
                Assert.AreEqual(PetActionClips.DozeLoop, view.CurrentClipId);

                runner.Tick(TimeSpan.FromMilliseconds(5550));
                Assert.AreEqual(PetActionClips.WakeUp, view.CurrentClipId);
            }
            catch (Exception exception) { failure = exception; }
            finally { Dispatcher.CurrentDispatcher.InvokeShutdown(); }
        });
        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();
        Assert.IsTrue(thread.Join(TimeSpan.FromSeconds(5)), "Looping sprite playback thread did not exit.");
        if (failure is not null) Assert.Fail(failure.ToString());
    }

    [TestMethod]
    public void SpriteView_LoadsAtlasAndStartsBothClips()
    {
        Exception? failure = null;
        var thread = new Thread(() =>
        {
            try
            {
                var root = FindRepositoryRoot();
                var catalog = RuntimeAnimationCatalog.Load(Path.Combine(root, "asset", "bolttagu", "build"));
                using var view = new PetSpriteView(catalog);

                view.Play("idle_breathe");
                Assert.AreEqual("idle_breathe", view.CurrentClipId);
                Assert.AreEqual(0, view.CurrentFrameIndex);
                view.Play("click");
                Assert.AreEqual("click", view.CurrentClipId);
                Assert.AreEqual(0, view.CurrentFrameIndex);
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

        Assert.IsTrue(thread.Join(TimeSpan.FromSeconds(5)), "Sprite view smoke thread did not exit.");
        if (failure is not null)
        {
            Assert.Fail(failure.ToString());
        }
    }

    [TestMethod]
    public void SpriteView_RendersVisibleAtlasPixels()
    {
        Exception? failure = null;
        var thread = new Thread(() =>
        {
            try
            {
                var root = FindRepositoryRoot();
                var catalog = RuntimeAnimationCatalog.Load(Path.Combine(root, "asset", "bolttagu", "build"));
                using var view = new PetSpriteView(catalog);
                view.Play("idle_breathe");
                view.Measure(new Size(220, 220));
                view.Arrange(new Rect(0, 0, 220, 220));
                view.UpdateLayout();

                var rendered = new RenderTargetBitmap(220, 220, 96, 96, PixelFormats.Pbgra32);
                rendered.Render(view);
                var pixels = new byte[220 * 220 * 4];
                rendered.CopyPixels(pixels, 220 * 4, 0);
                var visiblePixels = 0;
                for (var index = 3; index < pixels.Length; index += 4)
                {
                    if (pixels[index] > 0)
                    {
                        visiblePixels++;
                    }
                }

                Assert.IsGreaterThan(10_000, visiblePixels, "Atlas sprite did not render enough visible pixels.");
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

        Assert.IsTrue(thread.Join(TimeSpan.FromSeconds(5)), "Sprite render thread did not exit.");
        if (failure is not null)
        {
            Assert.Fail(failure.ToString());
        }
    }

    [TestMethod]
    public void RealClickPlayback_CompletesAndReturnsToIdle()
    {
        Exception? failure = null;
        var thread = new Thread(() =>
        {
            try
            {
                var root = FindRepositoryRoot();
                var catalog = RuntimeAnimationCatalog.Load(Path.Combine(root, "asset", "bolttagu", "build"));
                using var view = new PetSpriteView(catalog);
                using var controller = new PetAnimationController(
                    view,
                    new TestWindow(),
                    new BehaviorPlanner(new FixedRandom()),
                    new FixedClock(),
                    new FixedSurfaceProvider());
                controller.Start();
                controller.ReactToClick();

                var frame = new DispatcherFrame();
                var timeout = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(1800) };
                timeout.Tick += (_, _) =>
                {
                    timeout.Stop();
                    frame.Continue = false;
                };
                timeout.Start();
                Dispatcher.PushFrame(frame);

                Assert.AreEqual("idle_breathe", view.CurrentClipId);
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

        Assert.IsTrue(thread.Join(TimeSpan.FromSeconds(5)), "Click playback thread did not exit.");
        if (failure is not null)
        {
            Assert.Fail(failure.ToString());
        }
    }

    [TestMethod]
    public void RealSpawnPlayback_CompletesAndEntersIdle()
    {
        Exception? failure = null;
        var thread = new Thread(() =>
        {
            try
            {
                var root = FindRepositoryRoot();
                var catalog = RuntimeAnimationCatalog.Load(Path.Combine(root, "asset", "bolttagu", "build"));
                using var view = new PetSpriteView(catalog);
                using var controller = new PetAnimationController(
                    view,
                    new TestWindow(),
                    new BehaviorPlanner(new FixedRandom()),
                    new FixedClock(),
                    new FixedSurfaceProvider());
                controller.Start();
                Assert.AreEqual(PetRuntimeState.Launching, controller.State);

                var frame = new DispatcherFrame();
                var timeout = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(1200) };
                timeout.Tick += (_, _) =>
                {
                    timeout.Stop();
                    frame.Continue = false;
                };
                timeout.Start();
                Dispatcher.PushFrame(frame);

                Assert.AreEqual(PetRuntimeState.Idle, controller.State);
                Assert.AreEqual("idle_breathe", view.CurrentClipId);
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

        Assert.IsTrue(thread.Join(TimeSpan.FromSeconds(5)), "Spawn playback thread did not exit.");
        if (failure is not null)
        {
            Assert.Fail(failure.ToString());
        }
    }

    private static string FindRepositoryRoot()
    {
        var current = new DirectoryInfo(AppContext.BaseDirectory);
        while (current is not null)
        {
            if (File.Exists(Path.Combine(current.FullName, "Bolttagu.slnx")))
            {
                return current.FullName;
            }
            current = current.Parent;
        }
        throw new DirectoryNotFoundException("Could not locate repository root.");
    }

    private sealed class FixedRandom : IRandomSource
    {
        public int NextInt(int minimumInclusive, int maximumExclusive) => minimumInclusive;
    }

    private sealed class FixedClock : IMonotonicClock
    {
        public TimeSpan Elapsed => TimeSpan.Zero;
    }

    private sealed class TestWindow : IOverlayWindow
    {
        public bool IsVisible => true;
        public ScreenPoint Position { get; private set; }
        public ScreenSize Size => new(220, 220);
        public ScreenArea WorkArea => new(new(0, 0), new(1920, 1080));
        public event EventHandler? ClickObserved { add { } remove { } }
        public event EventHandler? DragStarted { add { } remove { } }
        public event EventHandler? DragCompleted { add { } remove { } }
        public event EventHandler? DragCanceled { add { } remove { } }
        public event EventHandler? ExitRequested { add { } remove { } }
        public event EventHandler<double>? DpiScaleChanged { add { } remove { } }
        public void ShowOverlay() { }
        public void HideOverlay() { }
        public void PlaceAtBottomRight(double margin) { }
        public void MoveTo(ScreenPoint position) => Position = position;
        public void CloseOverlay() { }
    }

    private sealed class FixedSurfaceProvider : IDesktopSurfaceProvider
    {
        public DesktopSurface FindFirstBelow(double centerX, double fromY, ScreenArea workArea) =>
            new(new(new(0, workArea.Bottom), new(workArea.Size.Width, 1)), DesktopSurfaceKind.Taskbar);

        public bool TryRefreshSupport(
            DesktopSurface expected,
            double centerX,
            double footY,
            ScreenArea workArea,
            out DesktopSurface current)
        {
            current = FindFirstBelow(centerX, footY, workArea);
            return Math.Abs(current.Top - footY) <= 3;
        }
    }
}

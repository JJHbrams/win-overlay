using Bolttagu.Contracts;
using Bolttagu.Platform.Windows;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Shapes;
using System.Windows.Threading;

namespace Bolttagu.Architecture.Tests;

[TestClass]
public sealed class VisualGeometryDetectorTests
{
    [TestMethod]
    public void Detector_GroupsGlyphsIntoBoundedTextSurfaceAndFindsVerticalLine()
    {
        var pixels = WhiteFrame(240, 180);
        DrawBlackRectangle(pixels, 240, 20, 40, 8, 18);
        DrawBlackRectangle(pixels, 240, 34, 38, 9, 20);
        DrawBlackRectangle(pixels, 240, 50, 41, 7, 17);
        DrawBlackRectangle(pixels, 240, 20, 100, 150, 1);
        DrawBlackRectangle(pixels, 240, 180, 20, 3, 130);
        var frame = new CapturedWindowFrame(42, DateTimeOffset.UnixEpoch, new(100, 200), 1,
            240, 180, 240 * 4, pixels);

        var result = new VisualGeometryDetector().Detect(frame);

        var text = result.Single(geometry => geometry.Kind == VisualGeometryKind.TextLine);
        Assert.IsInRange(118d, 121d, text.Bounds.Origin.X);
        Assert.IsInRange(156d, 159d, text.Bounds.Right);
        Assert.IsInRange(237d, 240d, text.Bounds.Origin.Y);
        var line = result.Single(geometry => geometry.Kind == VisualGeometryKind.VerticalLine);
        Assert.IsInRange(278d, 281d, line.Bounds.Origin.X);
        Assert.IsInRange(282d, 285d, line.Bounds.Right);
        Assert.IsGreaterThanOrEqualTo(120, line.Bounds.Size.Height);
        var horizontal = result.Single(geometry => geometry.Kind == VisualGeometryKind.HorizontalLine);
        Assert.IsGreaterThanOrEqualTo(145, horizontal.Bounds.Size.Width);
        Assert.IsLessThanOrEqualTo(5, horizontal.Bounds.Size.Height);
    }

    [TestMethod]
    public void CollisionMask_RaycastsToGlyphPixelsAndReturnsTheLocalHorizontalRun()
    {
        var pixels = WhiteFrame(240, 180);
        DrawBlackRectangle(pixels, 240, 20, 40, 8, 18);
        DrawBlackRectangle(pixels, 240, 34, 38, 9, 20);
        DrawBlackRectangle(pixels, 240, 50, 41, 7, 17);
        var frame = new CapturedWindowFrame(42, DateTimeOffset.UnixEpoch, new(100, 200), 1,
            240, 180, 240 * 4, pixels);

        var analysis = new VisualGeometryDetector().Analyze(frame);
        var found = analysis.CollisionMask.TryFindPlatform(125, 210, 300, out var platform);

        Assert.IsTrue(found);
        Assert.AreEqual(VisualGeometryKind.TextLine, platform.Kind);
        Assert.IsInRange(235d, 242d, platform.Bounds.Origin.Y);
        Assert.IsLessThanOrEqualTo(125d, platform.Bounds.Origin.X);
        Assert.IsGreaterThanOrEqualTo(150d, platform.Bounds.Right);
    }

    [TestMethod]
    public void Detector_ExcludesThePetWindowFromGeometryAndCollision()
    {
        var pixels = WhiteFrame(240, 180);
        DrawBlackRectangle(pixels, 240, 20, 40, 150, 1);
        DrawBlackRectangle(pixels, 240, 180, 20, 3, 130);
        var frame = new CapturedWindowFrame(42, DateTimeOffset.UnixEpoch, new(0, 0), 1,
            240, 180, 240 * 4, pixels, [new(10, 10, 200, 160)]);

        var analysis = new VisualGeometryDetector().Analyze(frame);

        Assert.IsEmpty(analysis.Geometry);
        Assert.IsFalse(analysis.CollisionMask.TryFindPlatform(50, 0, 180, out _));
    }

    [TestMethod]
    public void OcclusionMerger_PreservesOnlyPriorGeometryHiddenBehindThePet()
    {
        var hidden = new VisualGeometry(7, VisualGeometryKind.HorizontalLine,
            new(new(100, 220), new(180, 2)), 42);
        var noLongerPresent = new VisualGeometry(8, VisualGeometryKind.TextLine,
            new(new(500, 400), new(120, 20)), 42);
        var detected = new VisualGeometry(9, VisualGeometryKind.VerticalLine,
            new(new(700, 100), new(2, 200)), 42);
        var previous = new VisualGeometrySnapshot(42, DateTimeOffset.UnixEpoch,
            [hidden, noLongerPresent]);
        var frame = new CapturedWindowFrame(42, DateTimeOffset.UnixEpoch, new(0, 0), 0.25,
            480, 270, 480 * 4, WhiteFrame(480, 270), [new(20, 40, 80, 70)]);

        var merged = VisualGeometryOcclusionMerger.Merge([detected], previous, frame);

        CollectionAssert.AreEquivalent(new long[] { 7, 9 }, merged.Select(item => item.Id).ToArray());
    }

    [TestMethod]
    public void SceneChangeDetector_RefreshesOnLargeVisibleContentChangeButIgnoresPetExclusion()
    {
        var detector = new VisualSceneChangeDetector();
        var white = new CapturedWindowFrame(42, DateTimeOffset.UnixEpoch, new(0, 0), 1,
            240, 180, 240 * 4, WhiteFrame(240, 180), [new(0, 0, 40, 40)]);
        var excludedPixels = WhiteFrame(240, 180);
        DrawBlackRectangle(excludedPixels, 240, 0, 0, 40, 40);
        var excludedOnly = white with { Bgra32 = excludedPixels };
        var changedPixels = WhiteFrame(240, 180);
        DrawBlackRectangle(changedPixels, 240, 0, 0, 240, 180);
        var black = white with { Bgra32 = changedPixels };

        Assert.IsFalse(detector.Observe(white));
        Assert.IsFalse(detector.Observe(excludedOnly));
        Assert.IsTrue(detector.Observe(black));
    }

    [TestMethod]
    public void SceneChangeDetector_DetectsSparseTextScrolling()
    {
        var detector = new VisualSceneChangeDetector();
        var beforePixels = WhiteFrame(240, 180);
        var afterPixels = WhiteFrame(240, 180);
        for (var x = 48; x <= 192; x += 16)
        {
            DrawBlackRectangle(beforePixels, 240, x, 40, 8, 12);
            DrawBlackRectangle(afterPixels, 240, x, 48, 8, 12);
        }
        var before = new CapturedWindowFrame(42, DateTimeOffset.UnixEpoch, new(0, 0), 1,
            240, 180, 240 * 4, beforePixels, [new(0, 0, 32, 32)]);
        var after = before with { Bgra32 = afterPixels };

        Assert.IsFalse(detector.Observe(before));
        Assert.IsTrue(detector.Observe(after));
    }

    [TestMethod]
    public void ScenePublicationGate_DebouncesTransitionFramesAndReplacesOnceStable()
    {
        var gate = new VisualScenePublicationGate();

        Assert.IsFalse(gate.ShouldPublish(sceneChanged: true, out var firstReplace));
        Assert.IsFalse(firstReplace);
        Assert.IsFalse(gate.ShouldPublish(sceneChanged: true, out var secondReplace));
        Assert.IsFalse(secondReplace);
        Assert.IsTrue(gate.ShouldPublish(sceneChanged: false, out var stableReplace));
        Assert.IsTrue(stableReplace);
        Assert.IsTrue(gate.ShouldPublish(sceneChanged: false, out var normalReplace));
        Assert.IsFalse(normalReplace);
    }

    [TestMethod]
    public void SnapshotTracker_UsesOneMissGraceThenInvalidatesAndRejectsStaleData()
    {
        var tracker = new VisualGeometrySnapshotTracker();
        var geometry = new[]
        {
            new VisualGeometry(7, VisualGeometryKind.TextLine, new(new(10, 20), new(100, 12)), 3),
        };
        var start = DateTimeOffset.UnixEpoch;
        tracker.Observe(3, start, geometry);
        tracker.Observe(3, start.AddMilliseconds(250), []);
        Assert.IsNotNull(tracker.GetLatest(start.AddMilliseconds(300), TimeSpan.FromMilliseconds(750)));

        tracker.Observe(3, start.AddMilliseconds(500), []);
        Assert.HasCount(0, tracker.GetLatest(start.AddMilliseconds(500), TimeSpan.FromMilliseconds(750))!.Geometry);
        Assert.IsNull(tracker.GetLatest(start.AddMilliseconds(1300), TimeSpan.FromMilliseconds(750)));

        tracker.Observe(4, start.AddMilliseconds(1400), null);
        Assert.IsNull(tracker.GetLatest(start.AddMilliseconds(1400), TimeSpan.FromMilliseconds(750)));
    }

    [TestMethod]
    public void PublishedSnapshot_RemainsUsableAcrossAHighResolutionScanInterval()
    {
        var tracker = new VisualGeometrySnapshotTracker();
        var completedAt = DateTimeOffset.UnixEpoch.AddMilliseconds(1400);
        tracker.Observe(3, completedAt,
        [
            new VisualGeometry(7, VisualGeometryKind.TextLine, new(new(10, 20), new(100, 12)), 3),
        ]);

        Assert.IsNotNull(tracker.GetLatest(
            completedAt.AddMilliseconds(1600),
            VisualGeometryScanner.MaximumSnapshotAge));
        Assert.IsNull(tracker.GetLatest(
            completedAt.AddMilliseconds(3001),
            VisualGeometryScanner.MaximumSnapshotAge));
    }

    [TestMethod]
    public void ScanScheduler_IsSingleFlightAndEnforcesTwoHertzInterval()
    {
        var scheduler = new VisualScanScheduler(TimeSpan.FromMilliseconds(500));
        var start = DateTimeOffset.UnixEpoch;
        Assert.IsTrue(scheduler.TryStart(start));
        Assert.IsFalse(scheduler.TryStart(start.AddMilliseconds(500)), "An active scan must reject overlap.");
        scheduler.Complete();
        Assert.IsFalse(scheduler.TryStart(start.AddMilliseconds(499)));
        Assert.IsTrue(scheduler.TryStart(start.AddMilliseconds(500)));
    }

    [TestMethod]
    public void GdiCapture_VisibleDisplayProducesTextAndVerticalGeometry()
    {
        Exception? failure = null;
        var thread = new Thread(() =>
        {
            Window? window = null;
            Window? sensorWindow = null;
            try
            {
                var canvas = new Canvas { Background = System.Windows.Media.Brushes.White };
                var text = new TextBlock
                {
                    Text = "BOLTTAGU WALKS ON THIS SENTENCE",
                    FontSize = 28,
                    FontWeight = FontWeights.Bold,
                    Foreground = System.Windows.Media.Brushes.Black,
                };
                Canvas.SetLeft(text, 40);
                Canvas.SetTop(text, 90);
                var line = new Rectangle
                {
                    Width = 3,
                    Height = 190,
                    Fill = System.Windows.Media.Brushes.Black,
                };
                Canvas.SetLeft(line, 500);
                Canvas.SetTop(line, 55);
                canvas.Children.Add(text);
                canvas.Children.Add(line);
                window = new()
                {
                    Title = "Bolttagu Visual Surface Fixture",
                    Width = 640,
                    Height = 360,
                    Left = 120,
                    Top = 100,
                    Content = canvas,
                    Background = System.Windows.Media.Brushes.White,
                };
                window.Show();
                var handle = new WindowInteropHelper(window).Handle;
                var deadline = DateTime.UtcNow + TimeSpan.FromSeconds(2);
                do
                {
                    window.Activate();
                    ForceForeground(handle);
                    PumpDispatcherOnce();
                    if (GetForegroundWindow() == handle) break;
                    Thread.Sleep(25);
                } while (DateTime.UtcNow < deadline);
                Assert.AreEqual(handle, GetForegroundWindow());

                sensorWindow = new()
                {
                    Width = 48,
                    Height = 48,
                    Left = 900,
                    Top = 700,
                    ShowActivated = false,
                    ShowInTaskbar = false,
                    Content = new Border { Background = System.Windows.Media.Brushes.Magenta },
                };
                sensorWindow.Show();
                var sensorHandle = new WindowInteropHelper(sensorWindow).Handle;
                PumpDispatcherOnce();

                var capture = new GdiVisibleDisplayFrameCapture(sensorHandle)
                    .Capture(DateTimeOffset.UtcNow);
                Assert.AreNotEqual(0, capture.CaptureScopeId);
                Assert.IsNotNull(capture.Frame);
                Assert.HasCount(1, capture.Frame.Exclusions!);
                var geometry = new VisualGeometryDetector().Detect(capture.Frame);

                Assert.IsTrue(geometry.Any(item =>
                    item.Kind == VisualGeometryKind.TextLine && item.Bounds.Size.Width >= 180));
                Assert.IsTrue(geometry.Any(item =>
                    item.Kind == VisualGeometryKind.VerticalLine && item.Bounds.Size.Height >= 150));
            }
            catch (Exception exception) { failure = exception; }
            finally
            {
                sensorWindow?.Close();
                window?.Close();
                Dispatcher.CurrentDispatcher.InvokeShutdown();
            }
        });
        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();
        Assert.IsTrue(thread.Join(TimeSpan.FromSeconds(10)), "Foreground visual fixture did not exit.");
        if (failure is not null) Assert.Fail(failure.ToString());
    }

    private static void PumpDispatcherOnce()
    {
        var frame = new DispatcherFrame();
        Dispatcher.CurrentDispatcher.BeginInvoke(
            DispatcherPriority.ApplicationIdle,
            new Action(() => frame.Continue = false));
        Dispatcher.PushFrame(frame);
    }

    private static void ForceForeground(IntPtr handle)
    {
        var currentThread = GetCurrentThreadId();
        var foregroundThread = GetWindowThreadProcessId(GetForegroundWindow(), IntPtr.Zero);
        var attached = foregroundThread != 0 && foregroundThread != currentThread &&
            AttachThreadInput(currentThread, foregroundThread, true);
        try
        {
            _ = BringWindowToTop(handle);
            _ = SetForegroundWindow(handle);
        }
        finally
        {
            if (attached) _ = AttachThreadInput(currentThread, foregroundThread, false);
        }
    }

    private static byte[] WhiteFrame(int width, int height)
    {
        var pixels = new byte[width * height * 4];
        for (var index = 0; index < pixels.Length; index += 4)
        {
            pixels[index] = 255;
            pixels[index + 1] = 255;
            pixels[index + 2] = 255;
            pixels[index + 3] = 255;
        }
        return pixels;
    }

    private static void DrawBlackRectangle(byte[] pixels, int width, int left, int top, int rectWidth, int rectHeight)
    {
        for (var y = top; y < top + rectHeight; y++)
        {
            for (var x = left; x < left + rectWidth; x++)
            {
                var index = (y * width + x) * 4;
                pixels[index] = 0;
                pixels[index + 1] = 0;
                pixels[index + 2] = 0;
            }
        }
    }

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool SetForegroundWindow(IntPtr handle);

    [DllImport("user32.dll")]
    private static extern IntPtr GetForegroundWindow();

    [DllImport("kernel32.dll")]
    private static extern uint GetCurrentThreadId();

    [DllImport("user32.dll")]
    private static extern uint GetWindowThreadProcessId(IntPtr handle, IntPtr processId);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool AttachThreadInput(uint idAttach, uint idAttachTo, bool attach);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool BringWindowToTop(IntPtr handle);
}

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
            ForegroundVisualGeometryScanner.MaximumSnapshotAge));
        Assert.IsNull(tracker.GetLatest(
            completedAt.AddMilliseconds(3001),
            ForegroundVisualGeometryScanner.MaximumSnapshotAge));
    }

    [TestMethod]
    public void ScanScheduler_IsSingleFlightAndEnforcesFourHertzInterval()
    {
        var scheduler = new VisualScanScheduler(TimeSpan.FromMilliseconds(250));
        var start = DateTimeOffset.UnixEpoch;
        Assert.IsTrue(scheduler.TryStart(start));
        Assert.IsFalse(scheduler.TryStart(start.AddMilliseconds(500)), "An active scan must reject overlap.");
        scheduler.Complete();
        Assert.IsFalse(scheduler.TryStart(start.AddMilliseconds(249)));
        Assert.IsTrue(scheduler.TryStart(start.AddMilliseconds(250)));
    }

    [TestMethod]
    public void GdiCapture_ForegroundFixtureProducesTextAndVerticalGeometry()
    {
        Exception? failure = null;
        var thread = new Thread(() =>
        {
            Window? window = null;
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
                window.Activate();
                ForceForeground(handle);
                PumpDispatcherOnce();
                Assert.AreEqual(handle, GetForegroundWindow());

                var capture = new GdiForegroundWindowFrameCapture(() => IntPtr.Zero)
                    .Capture(DateTimeOffset.UtcNow);
                Assert.AreEqual(handle.ToInt64(), capture.ForegroundWindowId);
                Assert.IsNotNull(capture.Frame);
                var geometry = new VisualGeometryDetector().Detect(capture.Frame);

                Assert.IsTrue(geometry.Any(item =>
                    item.Kind == VisualGeometryKind.TextLine && item.Bounds.Size.Width >= 180));
                Assert.IsTrue(geometry.Any(item =>
                    item.Kind == VisualGeometryKind.VerticalLine && item.Bounds.Size.Height >= 150));
            }
            catch (Exception exception) { failure = exception; }
            finally
            {
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

using Bolttagu.Contracts;
using Bolttagu.Platform.Windows;

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
}

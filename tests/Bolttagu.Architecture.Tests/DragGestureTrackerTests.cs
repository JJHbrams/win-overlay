using Bolttagu.Contracts;
using Bolttagu.Platform.Windows;

namespace Bolttagu.Architecture.Tests;

[TestClass]
public sealed class DragGestureTrackerTests
{
    [TestMethod]
    public void MovementBelowThreshold_RemainsClick()
    {
        var tracker = new DragGestureTracker();
        tracker.Begin(new(100, 100), new(500, 400));
        var update = tracker.Move(new(102, 102), 1, 1, 4, 4);
        Assert.AreEqual(DragGestureResult.None, update.Result);
        Assert.AreEqual(DragGestureResult.Click, tracker.Complete());
    }

    [TestMethod]
    public void DragUsesDpiAdjustedDeltaAndCompletes()
    {
        var tracker = new DragGestureTracker();
        tracker.Begin(new(100, 100), new(500, 400));
        var update = tracker.Move(new(120, 110), 2, 2, 4, 4);
        Assert.AreEqual(DragGestureResult.DragStarted, update.Result);
        Assert.AreEqual(new ScreenPoint(510, 405), update.WindowPosition);
        Assert.AreEqual(DragGestureResult.DragCompleted, tracker.Complete());
    }

    [TestMethod]
    public void CaptureLossAfterThreshold_CancelsDragAndClearsState()
    {
        var tracker = new DragGestureTracker();
        tracker.Begin(new(100, 100), new(500, 400));
        tracker.Move(new(120, 100), 1, 1, 4, 4);
        Assert.AreEqual(DragGestureResult.DragCanceled, tracker.Cancel());
        Assert.IsFalse(tracker.IsActive);
        Assert.IsFalse(tracker.IsDragging);
    }
}

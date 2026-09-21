using Bolttagu.Contracts;
using Bolttagu.Platform.Windows;

namespace Bolttagu.Architecture.Tests;

[TestClass]
public sealed class DesktopSurfaceSelectorTests
{
    [TestMethod]
    public void SelectsFirstSurfaceBelowProbeAtSameX()
    {
        var workArea = new ScreenArea(new(0, 0), new(1920, 1040));
        DesktopSurface[] candidates =
        [
            new(new(new(600, 700), new(800, 300)), DesktopSurfaceKind.Window),
            new(new(new(0, 1040), new(1920, 1)), DesktopSurfaceKind.Taskbar),
            new(new(new(100, 500), new(300, 400)), DesktopSurfaceKind.Window),
        ];

        var selected = DesktopSurfaceSelector.FindFirstBelow(candidates, 800, 400, workArea);

        Assert.AreEqual(700, selected.Top);
        Assert.AreEqual(DesktopSurfaceKind.Window, selected.Kind);
    }

    [TestMethod]
    public void IgnoresWindowThatDoesNotContainProbeX()
    {
        var workArea = new ScreenArea(new(0, 0), new(1920, 1040));
        DesktopSurface[] candidates =
        [
            new(new(new(100, 500), new(300, 400)), DesktopSurfaceKind.Window),
            new(new(new(0, 1040), new(1920, 1)), DesktopSurfaceKind.Taskbar),
        ];

        var selected = DesktopSurfaceSelector.FindFirstBelow(candidates, 800, 400, workArea);

        Assert.AreEqual(1040, selected.Top);
        Assert.AreEqual(DesktopSurfaceKind.Taskbar, selected.Kind);
    }

    [TestMethod]
    public void NoCandidateFallsBackToWorkAreaBottom()
    {
        var workArea = new ScreenArea(new(-1920, 0), new(1920, 1040));

        var selected = DesktopSurfaceSelector.FindFirstBelow([], -500, 400, workArea);

        Assert.AreEqual(1040, selected.Top);
        Assert.AreEqual(-1920, selected.Left);
        Assert.AreEqual(DesktopSurfaceKind.WorkAreaFallback, selected.Kind);
    }

    [TestMethod]
    public void CoveredWindowTop_IsNotAValidLandingSurface()
    {
        var workArea = new ScreenArea(new(0, 0), new(1920, 1040));
        DesktopSurface[] candidates =
        [
            new(new(new(500, 400), new(700, 500)), DesktopSurfaceKind.Window, 10, 0),
            new(new(new(400, 700), new(900, 300)), DesktopSurfaceKind.Window, 20, 1),
            new(new(new(0, 1040), new(1920, 1)), DesktopSurfaceKind.Taskbar, -1),
        ];

        var selected = DesktopSurfaceSelector.FindFirstBelow(candidates, 800, 600, workArea);

        Assert.AreEqual(1040, selected.Top);
        Assert.AreEqual(DesktopSurfaceKind.Taskbar, selected.Kind);
    }

    [TestMethod]
    public void WindowTop_RemainsExposedWhenFrontWindowDoesNotCoverProbe()
    {
        DesktopSurface[] candidates =
        [
            new(new(new(0, 400), new(200, 500)), DesktopSurfaceKind.Window, 10, 0),
            new(new(new(400, 700), new(900, 300)), DesktopSurfaceKind.Window, 20, 1),
        ];

        Assert.IsTrue(DesktopSurfaceSelector.IsTopExposed(candidates, candidates[1], 800));
    }

    [TestMethod]
    public void RopeObstacle_RequiresHigherNonMaximizedFrontExposedWindowAtLeadingEdge()
    {
        var support = new DesktopSurface(new(new(0, 720), new(1200, 300)), DesktopSurfaceKind.Window, 1, 2);
        DesktopSurface[] candidates =
        [
            support,
            new(new(new(400, 300), new(500, 600)), DesktopSurfaceKind.Window, 2, 0, true, false),
        ];

        var found = DesktopSurfaceSelector.TryFindRopeClimbObstacle(
            candidates, support, 720, 320, 500, FacingDirection.Right, new(220, 220), out var obstacle);

        Assert.IsTrue(found);
        Assert.AreEqual(2L, obstacle.Id);
    }

    [TestMethod]
    public void RopeObstacle_UsesForegroundWindowEdgeExtensionWithoutVerticalBodyOverlap()
    {
        var support = new DesktopSurface(new(new(0, 720), new(1200, 300)), DesktopSurfaceKind.Window, 1, 2);
        var floatingForeground = new DesktopSurface(
            new(new(400, 100), new(500, 180)), DesktopSurfaceKind.Window, 2, 0, true, false);

        var found = DesktopSurfaceSelector.TryFindRopeClimbObstacle(
            [support, floatingForeground], support, 720, 320, 500,
            FacingDirection.Right, new(220, 220), out var obstacle);

        Assert.IsTrue(found, "The vertical extension of the foreground window edge must remain climbable.");
        Assert.AreEqual(2L, obstacle.Id);
    }

    [TestMethod]
    public void RopeObstacle_RejectsMaximizedTaskbarNoClearanceAndNonFrontWindows()
    {
        var support = new DesktopSurface(new(new(0, 720), new(1200, 300)), DesktopSurfaceKind.Window, 1, 3);
        var taskbar = new DesktopSurface(new(new(400, 300), new(500, 600)), DesktopSurfaceKind.Taskbar, 2, 0);
        var maximized = new DesktopSurface(new(new(400, 300), new(500, 600)), DesktopSurfaceKind.Window, 3, 0, true, true);
        var low = new DesktopSurface(new(new(400, 550), new(500, 450)), DesktopSurfaceKind.Window, 4, 0, true, false);
        var nonFront = new DesktopSurface(new(new(400, 300), new(500, 600)), DesktopSurfaceKind.Window, 5, 3, false, false);

        foreach (var rejected in new[] { taskbar, maximized, low, nonFront })
        {
            var found = DesktopSurfaceSelector.TryFindRopeClimbObstacle(
                [support, rejected], support, 720, 320, 500, FacingDirection.Right, new(220, 220), out _);
            Assert.IsFalse(found, $"{rejected.Kind}/{rejected.Id} unexpectedly qualified.");
        }
    }

    [TestMethod]
    public void ClimbIntercept_SelectsFirstTopEncounteredOnUpwardPath()
    {
        DesktopSurface[] candidates =
        [
            new(new(new(0, 600), new(1000, 400)), DesktopSurfaceKind.Window, 1, 0, true, false),
            new(new(new(0, 450), new(1000, 400)), DesktopSurfaceKind.Window, 2, 1, false, false),
        ];

        var intercept = DesktopSurfaceSelector.FindClimbIntercept(candidates, 300, 720, 300);

        Assert.IsNotNull(intercept);
        Assert.AreEqual(600, intercept.Value.Top);
    }

    [TestMethod]
    public void ClimbIntercept_RejectsTopmostExposedWindowWhenItIsNotForeground()
    {
        DesktopSurface[] candidates =
        [
            new(new(new(0, 600), new(1000, 300)), DesktopSurfaceKind.Window, 1, 0, false, false),
        ];

        Assert.IsNull(DesktopSurfaceSelector.FindClimbIntercept(candidates, 300, 720, 300));
    }

    [TestMethod]
    public void TextLineIsLandingSurfaceAndVerticalLineIsClimbOnly()
    {
        var workArea = new ScreenArea(new(0, 0), new(1920, 1040));
        var text = new DesktopSurface(
            new(new(200, 500), new(300, 24)), DesktopSurfaceKind.TextLine, 10, 0, true);
        var line = new DesktopSurface(
            new(new(500, 220), new(4, 300)), DesktopSurfaceKind.VerticalLine, 11, 0, true);

        var selected = DesktopSurfaceSelector.FindFirstBelow([text, line], 300, 300, workArea);
        Assert.AreEqual(DesktopSurfaceKind.TextLine, selected.Kind);

        var found = DesktopSurfaceSelector.TryFindRopeClimbObstacle(
            [text, line], text, 500, 450, 520, FacingDirection.Right, new(220, 220), out var obstacle);
        Assert.IsTrue(found);
        Assert.AreEqual(DesktopSurfaceKind.VerticalLine, obstacle.Kind);

        var intercept = DesktopSurfaceSelector.FindClimbIntercept([text, line], 300, 720, 300);
        Assert.IsNotNull(intercept);
        Assert.AreEqual(DesktopSurfaceKind.TextLine, intercept.Value.Kind);
    }
}

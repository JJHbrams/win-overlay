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
}

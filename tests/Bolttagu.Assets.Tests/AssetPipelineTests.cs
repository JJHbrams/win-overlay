using Bolttagu.Assets;
using Bolttagu.Contracts;
using System.IO;
using System.Linq;

namespace Bolttagu.Assets.Tests;

[TestClass]
public sealed class AssetPipelineTests
{
    private static string RepositoryRoot => FindRepositoryRoot();

    [TestMethod]
    public void UpstreamSnapshot_MatchesInventory()
    {
        var inventoryPath = Path.Combine(RepositoryRoot, "asset", "bolttagu", "inventory.json");
        var inventory = AssetInventoryVerifier.Load(inventoryPath);

        var issues = AssetInventoryVerifier.Verify(RepositoryRoot, inventory);

        Assert.HasCount(0, issues, string.Join(Environment.NewLine, issues));
        Assert.HasCount(6, inventory.Files);
    }

    [TestMethod]
    public void PreviewPack_HasValidRgbaFramesAndPivots()
    {
        var packPath = Path.Combine(
            RepositoryRoot,
            "asset",
            "bolttagu",
            "derived",
            "animations",
            "pack.json");
        var pack = AnimationPackLoader.Load(packPath);

        var issues = AnimationPackValidator.Validate(packPath, pack);

        Assert.HasCount(0, issues, string.Join(Environment.NewLine, issues));
        CollectionAssert.AreEqual(
            new[] { "idle_breathe", "click", "walk", "turn", "drag_dangle", "drop_land" },
            pack.Clips.Select(clip => clip.Id).ToArray());
    }

    [TestMethod]
    public void PngInspector_ReportsTurnaroundAlpha()
    {
        var path = Path.Combine(
            RepositoryRoot,
            "asset",
            "bolttagu",
            "derived",
            "model",
            "turnaround-v1.png");

        var metadata = PngInspector.Read(path);

        Assert.AreEqual(1774, metadata.Width);
        Assert.AreEqual(887, metadata.Height);
        Assert.IsTrue(metadata.HasAlpha);
    }

    [TestMethod]
    public void InvalidPack_ReportsOpaqueFrameAndWrongCanvas()
    {
        var temporaryRoot = Path.Combine(Path.GetTempPath(), $"bolttagu-assets-{Guid.NewGuid():N}");
        Directory.CreateDirectory(temporaryRoot);
        try
        {
            var source = Path.Combine(
                RepositoryRoot,
                "asset",
                "bolttagu",
                "upstream",
                "engram",
                "set",
                "effects",
                "idle.png");
            var framePath = Path.Combine(temporaryRoot, "opaque.png");
            File.Copy(source, framePath);
            var packPath = Path.Combine(temporaryRoot, "pack.json");
            File.WriteAllText(packPath, "{}");
            var pack = new AnimationPack(
                1,
                "invalid-fixture",
                new(512, 512),
                [new("idle", true, [new("opaque.png", 100, new(256, 480))])]);

            var issues = AnimationPackValidator.Validate(packPath, pack);

            Assert.IsTrue(issues.Any(issue => issue.Message.Contains("Expected 512x512", StringComparison.Ordinal)));
            Assert.IsTrue(issues.Any(issue => issue.Message.Contains("must be an RGBA", StringComparison.Ordinal)));
        }
        finally
        {
            Directory.Delete(temporaryRoot, recursive: true);
        }
    }

    [TestMethod]
    public void RuntimeCatalog_ContainsArtForEveryImplementedAction()
    {
        var buildRoot = Path.Combine(RepositoryRoot, "asset", "bolttagu", "build");

        var catalog = RuntimeAnimationCatalog.Load(buildRoot);

        Assert.IsFalse(catalog.IsFallback);
        Assert.HasCount(4, catalog.GetClip("idle_breathe").Frames);
        Assert.HasCount(4, catalog.GetClip("click").Frames);
        Assert.HasCount(4, catalog.GetClip("walk").Frames);
        Assert.HasCount(4, catalog.GetClip("turn").Frames);
        Assert.HasCount(4, catalog.GetClip("drag_dangle").Frames);
        Assert.HasCount(4, catalog.GetClip("drop_land").Frames);
        CollectionAssert.AreEquivalent(
            Enum.GetValues<PetAction>(),
            PetActionClips.All.Keys.ToArray(),
            "Every implemented action must declare a corresponding art clip.");
        foreach (var clipId in PetActionClips.All.Values)
        {
            Assert.IsGreaterThan(0, catalog.GetClip(clipId).Frames.Count, $"Missing art for {clipId}.");
        }
    }

    [TestMethod]
    public void RuntimeCatalog_UsesStaticFallbackForInvalidCatalog()
    {
        var temporaryRoot = Path.Combine(Path.GetTempPath(), $"bolttagu-catalog-{Guid.NewGuid():N}");
        Directory.CreateDirectory(temporaryRoot);
        try
        {
            File.WriteAllText(Path.Combine(temporaryRoot, "catalog.json"), "not-json");
            var fallback = Path.Combine(
                RepositoryRoot,
                "asset",
                "bolttagu",
                "upstream",
                "engram",
                "character.png");

            var catalog = RuntimeAnimationCatalog.LoadOrFallback(temporaryRoot, fallback);

            Assert.IsTrue(catalog.IsFallback);
            Assert.HasCount(1, catalog.GetClip("idle_breathe").Frames);
            Assert.HasCount(1, catalog.GetClip("click").Frames);
            Assert.HasCount(1, catalog.GetClip("walk").Frames);
            Assert.HasCount(1, catalog.GetClip("turn").Frames);
            Assert.HasCount(1, catalog.GetClip("drag_dangle").Frames);
            Assert.HasCount(1, catalog.GetClip("drop_land").Frames);
        }
        finally
        {
            Directory.Delete(temporaryRoot, recursive: true);
        }
    }

    private static string FindRepositoryRoot()
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);
        while (directory is not null)
        {
            if (File.Exists(Path.Combine(directory.FullName, "Bolttagu.slnx")))
            {
                return directory.FullName;
            }
            directory = directory.Parent;
        }

        throw new DirectoryNotFoundException("Could not find repository root.");
    }
}

using Bolttagu.Assets;
using Bolttagu.AssetBuild;
using Bolttagu.Contracts;
using Bolttagu.Core;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Windows.Media;
using System.Windows.Media.Imaging;

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
            new[]
            {
                "idle_breathe", "idle_dazed", "idle_proud", "idle_pout", "click", "walk", "run", "click_huff", "turn", "drag_held_idle",
                "drag_pulled", "spawn_in", "despawn_out", "drop_land", "turn_to_idle", "fall",
                "sit_down", "sit_settle", "doze_enter", "doze_loop", "wake_up", "stand_up",
                "doze_startle", "look_around", "stretch", "land_recover",
                "rope_climb_prepare", "rope_climb_loop", "rope_climb_finish",
                "free_climb_prepare", "free_climb_loop", "free_climb_finish",
                "rope_climb_down_prepare", "rope_climb_down_loop", "rope_climb_down_finish",
                "free_climb_down_prepare", "free_climb_down_loop", "free_climb_down_finish"
            },
            pack.Clips.Select(clip => clip.Id).ToArray());
    }

    [TestMethod]
    public void AnimationShowcaseGif_RotatesThroughEveryBuiltFrame()
    {
        var path = Path.Combine(RepositoryRoot, "asset", "bolttagu", "build", "review", "animation-showcase.gif");
        using var stream = File.OpenRead(path);
        var decoder = new GifBitmapDecoder(stream, BitmapCreateOptions.PreservePixelFormat, BitmapCacheOption.OnLoad);

        Assert.HasCount(147, decoder.Frames);
        Assert.AreEqual(256, decoder.Frames[0].PixelWidth);
        Assert.AreEqual(288, decoder.Frames[0].PixelHeight);
        Assert.Contains("NETSCAPE2.0", Encoding.ASCII.GetString(File.ReadAllBytes(path)));
    }

    [TestMethod]
    public void IdleExpressionShowcases_AreSeparateSlowLoopingGifs()
    {
        foreach (var clipId in new[] { PetActionClips.IdleDazed, PetActionClips.IdleProud, PetActionClips.IdlePout })
        {
            var path = Path.Combine(RepositoryRoot, "asset", "bolttagu", "build", "review", $"{clipId}.gif");
            using var stream = File.OpenRead(path);
            var decoder = new GifBitmapDecoder(stream, BitmapCreateOptions.PreservePixelFormat, BitmapCacheOption.OnLoad);
            Assert.HasCount(4, decoder.Frames, $"{clipId} must show its own complete action, not the full animation catalog.");
            CollectionAssert.AreEqual(new ushort[] { 50, 45, 120, 50 },
                decoder.Frames.Select(frame => (ushort)((BitmapMetadata)frame.Metadata).GetQuery("/grctlext/Delay")!).ToArray());
            Assert.Contains("NETSCAPE2.0", Encoding.ASCII.GetString(File.ReadAllBytes(path)));
        }
    }

    [TestMethod]
    public void IdleExpressionFrames_KeepGroundBaselineAcrossKeyframes()
    {
        var path = Path.Combine(RepositoryRoot, "asset", "bolttagu", "build", "review", "frame-metrics.json");
        using var document = JsonDocument.Parse(File.ReadAllText(path));
        var frames = document.RootElement.GetProperty("frames").EnumerateArray().ToArray();
        foreach (var clipId in new[] { PetActionClips.IdleDazed, PetActionClips.IdleProud, PetActionClips.IdlePout })
        {
            var clipFrames = frames.Where(frame => frame.GetProperty("clipId").GetString() == clipId).ToArray();
            Assert.HasCount(4, clipFrames);
            Assert.IsTrue(clipFrames.All(frame => frame.GetProperty("bottom").GetInt32() == 477),
                $"{clipId} must keep both shoes on the same ground baseline.");
        }
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
    public void BrandingAssets_HaveWideBannerAndMultiResolutionWindowsIcon()
    {
        var brandingRoot = Path.Combine(RepositoryRoot, "asset", "bolttagu", "derived", "branding");
        var banner = PngInspector.Read(Path.Combine(brandingRoot, "readme-banner.png"));
        var iconMaster = PngInspector.Read(Path.Combine(brandingRoot, "bolttagu-icon-master.png"));

        Assert.AreEqual(2172, banner.Width);
        Assert.AreEqual(724, banner.Height);
        Assert.AreEqual(iconMaster.Width, iconMaster.Height);
        Assert.IsTrue(iconMaster.HasAlpha);

        using var stream = File.OpenRead(Path.Combine(brandingRoot, "bolttagu.ico"));
        using var reader = new BinaryReader(stream);
        Assert.AreEqual((ushort)0, reader.ReadUInt16());
        Assert.AreEqual((ushort)1, reader.ReadUInt16());
        var count = reader.ReadUInt16();
        Assert.AreEqual((ushort)7, count);
        var sizes = new List<int>();
        for (var index = 0; index < count; index++)
        {
            var width = reader.ReadByte();
            var height = reader.ReadByte();
            sizes.Add(width == 0 ? 256 : width);
            Assert.AreEqual(width, height);
            reader.ReadBytes(14);
        }
        CollectionAssert.AreEqual(new[] { 16, 24, 32, 48, 64, 128, 256 }, sizes);
    }

    [TestMethod]
    public void RecipeCalibration_ValidatesCanonicalIdleAndControlsEmissionWithoutScaleDrift()
    {
        var root = Path.Combine(Path.GetTempPath(), $"bolttagu-calibration-{Guid.NewGuid():N}");
        var modelRoot = Path.Combine(root, "asset", "bolttagu", "derived", "model");
        Directory.CreateDirectory(modelRoot);
        File.WriteAllText(Path.Combine(root, "Bolttagu.slnx"), "<Solution />");
        File.Copy(
            Path.Combine(RepositoryRoot, "asset", "bolttagu", "derived", "model", "turnaround-v1.png"),
            Path.Combine(modelRoot, "turnaround-v1.png"));
        var recipePath = Path.Combine(modelRoot, "animation-recipes.json");
        File.WriteAllText(recipePath, """
            {
              "schemaVersion": 1,
              "source": "turnaround-v1.png",
              "sourceRect": { "x": 0, "y": 0, "width": 443, "height": 887 },
              "canvas": { "width": 512, "height": 512 },
              "padding": 32,
              "clips": [
                {
                  "id": "legacy",
                  "frames": [{ "scaleX": 1, "scaleY": 1, "offsetX": 0, "offsetY": 0 }]
                },
                {
                  "id": "calibrated_hidden",
                  "calibration": { "sourceRect": { "x": 0, "y": 0, "width": 443, "height": 887 } },
                  "frames": [{ "scaleX": 1, "scaleY": 1, "offsetX": 0, "offsetY": 0 }]
                },
                {
                  "id": "calibrated_terminal",
                  "calibration": {
                    "sourceRect": { "x": 0, "y": 0, "width": 443, "height": 887 },
                    "emit": true
                  },
                  "frames": [{ "scaleX": 1, "scaleY": 1, "offsetX": 0, "offsetY": 0 }]
                }
              ]
            }
            """);
        try
        {
            Assert.AreEqual(0, Program.Main(["generate", root]));

            var animationRoot = Path.Combine(root, "asset", "bolttagu", "derived", "animations");
            Assert.HasCount(1, Directory.EnumerateFiles(Path.Combine(animationRoot, "legacy", "frames"), "*.png"));
            Assert.HasCount(1, Directory.EnumerateFiles(Path.Combine(animationRoot, "calibrated_hidden", "frames"), "*.png"),
                "A calibration frame is metadata unless explicitly emitted.");
            Assert.HasCount(2, Directory.EnumerateFiles(Path.Combine(animationRoot, "calibrated_terminal", "frames"), "*.png"),
                "Terminal idle-return clips may opt in to emit their calibration frame.");

            var legacy = GetAlphaBounds(LoadBgra32(Path.Combine(animationRoot, "legacy", "frames", "000.png")));
            var calibrated = GetAlphaBounds(LoadBgra32(Path.Combine(animationRoot, "calibrated_hidden", "frames", "000.png")));
            var terminal = GetAlphaBounds(LoadBgra32(Path.Combine(animationRoot, "calibrated_terminal", "frames", "001.png")));
            Assert.AreEqual(legacy, calibrated, "Explicit calibration preserves legacy reference-frame output.");
            Assert.AreEqual(legacy, terminal, "The emitted canonical idle has the same shared scale and ground baseline.");
            Assert.IsInRange(477, 480, calibrated.Bottom, "Grounded calibration must use the common bottom baseline.");

            File.WriteAllText(recipePath, """
                {
                  "schemaVersion": 1,
                  "source": "turnaround-v1.png",
                  "sourceRect": { "x": 0, "y": 0, "width": 443, "height": 887 },
                  "canvas": { "width": 512, "height": 512 },
                  "padding": 32,
                  "clips": [{
                    "id": "invalid_calibration",
                    "calibration": { "sourceRect": { "x": 1774, "y": 0, "width": 1, "height": 887 } },
                    "frames": [{ "scaleX": 1, "scaleY": 1, "offsetX": 0, "offsetY": 0 }]
                  }]
                }
                """);
            Assert.AreEqual(1, Program.Main(["generate", root]), "Out-of-bounds calibration rectangles must be rejected.");
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public void IdleRig_ComposesFixedCanvasFramesWithCanonicalLayerDefaults()
    {
        var root = Path.Combine(Path.GetTempPath(), $"bolttagu-idle-rig-{Guid.NewGuid():N}");
        var modelRoot = Path.Combine(root, "asset", "bolttagu", "derived", "model");
        var rigRoot = Path.Combine(modelRoot, "idle-rig");
        Directory.CreateDirectory(rigRoot);
        try
        {
            File.WriteAllText(Path.Combine(root, "Bolttagu.slnx"), "<Solution />");
            var calibration = Path.Combine(RepositoryRoot, "asset", "bolttagu", "derived", "model", "canonical-idle-calibration-v1.png");
            File.Copy(calibration, Path.Combine(modelRoot, "canonical.png"));
            File.Copy(calibration, Path.Combine(rigRoot, "part.png"));
            File.WriteAllText(Path.Combine(modelRoot, "animation-recipes.json"), """
                { "schemaVersion": 1, "source": "canonical.png", "sourceRect": { "x": 0, "y": 0, "width": 512, "height": 512 }, "canvas": { "width": 512, "height": 512 }, "padding": 32, "clips": [] }
                """);
            File.WriteAllText(Path.Combine(modelRoot, "idle-rig.json"), """
                {
                  "schemaVersion": 1,
                  "canvas": { "width": 512, "height": 512 },
                  "clips": [
                    { "id": "idle_dazed", "frames": [{ "layers": [
                      { "id":"body", "source":"part.png", "drawOrder":10 }, { "id":"head", "source":"part.png", "drawOrder":20, "rotationDeg":2 },
                      { "id":"left_arm", "source":"part.png", "drawOrder":5, "scaleX":0.98 }, { "id":"right_arm", "source":"part.png", "drawOrder":25 },
                      { "id":"left_leg", "source":"part.png", "drawOrder":1 }, { "id":"right_leg", "source":"part.png", "drawOrder":2 }
                    ] }] },
                    { "id": "idle_proud", "frames": [{ "layers": [
                      { "id":"body", "source":"part.png" }, { "id":"head", "source":"part.png" }, { "id":"left_arm", "source":"part.png" },
                      { "id":"right_arm", "source":"part.png" }, { "id":"left_leg", "source":"part.png" }, { "id":"right_leg", "source":"part.png" }
                    ] }] },
                    { "id": "idle_pout", "frames": [{ "layers": [
                      { "id":"body", "source":"part.png" }, { "id":"head", "source":"part.png" }, { "id":"left_arm", "source":"part.png" },
                      { "id":"right_arm", "source":"part.png" }, { "id":"left_leg", "source":"part.png" }, { "id":"right_leg", "source":"part.png" }
                    ] }] }
                  ]
                }
                """);

            Assert.AreEqual(0, Program.Main(["generate", root]));
            foreach (var clipId in new[] { "idle_dazed", "idle_proud", "idle_pout" })
            {
                var frame = PngInspector.Read(Path.Combine(root, "asset", "bolttagu", "derived", "animations", clipId, "frames", "000.png"));
                Assert.AreEqual(512, frame.Width);
                Assert.AreEqual(512, frame.Height);
                Assert.IsTrue(frame.HasAlpha);
            }

            var rigPath = Path.Combine(modelRoot, "idle-rig.json");
            var validRig = File.ReadAllText(rigPath);
            File.WriteAllText(rigPath, validRig.Replace("\"schemaVersion\": 1", "\"schemaVersion\": 2", StringComparison.Ordinal));
            Assert.AreEqual(1, Program.Main(["generate", root]), "Unsupported rig schemas must fail before emitting a new build.");
            File.WriteAllText(rigPath, validRig.Replace("part.png", "../part.png", StringComparison.Ordinal));
            Assert.AreEqual(1, Program.Main(["generate", root]), "Rig sources must not escape idle-rig/.");
            File.WriteAllText(rigPath, validRig.Replace("\"id\":\"right_leg\"", "\"id\":\"missing_leg\"", StringComparison.Ordinal));
            Assert.AreEqual(1, Program.Main(["generate", root]), "Each keyframe must declare both leg slots.");
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    [TestMethod]
    public void CellIsolatedAnimationSources_HaveTransparentGutters()
    {
        var modelRoot = Path.Combine(RepositoryRoot, "asset", "bolttagu", "derived", "model");
        var sources = new[]
        {
            "drag-held-idle-grid-v2.png",
            "drag-pulled-grid-v5.png",
            "spawn-in-grid-v3.png",
            "despawn-out-grid-v2.png",
        };

        foreach (var source in sources)
        {
            var path = Path.Combine(modelRoot, source);
            var bitmap = LoadBgra32(path);
            Assert.AreEqual(1536, bitmap.PixelWidth, source);
            Assert.AreEqual(1024, bitmap.PixelHeight, source);
            Assert.AreEqual(0, CountVisibleGutterPixels(bitmap, gutterWidth: 4),
                $"{source} contains visible pixels on a 512x512 cell boundary.");
        }

        foreach (var source in new[] { "rope-climb-grid-v1.png", "free-climb-grid-v1.png" })
        {
            var path = Path.Combine(modelRoot, source);
            var bitmap = LoadBgra32(path);
            Assert.AreEqual(1774, bitmap.PixelWidth, source);
            Assert.AreEqual(887, bitmap.PixelHeight, source);
        }
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
        Assert.HasCount(4, catalog.GetClip("click_huff").Frames);
        Assert.HasCount(4, catalog.GetClip("walk").Frames);
        Assert.HasCount(4, catalog.GetClip("turn").Frames);
        Assert.HasCount(6, catalog.GetClip("drag_held_idle").Frames);
        Assert.HasCount(6, catalog.GetClip("drag_pulled").Frames);
        Assert.HasCount(6, catalog.GetClip("spawn_in").Frames);
        Assert.HasCount(6, catalog.GetClip("despawn_out").Frames);
        Assert.HasCount(4, catalog.GetClip("drop_land").Frames);
        Assert.HasCount(4, catalog.GetClip("turn_to_idle").Frames);
        Assert.HasCount(1, catalog.GetClip("fall").Frames);
        Assert.HasCount(6, catalog.GetClip("sit_down").Frames);
        Assert.HasCount(3, catalog.GetClip("sit_settle").Frames);
        Assert.HasCount(3, catalog.GetClip("doze_enter").Frames);
        Assert.HasCount(4, catalog.GetClip("doze_loop").Frames);
        Assert.HasCount(6, catalog.GetClip("wake_up").Frames);
        Assert.HasCount(3, catalog.GetClip("stand_up").Frames);
        Assert.HasCount(3, catalog.GetClip("doze_startle").Frames);
        Assert.HasCount(6, catalog.GetClip("look_around").Frames);
        Assert.HasCount(6, catalog.GetClip("stretch").Frames);
        Assert.HasCount(6, catalog.GetClip("land_recover").Frames);
        Assert.HasCount(2, catalog.GetClip("rope_climb_prepare").Frames);
        Assert.HasCount(4, catalog.GetClip("rope_climb_loop").Frames);
        Assert.HasCount(2, catalog.GetClip("rope_climb_finish").Frames);
        Assert.HasCount(1, catalog.GetClip("free_climb_prepare").Frames);
        Assert.HasCount(5, catalog.GetClip("free_climb_loop").Frames);
        Assert.HasCount(2, catalog.GetClip("free_climb_finish").Frames);
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
    public void BehaviorDefinitions_ReferenceBuiltCatalogClipsAndDozeCycleTiming()
    {
        var catalog = RuntimeAnimationCatalog.Load(Path.Combine(RepositoryRoot, "asset", "bolttagu", "build"));
        var known = BehaviorDefinitions.Autonomous
            .SelectMany(definition => definition.Steps)
            .Select(step => step.ClipId)
            .ToHashSet(StringComparer.Ordinal);

        BehaviorDefinitionValidator.ValidateAll(BehaviorDefinitions.Autonomous, known);
        foreach (var clipId in known)
        {
            Assert.IsGreaterThan(0, catalog.GetClip(clipId).Frames.Count, $"Behavior clip '{clipId}' is absent from the built catalog.");
        }

        var actualCycle = catalog.GetClip(PetActionClips.DozeLoop).Frames.Aggregate(
            TimeSpan.Zero, (total, frame) => total + frame.Duration);
        Assert.AreEqual(BehaviorDefinitions.DozeLoopCycleDuration, actualCycle, "Doze loop contract drifted from pack frame timing.");
    }

    [TestMethod]
    public void ReviewArtifacts_UseCanonicalCaptureBoxAndReadableTiming()
    {
        var buildRoot = Path.Combine(RepositoryRoot, "asset", "bolttagu", "build");
        var sheet = PngInspector.Read(Path.Combine(buildRoot, "review", "contact-sheet.png"));
        Assert.AreEqual(1024, sheet.Width);
        Assert.IsGreaterThan(1000, sheet.Height);
        var scaleAudit = PngInspector.Read(Path.Combine(buildRoot, "review", "scale-audit-sheet.png"));
        Assert.AreEqual(1024, scaleAudit.Width);
        Assert.AreEqual(1752, scaleAudit.Height);

        using var metrics = JsonDocument.Parse(File.ReadAllText(
            Path.Combine(buildRoot, "review", "frame-metrics.json")));
        var grounded = new[] { "idle_breathe", "click", "click_huff", "walk", "turn" };
        foreach (var clipId in grounded)
        {
            var reference = metrics.RootElement.GetProperty("frames")
                .EnumerateArray()
                .Single(frame => frame.GetProperty("clipId").GetString() == clipId &&
                                 frame.GetProperty("index").GetInt32() == 0);
            Assert.IsInRange(411, 429, reference.GetProperty("height").GetInt32(), $"{clipId} scale drifted.");
            Assert.IsInRange(477, 480, reference.GetProperty("bottom").GetInt32(), $"{clipId} ground anchor drifted.");
        }

        var packPath = Path.Combine(RepositoryRoot, "asset", "bolttagu", "derived", "animations", "pack.json");
        var pack = AnimationPackLoader.Load(packPath);
        foreach (var dragId in new[] { "drag_held_idle", "drag_pulled" })
        {
            var drag = pack.Clips.Single(clip => clip.Id == dragId);
            foreach (var frame in drag.Frames)
            {
                Assert.IsGreaterThanOrEqualTo(100, frame.DurationMs);
                Assert.AreEqual(104, frame.Pivot.Y);
            }
            Assert.HasCount(6, drag.Frames);
        }
        var spawn = pack.Clips.Single(clip => clip.Id == "spawn_in");
        var despawn = pack.Clips.Single(clip => clip.Id == "despawn_out");
        Assert.IsFalse(spawn.Loop);
        Assert.IsFalse(despawn.Loop);
        Assert.IsGreaterThanOrEqualTo(800, spawn.Frames.Sum(frame => frame.DurationMs));
        Assert.IsGreaterThanOrEqualTo(800, despawn.Frames.Sum(frame => frame.DurationMs));
        var huff = pack.Clips.Single(clip => clip.Id == "click_huff");
        Assert.IsGreaterThanOrEqualTo(800, huff.Frames.Sum(frame => frame.DurationMs));
        var landing = pack.Clips.Single(clip => clip.Id == "drop_land");
        Assert.IsGreaterThanOrEqualTo(600, landing.Frames.Sum(frame => frame.DurationMs));
        var ropeLoop = pack.Clips.Single(clip => clip.Id == "rope_climb_loop");
        Assert.EndsWith("001-left-v2.png", ropeLoop.Frames[1].Path, StringComparison.Ordinal);
        Assert.EndsWith("003-left.png", ropeLoop.Frames[3].Path, StringComparison.Ordinal);
        Assert.IsTrue(ropeLoop.Frames
            .All(frame => frame.Contacts?.Count(contact => contact.Kind == "hand") == 1),
            "Each rope frame must expose exactly one unambiguous gripping hand.");

        var representativeFrames = metrics.RootElement.GetProperty("frames").EnumerateArray().ToArray();
        var idle = representativeFrames.Single(frame =>
            frame.GetProperty("clipId").GetString() == "idle_breathe" && frame.GetProperty("index").GetInt32() == 0);
        var held = representativeFrames.Single(frame =>
            frame.GetProperty("clipId").GetString() == "drag_held_idle" && frame.GetProperty("index").GetInt32() == 0);
        var pulled = representativeFrames.Single(frame =>
            frame.GetProperty("clipId").GetString() == "drag_pulled" && frame.GetProperty("index").GetInt32() == 0);
        var fall = representativeFrames.Single(frame =>
            frame.GetProperty("clipId").GetString() == "fall" && frame.GetProperty("index").GetInt32() == 0);
        Assert.IsInRange(400, 408, held.GetProperty("height").GetInt32(), "Held drag is undersized.");
        Assert.IsInRange(372, 380, pulled.GetProperty("height").GetInt32(), "Pulled drag scale drifted.");
        Assert.IsInRange(345, 355, fall.GetProperty("height").GetInt32(), "Fall pose scale drifted.");
        Assert.IsInRange(238, 252, fall.GetProperty("width").GetInt32(), "Fall head/body scale drifted.");
        Assert.IsLessThan(idle.GetProperty("height").GetInt32(), held.GetProperty("height").GetInt32());
        Assert.IsLessThan(idle.GetProperty("height").GetInt32(), fall.GetProperty("height").GetInt32());
        var look = representativeFrames.Single(item =>
            item.GetProperty("clipId").GetString() == "look_around" && item.GetProperty("index").GetInt32() == 0);
        Assert.IsInRange(228, 240, look.GetProperty("width").GetInt32(), "Look-around head/body scale drifted.");
        Assert.IsInRange(411, 429, look.GetProperty("height").GetInt32(), "Look-around scale drifted.");
        Assert.IsInRange(477, 480, look.GetProperty("bottom").GetInt32(), "Look-around ground anchor drifted.");
        var stretch = representativeFrames.Single(item =>
            item.GetProperty("clipId").GetString() == "stretch" && item.GetProperty("index").GetInt32() == 0);
        Assert.IsInRange(262, 278, stretch.GetProperty("width").GetInt32(), "Stretch head/body scale drifted.");
        Assert.IsInRange(446, 460, stretch.GetProperty("height").GetInt32(), "Stretch scale drifted.");
        Assert.IsInRange(477, 480, stretch.GetProperty("bottom").GetInt32(), "Stretch ground anchor drifted.");
        var doze = representativeFrames.Single(frame =>
            frame.GetProperty("clipId").GetString() == "doze_loop" && frame.GetProperty("index").GetInt32() == 0);
        Assert.IsInRange(350, 365, doze.GetProperty("height").GetInt32(), "Doze scale drifted.");
        Assert.IsInRange(240, 260, doze.GetProperty("width").GetInt32(), "Doze head/body scale drifted.");
        Assert.IsInRange(477, 480, doze.GetProperty("bottom").GetInt32(), "Doze ground anchor drifted.");
        var wake = representativeFrames.Single(frame =>
            frame.GetProperty("clipId").GetString() == "wake_up" && frame.GetProperty("index").GetInt32() == 5);
        Assert.IsInRange(228, 240, wake.GetProperty("width").GetInt32(), "Wake-up head/body scale drifted.");
        Assert.IsInRange(411, 429, wake.GetProperty("height").GetInt32(), "Wake-up scale drifted.");
        var seated = representativeFrames.Single(frame =>
            frame.GetProperty("clipId").GetString() == "sit_down" && frame.GetProperty("index").GetInt32() == 5);
        Assert.IsInRange(228, 242, seated.GetProperty("width").GetInt32(), "Seated head/body scale drifted.");
        Assert.IsGreaterThanOrEqualTo(100, seated.GetProperty("y").GetInt32(),
            "Sit-down final frame contains pixels above the expected character bounds; check for adjacent-cell bleed.");
        foreach (var (clipId, index) in new[]
                 {
                     ("sit_down", 3), ("sit_down", 4), ("sit_down", 5),
                     ("sit_settle", 0), ("sit_settle", 1), ("sit_settle", 2),
                 })
        {
            var frame = representativeFrames.Single(item =>
                item.GetProperty("clipId").GetString() == clipId && item.GetProperty("index").GetInt32() == index);
            Assert.IsGreaterThanOrEqualTo(100, frame.GetProperty("y").GetInt32(),
                $"{clipId}/{index} contains pixels above the seated character; check for adjacent-cell bleed.");
        }

        foreach (var clipId in new[]
                 {
                     "rope_climb_prepare", "rope_climb_loop", "rope_climb_finish",
                     "free_climb_prepare", "free_climb_loop", "free_climb_finish"
                 })
        {
            foreach (var frame in representativeFrames.Where(item =>
                         item.GetProperty("clipId").GetString() == clipId))
            {
                Assert.IsGreaterThanOrEqualTo(24, frame.GetProperty("x").GetInt32(),
                    $"{clipId} touches the capture-box edge; check for adjacent-cell bleed.");
                Assert.IsGreaterThanOrEqualTo(20, frame.GetProperty("y").GetInt32(),
                    $"{clipId} touches the capture-box edge; check for adjacent-cell bleed.");
                Assert.IsLessThanOrEqualTo(480, frame.GetProperty("bottom").GetInt32(),
                    $"{clipId} exceeds the canonical foot baseline.");
            }
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
            Assert.HasCount(1, catalog.GetClip("click_huff").Frames);
            Assert.HasCount(1, catalog.GetClip("walk").Frames);
            Assert.HasCount(1, catalog.GetClip("turn").Frames);
            Assert.HasCount(1, catalog.GetClip("drag_held_idle").Frames);
            Assert.HasCount(1, catalog.GetClip("drag_pulled").Frames);
            Assert.HasCount(1, catalog.GetClip("spawn_in").Frames);
            Assert.HasCount(1, catalog.GetClip("despawn_out").Frames);
            Assert.HasCount(1, catalog.GetClip("drop_land").Frames);
            Assert.HasCount(1, catalog.GetClip("turn_to_idle").Frames);
            Assert.HasCount(1, catalog.GetClip("fall").Frames);
            foreach (var clipId in new[]
                     {
                         "sit_down", "sit_settle", "doze_enter", "doze_loop", "wake_up", "stand_up",
                         "doze_startle", "look_around", "stretch", "land_recover",
                         "rope_climb_prepare", "rope_climb_loop", "rope_climb_finish",
                         "free_climb_prepare", "free_climb_loop", "free_climb_finish"
                     })
            {
                Assert.HasCount(1, catalog.GetClip(clipId).Frames);
            }
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

    private static BitmapSource LoadBgra32(string path)
    {
        using var stream = File.OpenRead(path);
        var source = BitmapDecoder.Create(
            stream,
            BitmapCreateOptions.PreservePixelFormat,
            BitmapCacheOption.OnLoad).Frames[0];
        var converted = new FormatConvertedBitmap(source, PixelFormats.Bgra32, null, 0);
        converted.Freeze();
        return converted;
    }

    private static int CountVisibleGutterPixels(BitmapSource bitmap, int gutterWidth)
    {
        var stride = bitmap.PixelWidth * 4;
        var pixels = new byte[stride * bitmap.PixelHeight];
        bitmap.CopyPixels(pixels, stride, 0);
        var count = 0;
        for (var cell = 0; cell < 6; cell++)
        {
            var originX = (cell % 3) * 512;
            var originY = (cell / 3) * 512;
            for (var inset = 0; inset < gutterWidth; inset++)
            {
                for (var offset = 0; offset < 512; offset++)
                {
                    count += IsVisible(originX + offset, originY + inset) ? 1 : 0;
                    count += IsVisible(originX + offset, originY + 511 - inset) ? 1 : 0;
                    count += IsVisible(originX + inset, originY + offset) ? 1 : 0;
                    count += IsVisible(originX + 511 - inset, originY + offset) ? 1 : 0;
                }
            }
        }
        return count;

        bool IsVisible(int x, int y) => pixels[(y * stride) + (x * 4) + 3] > 8;
    }

    private static (int Width, int Height, int Bottom) GetAlphaBounds(BitmapSource bitmap)
    {
        var stride = bitmap.PixelWidth * 4;
        var pixels = new byte[stride * bitmap.PixelHeight];
        bitmap.CopyPixels(pixels, stride, 0);
        var minX = bitmap.PixelWidth;
        var minY = bitmap.PixelHeight;
        var maxX = -1;
        var maxY = -1;
        for (var y = 0; y < bitmap.PixelHeight; y++)
        {
            for (var x = 0; x < bitmap.PixelWidth; x++)
            {
                if (pixels[(y * stride) + (x * 4) + 3] <= 8) continue;
                minX = Math.Min(minX, x);
                minY = Math.Min(minY, y);
                maxX = Math.Max(maxX, x);
                maxY = Math.Max(maxY, y);
            }
        }

        Assert.IsGreaterThanOrEqualTo(minX, maxX);
        return (maxX - minX + 1, maxY - minY + 1, maxY);
    }

}

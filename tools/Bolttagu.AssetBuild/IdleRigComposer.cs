using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Windows;
using System.Windows.Media;
using System.Windows.Media.Imaging;

namespace Bolttagu.AssetBuild;

/// <summary>
/// Converts the deliberately small idle-rig source contract into the ordinary frame files
/// consumed by the existing animation pack/compiler.  This is intentionally an offline
/// compositor: the runtime continues to render a single atlas crop per frame.
/// </summary>
internal static class IdleRigComposer
{
    private static readonly RigPoint CanonicalPivot = new(256, 480);
    private static readonly RigPoint Zero = new(0, 0);
    private static readonly HashSet<string> AllowedClipIds = new(StringComparer.Ordinal)
    {
        "idle_dazed", "idle_proud", "idle_pout"
    };
    private static readonly string[] RequiredSlots =
        ["head", "body", "left_arm", "right_arm", "left_leg", "right_leg"];

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true
    };

    public static int ComposeIfPresent(string modelRoot, string animationRoot)
    {
        var rigPath = Path.Combine(modelRoot, "idle-rig.json");
        if (!File.Exists(rigPath))
        {
            return 0;
        }

        var rig = JsonSerializer.Deserialize<IdleRig>(File.ReadAllText(rigPath), JsonOptions)
            ?? throw new InvalidDataException($"{rigPath} is empty.");

        var sourceRoot = Path.Combine(modelRoot, "idle-rig");
        if (!Directory.Exists(sourceRoot))
        {
            throw new DirectoryNotFoundException($"Idle rig source directory is missing: {sourceRoot}");
        }
        ValidateRig(rig, rigPath, sourceRoot);
        var clips = rig.Clips!;

        var cache = new Dictionary<string, BitmapSource>(StringComparer.OrdinalIgnoreCase);
        var written = 0;
        foreach (var clip in clips.OrderBy(item => item.Id, StringComparer.Ordinal))
        {
            var frames = clip.Frames!;
            var outputDirectory = Path.Combine(animationRoot, clip.Id, "frames");
            Directory.CreateDirectory(outputDirectory);
            for (var index = 0; index < frames.Count; index++)
            {
                var target = new RenderTargetBitmap(512, 512, 96, 96, PixelFormats.Pbgra32);
                var visual = new DrawingVisual();
                using (var drawing = visual.RenderOpen())
                {
                    foreach (var layer in frames[index].Layers!
                                 .OrderBy(item => item.DrawOrder)
                                 .ThenBy(item => item.Id, StringComparer.Ordinal))
                    {
                        var sourcePath = ResolveContained(sourceRoot, layer.Source);
                        if (!cache.TryGetValue(sourcePath, out var source))
                        {
                            source = LoadBitmap(sourcePath);
                            cache.Add(sourcePath, source);
                        }

                        var pivot = layer.Pivot ?? CanonicalPivot;
                        var localPivot = layer.LocalPivot ?? CanonicalPivot;
                        var offset = layer.Offset ?? Zero;
                        var scaleX = layer.ScaleX ?? 1;
                        var scaleY = layer.ScaleY ?? 1;
                        var rotation = layer.RotationDeg ?? 0;
                        var transforms = new TransformGroup();
                        transforms.Children.Add(new TranslateTransform(-localPivot.X, -localPivot.Y));
                        transforms.Children.Add(new ScaleTransform(scaleX, scaleY));
                        transforms.Children.Add(new RotateTransform(rotation));
                        transforms.Children.Add(new TranslateTransform(pivot.X + offset.X, pivot.Y + offset.Y));
                        drawing.PushTransform(transforms);
                        drawing.DrawImage(source, new Rect(0, 0, source.PixelWidth, source.PixelHeight));
                        drawing.Pop();
                    }
                }

                target.Render(visual);
                SavePng(target, Path.Combine(outputDirectory, $"{index:D3}.png"));
                written++;
            }
        }

        return written;
    }

    private static void ValidateRig(IdleRig rig, string rigPath, string sourceRoot)
    {
        if (rig.SchemaVersion != 1)
        {
            throw new InvalidDataException($"Unsupported idle rig schema {rig.SchemaVersion}.");
        }
        if (rig.Canvas is null || rig.Canvas.Width != 512 || rig.Canvas.Height != 512)
        {
            throw new InvalidDataException("Idle rig canvas must be exactly 512x512.");
        }
        if (rig.Clips is null || rig.Clips.Count == 0)
        {
            throw new InvalidDataException("Idle rig must declare one or more clips.");
        }

        var ids = new HashSet<string>(StringComparer.Ordinal);
        foreach (var clip in rig.Clips)
        {
            if (string.IsNullOrWhiteSpace(clip.Id) || !AllowedClipIds.Contains(clip.Id))
            {
                throw new InvalidDataException($"Idle rig clip '{clip.Id}' is not one of {string.Join(", ", AllowedClipIds.Order())}.");
            }
            if (!ids.Add(clip.Id))
            {
                throw new InvalidDataException($"Idle rig declares duplicate clip '{clip.Id}'.");
            }
            if (clip.Frames is null || clip.Frames.Count == 0)
            {
                throw new InvalidDataException($"Idle rig clip '{clip.Id}' has no frames.");
            }

            for (var index = 0; index < clip.Frames.Count; index++)
            {
                var layers = clip.Frames[index].Layers;
                if (layers is null || layers.Count == 0)
                {
                    throw new InvalidDataException($"Idle rig clip '{clip.Id}' frame {index} has no layers.");
                }
                var layerIds = new HashSet<string>(StringComparer.Ordinal);
                foreach (var layer in layers)
                {
                    if (string.IsNullOrWhiteSpace(layer.Id) || !layerIds.Add(layer.Id))
                    {
                        throw new InvalidDataException($"Idle rig clip '{clip.Id}' frame {index} has a missing or duplicate layer id.");
                    }
                    if (string.IsNullOrWhiteSpace(layer.Source) || !layer.Source.EndsWith(".png", StringComparison.OrdinalIgnoreCase))
                    {
                        throw new InvalidDataException($"Idle rig clip '{clip.Id}' frame {index} layer '{layer.Id}' must name a PNG source.");
                    }
                    ResolveContained(sourceRoot, layer.Source);
                    if ((layer.ScaleX is not null && (!double.IsFinite(layer.ScaleX.Value) || layer.ScaleX.Value <= 0)) ||
                        (layer.ScaleY is not null && (!double.IsFinite(layer.ScaleY.Value) || layer.ScaleY.Value <= 0)) ||
                        (layer.RotationDeg is not null && !double.IsFinite(layer.RotationDeg.Value)))
                    {
                        throw new InvalidDataException($"Idle rig clip '{clip.Id}' frame {index} layer '{layer.Id}' has an invalid scale or rotation.");
                    }
                }
                var missingSlots = RequiredSlots.Where(slot => !layerIds.Contains(slot)).ToArray();
                if (missingSlots.Length > 0)
                {
                    throw new InvalidDataException($"Idle rig clip '{clip.Id}' frame {index} is missing required slots: {string.Join(", ", missingSlots)}.");
                }
            }
        }
        var missingClips = AllowedClipIds.Where(id => !ids.Contains(id)).ToArray();
        if (missingClips.Length > 0)
        {
            throw new InvalidDataException($"Idle rig must declare all expression clips; missing: {string.Join(", ", missingClips)}.");
        }
    }

    private static string ResolveContained(string root, string relativePath)
    {
        var normalizedRoot = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        var candidate = Path.GetFullPath(Path.Combine(normalizedRoot, relativePath.Replace('/', Path.DirectorySeparatorChar)));
        if (!candidate.StartsWith(normalizedRoot, StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidDataException($"Path escapes idle-rig source directory: {relativePath}");
        }
        if (!File.Exists(candidate))
        {
            throw new FileNotFoundException($"Idle rig source is missing: {relativePath}", candidate);
        }
        return candidate;
    }

    private static BitmapSource LoadBitmap(string path)
    {
        using var stream = File.OpenRead(path);
        var frame = BitmapDecoder.Create(stream, BitmapCreateOptions.PreservePixelFormat, BitmapCacheOption.OnLoad).Frames[0];
        frame.Freeze();
        return frame;
    }

    private static void SavePng(BitmapSource bitmap, string path)
    {
        var encoder = new PngBitmapEncoder();
        encoder.Frames.Add(BitmapFrame.Create(bitmap));
        using var stream = new FileStream(path, FileMode.Create, FileAccess.Write, FileShare.None);
        encoder.Save(stream);
    }
}

internal sealed record IdleRig(int SchemaVersion, RigCanvas? Canvas, IReadOnlyList<RigClip>? Clips);
internal sealed record RigCanvas(int Width, int Height);
internal sealed record RigClip(string Id, IReadOnlyList<RigFrame>? Frames);
internal sealed record RigFrame(IReadOnlyList<RigLayer>? Layers);
internal sealed record RigLayer(
    string Id,
    string Source,
    RigPoint? Pivot = null,
    RigPoint? LocalPivot = null,
    RigPoint? Offset = null,
    int DrawOrder = 0,
    double? RotationDeg = null,
    double? ScaleX = null,
    double? ScaleY = null);
internal sealed record RigPoint(int X, int Y);

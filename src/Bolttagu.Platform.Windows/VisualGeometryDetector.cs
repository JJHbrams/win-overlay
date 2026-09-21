using Bolttagu.Contracts;

namespace Bolttagu.Platform.Windows;

public enum VisualGeometryKind
{
    TextLine,
    VerticalLine,
}

public readonly record struct VisualGeometry(
    long Id,
    VisualGeometryKind Kind,
    ScreenArea Bounds,
    long ForegroundWindowId);

public sealed record VisualGeometrySnapshot(
    long ForegroundWindowId,
    DateTimeOffset CapturedAt,
    IReadOnlyList<VisualGeometry> Geometry,
    VisualCollisionMask? CollisionMask = null);

public sealed record VisualGeometryAnalysis(
    IReadOnlyList<VisualGeometry> Geometry,
    VisualCollisionMask CollisionMask);

public sealed record CapturedWindowFrame(
    long ForegroundWindowId,
    DateTimeOffset CapturedAt,
    ScreenPoint ScreenOrigin,
    double CoordinateScale,
    int Width,
    int Height,
    int Stride,
    byte[] Bgra32);

public sealed class VisualCollisionMask(
    long foregroundWindowId,
    ScreenPoint screenOrigin,
    double coordinateScale,
    int width,
    int height,
    bool[] solid)
{
    private const double FootSensorHalfWidthDip = 12;
    private const double MaximumBridgeGapDip = 18;
    private const double GlyphBandHeightDip = 48;
    private const double MinimumPlatformWidthDip = 10;

    public bool TryFindPlatform(double screenX, double fromScreenY, double toScreenY, out VisualGeometry platform)
    {
        platform = default;
        if (solid.Length != width * height || coordinateScale <= 0 || toScreenY < fromScreenY) return false;
        var centerX = ToPixelX(screenX);
        if (centerX < 0 || centerX >= width) return false;
        var startY = Math.Clamp(ToPixelY(fromScreenY), 0, height - 1);
        var endY = Math.Clamp(ToPixelY(toScreenY), 0, height - 1);
        var halfWidth = Math.Max(2, (int)Math.Ceiling(FootSensorHalfWidthDip * coordinateScale));

        for (var y = startY; y <= endY; y++)
        {
            var hitX = FindSolidNear(y, centerX, halfWidth);
            if (hitX < 0 || !TryBuildRun(hitX, y, out var left, out var right)) continue;
            var bounds = new ScreenArea(
                new(screenOrigin.X + left / coordinateScale, screenOrigin.Y + y / coordinateScale),
                new((right - left) / coordinateScale, Math.Max(1, 1 / coordinateScale)));
            if (bounds.Size.Width < MinimumPlatformWidthDip) continue;
            platform = new(StablePlatformId(bounds), VisualGeometryKind.TextLine, bounds, foregroundWindowId);
            return true;
        }
        return false;
    }

    private int FindSolidNear(int y, int centerX, int halfWidth)
    {
        var left = Math.Max(0, centerX - halfWidth);
        var right = Math.Min(width - 1, centerX + halfWidth);
        for (var distance = 0; distance <= halfWidth; distance++)
        {
            var rightX = centerX + distance;
            if (rightX <= right && solid[y * width + rightX]) return rightX;
            var leftX = centerX - distance;
            if (distance > 0 && leftX >= left && solid[y * width + leftX]) return leftX;
        }
        return -1;
    }

    private bool TryBuildRun(int seedX, int topY, out int left, out int right)
    {
        var bandBottom = Math.Min(height, topY + Math.Max(2, (int)Math.Ceiling(GlyphBandHeightDip * coordinateScale)));
        var maximumGap = Math.Max(2, (int)Math.Ceiling(MaximumBridgeGapDip * coordinateScale));
        left = seedX;
        right = seedX + 1;
        var occupiedColumns = 0;

        var gap = 0;
        for (var x = seedX; x >= 0; x--)
        {
            if (ColumnHasSolid(x, topY, bandBottom))
            {
                left = x;
                occupiedColumns++;
                gap = 0;
            }
            else if (++gap > maximumGap) break;
        }

        gap = 0;
        for (var x = seedX + 1; x < width; x++)
        {
            if (ColumnHasSolid(x, topY, bandBottom))
            {
                right = x + 1;
                occupiedColumns++;
                gap = 0;
            }
            else if (++gap > maximumGap) break;
        }
        return occupiedColumns >= 3;
    }

    private bool ColumnHasSolid(int x, int top, int bottom)
    {
        for (var y = top; y < bottom; y++)
            if (solid[y * width + x]) return true;
        return false;
    }

    private int ToPixelX(double screenX) => (int)Math.Round((screenX - screenOrigin.X) * coordinateScale);
    private int ToPixelY(double screenY) => (int)Math.Floor((screenY - screenOrigin.Y) * coordinateScale);

    private long StablePlatformId(ScreenArea bounds)
    {
        unchecked
        {
            var hash = foregroundWindowId;
            hash = (hash * 397) ^ (long)Math.Round(bounds.Origin.X / 8d);
            hash = (hash * 397) ^ (long)Math.Round(bounds.Origin.Y / 4d);
            hash = (hash * 397) ^ (long)Math.Round(bounds.Size.Width / 8d);
            return hash == 0 ? 1 : hash;
        }
    }
}

public sealed class VisualGeometryDetector
{
    private const int EdgeThreshold = 36;
    private const double MinimumGlyphHeightDip = 6;
    private const double MaximumGlyphHeightDip = 48;
    private const double MaximumGlyphWidthDip = 64;
    private const double MaximumTextGapDip = 32;
    private const double MinimumVerticalHeightDip = 96;
    private const double MaximumVerticalWidthDip = 8;

    public IReadOnlyList<VisualGeometry> Detect(CapturedWindowFrame frame)
        => Analyze(frame).Geometry;

    public VisualGeometryAnalysis Analyze(CapturedWindowFrame frame)
    {
        Validate(frame);
        var luminance = BuildLuminance(frame);
        var edges = BuildEdgeMask(luminance, frame.Width, frame.Height);
        var components = FindComponents(edges, frame.Width, frame.Height);
        var output = new List<VisualGeometry>();
        output.AddRange(FindTextLines(frame, components));
        output.AddRange(FindVerticalLines(frame, edges));
        return new(output, new(
            frame.ForegroundWindowId,
            frame.ScreenOrigin,
            frame.CoordinateScale,
            frame.Width,
            frame.Height,
            edges));
    }

    private static byte[] BuildLuminance(CapturedWindowFrame frame)
    {
        var luminance = new byte[frame.Width * frame.Height];
        for (var y = 0; y < frame.Height; y++)
        {
            var row = y * frame.Stride;
            var targetRow = y * frame.Width;
            for (var x = 0; x < frame.Width; x++)
            {
                var source = row + (x * 4);
                var blue = frame.Bgra32[source];
                var green = frame.Bgra32[source + 1];
                var red = frame.Bgra32[source + 2];
                luminance[targetRow + x] = (byte)((red * 77 + green * 150 + blue * 29) >> 8);
            }
        }
        return luminance;
    }

    private static bool[] BuildEdgeMask(byte[] luminance, int width, int height)
    {
        var edges = new bool[width * height];
        for (var y = 1; y < height - 1; y++)
        {
            var row = y * width;
            for (var x = 1; x < width - 1; x++)
            {
                var index = row + x;
                var center = luminance[index];
                var contrast = Math.Max(
                    Math.Max(Math.Abs(center - luminance[index - 1]), Math.Abs(center - luminance[index + 1])),
                    Math.Max(Math.Abs(center - luminance[index - width]), Math.Abs(center - luminance[index + width])));
                edges[index] = contrast >= EdgeThreshold;
            }
        }
        return edges;
    }

    private static IReadOnlyList<Component> FindComponents(bool[] edges, int width, int height)
    {
        var visited = new bool[edges.Length];
        var queue = new Queue<int>();
        var components = new List<Component>();
        for (var index = 0; index < edges.Length; index++)
        {
            if (!edges[index] || visited[index]) continue;
            visited[index] = true;
            queue.Enqueue(index);
            var left = width;
            var right = 0;
            var top = height;
            var bottom = 0;
            var pixels = 0;
            while (queue.Count > 0)
            {
                var current = queue.Dequeue();
                var x = current % width;
                var y = current / width;
                left = Math.Min(left, x);
                right = Math.Max(right, x);
                top = Math.Min(top, y);
                bottom = Math.Max(bottom, y);
                pixels++;
                for (var offsetY = -1; offsetY <= 1; offsetY++)
                {
                    for (var offsetX = -1; offsetX <= 1; offsetX++)
                    {
                        if (offsetX == 0 && offsetY == 0) continue;
                        var nextX = x + offsetX;
                        var nextY = y + offsetY;
                        if (nextX < 0 || nextX >= width || nextY < 0 || nextY >= height) continue;
                        var next = nextY * width + nextX;
                        if (!edges[next] || visited[next]) continue;
                        visited[next] = true;
                        queue.Enqueue(next);
                    }
                }
            }
            components.Add(new(left, top, right + 1, bottom + 1, pixels));
        }
        return components;
    }

    private static IEnumerable<VisualGeometry> FindTextLines(
        CapturedWindowFrame frame,
        IReadOnlyList<Component> components)
    {
        var scale = frame.CoordinateScale;
        var glyphs = components
            .Where(component => component.Height >= MinimumGlyphHeightDip * scale)
            .Where(component => component.Height <= MaximumGlyphHeightDip * scale)
            .Where(component => component.Width <= MaximumGlyphWidthDip * scale)
            .Where(component => component.Pixels >= Math.Max(6, (component.Width + component.Height) / 2))
            .OrderBy(component => component.Bottom)
            .ThenBy(component => component.Left)
            .ToArray();

        var rows = new List<List<Component>>();
        foreach (var glyph in glyphs)
        {
            var tolerance = Math.Max(4 * scale, glyph.Height * 0.35);
            var row = rows.FirstOrDefault(candidate =>
                Math.Abs(candidate.Average(component => component.Bottom) - glyph.Bottom) <= tolerance);
            if (row is null)
            {
                row = [];
                rows.Add(row);
            }
            row.Add(glyph);
        }

        foreach (var row in rows)
        {
            var ordered = row.OrderBy(component => component.Left).ToArray();
            var run = new List<Component>();
            foreach (var glyph in ordered)
            {
                if (run.Count > 0 && glyph.Left - run[^1].Right > MaximumTextGapDip * scale)
                {
                    foreach (var geometry in ToTextGeometry(frame, run)) yield return geometry;
                    run.Clear();
                }
                run.Add(glyph);
            }
            foreach (var geometry in ToTextGeometry(frame, run)) yield return geometry;
        }
    }

    private static IEnumerable<VisualGeometry> ToTextGeometry(CapturedWindowFrame frame, IReadOnlyList<Component> run)
    {
        if (run.Count < 3) yield break;
        var left = run.Min(component => component.Left);
        var right = run.Max(component => component.Right);
        var top = run.Min(component => component.Top);
        var bottom = run.Max(component => component.Bottom);
        var bounds = ToScreenArea(frame, left, top, right, bottom);
        yield return new(StableId(frame.ForegroundWindowId, VisualGeometryKind.TextLine, bounds),
            VisualGeometryKind.TextLine, bounds, frame.ForegroundWindowId);
    }

    private static IEnumerable<VisualGeometry> FindVerticalLines(CapturedWindowFrame frame, bool[] edges)
    {
        var scale = frame.CoordinateScale;
        var minimumHeight = Math.Max(1, (int)Math.Ceiling(MinimumVerticalHeightDip * scale));
        var maximumWidth = Math.Max(1, (int)Math.Ceiling(MaximumVerticalWidthDip * scale));
        var spans = new List<Component>();
        for (var x = 4; x < frame.Width - 4; x++)
        {
            var start = -1;
            var last = -1;
            for (var y = 1; y < frame.Height - 1; y++)
            {
                if (!edges[y * frame.Width + x])
                {
                    if (last >= 0 && y - last <= 2) continue;
                    if (start >= 0 && last - start + 1 >= minimumHeight)
                        spans.Add(new(x, start, x + 1, last + 1, last - start + 1));
                    start = -1;
                    last = -1;
                    continue;
                }
                if (start < 0) start = y;
                last = y;
            }
            if (start >= 0 && last - start + 1 >= minimumHeight)
                spans.Add(new(x, start, x + 1, last + 1, last - start + 1));
        }

        var consumed = new bool[spans.Count];
        for (var index = 0; index < spans.Count; index++)
        {
            if (consumed[index]) continue;
            var seed = spans[index];
            var left = seed.Left;
            var right = seed.Right;
            var top = seed.Top;
            var bottom = seed.Bottom;
            consumed[index] = true;
            for (var next = index + 1; next < spans.Count; next++)
            {
                if (consumed[next] || spans[next].Left - right > maximumWidth) break;
                if (Math.Abs(spans[next].Top - top) > 4 * scale ||
                    Math.Abs(spans[next].Bottom - bottom) > 4 * scale) continue;
                right = spans[next].Right;
                top = Math.Min(top, spans[next].Top);
                bottom = Math.Max(bottom, spans[next].Bottom);
                consumed[next] = true;
            }
            if (right - left > maximumWidth) continue;
            var bounds = ToScreenArea(frame, left, top, right, bottom);
            yield return new(StableId(frame.ForegroundWindowId, VisualGeometryKind.VerticalLine, bounds),
                VisualGeometryKind.VerticalLine, bounds, frame.ForegroundWindowId);
        }
    }

    private static ScreenArea ToScreenArea(CapturedWindowFrame frame, int left, int top, int right, int bottom) =>
        new(
            new(frame.ScreenOrigin.X + left / frame.CoordinateScale,
                frame.ScreenOrigin.Y + top / frame.CoordinateScale),
            new((right - left) / frame.CoordinateScale,
                (bottom - top) / frame.CoordinateScale));

    private static long StableId(long foregroundWindowId, VisualGeometryKind kind, ScreenArea bounds)
    {
        unchecked
        {
            var hash = 1469598103934665603L;
            hash = (hash ^ foregroundWindowId) * 1099511628211L;
            hash = (hash ^ (long)kind) * 1099511628211L;
            hash = (hash ^ (long)Math.Round(bounds.Origin.X / 4d)) * 1099511628211L;
            hash = (hash ^ (long)Math.Round(bounds.Origin.Y / 4d)) * 1099511628211L;
            hash = (hash ^ (long)Math.Round(bounds.Size.Width / 4d)) * 1099511628211L;
            hash = (hash ^ (long)Math.Round(bounds.Size.Height / 4d)) * 1099511628211L;
            return hash == 0 ? long.MaxValue : hash;
        }
    }

    private static void Validate(CapturedWindowFrame frame)
    {
        if (frame.Width <= 0 || frame.Height <= 0 || frame.Stride < frame.Width * 4 ||
            frame.Bgra32.Length < frame.Stride * frame.Height || frame.CoordinateScale <= 0)
            throw new ArgumentException("Captured frame dimensions are invalid.", nameof(frame));
    }

    private readonly record struct Component(int Left, int Top, int Right, int Bottom, int Pixels)
    {
        public int Width => Right - Left;
        public int Height => Bottom - Top;
    }
}

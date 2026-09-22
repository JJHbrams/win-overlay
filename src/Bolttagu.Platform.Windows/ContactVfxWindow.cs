using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Media.Effects;
using System.Windows.Shapes;
using System.Windows.Threading;
using Bolttagu.Contracts;

namespace Bolttagu.Platform.Windows;

public readonly record struct VfxContact(SpriteContactKind Kind, ScreenPoint ScreenPosition);
public readonly record struct ContactVfxVisual(
    SpriteContactKind Kind,
    ScreenPoint ScreenPosition,
    double Opacity);

public sealed class ContactVfxTracker
{
    public const int MaximumMarks = 16;
    public static readonly TimeSpan FadeDelay = TimeSpan.FromMilliseconds(300);
    public static readonly TimeSpan Lifetime = TimeSpan.FromMilliseconds(600);
    private const double RefreshDistance = 10;
    private readonly List<Mark> _marks = [];
    private long _nextId;

    public void Update(IReadOnlyList<VfxContact> contacts, DateTimeOffset now)
    {
        RemoveExpired(now);
        foreach (var contact in contacts)
        {
            var existingIndex = _marks.FindIndex(mark =>
                mark.Kind == contact.Kind &&
                Distance(mark.Position, contact.ScreenPosition) <= RefreshDistance &&
                now - mark.LastSeenAt <= FadeDelay);
            if (existingIndex >= 0)
            {
                var existing = _marks[existingIndex];
                _marks[existingIndex] = existing with
                {
                    Position = contact.ScreenPosition,
                    LastSeenAt = now,
                };
            }
            else
            {
                _marks.Add(new(++_nextId, contact.Kind, contact.ScreenPosition, now, now));
            }
        }

        while (_marks.Count > MaximumMarks)
        {
            var oldest = _marks.OrderBy(mark => mark.CreatedAt).First();
            _marks.Remove(oldest);
        }
    }

    public IReadOnlyList<ContactVfxVisual> GetVisible(DateTimeOffset now)
    {
        RemoveExpired(now);
        return _marks.Select(mark => new ContactVfxVisual(
            mark.Kind,
            mark.Position,
            Opacity(mark, now))).ToArray();
    }

    public void Clear() => _marks.Clear();

    private void RemoveExpired(DateTimeOffset now) =>
        _marks.RemoveAll(mark => now - mark.LastSeenAt >= Lifetime);

    private static double Opacity(Mark mark, DateTimeOffset now)
    {
        var age = now - mark.LastSeenAt;
        if (age <= FadeDelay) return 1;
        return Math.Clamp(1 - (age - FadeDelay).TotalMilliseconds /
            (Lifetime - FadeDelay).TotalMilliseconds, 0, 1);
    }

    private static double Distance(ScreenPoint first, ScreenPoint second)
    {
        var x = first.X - second.X;
        var y = first.Y - second.Y;
        return Math.Sqrt(x * x + y * y);
    }

    private sealed record Mark(
        long Id,
        SpriteContactKind Kind,
        ScreenPoint Position,
        DateTimeOffset CreatedAt,
        DateTimeOffset LastSeenAt);
}

public sealed class ContactVfxWindow : Window, IDisposable
{
    private const int GwlExStyle = -20;
    private const nint WsExTransparent = 0x00000020;
    private const nint WsExToolWindow = 0x00000080;
    private const nint WsExNoActivate = 0x08000000;
    private const uint WdaExcludeFromCapture = 0x00000011;
    private readonly Canvas _canvas = new() { IsHitTestVisible = false };
    private readonly ContactVfxTracker _tracker = new();
    private IReadOnlyList<VisualGeometry> _debugGeometry = [];
    private SurfaceProbeDebug? _surfaceDebug;
    private readonly DispatcherTimer _timer;
    private bool _disposed;

    public ContactVfxWindow()
    {
        Title = "Bolttagu Contact VFX";
        WindowStyle = WindowStyle.None;
        ResizeMode = ResizeMode.NoResize;
        AllowsTransparency = true;
        Background = System.Windows.Media.Brushes.Transparent;
        Topmost = true;
        ShowInTaskbar = false;
        ShowActivated = false;
        IsHitTestVisible = false;
        Left = SystemParameters.VirtualScreenLeft;
        Top = SystemParameters.VirtualScreenTop;
        Width = SystemParameters.VirtualScreenWidth;
        Height = SystemParameters.VirtualScreenHeight;
        Content = _canvas;
        SourceInitialized += OnSourceInitialized;
        _timer = new(DispatcherPriority.Render, Dispatcher)
        {
            Interval = TimeSpan.FromMilliseconds(33),
        };
        _timer.Tick += OnTimerTick;
    }

    public void ShowLayer()
    {
        if (_disposed) return;
        if (!IsVisible) Show();
        _timer.Start();
    }

    public void HideLayer()
    {
        Clear();
        _timer.Stop();
        Hide();
    }

    public void UpdateContacts(IReadOnlyList<VfxContact> contacts)
    {
        if (_disposed) return;
        _tracker.Update(contacts, DateTimeOffset.UtcNow);
        Render(DateTimeOffset.UtcNow);
    }

    public void UpdateDebugGeometry(IReadOnlyList<VisualGeometry> geometry)
    {
        if (_disposed) return;
        _debugGeometry = geometry;
        Render(DateTimeOffset.UtcNow);
    }

    public void UpdateSurfaceDebug(SurfaceProbeDebug debug)
    {
        if (_disposed) return;
        _surfaceDebug = debug;
        Title = $"Bolttagu Contact VFX | {debug.Operation} valid={debug.Valid} " +
                $"surface={debug.Surface.Kind} text={debug.TextSurfaceCount} vertical={debug.VerticalSurfaceCount}";
        Render(DateTimeOffset.UtcNow);
    }

    public void Clear()
    {
        _tracker.Clear();
        _canvas.Children.Clear();
    }

    private void OnTimerTick(object? sender, EventArgs e) => Render(DateTimeOffset.UtcNow);

    private void Render(DateTimeOffset now)
    {
        _canvas.Children.Clear();
        foreach (var geometry in _debugGeometry)
            _canvas.Children.Add(CreateDebugSurface(geometry));
        if (_surfaceDebug is { } debug)
        {
            _canvas.Children.Add(CreateSelectedSurface(debug));
            _canvas.Children.Add(CreateProbe(debug));
        }
        foreach (var visual in _tracker.GetVisible(now))
        {
            _canvas.Children.Add(CreateWrinkle(visual));
        }
    }

    private static Shape CreateSelectedSurface(SurfaceProbeDebug debug)
    {
        var left = debug.Surface.Left - SystemParameters.VirtualScreenLeft;
        var top = debug.Surface.Top - SystemParameters.VirtualScreenTop;
        return new Line
        {
            X1 = left,
            X2 = debug.Surface.Right - SystemParameters.VirtualScreenLeft,
            Y1 = top,
            Y2 = top,
            Stroke = System.Windows.Media.Brushes.Gold,
            StrokeThickness = 4,
            Opacity = 0.9,
            IsHitTestVisible = false,
        };
    }

    private static Shape CreateProbe(SurfaceProbeDebug debug)
    {
        var ellipse = new Ellipse
        {
            Width = 10,
            Height = 10,
            Fill = debug.Valid ? System.Windows.Media.Brushes.Red : System.Windows.Media.Brushes.OrangeRed,
            Opacity = 0.9,
            IsHitTestVisible = false,
        };
        Canvas.SetLeft(ellipse, debug.Probe.X - SystemParameters.VirtualScreenLeft - 5);
        Canvas.SetTop(ellipse, debug.Probe.Y - SystemParameters.VirtualScreenTop - 5);
        return ellipse;
    }

    private static Shape CreateDebugSurface(VisualGeometry geometry)
    {
        var left = geometry.Bounds.Origin.X - SystemParameters.VirtualScreenLeft;
        var top = geometry.Bounds.Origin.Y - SystemParameters.VirtualScreenTop;
        if (geometry.Kind is VisualGeometryKind.TextLine or VisualGeometryKind.HorizontalLine)
        {
            return new Line
            {
                X1 = left,
                X2 = left + geometry.Bounds.Size.Width,
                Y1 = top,
                Y2 = top,
                Stroke = new SolidColorBrush(System.Windows.Media.Color.FromRgb(38, 235, 216)),
                StrokeThickness = 2,
                Opacity = 0.8,
                IsHitTestVisible = false,
            };
        }
        var rectangle = new System.Windows.Shapes.Rectangle
        {
            Width = Math.Max(2, geometry.Bounds.Size.Width),
            Height = geometry.Bounds.Size.Height,
            Stroke = new SolidColorBrush(System.Windows.Media.Color.FromRgb(236, 70, 220)),
            StrokeThickness = 2,
            Opacity = 0.7,
            IsHitTestVisible = false,
        };
        Canvas.SetLeft(rectangle, left);
        Canvas.SetTop(rectangle, top);
        return rectangle;
    }

    private static Path CreateWrinkle(ContactVfxVisual visual)
    {
        var radius = visual.Kind == SpriteContactKind.Hand ? 12d : 18d;
        var centerX = visual.ScreenPosition.X - SystemParameters.VirtualScreenLeft;
        var centerY = visual.ScreenPosition.Y - SystemParameters.VirtualScreenTop;
        var geometry = new StreamGeometry();
        using (var context = geometry.Open())
        {
            for (var offset = -1; offset <= 1; offset++)
            {
                var y = centerY + offset * 4;
                context.BeginFigure(new(centerX - radius, y), false, false);
                context.QuadraticBezierTo(
                    new(centerX, y - 3 - Math.Abs(offset)),
                    new(centerX + radius, y),
                    true,
                    false);
            }
        }
        geometry.Freeze();
        return new()
        {
            Data = geometry,
            Stroke = visual.Kind == SpriteContactKind.Hand
                ? new SolidColorBrush(System.Windows.Media.Color.FromRgb(236, 87, 204))
                : new SolidColorBrush(System.Windows.Media.Color.FromRgb(83, 220, 224)),
            StrokeThickness = 1.6,
            StrokeStartLineCap = PenLineCap.Round,
            StrokeEndLineCap = PenLineCap.Round,
            Opacity = visual.Opacity * 0.72,
            IsHitTestVisible = false,
            Effect = new BlurEffect { Radius = 1.5 },
        };
    }

    private void OnSourceInitialized(object? sender, EventArgs e)
    {
        var handle = new WindowInteropHelper(this).Handle;
        var style = GetWindowLongPtr(handle, GwlExStyle);
        SetWindowLongPtr(handle, GwlExStyle,
            style | WsExTransparent | WsExToolWindow | WsExNoActivate);
        _ = SetWindowDisplayAffinity(handle, WdaExcludeFromCapture);
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        _timer.Stop();
        _timer.Tick -= OnTimerTick;
        _debugGeometry = [];
        _surfaceDebug = null;
        Clear();
        Close();
    }

    [DllImport("user32.dll", EntryPoint = "GetWindowLongPtrW", SetLastError = true)]
    private static extern nint GetWindowLongPtr(IntPtr handle, int index);

    [DllImport("user32.dll", EntryPoint = "SetWindowLongPtrW", SetLastError = true)]
    private static extern nint SetWindowLongPtr(IntPtr handle, int index, nint newLong);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool SetWindowDisplayAffinity(IntPtr handle, uint affinity);
}

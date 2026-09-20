using Bolttagu.Contracts;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;

namespace Bolttagu.Presentation;

public sealed class PetSpriteView : UserControl, IAnimationPlayer
{
    private readonly IAnimationCatalog _catalog;
    private readonly Image _image;
    private readonly TextBlock _diagnosticText;
    private readonly DispatcherTimer _timer;
    private readonly ScaleTransform _facingTransform = new(1, 1);
    private readonly Dictionary<string, BitmapSource> _atlases = new(StringComparer.OrdinalIgnoreCase);
    private AnimationPlaybackCursor? _cursor;
    private bool _disposed;

    public PetSpriteView(IAnimationCatalog catalog)
    {
        _catalog = catalog ?? throw new ArgumentNullException(nameof(catalog));
        Width = 220;
        Height = 220;
        SnapsToDevicePixels = true;

        _image = new Image
        {
            Stretch = Stretch.Uniform,
            HorizontalAlignment = HorizontalAlignment.Stretch,
            VerticalAlignment = VerticalAlignment.Stretch,
            SnapsToDevicePixels = true
        };
        RenderOptions.SetBitmapScalingMode(_image, BitmapScalingMode.HighQuality);
        _image.RenderTransformOrigin = new Point(0.5, 0.5);
        _image.RenderTransform = _facingTransform;

        _diagnosticText = new TextBlock
        {
            Text = catalog.IsFallback ? "Static fallback" : "P3 · 100% DPI",
            FontSize = 11,
            Foreground = Brushes.White,
            Background = new SolidColorBrush(Color.FromArgb(145, 30, 22, 38)),
            Padding = new Thickness(5, 2, 5, 2),
            HorizontalAlignment = HorizontalAlignment.Center,
            VerticalAlignment = VerticalAlignment.Bottom,
            Margin = new Thickness(0, 0, 0, 2)
        };

        Content = new Grid { Children = { _image, _diagnosticText } };
        _timer = new DispatcherTimer(DispatcherPriority.Render, Dispatcher)
        {
            IsEnabled = false
        };
        _timer.Tick += OnTimerTick;
    }

    public string? CurrentClipId => _cursor?.Clip.Id;
    public FacingDirection Facing { get; private set; } = FacingDirection.Right;
    public int CurrentFrameIndex => _cursor?.FrameIndex ?? -1;
    public event EventHandler<AnimationPlaybackCompletedEventArgs>? PlaybackCompleted;

    public void Play(string clipId)
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        _timer.Stop();
        _cursor = new(_catalog.GetClip(clipId));
        RenderCurrentFrame();
        ScheduleCurrentFrame();
    }

    public void Stop()
    {
        _timer.Stop();
        _cursor = null;
        _image.Source = null;
    }

    public void SetFacing(FacingDirection facing)
    {
        Facing = facing;
        _facingTransform.ScaleX = facing == FacingDirection.Left ? -1 : 1;
    }

    public void SetDpiScale(double scale)
    {
        var prefix = _catalog.IsFallback ? "Static fallback" : "P3";
        _diagnosticText.Text = $"{prefix} · {scale:P0} DPI";
    }

    public void Dispose()
    {
        if (_disposed)
        {
            return;
        }
        _disposed = true;
        _timer.Stop();
        _timer.Tick -= OnTimerTick;
        _atlases.Clear();
        _image.Source = null;
    }

    private void OnTimerTick(object? sender, EventArgs e)
    {
        if (_cursor is null)
        {
            _timer.Stop();
            return;
        }

        if (_cursor.Advance())
        {
            var completedClip = _cursor.Clip.Id;
            _timer.Stop();
            PlaybackCompleted?.Invoke(this, new(completedClip));
            return;
        }

        RenderCurrentFrame();
        ScheduleCurrentFrame();
    }

    private void ScheduleCurrentFrame()
    {
        if (_cursor is null)
        {
            return;
        }
        _timer.Interval = _cursor.CurrentFrame.Duration;
        _timer.Start();
    }

    private void RenderCurrentFrame()
    {
        var frame = _cursor?.CurrentFrame ?? throw new InvalidOperationException("No active animation frame.");
        var atlas = GetAtlas(frame.AtlasPath);
        var rect = frame.SourceRect;
        _image.Source = new CroppedBitmap(atlas, new Int32Rect(rect.X, rect.Y, rect.Width, rect.Height));
    }

    private BitmapSource GetAtlas(string path)
    {
        if (_atlases.TryGetValue(path, out var cached))
        {
            return cached;
        }

        using var stream = File.OpenRead(path);
        var decoder = BitmapDecoder.Create(stream, BitmapCreateOptions.PreservePixelFormat, BitmapCacheOption.OnLoad);
        var atlas = decoder.Frames[0];
        atlas.Freeze();
        _atlases.Add(path, atlas);
        return atlas;
    }
}

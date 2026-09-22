using Bolttagu.Contracts;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;

namespace Bolttagu.Presentation;

public sealed class PetSpriteView : UserControl, IAnimationPlayer, IAnimationFrameSource
{
    public const double SpriteWidthDip = 220;
    public const double SpriteCanvasHeightDip = 220;
    public const double FootAlignedHeightDip = SpriteCanvasHeightDip * 480d / 512d;
    private readonly IAnimationCatalog _catalog;
    private readonly Image _image;
    private readonly DispatcherTimer _timer;
    private readonly ScaleTransform _facingTransform = new(1, 1);
    private readonly Dictionary<string, BitmapSource> _atlases = new(StringComparer.OrdinalIgnoreCase);
    private AnimationPlaybackCursor? _cursor;
    private bool _disposed;

    public PetSpriteView(IAnimationCatalog catalog)
    {
        _catalog = catalog ?? throw new ArgumentNullException(nameof(catalog));
        Width = SpriteWidthDip;
        Height = FootAlignedHeightDip;
        ClipToBounds = true;
        SnapsToDevicePixels = true;

        _image = new Image
        {
            Width = SpriteWidthDip,
            Height = SpriteCanvasHeightDip,
            Stretch = Stretch.Uniform,
            HorizontalAlignment = HorizontalAlignment.Left,
            VerticalAlignment = VerticalAlignment.Top,
            SnapsToDevicePixels = true
        };
        RenderOptions.SetBitmapScalingMode(_image, BitmapScalingMode.HighQuality);
        _image.RenderTransformOrigin = new Point(0.5, 0.5);
        _image.RenderTransform = _facingTransform;

        Content = _image;
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
    public event EventHandler<AnimationFramePresentedEventArgs>? FramePresented;

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
        _ = scale;
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
        var viewWidth = SpriteWidthDip;
        var viewHeight = SpriteCanvasHeightDip;
        var scale = Math.Min(viewWidth / rect.Width, viewHeight / rect.Height);
        var offsetX = (viewWidth - rect.Width * scale) / 2d;
        var offsetY = (viewHeight - rect.Height * scale) / 2d;
        var contacts = frame.ContactAnchors.Select(contact =>
        {
            var localX = offsetX + contact.Point.X * scale;
            if (Facing == FacingDirection.Left) localX = viewWidth - localX;
            return new RenderedSpriteContact(
                contact.Kind,
                new(localX, offsetY + contact.Point.Y * scale));
        }).ToArray();
        FramePresented?.Invoke(this, new(_cursor!.Clip.Id, _cursor.FrameIndex, contacts));
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

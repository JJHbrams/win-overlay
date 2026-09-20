using Bolttagu.Contracts;

namespace Bolttagu.Runtime;

public sealed class PetAnimationController : IDisposable
{
    public const string IdleClip = "idle_breathe";
    public const string ClickClip = "click";

    private readonly IAnimationPlayer _player;
    private bool _disposed;

    public PetAnimationController(IAnimationPlayer player)
    {
        _player = player ?? throw new ArgumentNullException(nameof(player));
        _player.PlaybackCompleted += OnPlaybackCompleted;
    }

    public void Start()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        _player.Play(IdleClip);
    }

    public void ReactToClick()
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        _player.Play(ClickClip);
    }

    public void Dispose()
    {
        if (_disposed)
        {
            return;
        }
        _disposed = true;
        _player.PlaybackCompleted -= OnPlaybackCompleted;
        _player.Stop();
    }

    private void OnPlaybackCompleted(object? sender, AnimationPlaybackCompletedEventArgs e)
    {
        if (!_disposed && e.ClipId.Equals(ClickClip, StringComparison.Ordinal))
        {
            _player.Play(IdleClip);
        }
    }
}

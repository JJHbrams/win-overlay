using Bolttagu.Contracts;

namespace Bolttagu.Presentation;

public sealed class AnimationPlaybackCursor
{
    public AnimationPlaybackCursor(SpriteClip clip)
    {
        ArgumentNullException.ThrowIfNull(clip);
        if (clip.Frames.Count == 0)
        {
            throw new ArgumentException("Animation clip must contain frames.", nameof(clip));
        }
        Clip = clip;
    }

    public SpriteClip Clip { get; }
    public int FrameIndex { get; private set; }
    public SpriteFrame CurrentFrame => Clip.Frames[FrameIndex];

    public bool Advance()
    {
        if (FrameIndex + 1 < Clip.Frames.Count)
        {
            FrameIndex++;
            return false;
        }
        if (Clip.Loop)
        {
            FrameIndex = 0;
            return false;
        }
        return true;
    }
}

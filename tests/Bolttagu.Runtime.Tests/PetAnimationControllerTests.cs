using Bolttagu.Contracts;

namespace Bolttagu.Runtime.Tests;

[TestClass]
public sealed class PetAnimationControllerTests
{
    [TestMethod]
    public void ClickCompletion_ReturnsToIdle()
    {
        using var player = new FakeAnimationPlayer();
        using var controller = new PetAnimationController(player);

        controller.Start();
        controller.ReactToClick();
        player.Complete("click");

        CollectionAssert.AreEqual(
            new[] { "idle_breathe", "click", "idle_breathe" },
            player.PlayedClips.ToArray());
    }

    [TestMethod]
    public void RepeatedClick_RestartsClickClip()
    {
        using var player = new FakeAnimationPlayer();
        using var controller = new PetAnimationController(player);

        controller.Start();
        controller.ReactToClick();
        controller.ReactToClick();

        CollectionAssert.AreEqual(
            new[] { "idle_breathe", "click", "click" },
            player.PlayedClips.ToArray());
    }

    private sealed class FakeAnimationPlayer : IAnimationPlayer
    {
        public List<string> PlayedClips { get; } = [];
        public string? CurrentClipId { get; private set; }
        public event EventHandler<AnimationPlaybackCompletedEventArgs>? PlaybackCompleted;

        public void Play(string clipId)
        {
            CurrentClipId = clipId;
            PlayedClips.Add(clipId);
        }

        public void Complete(string clipId) =>
            PlaybackCompleted?.Invoke(this, new(clipId));

        public void Stop() => CurrentClipId = null;
        public void Dispose() { }
    }
}

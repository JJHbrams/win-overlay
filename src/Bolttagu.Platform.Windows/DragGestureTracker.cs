using Bolttagu.Contracts;

namespace Bolttagu.Platform.Windows;

public enum DragGestureResult
{
    None,
    Click,
    DragStarted,
    DragMoved,
    DragCompleted,
    DragCanceled,
}

public readonly record struct DragGestureUpdate(
    DragGestureResult Result,
    ScreenPoint WindowPosition);

public sealed class DragGestureTracker
{
    private ScreenPoint _pointerOrigin;
    private ScreenPoint _windowOrigin;

    public bool IsActive { get; private set; }
    public bool IsDragging { get; private set; }

    public void Begin(ScreenPoint pointer, ScreenPoint windowPosition)
    {
        _pointerOrigin = pointer;
        _windowOrigin = windowPosition;
        IsActive = true;
        IsDragging = false;
    }

    public DragGestureUpdate Move(
        ScreenPoint pointer,
        double dpiScaleX,
        double dpiScaleY,
        double thresholdX,
        double thresholdY)
    {
        if (!IsActive) return new(DragGestureResult.None, _windowOrigin);
        var deltaX = (pointer.X - _pointerOrigin.X) / dpiScaleX;
        var deltaY = (pointer.Y - _pointerOrigin.Y) / dpiScaleY;
        if (!IsDragging && Math.Abs(deltaX) < thresholdX && Math.Abs(deltaY) < thresholdY)
        {
            return new(DragGestureResult.None, _windowOrigin);
        }

        var result = IsDragging ? DragGestureResult.DragMoved : DragGestureResult.DragStarted;
        IsDragging = true;
        return new(result, new(_windowOrigin.X + deltaX, _windowOrigin.Y + deltaY));
    }

    public DragGestureResult Complete()
    {
        if (!IsActive) return DragGestureResult.None;
        var result = IsDragging ? DragGestureResult.DragCompleted : DragGestureResult.Click;
        Reset();
        return result;
    }

    public DragGestureResult Cancel()
    {
        if (!IsActive) return DragGestureResult.None;
        var result = IsDragging ? DragGestureResult.DragCanceled : DragGestureResult.None;
        Reset();
        return result;
    }

    private void Reset()
    {
        IsActive = false;
        IsDragging = false;
    }
}

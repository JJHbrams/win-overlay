using Bolttagu.Contracts;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Input;
using System.Windows.Interop;
using System.Windows.Media;

namespace Bolttagu.Platform.Windows;

public sealed class OverlayWindow : Window, IOverlayWindow
{
    private const int WmDpiChanged = 0x02E0;
    private const int GwlExStyle = -20;
    private const nint WsExNoActivate = 0x08000000;
    private readonly DragGestureTracker _dragGesture = new();
    private bool _releasingCapture;
    private ScreenPoint _dragAnchorCorrection;

    public OverlayWindow(UIElement content)
    {
        Title = "Bolttagu Desktop Pet";
        Width = 220;
        Height = 220;
        WindowStyle = WindowStyle.None;
        ResizeMode = ResizeMode.NoResize;
        AllowsTransparency = true;
        Background = System.Windows.Media.Brushes.Transparent;
        Topmost = true;
        ShowInTaskbar = false;
        ShowActivated = false;
        Content = content;
        PreviewMouseLeftButtonDown += OnPreviewMouseLeftButtonDown;
        PreviewMouseMove += OnPreviewMouseMove;
        PreviewMouseLeftButtonUp += OnPreviewMouseLeftButtonUp;
        LostMouseCapture += OnLostMouseCapture;
        ContextMenu = BuildContextMenu();
        SourceInitialized += OnSourceInitialized;
    }

    public ScreenPoint Position => new(Left, Top);
    ScreenSize IOverlayWindow.Size => new(ActualWidth, ActualHeight);
    public ScreenArea WorkArea
    {
        get
        {
            var area = SystemParameters.WorkArea;
            return new(new(area.Left, area.Top), new(area.Width, area.Height));
        }
    }
    public event EventHandler? ClickObserved;
    public event EventHandler? DragStarted;
    public event EventHandler? DragCompleted;
    public event EventHandler? DragCanceled;
    public event EventHandler? ExitRequested;
    public event EventHandler<double>? DpiScaleChanged;
    public void ShowOverlay() => Show();
    public void HideOverlay() { CancelPointerInteraction(); Hide(); }
    public void CloseOverlay() { CancelPointerInteraction(); Close(); }

    public void PlaceAtBottomRight(double margin)
    {
        var area = SystemParameters.WorkArea;
        Left = Math.Max(area.Left, area.Right - Width - margin);
        Top = Math.Max(area.Top, area.Bottom - Height - margin);
    }

    public void MoveTo(ScreenPoint position)
    {
        var area = WorkArea;
        Left = Math.Clamp(position.X, area.Origin.X, Math.Max(area.Origin.X, area.Right - ActualWidth));
        Top = Math.Clamp(position.Y, area.Origin.Y, Math.Max(area.Origin.Y, area.Bottom - ActualHeight));
    }

    private System.Windows.Controls.ContextMenu BuildContextMenu()
    {
        var hide = new System.Windows.Controls.MenuItem { Header = "숨기기" };
        hide.Click += (_, _) => HideOverlay();
        var exit = new System.Windows.Controls.MenuItem { Header = "종료" };
        exit.Click += (_, _) => ExitRequested?.Invoke(this, EventArgs.Empty);
        return new System.Windows.Controls.ContextMenu { Items = { hide, exit } };
    }

    private void OnPreviewMouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (e.ChangedButton != MouseButton.Left || e.ButtonState != MouseButtonState.Pressed) return;
        var pointer = PointToScreen(e.GetPosition(this));
        var local = e.GetPosition(this);
        _dragAnchorCorrection = new(
            local.X - (ActualWidth / 2d),
            local.Y - (ActualHeight * 104d / 512d));
        _dragGesture.Begin(new(pointer.X, pointer.Y), Position);
        if (!CaptureMouse())
        {
            _dragGesture.Cancel();
            return;
        }
        e.Handled = true;
    }

    private void OnPreviewMouseMove(object sender, System.Windows.Input.MouseEventArgs e)
    {
        if (!_dragGesture.IsActive || e.LeftButton != MouseButtonState.Pressed) return;
        var pointer = PointToScreen(e.GetPosition(this));
        var dpi = VisualTreeHelper.GetDpi(this);
        var update = _dragGesture.Move(
            new(pointer.X, pointer.Y),
            dpi.DpiScaleX,
            dpi.DpiScaleY,
            SystemParameters.MinimumHorizontalDragDistance,
            SystemParameters.MinimumVerticalDragDistance);
        if (update.Result == DragGestureResult.None) return;
        if (update.Result == DragGestureResult.DragStarted)
        {
            DragStarted?.Invoke(this, EventArgs.Empty);
        }
        MoveTo(new(
            update.WindowPosition.X + _dragAnchorCorrection.X,
            update.WindowPosition.Y + _dragAnchorCorrection.Y));
        e.Handled = true;
    }

    private void OnPreviewMouseLeftButtonUp(object sender, MouseButtonEventArgs e)
    {
        if (!_dragGesture.IsActive || e.ChangedButton != MouseButton.Left) return;
        var result = _dragGesture.Complete();
        ReleasePointerCapture();
        if (result == DragGestureResult.DragCompleted) DragCompleted?.Invoke(this, EventArgs.Empty);
        else if (result == DragGestureResult.Click) ClickObserved?.Invoke(this, EventArgs.Empty);
        e.Handled = true;
    }

    private void OnLostMouseCapture(object sender, System.Windows.Input.MouseEventArgs e)
    {
        if (_releasingCapture || !_dragGesture.IsActive) return;
        if (_dragGesture.Cancel() == DragGestureResult.DragCanceled)
            DragCanceled?.Invoke(this, EventArgs.Empty);
    }

    private void CancelPointerInteraction()
    {
        if (!_dragGesture.IsActive) return;
        var result = _dragGesture.Cancel();
        ReleasePointerCapture();
        if (result == DragGestureResult.DragCanceled) DragCanceled?.Invoke(this, EventArgs.Empty);
    }

    private void ReleasePointerCapture()
    {
        if (!IsMouseCaptured) return;
        _releasingCapture = true;
        ReleaseMouseCapture();
        _releasingCapture = false;
    }

    private void OnSourceInitialized(object? sender, EventArgs e)
    {
        if (PresentationSource.FromVisual(this) is HwndSource source)
        {
            SetNoActivateStyle(source.Handle);
            source.AddHook(WndProc);
        }
        DpiScaleChanged?.Invoke(this, VisualTreeHelper.GetDpi(this).DpiScaleX);
    }

    private static void SetNoActivateStyle(IntPtr hwnd)
    {
        var style = GetWindowLongPtr(hwnd, GwlExStyle);
        var noActivateStyle = style | WsExNoActivate;
        if (style != noActivateStyle) SetWindowLongPtr(hwnd, GwlExStyle, noActivateStyle);
    }

    [DllImport("user32.dll", EntryPoint = "GetWindowLongPtrW", SetLastError = true)]
    private static extern nint GetWindowLongPtr(IntPtr hwnd, int index);

    [DllImport("user32.dll", EntryPoint = "SetWindowLongPtrW", SetLastError = true)]
    private static extern nint SetWindowLongPtr(IntPtr hwnd, int index, nint newLong);

    private IntPtr WndProc(IntPtr hwnd, int message, IntPtr wParam, IntPtr lParam, ref bool handled)
    {
        if (message == WmDpiChanged)
        {
            var dpi = unchecked((ushort)(long)wParam);
            DpiScaleChanged?.Invoke(this, dpi / 96d);
        }
        return IntPtr.Zero;
    }
}

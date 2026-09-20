using Bolttagu.Contracts;
using System.Windows;
using System.Windows.Input;
using System.Windows.Interop;
using System.Windows.Media;

namespace Bolttagu.Platform.Windows;

public sealed class OverlayWindow : Window, IOverlayWindow
{
    private const int WmDpiChanged = 0x02E0;

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
        Content = content;
        PreviewMouseLeftButtonDown += OnPreviewMouseLeftButtonDown;
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
    public event EventHandler? ExitRequested;
    public event EventHandler<double>? DpiScaleChanged;
    public void ShowOverlay() { Show(); Activate(); }
    public void HideOverlay() => Hide();
    public void CloseOverlay() => Close();

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
        if (e.ButtonState != MouseButtonState.Pressed) return;
        var startLeft = Left;
        var startTop = Top;
        try
        {
            DragMove();
            var movedX = Math.Abs(Left - startLeft);
            var movedY = Math.Abs(Top - startTop);
            if (movedX <= SystemParameters.MinimumHorizontalDragDistance &&
                movedY <= SystemParameters.MinimumVerticalDragDistance)
            {
                ClickObserved?.Invoke(this, EventArgs.Empty);
            }
        }
        catch (InvalidOperationException) { }
    }

    private void OnSourceInitialized(object? sender, EventArgs e)
    {
        if (PresentationSource.FromVisual(this) is HwndSource source) source.AddHook(WndProc);
        DpiScaleChanged?.Invoke(this, VisualTreeHelper.GetDpi(this).DpiScaleX);
    }

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

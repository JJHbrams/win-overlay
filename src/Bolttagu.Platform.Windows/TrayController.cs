using Bolttagu.Contracts;
using System.Drawing;
using Forms = System.Windows.Forms;

namespace Bolttagu.Platform.Windows;

public sealed class TrayController : ITrayController
{
    private readonly Forms.NotifyIcon _notifyIcon;
    private readonly Icon? _ownedIcon;

    public TrayController()
    {
        var menu = new Forms.ContextMenuStrip();
        menu.Items.Add("표시", null, (_, _) => ShowRequested?.Invoke(this, EventArgs.Empty));
        menu.Items.Add("숨기기", null, (_, _) => HideRequested?.Invoke(this, EventArgs.Empty));
        menu.Items.Add(new Forms.ToolStripSeparator());
        menu.Items.Add("종료", null, (_, _) => ExitRequested?.Invoke(this, EventArgs.Empty));
        _ownedIcon = LoadApplicationIcon();
        _notifyIcon = new Forms.NotifyIcon
        {
            Icon = _ownedIcon ?? SystemIcons.Application,
            Text = "Bolttagu P2",
            Visible = true,
            ContextMenuStrip = menu,
        };
        _notifyIcon.DoubleClick += (_, _) => ShowRequested?.Invoke(this, EventArgs.Empty);
    }

    public event EventHandler? ShowRequested;
    public event EventHandler? HideRequested;
    public event EventHandler? ExitRequested;
    public void SetStatus(string status) => _notifyIcon.Text = status.Length <= 63 ? status : status[..63];
    public void Dispose()
    {
        _notifyIcon.Visible = false;
        _notifyIcon.Dispose();
        _ownedIcon?.Dispose();
    }

    private static Icon? LoadApplicationIcon()
    {
        var executablePath = Environment.ProcessPath;
        if (string.IsNullOrWhiteSpace(executablePath))
        {
            return null;
        }

        try
        {
            return Icon.ExtractAssociatedIcon(executablePath);
        }
        catch (Exception)
        {
            return null;
        }
    }
}

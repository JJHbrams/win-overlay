using Bolttagu.Contracts;
using System.Drawing;
using Forms = System.Windows.Forms;

namespace Bolttagu.Platform.Windows;

public sealed class TrayController : ITrayController
{
    private readonly Forms.NotifyIcon _notifyIcon;

    public TrayController()
    {
        var menu = new Forms.ContextMenuStrip();
        menu.Items.Add("표시", null, (_, _) => ShowRequested?.Invoke(this, EventArgs.Empty));
        menu.Items.Add("숨기기", null, (_, _) => HideRequested?.Invoke(this, EventArgs.Empty));
        menu.Items.Add(new Forms.ToolStripSeparator());
        menu.Items.Add("종료", null, (_, _) => ExitRequested?.Invoke(this, EventArgs.Empty));
        _notifyIcon = new Forms.NotifyIcon
        {
            Icon = SystemIcons.Application,
            Text = "Bolttagu P0",
            Visible = true,
            ContextMenuStrip = menu,
        };
        _notifyIcon.DoubleClick += (_, _) => ShowRequested?.Invoke(this, EventArgs.Empty);
    }

    public event EventHandler? ShowRequested;
    public event EventHandler? HideRequested;
    public event EventHandler? ExitRequested;
    public void SetStatus(string status) => _notifyIcon.Text = status.Length <= 63 ? status : status[..63];
    public void Dispose() { _notifyIcon.Visible = false; _notifyIcon.Dispose(); }
}


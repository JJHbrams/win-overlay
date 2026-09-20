using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Animation;
using System.Windows.Shapes;

namespace Bolttagu.Presentation;

public sealed class PetPlaceholderView : UserControl
{
    private readonly ScaleTransform _scale = new(1, 1);
    private readonly TextBlock _diagnosticText;

    public PetPlaceholderView()
    {
        Width = 220;
        Height = 220;
        RenderTransformOrigin = new Point(0.5, 0.82);
        RenderTransform = _scale;
        var canvas = new Canvas { Width = 220, Height = 220, Background = Brushes.Transparent };
        canvas.Children.Add(CreateEar(42, 34, -18));
        canvas.Children.Add(CreateEar(138, 34, 18));
        var head = new Ellipse
        {
            Width = 176,
            Height = 160,
            Stroke = new SolidColorBrush(Color.FromRgb(48, 35, 62)),
            StrokeThickness = 7,
            Fill = new RadialGradientBrush(Color.FromRgb(255, 225, 226), Color.FromRgb(236, 168, 192)),
        };
        Canvas.SetLeft(head, 22);
        Canvas.SetTop(head, 42);
        canvas.Children.Add(head);
        canvas.Children.Add(CreateEye(66, 94));
        canvas.Children.Add(CreateEye(128, 94));
        var mouth = new TextBlock
        {
            Text = "ω",
            FontSize = 34,
            FontWeight = FontWeights.Bold,
            Foreground = new SolidColorBrush(Color.FromRgb(58, 38, 67)),
        };
        Canvas.SetLeft(mouth, 90);
        Canvas.SetTop(mouth, 124);
        canvas.Children.Add(mouth);
        var halo = new Ellipse
        {
            Width = 100,
            Height = 30,
            Stroke = new SolidColorBrush(Color.FromRgb(220, 94, 234)),
            StrokeThickness = 7,
            Fill = Brushes.Transparent,
        };
        Canvas.SetLeft(halo, 60);
        Canvas.SetTop(halo, 16);
        canvas.Children.Add(halo);
        _diagnosticText = new TextBlock
        {
            Text = "P0 · 100% DPI",
            FontSize = 12,
            Foreground = Brushes.White,
            Background = new SolidColorBrush(Color.FromArgb(150, 30, 22, 38)),
            Padding = new Thickness(6, 2, 6, 2),
        };
        Canvas.SetLeft(_diagnosticText, 65);
        Canvas.SetTop(_diagnosticText, 194);
        canvas.Children.Add(_diagnosticText);
        Content = canvas;
    }

    public void ReactToClick()
    {
        var animation = new DoubleAnimation
        {
            From = 1,
            To = 0.86,
            Duration = TimeSpan.FromMilliseconds(90),
            AutoReverse = true,
            EasingFunction = new QuadraticEase(),
        };
        _scale.BeginAnimation(ScaleTransform.ScaleXProperty, animation);
        _scale.BeginAnimation(ScaleTransform.ScaleYProperty, animation);
    }

    public void SetDpiScale(double scale) => _diagnosticText.Text = $"P0 · {scale:P0} DPI";

    private static Polygon CreateEar(double left, double top, double angle)
    {
        var ear = new Polygon
        {
            Points = [new Point(0, 52), new Point(28, 0), new Point(56, 52)],
            Fill = new SolidColorBrush(Color.FromRgb(91, 63, 112)),
            Stroke = new SolidColorBrush(Color.FromRgb(48, 35, 62)),
            StrokeThickness = 7,
            RenderTransformOrigin = new Point(0.5, 0.8),
            RenderTransform = new RotateTransform(angle),
        };
        Canvas.SetLeft(ear, left);
        Canvas.SetTop(ear, top);
        return ear;
    }

    private static Ellipse CreateEye(double left, double top)
    {
        var eye = new Ellipse { Width = 25, Height = 38, Fill = new SolidColorBrush(Color.FromRgb(48, 35, 62)) };
        Canvas.SetLeft(eye, left);
        Canvas.SetTop(eye, top);
        return eye;
    }
}


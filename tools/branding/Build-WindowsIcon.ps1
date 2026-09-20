[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $InputPng,

    [Parameter(Mandatory)]
    [string] $OutputIco,

    [int[]] $Sizes = @(16, 24, 32, 48, 64, 128, 256)
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName WindowsBase

$inputPath = (Resolve-Path -LiteralPath $InputPng).Path
$outputPath = [System.IO.Path]::GetFullPath($OutputIco)
$outputDirectory = [System.IO.Path]::GetDirectoryName($outputPath)
[System.IO.Directory]::CreateDirectory($outputDirectory) | Out-Null

$source = [System.Windows.Media.Imaging.BitmapImage]::new()
$source.BeginInit()
$source.CacheOption = [System.Windows.Media.Imaging.BitmapCacheOption]::OnLoad
$source.UriSource = [Uri]::new($inputPath)
$source.EndInit()
$source.Freeze()

$frames = foreach ($size in ($Sizes | Sort-Object -Unique)) {
    if ($size -lt 16 -or $size -gt 256) {
        throw "ICO size must be between 16 and 256 pixels: $size"
    }

    $visual = [System.Windows.Media.DrawingVisual]::new()
    $context = $visual.RenderOpen()
    $context.DrawImage($source, [System.Windows.Rect]::new(0, 0, $size, $size))
    $context.Close()

    $bitmap = [System.Windows.Media.Imaging.RenderTargetBitmap]::new(
        $size, $size, 96, 96, [System.Windows.Media.PixelFormats]::Pbgra32)
    $bitmap.Render($visual)
    $encoder = [System.Windows.Media.Imaging.PngBitmapEncoder]::new()
    $encoder.Frames.Add([System.Windows.Media.Imaging.BitmapFrame]::Create($bitmap))
    $stream = [System.IO.MemoryStream]::new()
    $encoder.Save($stream)
    [pscustomobject]@{ Size = $size; Bytes = $stream.ToArray() }
    $stream.Dispose()
}

$output = [System.IO.File]::Open($outputPath, [System.IO.FileMode]::Create)
$writer = [System.IO.BinaryWriter]::new($output)
try {
    $writer.Write([uint16]0)
    $writer.Write([uint16]1)
    $writer.Write([uint16]$frames.Count)
    $offset = 6 + (16 * $frames.Count)
    foreach ($frame in $frames) {
        $dimension = if ($frame.Size -eq 256) { 0 } else { $frame.Size }
        $writer.Write([byte]$dimension)
        $writer.Write([byte]$dimension)
        $writer.Write([byte]0)
        $writer.Write([byte]0)
        $writer.Write([uint16]1)
        $writer.Write([uint16]32)
        $writer.Write([uint32]$frame.Bytes.Length)
        $writer.Write([uint32]$offset)
        $offset += $frame.Bytes.Length
    }
    foreach ($frame in $frames) {
        $writer.Write([byte[]]$frame.Bytes)
    }
}
finally {
    $writer.Dispose()
    $output.Dispose()
}

Write-Host "Created $outputPath with $($frames.Count) PNG-compressed icon sizes."

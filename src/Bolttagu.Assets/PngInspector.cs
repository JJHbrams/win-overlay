using System.Buffers.Binary;

namespace Bolttagu.Assets;

public static class PngInspector
{
    private static readonly byte[] Signature = [137, 80, 78, 71, 13, 10, 26, 10];

    public static PngMetadata Read(string path)
    {
        using var stream = File.OpenRead(path);
        Span<byte> header = stackalloc byte[33];
        if (stream.Read(header) != header.Length || !header[..8].SequenceEqual(Signature))
        {
            throw new InvalidDataException("File is not a valid PNG header.");
        }
        if (!header.Slice(12, 4).SequenceEqual("IHDR"u8))
        {
            throw new InvalidDataException("PNG does not begin with IHDR.");
        }

        return new(
            BinaryPrimitives.ReadInt32BigEndian(header.Slice(16, 4)),
            BinaryPrimitives.ReadInt32BigEndian(header.Slice(20, 4)),
            header[24],
            header[25]);
    }
}

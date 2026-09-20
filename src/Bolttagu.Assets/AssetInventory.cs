using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Bolttagu.Assets;

public sealed record AssetInventory(
    int SchemaVersion,
    AssetSource Source,
    string Usage,
    IReadOnlyList<InventoryEntry> Files);

public sealed record AssetSource(string Name, string Revision);

public sealed record InventoryEntry(
    string SourcePath,
    string TargetPath,
    long Bytes,
    string Sha256);

public sealed record VerificationIssue(string Path, string Message);

public static class AssetInventoryVerifier
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        Converters = { new JsonStringEnumConverter() }
    };

    public static AssetInventory Load(string inventoryPath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(inventoryPath);
        var json = File.ReadAllText(inventoryPath);
        return JsonSerializer.Deserialize<AssetInventory>(json, JsonOptions)
            ?? throw new InvalidDataException("Inventory JSON is empty.");
    }

    public static IReadOnlyList<VerificationIssue> Verify(string repositoryRoot, AssetInventory inventory)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(repositoryRoot);
        ArgumentNullException.ThrowIfNull(inventory);

        var root = Path.GetFullPath(repositoryRoot);
        var issues = new List<VerificationIssue>();

        if (inventory.SchemaVersion != 1)
        {
            issues.Add(new("inventory.json", $"Unsupported schema version {inventory.SchemaVersion}."));
        }

        foreach (var entry in inventory.Files.OrderBy(file => file.TargetPath, StringComparer.Ordinal))
        {
            string path;
            try
            {
                path = ResolveContainedPath(root, entry.TargetPath);
            }
            catch (InvalidDataException exception)
            {
                issues.Add(new(entry.TargetPath, exception.Message));
                continue;
            }

            if (!File.Exists(path))
            {
                issues.Add(new(entry.TargetPath, "File is missing."));
                continue;
            }

            var info = new FileInfo(path);
            if (info.Length != entry.Bytes)
            {
                issues.Add(new(entry.TargetPath, $"Expected {entry.Bytes} bytes, got {info.Length}."));
            }

            using var stream = File.OpenRead(path);
            var actualHash = Convert.ToHexString(SHA256.HashData(stream));
            if (!actualHash.Equals(entry.Sha256, StringComparison.OrdinalIgnoreCase))
            {
                issues.Add(new(entry.TargetPath, $"SHA-256 mismatch: {actualHash}."));
            }
        }

        return issues;
    }

    internal static string ResolveContainedPath(string root, string relativePath)
    {
        if (Path.IsPathRooted(relativePath))
        {
            throw new InvalidDataException("Paths must be repository-relative.");
        }

        var normalizedRoot = Path.GetFullPath(root).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        var candidate = Path.GetFullPath(Path.Combine(normalizedRoot, relativePath.Replace('/', Path.DirectorySeparatorChar)));
        if (!candidate.StartsWith(normalizedRoot, StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidDataException("Path escapes the repository root.");
        }

        return candidate;
    }
}

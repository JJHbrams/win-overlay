using System.IO;
using System.Xml.Linq;

namespace Bolttagu.Architecture.Tests;

[TestClass]
public sealed class DependencyRulesTests
{
    private static readonly IReadOnlyDictionary<string, string[]> AllowedDependencies =
        new Dictionary<string, string[]>(StringComparer.Ordinal)
        {
            ["Bolttagu.Contracts"] = [],
            ["Bolttagu.Core"] = ["Bolttagu.Contracts"],
            ["Bolttagu.Runtime"] = ["Bolttagu.Contracts", "Bolttagu.Core"],
            ["Bolttagu.Assets"] = ["Bolttagu.Contracts"],
            ["Bolttagu.Presentation"] = ["Bolttagu.Contracts"],
            ["Bolttagu.Platform.Windows"] = ["Bolttagu.Contracts"],
            ["Bolttagu.Diagnostics"] = ["Bolttagu.Contracts"],
            ["Bolttagu.App"] =
            [
                "Bolttagu.Assets",
                "Bolttagu.Contracts",
                "Bolttagu.Diagnostics",
                "Bolttagu.Platform.Windows",
                "Bolttagu.Presentation",
                "Bolttagu.Runtime",
            ],
        };

    [TestMethod]
    public void SourceProjects_OnlyUseApprovedProjectReferences()
    {
        var repository = FindRepositoryRoot();
        var violations = new List<string>();

        foreach (var projectPath in Directory.EnumerateFiles(
                     Path.Combine(repository, "src"),
                     "*.csproj",
                     SearchOption.AllDirectories))
        {
            var projectName = Path.GetFileNameWithoutExtension(projectPath);
            Assert.IsTrue(AllowedDependencies.TryGetValue(projectName, out var allowed),
                $"Add an explicit dependency policy for {projectName}.");

            var document = XDocument.Load(projectPath);
            var references = document.Descendants("ProjectReference")
                .Select(element => element.Attribute("Include")?.Value)
                .Where(value => !string.IsNullOrWhiteSpace(value))
                .Select(value => Path.GetFileNameWithoutExtension(value!))
                .OrderBy(value => value, StringComparer.Ordinal)
                .ToArray();

            foreach (var reference in references.Except(allowed!, StringComparer.Ordinal))
            {
                violations.Add($"{projectName} -> {reference}");
            }
        }

        Assert.IsEmpty(violations,
            $"Forbidden project references:{Environment.NewLine}{string.Join(Environment.NewLine, violations)}");
    }

    [TestMethod]
    public void CoreProject_RemainsPlatformNeutral()
    {
        var repository = FindRepositoryRoot();
        var projectPath = Path.Combine(repository, "src", "Bolttagu.Core", "Bolttagu.Core.csproj");
        var project = File.ReadAllText(projectPath);

        Assert.IsFalse(project.Contains("-windows", StringComparison.OrdinalIgnoreCase));
        Assert.IsFalse(project.Contains("UseWPF", StringComparison.OrdinalIgnoreCase));
        Assert.IsFalse(project.Contains("UseWindowsForms", StringComparison.OrdinalIgnoreCase));
        Assert.IsFalse(project.Contains("PackageReference", StringComparison.OrdinalIgnoreCase));
    }

    private static string FindRepositoryRoot()
    {
        var current = new DirectoryInfo(AppContext.BaseDirectory);
        while (current is not null)
        {
            if (File.Exists(Path.Combine(current.FullName, "Bolttagu.slnx")))
            {
                return current.FullName;
            }

            current = current.Parent;
        }

        throw new DirectoryNotFoundException("Could not locate the repository root from the test output.");
    }
}

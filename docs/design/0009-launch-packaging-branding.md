# 0009 — Launch, packaging, and branding

> Status: implemented

## Intent

Provide two dependable Windows entry points without requiring administrator privileges:

- `Run-Bolttagu.ps1` starts a Debug build from a checkout using the repository-local SDK.
- `scripts/Publish-WinX64.ps1` produces a distributable, self-contained, single-file `Bolttagu.exe`.

## Delivery contract

| Concern | Contract |
| --- | --- |
| SDK | Both scripts use `.dotnet\\dotnet.exe`; if absent, they call `scripts/bootstrap.ps1`. They do not modify PATH or require elevation. |
| Local launch | Restore, deterministic art build, and Debug build complete before `Bolttagu.exe` is started. Errors name the failed stage and exit non-zero. |
| Publish | Default output is cleaned before publish, then `artifacts/publish/win-x64/Bolttagu.exe` is generated for `win-x64`, self-contained and single-file. `-KeepExistingOutput` is an explicit escape hatch. |
| Art | The publish script regenerates the deterministic art pack unless `-SkipAssetBuild` is explicitly requested. |
| Icon | When `asset/bolttagu/derived/branding/bolttagu.ico` is present, `Bolttagu.App.csproj` embeds it as the Windows application icon. |
| CI | CI invokes the publish script and uploads the publish directory as `Bolttagu-win-x64`. |

## Operator commands

```powershell
.\Run-Bolttagu.ps1
.\scripts\Publish-WinX64.ps1
```

The generated `artifacts/` directory is intentionally ignored by Git.

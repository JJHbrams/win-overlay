---
id: 0009-launch-packaging-branding
title: 실행 패키징과 브랜딩
tier: S
status: done
issue:
owner: antio
created: 2026-09-21
---

# 실행 패키징과 브랜딩

> tier **S** — 작음 — 의도·수용기준·확정사실·변경지점·착수순서

## 1. 의도 (Intent)

| 항목 | 내용 |
|---|---|
| 문제 | 개발 명령을 모르는 사용자에게 즉시 실행할 진입점이 없고, 배포 가능한 EXE와 일관된 앱 아이콘·README 첫인상도 없다. |
| 왜 지금 | 기본 상호작용과 애니메이션이 동작하므로 소스 체크아웃과 CI에서 동일하게 재현되는 실행·배포 경로가 필요하다. |
| 주 사용자 | Windows에서 볼따구를 바로 실행하려는 사용자와 배포물을 만드는 유지보수자. |
| 불변식 | 관리자 권한이나 시스템 PATH 변경을 요구하지 않는다. 아트 빌드는 기존 결정적 파이프라인을 사용한다. 대형 EXE는 Git에 커밋하지 않는다. |
| 비목표 | 설치 프로그램, 코드 서명, 자동 업데이트, 다른 CPU·운영체제용 패키지는 이번 범위에 포함하지 않는다. |

## 2. 수용 기준 (Acceptance)

| ID | 수용 기준 | 검증 방법 |
|---|---|---|
| AC-1 | 루트의 `Run-Bolttagu.ps1`가 저장소 로컬 SDK를 준비하고 restore·아트 빌드·Debug 빌드 후 앱을 시작한다. | 스크립트 실행 후 프로세스가 살아 있는지 확인하고 종료한다. |
| AC-2 | `scripts/Publish-WinX64.ps1`가 self-contained 단일 파일 `artifacts/publish/win-x64/Bolttagu.exe`를 만든다. | 스크립트 종료 코드, 파일 존재·크기, 독립 프로세스 기동을 확인한다. |
| AC-3 | 다중 해상도 Windows 아이콘이 EXE와 트레이에 적용되고 README에 배너·즉시 실행·배포 명령이 표시된다. | ICO 엔트리 검사, EXE 연관 아이콘 추출, README 경로·명령 검토로 확인한다. |
| AC-4 | CI가 빌드·테스트·publish를 수행하고 `Bolttagu-win-x64` artifact를 업로드하며 생성물은 Git에서 제외된다. | workflow와 `.gitignore`를 검사하고 GitHub Actions 실행 결과를 확인한다. |

## 3. 확정 사실 (Findings)

| 항목 | 확인된 사실 | 설계 반영 |
|---|---|---|
| SDK | `global.json`은 .NET SDK 10.0.401을 고정하고 `scripts/bootstrap.ps1`가 `.dotnet/`에 설치한다. | 두 진입 스크립트 모두 같은 로컬 SDK와 bootstrap을 재사용한다. |
| 앱 | WPF 앱의 출력은 `WinExe`이고 기존 빌드는 `Bolttagu.App.exe` 이름을 사용했다. | assembly 이름을 `Bolttagu`로 고정해 실행·배포 파일명을 단순화한다. |
| 자산 | 앱은 `asset/bolttagu/build`와 upstream fallback을 content로 포함한다. | 실행·publish 전에 기본적으로 결정적 아트 빌드를 수행한다. |
| 브랜딩 | README용 3:1 배너와 투명 정사각 아이콘 원본을 만들었고 ICO는 16~256px의 7개 크기를 포함한다. | 아이콘은 프로젝트의 `ApplicationIcon`과 실행 중 tray icon 양쪽에서 사용한다. |

## 9. 변경 지점

| 파일 | 변경 |
|---|---|
| `Run-Bolttagu.ps1` | 저장소 로컬 SDK 기반 원클릭 실행 진입점을 제공한다. |
| `scripts/Publish-WinX64.ps1` | Windows x64 self-contained 단일 EXE를 생성한다. |
| `src/Bolttagu.App/Bolttagu.App.csproj` | 출력 이름과 Windows application icon을 등록한다. |
| `src/Bolttagu.Platform.Windows/TrayController.cs` | 실행 파일에 임베드된 아이콘을 tray icon으로 사용한다. |
| `asset/bolttagu/derived/branding/readme-banner.png` | README 상단 배너를 제공한다. |
| `asset/bolttagu/derived/branding/bolttagu-icon-master.png` | 아이콘 파생의 투명 원본을 제공한다. |
| `asset/bolttagu/derived/branding/bolttagu.ico` | EXE에 임베드할 다중 해상도 Windows 아이콘을 제공한다. |
| `tools/branding/Build-WindowsIcon.ps1` | 아이콘 원본에서 ICO를 재생성한다. |
| `README.md` | 바로 실행, EXE 생성, 배포 주의사항과 배너를 안내한다. |
| `.github/workflows/ci.yml` | publish를 실행하고 Windows artifact를 업로드한다. |
| `.gitignore` | 생성된 `artifacts/`를 제외한다. |

## 10. 잠재 문제 & 대응

| 문제 | 대응 |
|---|---|
| self-contained 단일 EXE의 용량이 크다. | Git에는 넣지 않고 CI artifact 또는 GitHub Release로 배포한다. |
| 코드 서명이 없어 SmartScreen 경고가 발생할 수 있다. | README에 명시하고 정식 배포 단계에서 인증서 기반 서명을 별도 도입한다. |
| 그래픽 UI의 장기 동작은 자동 smoke test만으로 완전히 보증되지 않는다. | 프로세스 기동을 자동 확인하고 실제 상호작용은 기존 런타임·아키텍처 테스트와 수동 QA로 보완한다. |

## 11. 착수 순서

- [x] 1. 로컬 SDK를 재사용하는 실행·publish 스크립트를 추가하고 실제 프로세스 기동을 확인한다. (AC-1, AC-2)
- [x] 2. 배너와 다중 해상도 아이콘을 만들고 EXE·tray·README에 연결한다. (AC-3)
- [x] 3. CI artifact 업로드와 생성물 ignore 규칙을 추가하고 원격 Actions에서 확인한다. (AC-4)

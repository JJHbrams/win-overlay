# ADR-0001: Windows 런타임 스택

- 상태: Accepted
- 날짜: 2026-09-20

## 결정

지원되는 LTS .NET 10 SDK와 WPF를 기본 Windows 런타임으로 사용한다. SDK는 시스템 전역이
아니라 저장소의 `.dotnet/`에 설치하고 `global.json`으로 10.0.401을 고정한다.

Presentation과 Platform.Windows는 WPF/Win32를 사용할 수 있지만 Core, Runtime,
Contracts, Assets, Diagnostics에는 WPF 타입을 노출하지 않는다.

## 근거

- 대상 제품은 Windows 전용 투명 topmost 오버레이, 포인터 캡처, per-monitor DPI와 트레이가 필요하다.
- 현재 PC에는 Desktop Runtime 6~9가 있으나 SDK는 없었다. 공식 비관리자 설치 스크립트로
  .NET 10.0.401 SDK를 프로젝트 로컬에 설치했다. (직접 측정, 2026-09-20)
- Python 3.12와 tkinter는 설치되어 있으나 typed project boundary와 Windows lifecycle 검증을
  우선해 WPF를 기본 후보로 선택했다. (직접 측정, 2026-09-20)

## P0 검증 항목

- 투명하고 borderless인 topmost 창
- 마우스 drag와 click 반응
- PerMonitorV2 manifest와 DPI 변경 관측
- 트레이 show/hide/exit
- framework-dependent `win-x64` publish
- architecture dependency test

## 제약과 후속 결정

`AllowsTransparency=true`는 WPF의 layered window 경로를 사용한다. P0/P2 성능 측정에서
목표를 만족하지 못할 때만 Presentation adapter에 Skia 등 다른 renderer를 검토한다.
Core와 Runtime 계약은 교체하지 않는다.

## 검증 결과

- Release solution build: 경고 0, 오류 0
- architecture·WPF HWND·tray smoke test: 4/4 통과
- self-contained win-x64 publish 성공
- publish 실행 파일 SHA-256: `CD129A71629B5F638EB853B497633E4F202C08921F00E61F0A2CBAB26C065B32`
- 실제 publish 프로세스가 2초 후 응답 상태를 유지했고 working set은 138.5MB였으며,
  종료 후 잔류 프로세스는 0개였다. (직접 측정, 2026-09-20)

현재 자동화 환경은 네이티브 창 inventory를 노출하지 않아 사람 눈으로 보는 투명도·드래그 체감은
P2 수직 슬라이스의 사용자 확인 항목으로 유지한다. WPF smoke test에서는 실제 HWND 생성과
`AllowsTransparency`, `Topmost`, `ShowInTaskbar` 속성을 검증했다.

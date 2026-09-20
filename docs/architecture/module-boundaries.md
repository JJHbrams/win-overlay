# Module Boundaries

프로젝트 참조는 아래 방향만 허용한다. `Bolttagu.Architecture.Tests`가 실제 `.csproj`
참조를 검사하며 새 프로젝트는 먼저 정책에 등록해야 한다.

| 프로젝트 | 허용 참조 |
|---|---|
| `Bolttagu.Contracts` | 없음 |
| `Bolttagu.Core` | Contracts |
| `Bolttagu.Runtime` | Contracts, Core |
| `Bolttagu.Assets` | Contracts |
| `Bolttagu.Presentation` | Contracts |
| `Bolttagu.Platform.Windows` | Contracts |
| `Bolttagu.Diagnostics` | Contracts |
| `Bolttagu.App` | 모든 구현 모듈을 조립할 수 있음 |

Core는 `net10.0`을 유지하며 Windows target, WPF, WinForms, 외부 package reference를
가질 수 없다. UI와 OS 객체를 다른 모듈로 전달할 때는 Contracts의 값 타입과 port만 사용한다.


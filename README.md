# Bolttagu Desktop Pet

독립 실행되는 Windows용 볼따구 데스크톱 펫이다. Engram은 필수 구성 요소가 아니며,
현재 P0에서는 투명 창·드래그·DPI·트레이와 모듈 경계를 검증한다.

## 개발 환경

프로젝트 전용 .NET 10 LTS SDK를 `.dotnet/`에 설치한다. 저장소는 `global.json`으로
SDK 10.0.401을 고정한다.

```powershell
& .\scripts\bootstrap.ps1
$dotnetExe = Join-Path $PWD '.dotnet\dotnet.exe'
& $dotnetExe restore Bolttagu.slnx
& $dotnetExe build Bolttagu.slnx --no-restore
& $dotnetExe test Bolttagu.slnx --no-build
& $dotnetExe run --project src\Bolttagu.App\Bolttagu.App.csproj
```

## P0 조작

- 왼쪽 버튼으로 캐릭터 창을 드래그한다.
- 클릭을 놓으면 squash 반응이 재생된다.
- 오른쪽 메뉴 또는 트레이에서 숨김·표시·종료를 선택한다.
- 캐릭터 아래의 표시는 현재 WPF DPI scale이다.

## 아트 파이프라인

Engram에서 가져온 원본은 `asset/bolttagu/upstream` 아래의 불변 snapshot이며 앱은 Engram
설치 경로를 읽지 않는다. P1 preview frame과 atlas를 다시 만들려면 다음을 실행한다.

```powershell
.\.dotnet\dotnet.exe run --project .\tools\Bolttagu.AssetBuild -- all
```

세부 규칙과 라이선스 주의사항은 `asset/bolttagu/README.md`를 참고한다.

## 설계 정본

- `docs/design/0001-bolttagu-art-pack.md`
- `docs/design/0002-desktop-pet-architecture.md`
- `docs/design/0003-desktop-pet-implementation-roadmap.md`

---
id: 0001-bolttagu-art-pack
title: 볼따구 아트팩 기반
tier: S
status: done
issue: 
owner: antio
created: 2026-09-20
---

# 볼따구 아트팩 기반

> tier **S** — 작음 — 의도·수용기준·확정사실·변경지점·착수순서
> 채우는 순서: §1 의도 → §2 수용기준 → §3 확정사실(조사) → 다이어그램 → §9 변경지점 → §11 착수순서

## 1. 의도 (Intent)

| 항목 | 내용 |
|---|---|
| 문제 | 독립형 볼따구 데스크톱 펫을 만들 새 프로젝트에 애니메이션 기준본과 파생 작업 영역이 없어, 원본 훼손 없이 아트를 확장할 수 없다. |
| 왜 지금 | 데스크톱 펫의 이동·반응·상호작용을 구현하기 전에 안정적인 캐릭터 아트 기준과 파일 계약이 필요하다. |
| 주 사용자 | 볼따구의 새 포즈·동작·효과를 제작하고 독립형 데스크톱 펫 앱에서 소비하려는 이 프로젝트의 개발자 겸 아트 작업자. |
| 불변식 | 가져오는 Engram 원본 파일은 수정하지 않는다. 복사본의 SHA-256을 기록한다. 파생 아트는 기준본과 별도 디렉터리에 둔다. 앱은 Engram 설치나 실행 여부에 의존하지 않는다. |
| 비목표 | 이번 슬라이스에서는 데스크톱 펫 런타임, 자유 보행, 클릭·드래그 상호작용, Engram 연동, 신규 생성형 아트 제작을 구현하지 않는다. |

## 2. 수용 기준 (Acceptance)

| ID | 수용 기준 | 검증 방법 |
|---|---|---|
| AC-1 | Engram 기본 캐릭터, 24셀 상태 시트, idle/click 효과, 상태·세트 manifest가 `asset/bolttagu/upstream/engram` 아래에 복사되고 원본과 SHA-256이 일치한다. | PowerShell `Get-FileHash -Algorithm SHA256`로 원본과 복사본을 쌍별 비교한다. |
| AC-2 | 기준본과 분리된 `asset/bolttagu/derived` 구조 및 명명·캔버스·투명도·원본 불변 규칙이 문서화된다. | 디렉터리 존재 여부와 `asset/bolttagu/README.md`의 필수 규칙을 수동 검사한다. |
| AC-3 | 복사 자산의 출처, 원본 상대 경로, 크기, SHA-256이 기계 판독 가능한 inventory에 기록된다. | `asset/bolttagu/inventory.json`을 JSON 파싱하고 실제 파일의 크기·해시와 비교한다. |

## 3. 확정 사실 (Findings)

설계 전에 **실제로 확인한 것만** 적는다. 추측은 §10 으로 보낸다.

| 항목 | 확인된 사실 | 설계 반영 |
|---|---|---|
| 대상 저장소 | `win-overlay`는 .NET 10/WPF solution과 모듈 경계를 갖춘 Git 저장소이며 P1 작업은 `feat/p1-asset-pipeline` 브랜치에서 수행한다. `git status`, `Bolttagu.slnx`, 프로젝트 참조를 확인했다. | 자산은 코드와 분리된 `asset/bolttagu`를 루트로 사용하고 compiler만 `Bolttagu.Assets`를 참조한다. |
| 기본 캐릭터 | 원본 `engram.png`는 606×606, 32bpp ARGB이며 SHA-256은 `83C950A36F8A7DAD8FDE944F6FE19A1E4104140189B273F18E138C427121EA3A`다. | `upstream/engram/character.png`로 이름을 정규화하고 inventory에 원래 경로를 보존한다. |
| 상태 시트 | `reactions/engram/states.png`는 2604×1632, 32bpp ARGB이고 6열×4행, 셀 434×408, 상단 crop 32px 규약을 manifest가 선언한다. SHA-256은 `D80C3522B40B3F095CF80BD15925DE1C7B1B45074682178A4BF93B8D43CF82D8`다. | 시트와 원본 manifest를 함께 복사해 프레임 의미와 crop 정보를 잃지 않는다. |
| 효과 자산 | idle/click 효과는 각각 1254×1254, 24bpp RGB이며 세트 manifest가 상대 경로와 thickness를 선언한다. | 효과 파일과 세트 manifest를 같은 상대 구조로 보존한다. |
| 제품 경계 | 사용자가 지정한 목표는 Engram 외장 오버레이가 아니라 영상의 「데스크탑 버터」와 유사한 독립형 데스크톱 펫이며, Engram은 초기 볼따구 애니메이션 에셋의 출처일 뿐이다. | 모든 자산을 이 프로젝트가 독립 소유하도록 복사하고 현재 설계에서 Engram API·설정·런타임을 제외한다. |

## 9. 변경 지점

경로는 백틱으로. 새로 만드는 파일은 `(신규)` 를 붙인다 — `check` 가 실존 여부를 본다.

| 파일 | 변경 |
|---|---|
| `asset/bolttagu/README.md` | 기준본 불변 규칙, 파생 아트 배치·명명 규약, 독립형 데스크톱 펫용 후속 제작 가이드를 기록한다. |
| `asset/bolttagu/inventory.json` | 출처, 원본 상대 경로, 대상 경로, 크기, SHA-256을 기록한다. |
| `asset/bolttagu/upstream/engram/character.png` | Engram 기본 볼따구 기준 이미지를 복사한다. |
| `asset/bolttagu/upstream/engram/reactions/manifest.yaml` | 상태·프레임 매핑 기준 manifest를 복사한다. |
| `asset/bolttagu/upstream/engram/reactions/states.png` | 24셀 상태 시트를 복사한다. |
| `asset/bolttagu/upstream/engram/set/manifest.yaml` | 기본 세트와 효과 경로 manifest를 복사한다. |
| `asset/bolttagu/upstream/engram/set/effects/idle.png` | idle 효과 기준본을 복사한다. |
| `asset/bolttagu/upstream/engram/set/effects/click.png` | click 효과 기준본을 복사한다. |
| `asset/bolttagu/derived/` | 파생 아트 전용 작업 영역을 생성한다. |

## 10. 잠재 문제 & 대응

| 문제 | 대응 |
|---|---|
| 원본 아트의 재배포 가능 범위가 저장소 안에서 명시적으로 확인되지 않았다. | 현 단계에서는 개인 로컬 프로젝트의 기준본으로만 취급하고, 공개 배포 전 권리·라이선스를 별도로 확인한다. |
| 원본 상태 시트에 chroma key와 alpha가 혼재할 수 있다. | 첫 파생 작업 전에 셀별 배경·경계 픽셀을 시각 검사하고, 기준본은 수정하지 않은 채 derived에서 정규화한다. |
| 후속 데스크톱 펫 런타임이 다른 manifest 형식을 요구할 수 있다. | 이번 inventory와 upstream 구조는 보존하고, 앱 전용 manifest는 derived 또는 별도 runtime 디렉터리에 생성한다. |

## 11. 착수 순서

각 항목에 담당 AC 를 적는다. `check` 가 고아 AC 를 잡아낸다.

- [x] 1. 지정한 Engram 기준 자산 6개를 원본 변경 없이 복사하고 해시를 대조한다. (AC-1)
- [x] 2. inventory를 작성하고 실제 파일 메타데이터와 검증한다. (AC-3)
- [x] 3. derived 작업 영역과 아트 확장 규칙을 작성한다. (AC-2)

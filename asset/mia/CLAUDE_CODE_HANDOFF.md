# Mia → Claude Code 인계

작성: 2026-11-04, Asia/Seoul. 사용자가 제작을 Claude Code로 인계하도록 요청하여 Codex의 제작·조사 에이전트를 중단했다. Blender는 종료하지 않았다. **이 문서는 인계 시점의 사실이며 모델 완성 보고가 아니다.**

최종 목적은 로컬 PC의 Engram 캐릭터 Mia를 독자적인 원화의 인상으로 모델링하고, 분리 가능한 헤어·의상·소품과 표정/동작 리깅을 거쳐 현재 이벤트에 매칭되는 애니메이션 sprite를 Blender에서 출력하는 것이다. 등신대 anime/cartoon 스타일이며 예시 캐릭터를 복제하는 작업이 아니다. 원화의 지친 눈매·메이크업·풍성한 웨이브/반묶음/브레이드, 현대적인 의상과 색감을 지켜야 한다.

최종 동작에는 공통 idle calibration, 캐릭터 크기/발바닥 anchor/카메라 일관성, 클립 전환·반복 이음새·프리롤/베이크 재현성과 약30fps 출력이 필요하다. 현재는 그 이전의 본체/헤어 기본 조형부터 미결이다. 물리를 모든 파트에 도입하거나 최종 모션부터 만드는 단계가 아니다.

## 1. 가장 먼저 확인할 현재 상태

작업 루트는 아래 경로다. 이 문서의 상대 경로는 모두 이 루트 기준이다.

```text
C:/Users/antio/.codex/worktrees/mia-current/win-overlay
```

- 현재 브랜치: `codex/mia-rib-arm01`. 인계 전 기준 HEAD는 `e1f6260d574d25805f736f89b3a9d4534b6e90c6`이며, 인계 문서/기존 진행 변경을 별도 커밋한다.
- 원격: `https://github.com/JJHbrams/win-overlay.git`. 이전부터 사용자가 커밋·푸시를 승인했다. 제작 브랜치 원격 목적지는 `codex/mia-v003-fit`이다. 다른 worktree에 체크아웃된 동명 로컬 브랜치를 바꾸지 않는다.
- Codex UI에 남은 `mia-reference-recovery/win-overlay`는 현재 제작 루트가 아니다. D 드라이브도 현재 제작 경로가 아니다.
- 실제 live body: `MIA_Review12_H_LiveRepair`, **137,341 정점 / 274,324 삼각형**, 단위 행렬, modifier 0, Shape Key 없음, parent 없음. 현재 바디에는 기존 리그가 연결되어 있지 않다.
- live body 좌표 SHA-256: `ba6537406312273401ad22367e34ba8226979ffb980babe5fd95a0c6f59ed829`.
- **최신 갈비 후보와 A/T 포즈는 한 번도 적용하지 않았다.** 갈비 선택 표시만 확인한 뒤 제거했다. 팔 시험 코드는 실행 전 결함이 발견되어 미설치 상태다.
- 인계 직전 MCP 조회에서 기존 21개 감시 actor가 수정 전과 동일함을 확인했다. pending scoped edit 없음, `MIA_ARMPOSE01` namespace 없음, 임시 선택/팔 진단 actor 없음.
- 실제 조회: `.mia-cache/body-h/live/rib01/handoff-probe.json` 및 `handoff-probe-call.json`. tuple/list를 JSON으로 정규화해 비교한 최종 성공 기록을 사용한다.
- 작은 증거 사본 `asset/mia/handoff/20261104/live-state.json`, `rib01.unapplied-forecast.json`, `arm-pose01.rejected-forecast.json`과 코드 스냅샷은 Git에도 보존한다. 큰 native/NPZ/원시 렌더는 로컬 cache만 사용한다. 파일 해시는 같은 폴더 `manifest.json`에 있다.
- 전체 Mia, 바디 해부 조형, 최종 텍스처/리깅/애니메이션은 **미완성·미승인**이다. 과거의 제한된 WIP PASS나 렌더 성공을 전체 승인으로 확대하지 않는다.

## 2. 필수 읽기 순서

1. 루트 `AGENTS.md`, `asset/mia/AGENTS.md`.
2. `.agents/skills/mia-reference-modeling/SKILL.md`와 `references/local-refinement.md`, `references/body-shaping.md`.
3. `asset/mia/CURRENT_STATE.json`의 `active_production_record`가 가리키는 `production_resume_20261104`. 오래된 상태를 파일명/버전 숫자로 선택하지 않는다.
4. `asset/mia/WORKING_PROTOCOL.md`, `REFERENCE_INDEX.md`, `REFERENCE_REVIEW_GATE.md`, `ARTIFACT_POLICY.md`.
5. `asset/mia/blender/mia-fit-v003/PROPORTION_H_PLAN.md`, `PROGRESS.md`, `asset/mia/blender/mia-refinement-v002/TRIAL_LOG.md`의 최신 기록.
6. 이 문서의 최신 사용자 피드백과 미완료 코드 경고. 기존 H/R 계획은 이 최신 피드백까지 반영해서 다시 실행 순서를 정해야 한다.

빠른 색인은 다음 명령이다. 원문·실제 이미지 확인을 대신하지 않는다.

```powershell
& 'C:/Users/antio/miniconda3/python.exe' -X utf8 -B tools/mia/pipeline/mia_pipeline.py context --root 'C:/Users/antio/.codex/worktrees/mia-current/win-overlay'
```

핵심 원화의 실제 경로:

| 역할 | 경로 |
|---|---|
| 얼굴 정체성/원래 헤어 | `asset/mia/references/received/mia-face-reaffirmed-20261031.png` |
| 16표정 및 미묘한 얼굴 각도 | `asset/mia/references/mia-expression-style-confirmed-20261031.png` |
| 착의·헤어 전체 정면/측면/후면/사선 | `asset/mia/references/mia-clean-master-v22.png` |
| 현재 바디 목표 v06 4뷰 | `asset/mia/references/received/mia-body-v06-confirmed-20261102.png` |
| 묶음머리로 목/어깨/등 가림을 해제한 보조 | `asset/mia/references/body-foundation/v06/mia-body-visibility-guide-v06.png` |
| 사용자가 재확인한 하단 E2/F2의 유방 뿌리·겨드랑이 | `asset/mia/references/received/mia-low-view-axilla-reaffirmed-20261103.png` |

가림 해제/추가 생성 뷰는 대응 구조를 이해하는 보조다. 생성 프롬프트의 각도를 실측 카메라로 취급하지 않는다. 얼굴 표정 시트도 눈/광대/코/입의 미묘한 yaw/pitch를 비교하는 참조로 써야 한다.

## 3. 실제 재개 파일과 파일명 함정

| 역할 | 루트 기준 경로 | 파일 SHA-256 |
|---|---|---|
| **현재 저장된 정적 WIP** | `.mia-cache/production-resume-20261104/Mia_Waist02_Static_WIP.blend` | `25c638a4406193dd0ff73efd3d253330bda7405a9c8c6ae83632fedaaa5725a8` |
| 허리 보정 전, 팔 길이 보정 포함 | `.mia-cache/production-resume-20261104/Mia_ArmLength02_Static_WIP.blend` | `ab11a0d25abe88dfbbaaf04858e31a954243e715c69e7eec1744328751691eb3` |
| 팔 길이 보정 전 AP695 WIP | `.mia-cache/production-resume-20261104/Mia_Resume_Static_WIP.blend` | `9c953fb48bf3c55595ca69d28523197b43b924550d96b6ad91a0792f4fabedb7` |
| 현재 Blender filepath에 표시된 **옛 재현 기준** | `.mia-cache/migration-to-C/Mia_Current_STATIC_WIP.blend` | `0d62eff09b4e95809a9f852d3e68654c1bb5a9e35fe70c065a939bc433e017ed` |

**Live filepath가 가리키는 0d62 파일의 디스크 형상과 현재 live 형상은 다르다.** 이후 보정은 RAM에서 진행하고 `copy=True`로 별도 저장했기 때문이다. 재시작할 때 이름이 Current인 0d62를 그대로 선택하면 이전 D 바디로 돌아간다. 현재 정적 형상 재개 기준은 25c638이다.

25c638은 286,076,473 bytes. 별도 Blender 프로세스에서 재열기하여 21개 actor fingerprint/재질 슬롯명, 보호 좌표와 UV/노멀 일치를 확인했다. 자료는 `.mia-cache/body-h/live/waist02/fresh-check.json`과 `native-expected.json`에 있다. 이것은 조형 승인 증거가 아니다.

다시 열면 Python `driver_namespace`의 복구/소유권 객체는 자동 저장되지 않는다. `v29_pigment_current.py::_snapshot()` 등은 `MIA_CurvedRear03Base` namespace를 전제한다. 새 세션에서는 `tools/mia/migration_c/restore_live_checkpoint.py`와 migration runtime 구조를 **먼저 읽고**, 최신 25c638/ba65와 호환되는 소유권 복구만 해야 한다. 옛 D69 좌표를 설치하는 복구 코드를 무심코 실행하지 않는다. 현재 열려 있는 Blender에는 필요한 소유권 정보가 있다.

원래 R3b/shoulder11 및 참조 원화는 보존 대상이다. 새 native와 원시 검토 자료는 로컬 ignored cache에 있으므로 Git clone만으로 이 모든 최신 파일이 내려오는 것은 아니다. 이 인계는 동일 PC의 실제 파일을 기준으로 한다.

## 4. 사용자 최종 피드백: 여섯 항목 모두 미해결

| 항목 | 사용자 지적 | 다음 판단 기준 |
|---|---|---|
| 팔 기본 자세·조형 | 상완–전완이 모든 뷰에서 이상하게 꺾임. 팔을 적당히 벌리고 거의 편 기본 자세에서 손/전완/상완의 비율과 이두·삼두·전완 볼륨을 봐야 함 | 대칭적인 작업 A포즈에서 두 분절의 축·길이·두께·팔꿈치 접속을 잡는다. 단순히 기존 꺾인 팔 전체를 회전하는 것으로 해결하지 않는다 |
| 흉곽·갈비 | 갈비 하부가 광배보다도 옆으로 튀어나오며 흉곽–허리–골반 곡선이 이상함 | 전/측/후면의 흉곽 덩어리와 하부 늑골–복사근 연결을 함께 구성한다. 유방 외곽을 갈비 폭으로 측정하지 않는다 |
| 허리 길이 | 원화와 세로 비율이 다름 | 흉곽 하단·자연 허리·골반/고관절의 기준선을 대응시키고 길이/위치를 비교한다. 허리 폭만 줄이는 조작을 반복하지 않는다 |
| 머리–몸 비율 | 최신 지적은 **머리가 지나치게 큼** | 헤어 포함/제외, 얼굴/두상, 어깨/전신의 실제 비율을 원화와 같은 카메라에서 계측한다. 정량 검토는 인계 전에 완료되지 않았으므로 자동 축소/옛 확대 지시 재적용 금지 |
| 후방 헤어 | 중앙이 비고 기존 헤어와 모양/밀도가 달라 측면·후면 볼륨이 이상함 | 원래 PIXAL 세밀한 형상과 추가한 넓은 리본형 lock의 표현 차이를 해결한다. 텍스처나 polygon 수만 늘려 끝내지 않는다 |
| 시상면·둔부 | 목–가슴–허리 S라인이 무너지고 엉덩이 볼륨 부족 | 측면 및 양 사선에서 자세와 실제 용적을 분리해 비교하고, 몸통–골반–둔부의 연속성을 맞춘다 |

사용자는 원화와 기초 해부학만 보아도 드러나는 오류가 여러 날 반복된 점을 문제 삼고 있다. 설명/조사/스킬/코드 작성만을 제작 개선으로 보고하면 안 된다. **다음 작업에서는 실제 Blender 수정과 실제 대응 이미지를 먼저 만들어야 한다.**

## 5. 무엇이 만들어졌고 무엇이 실패했는가

- 원화/컨셉·표정·속옷 바디 4뷰 및 보조 각도 자료가 이미 저장되어 있다. 새 디자인으로 바꾸는 작업이 아니다.
- 얼굴 내부 조형은 사용자가 한때 괜찮다고 수용했다. 이 수용은 현재 전신 비율·바디·헤어·텍스처 전체 승인이 아니다. 과거 얼굴 재제작 지시만 읽고 수용된 얼굴 정체성을 다시 덮어쓰지 않는다. 눈 좌우 하안검/쌍꺼풀, 눈썹 가시성/표면 잔차는 별도 상태를 확인한다.
- 현재 바디는 원래 본체의 평가된 WORLD 형상과 후속 제작 파트를 정적으로 조립한 연구 메시다. 원래 4,647 raw 정점용 `MIA_V27_SharedHeadBody`/`MIA_V06_RIG` pose helper와 호환되지 않는다.
- AP695에서 목/전방 상부 표면의 일부 개선을 보존했다. 이를 전체 흉곽 승인으로 취급하지 않는다.
- `arm-length02`: 몸통·상완·팔꿈치를 고정한 채 **팔꿈치 아래 길이/손 위치만** 보정. body183, nativeab11. 팔 전체 조형이나 기본 포즈를 완성한 작업이 아니다.
- `waist01` body6da: 좁힌 허리 위에 새 가로 꺾임이 생겨 실제 high/low/후면 검토에서 폐기, ba65 이전 body183으로 정확 복원했다.
- `waist02` bodyba65: 상단 보간을 완만하게 하여 제한된 허리 실루엣 WIP로 보존. 22,809점 변경, 114,500점 및 전체 Y/Z 보존. **사용자의 최신 갈비/허리 길이/전신 비율 지적으로 해부 조형은 계속 미결**이다.
- 폐기한 `arm-chain01` c9 broad torso carrier는 팔 길이를 고치면서 유방 뿌리·흉곽·어깨·광배를 망가뜨렸다. live select/apply가 차단되어 있다. 이 방식/실패안을 편의상 재사용하지 않는다.
- 이전 collar 구멍/능선 조작, cap quadric/전역 smoothing 등도 실제 보이는 회귀로 폐기한 기록이 있다. 숫자가 매끈해졌다는 이유로 되살리지 않는다.
- 기존 접촉 검사에서 팔 원위부의 inherited contact194개는 미해결 범위로 남아 있다. waist02 범위의 0 NEW 검사로 이것까지 없어진 것이 아니다.

원화 대비 실제 비교는 `asset/mia/reviews/waist02/source-before-after.jpg`, 원시 7뷰는 `.mia-cache/body-h/live/waist02/source/`에 있다. 최신 갈비 검토용 baseline7뷰는 `.mia-cache/body-h/live/rib01-before/after-v2/`이다. 모두 중립 무광 진단이며 최종 피부/메이크업 룩이 아니다.

## 6. 최신 미적용 갈비 후보

- 작업자 소스 커밋: `7375d73ebfbf62e86ddd353280f0b3ad1e9bdf06`, `tools/mia/integrated_finish/rib_oblique01.py` 한 파일만 추가한다. **canonical에 아직 merge하지 않았다.**
- 이동 소스 스냅샷: `asset/mia/handoff/20261104/rib_oblique01.source-only.py.txt`.
- 최신 payload: `.mia-cache/body-h/live/rib01/proposal-v3/proposal.npz`, 설명/검사: 같은 폴더 `forecast.json`.
- 후보 좌표 SHA: `c236171b70701eb8cce16aeeabee07bab5d876da017bf7a972ed233ed68bd6aa`.
- 하부 흉곽 측후면 일부 3,709점 소유권, 실제 3,190점 변경, 최대 약3.62mm. X 안쪽/Y 뒤쪽의 작은 조작이며 Z는 그대로다. 실제 패치 경계에서 12mm 지오데식 C2 falloff를 적용했다.
- 후보는 breast/front 분류 13,719점과 그 외 영역을 고정한다. 이 분류 자체가 완벽한 해부학 Face Set이라는 뜻은 아니다. 앞/뒤/실제 깊이 차폐를 켠 측면 선택을 확인했고 선택 표시를 제거했다.
- 선택 증거: `.mia-cache/body-h/live/rib01/selection-front-0.png`, `selection-back-0.png`, `selection-side-0.png`.
- V1은 선택 경계 fade가 없어 **CPU/소스 검토에서** 제외. V2/V3는 같은 C2 좌표이며 V3가 interface dihedral 기록을 추가했다. 실제 live 보정·렌더·충돌·원화 후보 비교·ART 판단은 **전부 미실행**이다.
- V3도 면적비 최대 약1.987, 국소 dihedral 증가 최대 약11.47°가 있다. no-flip만 보고 적용/채택하지 않는다. 최신 사용자의 몸통 전체 비율 문제를 이 작은 옆면 후보가 해결한다고 주장하지 않는다.

## 7. 중단된 팔 포즈 코드: 그대로 실행 금지

작업자 브랜치 `codex/mia-arm-pose01`, worktree `C:/Users/antio/.codex/worktrees/mia-arm-pose01/win-overlay`에 있다. HEAD는 `3605eec45d3ae30a737e0683d95e39843f76ac73`이며 **그 이후 미커밋 수정이 남아 있다.** canonical에는 아직 merge하지 않았다.

인계 시점 파일/미커밋 수정은 다음 텍스트 스냅샷으로 보존했다. 실행 파일이 아니다.

```text
asset/mia/handoff/20261104/arm_pose01.interrupted.py.txt
asset/mia/handoff/20261104/arm_pose01.interrupted.patch.txt
```

`_from_to()`와 `_pose_targets()`를 추가하는 도중 중단됐다. **CPU forecast와 Blender set_pose에 연결되지 않았다.** 현재 runtime은 여전히 bone-local Euler Y를 쓰고 있으므로 수정이 끝났다고 오인하지 않는다.

확인된 결함/수정 필요 사항:

| 결함 | 필요한 수정 |
|---|---|
| CPU의 world-Y 회전 부호는 우측 팔을 안쪽으로 돌렸고, runtime의 bone-local Y는 팔 벌림 대신 축 비틀림이 됨 | 실제 S/E/W와 목표 방향에서 from-to 회전을 구하고 bone rest matrix에 적용. CPU와 runtime의 동일한 공간/변환을 검증 |
| A45/T90 값을 현재 자세에 더하는 delta로 사용 | 현재 축을 기준으로 **목표 방향**으로 맞춘다. A는 거의 편 상완/전완 두 축을 각각 정렬해야 함 |
| CPU elbow_bend는 각도0이라 실질 검사가 없었음 | 상완/전완을 분리한 실제 elbow 변형을 계산 |
| 상·하완 가중치에 같은 fade를 곱함 | Armature 내부 정규화로 fade가 사라질 수 있다. 별도 modifier influence group 또는 identity bone 등을 이용해 전체 변형량을 제어하고 실제 평가 확인 |
| 두 본의 혼합이 어깨→손 전체에 퍼짐 | 팔꿈치 주위의 제한된 구간에서 혼합하고, 상완/전완 구간은 해당 분절을 따라가도록 구성 |
| 처음에는 percentile로 손/팔꿈치를 잘못 추정하고 손끝을 높이 필터로 누락 | 아래 실제 소유권과 단면/손목 자료 사용. 모든 손가락/분리 손톱 포함 여부 확인 |
| 너무 짧은 고정 shell 경계로 표면 접힘 발생 | 실제 경계 지오데식 fade와 필요한 어깨/전후 겨드랑이 인터페이스를 검토. DQ 설정 하나로 해결됐다고 주장하지 않음 |
| cleanup은 object 삭제 위주이며 예외 중간 복구/소유 mesh·armature data/선택·mode 복구가 불충분 | 설치 실패 및 정상 종료 모두 원본/컨텍스트를 정확히 복원하도록 보완 |

소스의 CPU forecast는 Work-A/T에서 min normal cosine 약−1, **REJECT** 상태다. `.mia-cache/body-h/live/arm-pose01/forecast.json`은 옛 잘못된 LBS 예측이며 DQ/실제 Blender 결과가 아니다. 실제 팔 리그나 포즈 복사본은 생성하지 않았다.

수정 설계 가설(미구현, 실제 검증 필요): 실제 shoulder S, elbow E, wrist W에서 upper/lower 길이를 유지한다. A 목표 방향 `du=dl=(side*sin45,0,-cos45)`, T는 `(side,0,0)`, elbow 진단은 A 상완과 전방 전완 등으로 둔다. RU는 E−S→du, Enew=S+Lu*du, RL은 W−E→dl로 정한다. 절대 armature 공간 변환 `U=T(S) RU T(-S)`, `L=T(Enew) RL T(-E)`를 각 bone rest matrix와 조합한다. 이는 일반적인 각도 처방이 아니라 이번 작업용 가설이다. 원래 자세 복귀·고정 영역·실제 평가/볼륨·접촉을 먼저 확인한다.

## 8. 팔·몸통 소유권의 함정과 검증된 자료

기준 topology는 current137341/274324이다. `.mia-cache/body-h/shape/assembly/live-D/atlas/surface.npz`는 `world`, `triangles`, `loop_uv`, `face_region`, `meshfaceid`를 포함한다. `triangles == current_faces[meshfaceid]`는 일치하지만 world는 **옛 D**이므로 좌표를 덮어쓰는 입력이 아니다.

- region1/2는 몸통 앞/뒤이지만 유방도 포함한다. 저장된 완전한 breast-core Face Set은 찾지 못했다.
- region6/7은 팔 분류지만 발/다리 오염이 있다. 예: face40101/vertex37922, face4855/vertex20243는 Z≈.049/.048의 발이다. label 전체를 팔로 쓰지 않는다.
- 손끝 seed R42692/L42572와 기존 arm-length02의 검증된 distal/손/손톱 소유권을 사용하고, 실제 연결 성분을 구한다.
- region14/15의 **기존 팔 접합 collar를 allowed graph에 포함해야** 손에서 상완까지 연결된다. 이를 빼면 선택이 Z≈1.107에서 끝나 팔꿈치 아래만 포즈하게 된다.
- 연결 성분+분리 손톱을 포함한 제안 core는 R19,444/L19,222, 합38,666점이었다. 이것도 어깨 경계의 해부학적 적합성 승인은 아니다.
- 상부 core 경계는 대략 `|X|.148–.187, Z1.254–1.3405`. shoulder 작업 proxy `Z1.361`보다 아래여서 적절한 shoulder/axilla 보간이 필요하다.
- 현재 elbow proxy는 actual `armR/L[12]` 단면 중심, Z≈1.137. wrist constriction은 이전 검증된 길이 보정 후 `(±.294,.012,.895)` 근처다. shoulder `(±.146,.008,1.361)`은 작업용 proxy이며 실측 관절 중심이라는 뜻은 아니다.

현재 topology의 면 범위는 `[start,end)`:

```text
neck 209484:221750   waist 221750:256750
armR 256750:265750   armL 265750:274324
```

`.mia-cache/migration-to-C/row-ownership.npz`: neck16×368, waist34×504, armR26×168, armL26×160. 팔 rows는 어깨 체인이 아니라 Z≈1.184→1.085의 접합 밴드다. sourcepart2도 팔/몸통이 섞여 있다. 이 라벨들을 해부학적 의미로 무비판적으로 쓰지 않는다.

## 9. 후방 헤어 조사 결과

현재 유지된 헤어19개는 원래 PIXAL에서 복사한 `MIA_Hair_CurvedRear03Base_RemainingMain`과 추가18개 lock이다. 9c 이후 waist02까지 19개 fingerprint는 동일했다.

- 숨겨진 원본 `MIA_V17_PIXAL_DetailedHair`: 100,383정점/120,915삼각형과 기존6UV가 남아 있다. 원본과 RemainingMain을 동시에 렌더하면 중복된다.
- RemainingMain은 원래 복사본에 GN underlap 마스크로1,781 loop faces를 가린 구성이다. 별도 UV7/정적 pigment는4,999 crown faces 중심이다. 하부 nape의 기존 표면 문제까지 모두 해결한 것이 아니다.
- 추가18개는 총46,692정점/93,312삼각형으로, 단순 low-poly 부족이라고 할 수 없다. 넓고 평평한 lancet/S-ribbon 단면과 규칙적인 겹침·길이·깊이 분포가 원화와 다르다.
- 생성 소스 `tools/mia/face_surface_live/prepare_curved_rear.py`는 거의 고정된 depth layer .116/.148/.158, 작은 깊이 변화, 단면 depth×.42 등을 사용한다. 측면에서 얇은 평행 띠처럼 보이는 것은 표현/조형 문제다.
- 현재 실제 이미지: `.mia-cache/production-resume-20261104/head-hair-orbit/06.png`(측면), `12.png`(후면). 원화는 불규칙하고 조밀한 여러 clump가 겹치지만 현재 중앙은 넓고 길고 규칙적인 리본에 가깝다. orbit crop은 끝단 전체를 보여주지 못할 수 있다.
- 별도18 lock의 공유 UV toon 룩/페인트·normal 완성도도 남아 있다. 텍스처만으로 빈 공간·길이·측면 두께를 해결할 수 없다.
- `rear_groom01` 실패 guide/M1 fringe field 등을 현재 채택본으로 되살리지 않는다. root 및 nape/crown의 유효한 개선을 보존하며 새 파트의 형상·레이어부터 검토한다.

## 10. 이어서 실제로 할 작업 순서

1. 현재 열린 Blender/25c638의 실제 상태와 기준 원화를 확인한다. 원화 정면·측면·후면·사선의 동일 종횡비/투영 비교에서 머리, 어깨, 흉곽 하단, 허리, 골반, 둔부와 팔 분절 기준선을 표로 만든다. **이번 새 정량 감사는 인계로 중단되어 미완료다.**
2. 팔 진단 코드의 공간/방향/소유권/가중치 오류를 고친 뒤 원본을 변경하지 않는 복사본에서 거의 편 작업 A포즈를 실제로 만든다. 상완/전완/손의 축·길이·근육 볼륨, 앞뒤 겨드랑이, 어깨/광배 연결을 정면/측면/사선/high/low로 확인한다. A포즈를 코드상 이름으로만 지정하고 완료라고 하지 않는다.
3. 원화의 전신 비율표에 맞춰 흉곽–허리–골반의 길이·폭·깊이, 시상면 S라인·둔부를 연속된 입체로 수정한다. 작은 패치만 번갈아 맞추지 않는다. 유효한 국소 형상은 보존하되, 비율 수정에 필요한 위치 이동까지 영구 고정하지 말고 명시적 transport/interface로 관리한다.
4. 머리 크기는 실제 비율 확인 후 결정한다. 변경한다면 얼굴/눈/눈썹/속눈썹/헤어/리그의 전체 부착 관계와 목 연결을 함께 다루고, 일부 머리 메시만 축소해 이목구비·표정을 분리시키지 않는다.
5. 후방 헤어는 별도 파트로 중앙 밀도, 불규칙한 clump/길이/단면 깊이를 원래 PIXAL 세밀함과 맞춘다. 원래 헤어 전체를 새 단순 리본으로 대체하지 않는다.
6. 각 작업의 source arm-down 비교와 A/T/elbow 변형 검토, 원화 대응 7뷰를 완성한다. 최종 UV·표면맵/메이크업·의상·표정/모션은 기본 조형이 실제 검토를 통과한 뒤 진행한다. Blender 렌더 sprite30fps와 VRM/Unity spring runtime은 구분한다.

## 11. 실제 편집·검수 규칙

- live Blender MCP를 사용한다. UI 컴퓨터 제어로 대체할 필요가 없었다. Python/bpy 사용 자체가 문제는 아니며, **실제 해부학 영역 선택 → 작은 편집 → 실제 표면/원화 비교 → keep/restore** 루프가 핵심이다.
- 새 coordinate delta는 `tools/mia/integrated_finish/scoped_mesh_edit.py`로 실제 editable/transition/fixed IDs, baseline SHA, topology를 확인한 뒤 설치한다. unsupported keys/modifiers를 몰래 제거하거나 검사 실패 후 raw 경로로 우회하지 않는다.
- 현재 지원 data-only 경로: `tools/mia/review_h/lab_mcp.py call --tool execute_blender_code --mesh-edit-job <cached-job.json> --report <report.json>`.
- 실제 선택/원화 파일의 해시를 job에 결합한다. 보호 정점이 한 점이라도 움직이면 편집 전에 거절해야 한다. 보호 영역도 실제로 맞는 영역인지 이미지로 검토한다.
- 원화 비교는 crop·회전·**균일** 배율·평행이동만 허용한다. 원화 가로세로 비율 변경, 부위별 warp, 뷰마다 별도 메시 변경으로 오차를 숨기지 않는다.
- 카메라/조명/포즈/활성키/컬러 관리/clip 범위를 기록한다. 현재 검토는 ORTHO와 camera clip0.1..10m를 사용했다. 이 범위가 모든 장면의 정답이라는 뜻은 아니다. 원점 이동으로 탐색 문제를 해결하지 않는다.
- source/baseline/candidate front/profile/back/oblique, 반대 사선/high/low가 필요하다. 가려지면 헤어를 잠시 숨기고 복원한다. 해부 조형은 중립 무광, 표면은 실제 연결된 shader/UV/색 경로와 목표 toon 룩을 별도로 본다.
- `asset/mia/blender/mia-reference-finish-v22/validate_reference_review.py`는 파일/카메라/뷰/정합 증거 검사다. evidence_valid는 ART PASS가 아니다. 실제 독립 이미지 판단과 잔차를 남긴다.
- current shader에는 Emission/ShaderToRGB 계열도 있다. 모든 영역이 일반 PBR 광원에 반응한다고 가정하지 않는다. 재질 노드 존재와 실제 활성 출력/렌더 적용을 구분한다.
- 프로젝트 hooks는 advisory다. 자동 실행/강제 차단/ART 판정을 검증한 것으로 주장하지 않는다. Claude Code에서 동일 hook이 자동 작동한다고 가정하지 않고 위 절차를 직접 따른다.

## 12. 도구와 안전한 재개 명령

Blender5.2.3 LTS: `C:/Program Files/Blender Foundation/Blender 5.2/blender.exe`.
Python: `C:/Users/antio/miniconda3/python.exe`(SciPy 없음). 기존 MCP client Python: `C:/Users/antio/.codex/tools/blender-lab-mcp-venv/Scripts/python.exe`.

Claude Code의 기존 Blender MCP 도구가 충분하면 그대로 사용한다. 새 MCP 설치/설정/권한 변경을 먼저 하지 않는다. 호스트 카탈로그와 실제 서버 스키마가 달랐기 때문에 아래 기존 wrapper를 사용했었다. 이 명령의 bpy는 **열린 Blender에서 실행**된다.

```powershell
# 실제 서버 스키마 확인
& 'C:/Users/antio/.codex/tools/blender-lab-mcp-venv/Scripts/python.exe' -X utf8 tools/mia/review_h/lab_mcp.py list --report .mia-cache/body-h/live/claude-tools.json

# 검토한 read-only 또는 범위 제한 스크립트 실행
& 'C:/Users/antio/.codex/tools/blender-lab-mcp-venv/Scripts/python.exe' -X utf8 tools/mia/review_h/lab_mcp.py call --tool execute_blender_code --code-file <검토한-script.py> --report .mia-cache/body-h/live/claude-review.json --timeout 180
```

wrapper는 `__file__`을 주입한다. screenshot 인자는 `--arguments`이며 `--arguments-file`이 아니다. raw bpy를 실행할 수 있다는 사실이 조형 품질이나 범위 보호를 자동 보장하지 않는다. 실행 결과가 진행 중 session이면 완료를 기다린 후 종속 호출을 한다.

이번 canonical에서 변경한 `capture_live_contour.py`에는 검토 object/detail/full-frame/view subset/diagnostic pose용 선택 인자를 추가했다. 기본 7뷰는 유지되고 현재 baseline capture는 실행했다. **새 팔 포즈 object를 이 옵션으로 촬영하는 경로는 아직 실행하지 않았다.**

## 13. Git/worktree와 저장 공간

- worker 소스는 canonical에 merge하지 않았다. 이 문서와 함께 source-only/중단 코드의 `.py.txt` 스냅샷 및 `manifest.json`을 보관한다. 안전성과 최신 사용자 요구를 검토한 뒤 필요한 소스만 가져온다.
- rib worker `C:/Users/antio/.codex/worktrees/mia-rib01-shape/win-overlay`는 불완전한 sparse 초기화 때문에 **추적 파일8,152개가 working-tree deletion으로 표시**된다. canonical 파일이 삭제된 것이 아니다. 이 WT에서 `git add .`/일괄 commit/강제 정리를 하면 안 된다. 인계 시 index의 삭제는 없었고, 검증된7375 커밋은 소스1파일만 추가한다.
- 잘못 만들었던 미공개 rib 커밋 `741cf25`는 폐기됐다. 절대 사용하지 않는다. 검증된7375만 검토한다.
- arm worker `C:/Users/antio/.codex/worktrees/mia-arm-pose01/win-overlay`는 HEAD3605 이후 소스1파일 미커밋 수정이 있다. 중단 diff는 HEAD 대비 스냅샷에 보존했다. 다른 작업자의 변경을 임의 reset/stash/삭제하지 않는다.
- 원본/채택본/고유 수작업과 dirty worktree를 강제 삭제하지 않는다. Git 이력 rewrite/force push/LFS 원격 삭제는 승인된 작업이 아니다.
- native·대량 render·bake 전에 아래 기존 guard를 실행한다. 실제 추가 예상량으로 예약한다.

```powershell
& 'C:/Users/antio/miniconda3/python.exe' -X utf8 -B asset/mia/blender/mia-fit-v003/integration/workspace-storage-20261103/storage_guard.py --reserve-mib <예상추가MiB>
```

C 여유20GiB 이상, 지정 component+cache+runtime temp+예약량 합2GiB 이하가 기준이다. 이번 시작 시 component 약1.67GB였고 현재 추가량은 실제 guard로 재확인한다. root만 대용량 writer 하나를 허용한다. 후보마다286MB native를 만들지 말고 작은 델타/실제 비교 자료를 보관한 뒤 채택 시 한 번 저장한다. source-only worker마다 공통 asset/native를 복제하지 않는다.

이전 약200GB 문제의 정리/거절 이력은 WORKING_PROTOCOL/저장 공간 기록에 있다. D 전체 삭제/과거 백업 삭제 등 자동 검토가 거절한 작업을 다른 수단으로 재시도하지 않는다. 프로그램 제거로 사용자가 확보한 공간을 에이전트가 회수한 공간으로 보고하지 않는다.

## 14. 조사 자료와 실제 접근 수준

| 제작자/자료 | 실제 확인 | 적용할 원칙/한계 |
|---|---|---|
| Julien Kaspar, [Fine Control](https://studio.blender.org/training/blender-fundamentals-45-lts/fine-control/) | 공개 HTML 본문, 전체 영상 아님 | joined arm 수정 시 torso mask, Face Set/visibility 분리, 버전 비교. 해시 검사는 이 프로젝트의 자동화이며 현업 보편 도그마가 아님 |
| Kaspar, [Clothing Shapes](https://studio.blender.org/training/realistic-human-research/clothing-shapes/) | 공개 HTML 본문, 영상 아님 | A조형→예비rig→A/T·joint 검사 사례. T나45°가 모든 모델의 의무라는 근거가 아님 |
| Stan Prokopenko, [Anatomy of the Rib Cage](https://www.proko.com/course-lesson/anatomy-of-the-rib-cage) | 공개 Lesson Notes, 영상 아님 | 앞/옆/뒤 평면과 감싸 돌아가는 하부 arch. 미적 이상화 치수를 Mia에 강제하지 않음 |
| 치차ChiChaArt, [바디](https://www.youtube.com/watch?v=8kg_CpOkoDE), [얼굴](https://www.youtube.com/watch?v=6xuWKIplo7Q&t=4712s) | 사이드 조사에서 선택 자막/챕터/일부 프레임, 전편 연속 시청 아님 | 분리 헤드·헤어·바디, 눈/입 loop, 의상 독립, pose 후 weight 수정. URL 시각값을 실제 확인한 모든 영상 타임스탬프로 확대하지 않음 |
| Motomura / Arc System Works, [Skinning 자료](https://www.docswell.com/s/ASW_Academy/56JDMV-GG-Skinning) | 공개 슬라이드 텍스트 | 분리 파트/변형 topology와 volume loss. low-poly 예시의 편법을 노출 피부에 그대로 복사하지 않음 |

기존 종합 조사 Wiki 노트는 사용자 전달 기준 `mia-reference-mcp-review`, 이전 위치 `D:/intel_engram/docs/_inbox/mia-reference-mcp-review.md`다. 이번 Codex 세션에는 KG/Wiki/activity 도구가 노출되지 않아 최신 제작 내용을 Wiki에 동기화했다고 주장하지 않았다. 현재 저장소의 상태/계획/로그가 이번 실제 기록이다. Claude Code에서 도구가 연결되어 있다면 해당 노트를 조회하되 D 제작 의존성을 다시 만들지 않는다.

## 15. 인계 완료/재개 경계

Codex 제작 에이전트는 사용자 인계 요청에 따라 중단했다. 새 모델/리그/포즈/맵/의상/애니메이션을 적용하거나 native를 추가 저장하지 않았다. 실제 모델은 ba65/25c638 WIP이며 최신 여섯 과제는 전부 열려 있다.

다음 보고는 문서/헬퍼 작성량이 아니라 **실제 기본 포즈와 조형, 원화 대응 이미지, 보호/회귀/미해결**을 중심으로 해야 한다. 모델을 만들었다고 말하기 전에 사용자가 확인할 수 있는 실제 결과를 제시한다.

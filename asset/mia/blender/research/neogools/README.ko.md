# 너굴스 3D훈련소 — Mia 제작 참고 자료와 분석 범위

작성일: 2026-10-31 (Asia/Seoul)
상태: **얼굴 편과 별도 Blender 헤어 영상은 한국어 자동 자막·제한된 화면 표본으로 갱신됨 / 시리즈 2·3·최종을 포함한 나머지는 metadata-only**

이 근거를 후속 전문 제작 gate에 연결한 문서는 [Mia 애니메이션 제작 워크플로](../../mia-animation-production-workflow/README.ko.md)다. 이 링크는 모델 승인이나 제작 완료를 뜻하지 않는다.

## 확인 결과

사용자가 지정한 얼굴 영상은 단독 강의가 아니라, 같은 채널의 얼굴 → 손·의상 → 머리카락 → 텍스처링·렌더링으로 이어지는 네 편의 제작 과정에 속한다. 아래 제목·순서·길이·게시일은 채널의 공개 `/videos` 목록과 각 영상의 공개 player metadata에서 교차 확인했다. 시리즈 얼굴 편과 **별도** Blender 헤어 영상에는 각각 아래 범위의 자동 자막·제한된 화면 표본을 확인했다. 이는 전체 영상을 시청했다는 뜻은 아니다.

채널: [너굴스 3D훈련소](https://www.youtube.com/@Neogools_3D_Trainning), channelId `UCZ1X9qDnZZOyQ71yWTF2Kkw`.

| 순서 | 제목 및 원본 링크 | 길이 | 원본 게시일 | 확인한 범위 |
|---|---|---:|---|---|
| 1 | [나만 알고 싶은 원화를 이용해 쉽게 카툰 모델링하는 제작 과정 — 1부: 얼굴 편](https://www.youtube.com/watch?v=vJeCC_nGR_c) | 30:43 | 2024-07-04 | 한국어 자동 자막 전체 확인. 화면 표본 직접 관찰: 1:06, 3:46, 4:21, 6:36. 전체 시청은 아님 |
| 2 | [같은 제작 과정 — 2부: 손,의상 모델링 편](https://www.youtube.com/watch?v=4nmavWMCYPo) | 15:49 | 2024-07-12 | metadata-only. 제목은 몸이 아니라 **손, 의상**임 |
| 3 | [같은 제작 과정 — 3부: 머리카락 편](https://www.youtube.com/watch?v=2VlgljhQEhE) | 13:56 | 2024-07-28 | metadata-only |
| 최종 | [같은 제작 과정 — 최종: 텍스처링 및 렌더링 편](https://www.youtube.com/watch?v=iHMlszNdqjg) | 28:58 | 2024-08-12 | metadata-only |

네 편의 합계는 89:26이다. 날짜는 player metadata의 원래 게시일(미국 UTC−07 기준)을 유지했다. 얼굴 편은 3ds Max 자료이며, Blender에 버튼·단축키를 그대로 이식하지 않는다. 네 편 전체의 사용 도구·플러그인·정확한 조작 순서는 확정하지 않는다.

## 실제로 확인한 원화 기반 얼굴 제작 근거

얼굴 편의 자동 자막과 위 화면 표본에서 다음 순서를 확인했다. 각 항목은 영상 본문에 대한 요약이며, Mia에 그대로 적용했다는 뜻은 아니다.

| 시점 | 접근 수준 | 확인한 내용 | Mia 적용 가설 / 한계 |
|---|---|---|---|
| 1:06 | 화면 + 자동 자막 | 원화 이미지 plane 위에서 눈 윤곽을 따라 edge를 추가 | 눈·입·턱의 editable guide를 먼저 두고 완성 mesh로 오인하지 않는다. |
| 1:23 | 자동 자막 | vertex 이동 중 Preserve UV를 사용해 텍스처를 유지 | 현 UV를 실제로 수정하는 단계에서는 별도 백업·재투영 검증이 필요하다. 이번 작업공간은 UV를 건드리지 않는다. |
| 3:36 / 3:46 | 화면 + 자동 자막 | 평면적인 측면을 확인한 뒤 Preserve UV를 끄고 깊이를 준다 | 정면 인상만으로 복구하지 않고 동일 ortho 정면·측면 회귀 렌더를 남긴다. |
| 4:18 / 4:21 | 화면 + 자동 자막 | 측면 실루엣을 만들며 큰 형상을 우선한다 | Mia master sheet는 strict turnaround가 아니므로 깊이·기울기는 시각 보정 후보일 뿐 실측값이 아니다. |
| 4:29 | 자동 자막 | wire 정리보다 큰 silhouette을 먼저 잡는다 | guide를 랜덤/자동 생성하지 않고 수동 조정 대상으로 유지한다. |
| 6:26 / 6:36 | 화면 + 자동 자막 | 원화를 반투명 비교하며 윤곽을 보정한다 | reference UV crop과 current v06 read-only render를 별도 패널에 둔다. |
| 22:39, 24:05 | 자동 자막 | 회전·다각도에서 outline/wire를 확인·수정 | 화면 표본을 직접 확인하지 않았으므로 절차 가설로만 기록한다. |

별도 Blender 영상 [카툰스타일 헤어 만드는 법](https://www.youtube.com/watch?v=km7fhoqCTRk)은 한국어 자동 자막 전체를 확인했고, 2:20–2:21 curve/tilt 및 6:18 화면 표본을 직접 보았다. 0:13, 1:27, 2:17, 2:45, 6:17, 6:34, 7:00, 7:19은 자동 자막 근거이며 6:17의 convert 단계도 자막으로만 기록한다. 긴 웨이브·앞머리·땋은 머리의 최종 topology·리깅 방법을 이 근거만으로 확정하지 않는다.

네 편의 공개 설명은 네이버 카페와 카카오 커뮤니티 링크를 안내한다. 접근 가능한 설명에서 세부 챕터나 수업 단계의 추가 설명은 얻지 못했다. 커뮤니티에 메시지를 보내거나 가입하지 않았다.

## 같은 채널의 직접 관련 자료

| 자료 | 길이 / 원본 게시일 | Mia와 관련해 추가로 확인할 질문 |
|---|---|---|
| [블렌더를 활용해서 카툰스타일 헤어 만드는 법](https://www.youtube.com/watch?v=km7fhoqCTRk) | 8:56 / 2024-11-05 | 한국어 자동 자막 전체 확인. 화면 표본 2:20–2:21, 6:18 직접 관찰; 위의 자막-only timestamp 외에는 전체 시청 주장 없음. |
| [블렌더에서 UV를 새로 수정할 때 원본 텍스처를 살리는 방법](https://www.youtube.com/watch?v=5K5oCjHuYw8) | 3:11 / 2024-12-23 | UV 변경 전후 원본 텍스처 보존의 실제 작업법은 무엇인가? |
| [초간단하게 3ds Max에서 원화를 활용하여 손맵(Handpainted) 텍스처 만드는 비밀정보](https://www.youtube.com/watch?v=vpqQiXIO2Hs) | 2:55 / 2024-06-27 | 원화 색을 어떤 면에 어떻게 옮기며, 사선·측면의 색 연결은 어떻게 보정하는가? |

제목은 해당 주제를 다룬다는 근거일 뿐, 위 질문의 답을 얻었다는 근거는 아니다.

공개 채널의 재생목록 탭에서는 다음 목록도 확인했다. 현재 접근 가능한 목록 제목만 확인했으며 모든 항목·순서를 완전 수집한 것은 아니다.

- [블렌더 TIP](https://www.youtube.com/playlist?list=PLeILaOslhH0ECJT9Qka50kwqtJDYceFUo)
- [3ds max 꿀팁들](https://www.youtube.com/playlist?list=PLeILaOslhH0ELC-gjriUnent7-_qDqr-I)
- ["3ds max 캐릭터모델링 단계별 학습과정](https://www.youtube.com/playlist?list=PLeILaOslhH0EHa5pAfUlsdtfUq_kZcIb5)

공개 RSS의 Gradient_Layer_Hair, Yua liltoon/MMD, 얼굴 타임어택 등은 결과물·관련 주제 후보로 남긴다. 제목만으로 제작 강의나 같은 카툰 시리즈의 후속 편이라고 분류하지 않는다.

## 본문을 확보했을 때의 분석 순서

이 표는 **Mia를 위한 조사 계획**이다. 제작자가 실제로 사용한 기법이라고 인용하지 않는다.

| 우선순위 | 자료 | 관찰·기록할 항목 | Mia에서 검증할 결과 |
|---|---|---|---|
| P0 | 얼굴 편 | 원화 정합에 쓰는 카메라, 정면·옆면·사선 전환 시점, 눈/입 topology와 얼굴 깊이, 좌우 편집, 표면 음영과 기하의 역할 | 눈매·볼·턱의 원화 닮음과 실제 측면 부피를 별도로 검증. 다크서클로 형상 차이를 덮지 않음 |
| P0 | 머리카락 편 + Blender 헤어 | 두상 기준, 모근 연결, 큰 덩어리→세부의 순서, 곡면 단면·겹침, 뒷머리와 묶음, 법선·alpha의 역할 | 얼굴을 가리는 잘못된 cap, 납작한 후두부, 동일 굵기 rope/leaf 반복을 방지. 정면뿐 아니라 후면·고저 시점에서 확인 |
| P1 | 손·의상 편 | 신체에서 복제한 초기 표면 여부, 독립 옷 topology, 여유·두께·밑단, 가려진 몸체 관리, 손가락의 구조 | 두꺼운 floating crop, 열린 oversized cardigan, cargo의 실제 핏. 원본 신체를 보존하고 허용 포즈에서만 가림 검증 |
| P1 | 최종 텍스처·렌더링 | 피부/머리/의상 UV, 채색·그림자의 분리, toon ramp·outline·normal 제어, 조명 조건과 색 관리 | 정면에서만 성립하는 그림자·얼굴 방지. 실제 컬러와 중성 구조 검사, idle·blink·입 모양에서 일관성 확인 |
| P2 | UV 보존·손맵 단편 | 원화 투영·UV 변경의 입력과 출력, baking/재투영 여부, 이음새·왜곡 보정 | 표정에 붙는 눈 밑 톤과 디자인 포인트. 현 UV를 바꾸기 전에 데이터 보존 절차를 증명 |

관찰 기록의 최소 단위는 `영상 URL + 실제 timestamp + 확인한 장면/발언 + 재현 단계 + Mia 적용 여부`로 한다. 영상에서 보지 못한 항목은 빈칸/미확인으로 둔다. 예를 들어 Shell, smoothing group, projection 등을 썼다고 현재 단계에서 적지 않는다.

## Blender로 옮길 때 구분할 부분

아래는 도구에 독립적인 **일반적인 전이 판단**이며, 위 영상의 관찰 결과가 아니다.

- 원화의 눈·입·얼굴 윤곽을 맞추는 목표와, 메시 편집 도구의 버튼·단축키를 구분한다. Max 작업을 그대로 번역하기보다 Blender의 Mesh Edit, Mirror, Solidify, UV, normals, Shape Keys 등에서 같은 입력·출력을 시험한다.
- topology·실루엣·색·normals·toon 재질은 함께 검토하되, 색으로 실제 부피 손실이나 중복 표면을 가리지 않는다.
- 화장과 다크서클이 피부 UV에 그려져 있으면 같은 메시의 표정 변형을 따르게 설계할 수 있다. 표정 품질은 별도의 눈꺼풀·입 변형 시험으로 검증한다. 현재 Mia의 UV 기반 눈 밑 톤과 blink proof는 별도 직접 실험이며 이 채널에서 배운 기법이라고 주장하지 않는다.
- 모든 기법은 현재 Mia의 실제 source SHA와 좌표계에 연결하여 검증한다. 이번 헤어 추출에서 발견한 숨겨진 원본 object의 stale world matrix 문제 역시 영상 지식이 아니라 Blender 직접 측정에서 얻은 별도 교훈이다.

## 접근 제한과 미확인 사항

- 공개 watch HTML, oEmbed, RSS, 채널 `/videos` 및 `/playlists` HTML은 확보했다. 새로 확인한 시리즈 세 편과 보조 두 편은 public player metadata까지 저장했다.
- 얼굴 편과 별도 Blender 헤어 영상은 각각 별도 접근의 한국어 자동 자막으로 확인했다. 저장소에는 저작권상 원문 전체 자막을 복사하지 않고, 위의 최소 요약·접근 수준·timestamp만 기록한다.
- 얼굴 편의 네 화면 표본과 별도 Blender 헤어 영상의 2:20–2:21, 6:18 외에는 장면을 직접 본 것으로 주장하지 않는다. 6:17 convert 단계 등 자막-only 구간은 위 표의 범위를 넘겨 일반화하지 않는다.
- 따라서 **Mia 모델의 닮음·topology·rigging 검수는 여전히 미완료**다. 이 자료는 다음 비파괴 원화 정합 작업의 근거일 뿐이다.

## 저장한 1차 근거

위치: `D:/ai/Mia3DWork/research/neogools/`.

- 기존: `inventory.json`, `oembed_*.json`, `watch_*_summary.json`, `channel_rss.xml`, `rss_entries.json`, `storyboard_results.json`, 0-byte `captions_*.xml`.
- 추가: `channel_videos.html`, `channel_videos_initial.json`, `channel_videos_entries.json`, `channel_playlists.html`, `channel_playlists_initial.json`, `channel_playlists_entries.json`, `channel_page_fetch_results.json`.
- 추가: `expanded_video_metadata.json`, 새 5편의 `watch_<id>.html` 및 `watch_<id>_metadata.json`.
- 주의: Python 터미널의 CP949 출력은 한국어가 깨져 보였지만, 최종 저장 파일은 HTTP bytes를 UTF-8로 해석하고 UTF-8로 저장했다. 원본과 최종 metadata 문자열의 한글을 검증했다.

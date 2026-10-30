# 너굴스 3D훈련소 — Mia 제작 참고 자료와 분석 범위

작성일: 2026-10-31 (Asia/Seoul)
상태: **시리즈 구성 확인 완료 / 영상 본문 기법 분석 미완료**

## 확인 결과

사용자가 지정한 얼굴 영상은 단독 강의가 아니라, 같은 채널의 얼굴 → 손·의상 → 머리카락 → 텍스처링·렌더링으로 이어지는 네 편의 제작 과정에 속한다. 아래 제목·순서·길이·게시일은 채널의 공개 `/videos` 목록과 각 영상의 공개 player metadata에서 교차 확인했다. 이는 실제 제작 장면이나 음성 설명을 확인했다는 뜻은 아니다.

채널: [너굴스 3D훈련소](https://www.youtube.com/@Neogools_3D_Trainning), channelId `UCZ1X9qDnZZOyQ71yWTF2Kkw`.

| 순서 | 제목 및 원본 링크 | 길이 | 원본 게시일 | 확인한 범위 |
|---|---|---:|---|---|
| 1 | [나만 알고 싶은 원화를 이용해 쉽게 카툰 모델링하는 제작 과정 — 1부: 얼굴 편](https://www.youtube.com/watch?v=vJeCC_nGR_c) | 30:43 | 2024-07-04 | 제목·제작자·ID·길이·게시일·설명 |
| 2 | [같은 제작 과정 — 2부: 손,의상 모델링 편](https://www.youtube.com/watch?v=4nmavWMCYPo) | 15:49 | 2024-07-12 | 위와 같음. 제목은 몸이 아니라 **손, 의상**임 |
| 3 | [같은 제작 과정 — 3부: 머리카락 편](https://www.youtube.com/watch?v=2VlgljhQEhE) | 13:56 | 2024-07-28 | 위와 같음 |
| 최종 | [같은 제작 과정 — 최종: 텍스처링 및 렌더링 편](https://www.youtube.com/watch?v=iHMlszNdqjg) | 28:58 | 2024-08-12 | 위와 같음 |

네 편의 합계는 89:26이다. 날짜는 player metadata의 원래 게시일(미국 UTC−07 기준)을 유지했다. 사용자 설명에 따르면 얼굴 편은 3ds Max 자료다. 이번 조사에서 영상 UI를 직접 관찰하지 못했으므로, 네 편 전체의 사용 도구·플러그인·정확한 조작 순서는 아직 확정하지 않는다.

네 편의 공개 설명은 네이버 카페와 카카오 커뮤니티 링크를 안내한다. 접근 가능한 설명에서 세부 챕터나 수업 단계의 추가 설명은 얻지 못했다. 커뮤니티에 메시지를 보내거나 가입하지 않았다.

## 같은 채널의 직접 관련 자료

| 자료 | 길이 / 원본 게시일 | Mia와 관련해 추가로 확인할 질문 |
|---|---|---|
| [블렌더를 활용해서 카툰스타일 헤어 만드는 법](https://www.youtube.com/watch?v=km7fhoqCTRk) | 8:56 / 2024-11-05 | 머리 덩어리의 단면·겹침·모근과 끝 처리, 뒷머리 볼륨을 어떤 구조로 유지하는가? |
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
- 한국어 자동 자막 트랙은 표시되지만 기존 자막 endpoint의 본문은 0 byte였다. 공개 storyboard 요청은 403이었고 실제 장면 이미지는 얻지 못했다. 해당 실패 요청은 이번 조사에서 반복하지 않았다.
- native browser 접근은 Windows 현재 URL을 충분히 검증하지 못한다는 Computer Use 자동 정책 때문에 중단되었다. UI 재시도·우회는 하지 않았다.
- 따라서 **정확한 모델링 기법·영상 내 작업 순서·timestamp 기반 분석은 아직 미완료**다. 현재 얻은 것은 신뢰할 수 있는 자료 목록과 실제 본문을 검토할 때의 질문이다.
- 다음 분석에는 허용된 경로에서 볼 수 있는 영상 장면·음성/자막 본문이 필요하다. 그것이 확보되기 전까지 조회할 수 있었던 metadata를 본문 요약으로 바꾸지 않는다.

## 저장한 1차 근거

위치: `D:/ai/Mia3DWork/research/neogools/`.

- 기존: `inventory.json`, `oembed_*.json`, `watch_*_summary.json`, `channel_rss.xml`, `rss_entries.json`, `storyboard_results.json`, 0-byte `captions_*.xml`.
- 추가: `channel_videos.html`, `channel_videos_initial.json`, `channel_videos_entries.json`, `channel_playlists.html`, `channel_playlists_initial.json`, `channel_playlists_entries.json`, `channel_page_fetch_results.json`.
- 추가: `expanded_video_metadata.json`, 새 5편의 `watch_<id>.html` 및 `watch_<id>_metadata.json`.
- 주의: Python 터미널의 CP949 출력은 한국어가 깨져 보였지만, 최종 저장 파일은 HTTP bytes를 UTF-8로 해석하고 UTF-8로 저장했다. 원본과 최종 metadata 문자열의 한글을 검증했다.

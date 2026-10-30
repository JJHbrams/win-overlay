# Mia v02 절차적 얼굴 실험 — REJECTED

이 코드는 승인된 Mia 얼굴 제작 파이프라인이 아니다. Gaussian 기반 generic anatomy 편집, 수학적 얼굴 표면/CDT, smoothing과 접합을 반복했지만 원화 닮음과 안정적인 눈/귀 표면을 확보하지 못했다. 일반적인 VTuber 얼굴 제작 공정으로 설명하지 않는다.

원본과 실패 근거를 보존하기 위해 격리했다. 실제 시안·렌더는 `D:/ai/Mia3DWork/model-v02/anatomy/`에 있다. v5, v8, v12는 각각 216뷰를 만들었지만 얼굴 acceptance는 FAIL이었다. 최신 v15는 10개 확대 key view를 만든 실험으로, 과거 216뷰 결과를 최신 파일에 적용하지 않는다.

`model_v02_anatomy.py`의 체형 편집은 원본 Basis를 보존하고 가슴–허리–골반 형태 및 무릎 보정을 시험한 부분적 자료다. 얼굴·전체 캐릭터가 승인됐다는 뜻은 아니다. `model_v02_landmark_head.py`와 eye proof들은 후속 제작 기반으로 자동 선택하지 않는다.

후속 방향은 출처·권리가 확인된 anime 얼굴 기반의 표정용 topology를 유지하며, 눈·눈썹·속눈썹·texture·toon/normal·Shape Key를 함께 편집하는 것이다. 구조 QA와 작화 QA를 각각 수행하고 둘 다 확인한다. 분리된 얼굴 부품을 반드시 피부와 봉합하는 것을 요구하지 않는다.

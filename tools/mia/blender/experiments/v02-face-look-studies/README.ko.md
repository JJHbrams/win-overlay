# v02 얼굴 표면·표정 연구

이 폴더는 최종 Mia 얼굴이 아닌 제한된 실험이다.

- `apply_mia_face_look.py`: 실제 Skin UV 삼각형에 눈 밑 톤을 bake한다.
  neutral/blink 추종과 원본 UV·42개 표정 키 보존을 확인했다.
  다크서클 추가만으로 원화의 눈매·입매를 재현하지는 못했다.
- `probe_mia_eye_pose.py`: 원본 표정 키 조합의 실제 비교 렌더를 만든다.
- `refine_mia_face_art.py`: 기존 키만으로 관찰 표정을 시험했다.
  두꺼운 아이라인·높은 눈썹·작은 미소가 남아 작화 gate를 통과하지 못했다.
  proof 뒤 기본 표정 복원은 수정했으며 원본 메시를 바꾸지 않는다.

실제 native/PNG/report는 `D:/ai/Mia3DWork/model-v02/`의
face-look-stage, eye-pose-probe, face-art-stage에 보존했다. 이 중 일부는
역사적인 로컬 경로를 사용한다. 원화 기준은 저장소의
`mia-expression-style-confirmed-20261031.png`다.

이 실험의 데이터 보존·표정 재생 성공을 최종 얼굴 닮음의 승인으로
해석하지 않는다. 최종 작화는 눈꺼풀·눈썹·입의 실제 파트/재질 수정과
헤어를 포함한 여러 시점 검수로 별도 판단한다.

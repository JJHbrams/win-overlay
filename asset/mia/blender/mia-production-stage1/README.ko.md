# Mia Stage 1 — 전신 디자인 검토본

**기술 블록아웃 검증 완료 / ART NOTAPPROVED / 전체 캐릭터 INCOMPLETE.**

현재 파일은 `v11/Mia_Stage1_DesignReview.blend`다. 22개의 표시 메시로 머리/웨이브, 기존 braid, 하의/신발 디자인 표면과 새 crop·inner band·가디건·소매·끈·후면 가방·허리·목/복부 볼륨을 구성했다. 기존 native Face42/anatomy와 원본 디자인 표면은 숨김 보존한다. 승인 원화 두 장도 이미지로 내장했다.

`v11/report.json`은 출처·재사용/새 조형·미해결 사항을 기록한다. `v11/native-data-audit.json`은 저장 파일을 새 Blender에서 다시 열어 검사한 결과다. 7개의 source partition 전체에서 정점 좌표/UV 오차 0, 누락/중복 0, 원래 Face42 보존, active linked datablock 0 및 이미지 내장을 확인했다. raw GLB의 중복 삼각형 5/2개를 제외한 **Blender-imported face** 기준의 coverage다. original GLB/native 파일 SHA는 변하지 않았다.

## 남은 작업

- 눈/눈꺼풀/홍채와 표정의 원화 닮음, 손목/손, 의상 핏 정리.
- 머리/피부/헤어 경계와 production retopology. 현재 high-resolution 혼합 표면은 리깅용 완성 메시가 아니다.
- 최종 UV/텍스처, facial/body rig·수동 weight·corrective·허용 포즈 검사.
- 필요한 부위의 secondary motion, 공통 idle·전환·루프·30fps event 출력.

## 재현과 검수

1. `build_mia_design_blockout.py --output <absolute-output> --single <single-glb> --full <full-glb> --body-proxy <preserved-native>`를 background Blender에서 실행한다. 원본 경로/SHA는 Stage 0 및 workflow ledger 참조.
2. 생성 native를 열고 `finalize_mia_design_review.py -- <absolute-output>`로 승인 원화/상태를 내장한다.
3. `Mia_Stage1_DesignReview.blend`를 새 background Blender에서 열어 `verify_mia_design_blockout.py -- <absolute-output>`를 실행한다. 검사 스크립트는 모델을 저장하지 않는다.

앞선 v01–v10 실패/중간 조립은 로컬에 보존했다. 검증 기록은 최종 모델·아트·애니메이션 PASS로 재사용하지 않는다. Blender live viewer에는 원본 대신 검토용 사본을 게시했다.

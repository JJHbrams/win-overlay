# Mia layered foundation (INCOMPLETE)

이 디렉터리의 `Mia_LayeredFoundation_v01.blend`는 Mia 완성 모델이 아니다. 검증된 CC0 `Body Female - Stylized` 해부학 베이스를 별도 파일에 제한적으로 append한 재시작용 바탕이며, v45의 생성 메시·투영 텍스처·기하를 재사용하지 않는다.

현재 들어 있는 것은 `BodyHead_Master`, 기존 base eye geometry, 패킹된 승인 v22 참조 이미지, 그리고 스케일 가이드뿐이다. Hair, Garments, Bag, Hardware, RigGuide 컬렉션은 후속 소유 메시의 자리만 표시한 빈 계획 컬렉션이다. Mia 조형, 얼굴, 헤어, 의상, 가방, 하드웨어, 리그, corrective, 이벤트 애니메이션은 모두 미구현이다.

## 라이선스 범위

생성 스크립트는 Blender Human Base Meshes v1.4.1 번들 중 메타데이터가 CC0인 `Body Female - Stylized` 컬렉션만 append한다(저작자 메타데이터: Julien Kaspar). 번들에 함께 있는 Rain Rig의 CC-BY 텍스트는 다른 자산 범위이므로 이 foundation으로 import하지 않았다. 정확한 선택·토폴로지·해시는 `inventory.json`에 기록한다.

## 재현

```powershell
$blender = 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe'
& $blender --background --factory-startup --disable-autoexec --python tools/mia/blender/build_mia_layered_foundation.py -- `
  --source-bundle 'C:/Users/antio/.codex/visualizations/2026/10/29/01a1885c-8934-7af0-a487-a7f8d5981f65/mia-blender-source/human-base-meshes-v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend' `
  --reference-dir asset/mia/references `
  --output asset/mia/blender/mia-layered-foundation/Mia_LayeredFoundation_v01.blend `
  --report asset/mia/blender/mia-layered-foundation/inventory.json
```

원본 body는 의상 아래라는 이유만으로 삭제하거나 마스크하지 않는다. 실제 불투명 의상의 모든 허용 뷰·동작·그림자 커버리지가 검증된 뒤에만, 비파괴적인 outfit mask를 별도 검토할 수 있다. 앞머리는 보이는 이마·눈·관자놀이를 삭제할 근거가 아니다.

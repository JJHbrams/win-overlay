# Mia local 3D delivery provenance

This is a reproducible local draft record, not a production-asset approval. All model generation ran through native local ComfyUI Pixal3D/TRELLIS2 nodes on loopback; no image or asset was uploaded to a cloud service.

## Current draft inputs

- Body: `output/mia_pixal3d_mv512_tex2048_00001.glb` — SHA-256 `40EE1D976A20988E8959102A6EC053A892FD432B9D47ADF38322FBF562E55972` (14,797,208 bytes). Front/back MV, 512 geometry route, 2048 atlas.
- Selected original single-head source GLB: `output/mia_pixal_head512_tex2048_00001.glb` — SHA-256 `97D76C20E08D92B1E05079B9EC5D340683863A843F1D434A7DCD7C907FB34ADA`.
- Current projected-head draft: `projected_head/alternative_single/mia-head-v32-front-art-projected.blend` — SHA-256 `B2538334056F39E6F1E098198F4A9B1D06BB9E891272E06B41FAF791C42CB8FE`. Its geometry assertion is unchanged: 156,323 vertices / 198,513 polygons / geometry SHA `60e0eae70c73c29022a9202b91584298d91555a529739458668f908f6233461c` before and after projection.

Copy later for integration: the selected projected blend, the body GLB, and this record's companion [JSON](delivery_provenance.json). Use the D-artifact paths above; do not substitute the unselected v33/v34 head trials.

## Original source evidence

- A-pose front: `mia-rigging-apose-front-v30.png`, SHA-256 `63545F141A5CD86074BEC2A09CF66868223D8971B8D74E4A6A355704046794DA`.
- A-pose back: `mia-rigging-apose-back-v30.png`, SHA-256 `80DC674FC4E40901A190648CAF385E78C8DFCA6B3C718CC98A9E5921A45FFDEE`.
- A-pose side: `mia-rigging-apose-side-v30.png`, SHA-256 `356C805EEDE3720D86F7341FCD5DBD79B01215AF0F5FF6E7C5059059485AAFCB`.
- Source concept prompt: `mia-rigging-apose-front-prompt-v30.txt`, SHA-256 `BFB0562943D116D0E52DDAD1E64F4032C6D78661D7927D77AE6F5CD347DFBE8F`.

## Local native workflow

The bundled template was `3d_pixal3d_trellis2_image_to_model.json`. API graphs are retained at `pixal3d_mia_frontback_mv512_tex2048_api_prompt.json`, `pixal3d_mia_head512_tex2048_api_prompt.json`, and `pixal3d_mia_head_multiview512_tex2048_api_prompt.json`.

Generation used the 512 Pixal3D geometry route: structure VAE resolution 32, no 1536 cascade, remesh resolution 512, then 200,000-face midpoint decimation. Shape sampling used seed 42 / 20 Euler-normal steps / CFG 7.5; texture sampling used seed 43 / 12 Euler-normal steps / CFG 1. The body MV job was prompt `61b40a01-2c1f-466d-8f43-31d3d990d6c0` (97.40 s); the chosen single-head job was `3cceb12b-54cb-4224-91e5-3a620e98813e` (188.45 s).

The isolated server was `127.0.0.1:8197`, low-VRAM, 0.5 GB reserve, with custom/API nodes disabled and D: input/output/temp/user directories. It used embedded Python 3.13.14, Torch 2.13.0+cu130, CUDA on an RTX 3070 8 GB. Blender QA used 5.2.3 LTS.

## Preprocessing and projection

The body used alpha-aware `ImageCropToMask` 1024-square composites, black background, 1.1 padding and FOV 20°. The head used an original-pixel crop x=260, y=0, width=520, height=500, then the same native 1024 RGB/sRGB black-background compositing with 1.05 padding.

`projection_scripts/project_head_art.py` projects `projection_inputs/head_mv_condition_front.png` (SHA-256 `A3CE7C509B2432D0358A0B757475579D5E44472CB69F51ACF6B532C71847C7E8`) with canonical camera C=(0,-3.1192050007897403,0), forward +Y, right +X, up +Z, FOV 20°. It adds `UV_PROJ_FRONT` and `FaceProjectionWeight`, preserves original PBR albedo, and mixes packed original art only over bounded face/neck masks. Calibration is scale 1, zero offsets, strength 1. It does not create image planes or move geometry.

The MV head reference obeyed native slot orientation: front=0°, left=+90°, back=180°; the screen-left-facing profile was correctly sent to `left`, without mirroring.

## Weights and licenses

The exact model paths, byte sizes, SHA-256 values, and license observations are in [delivery_provenance.json](delivery_provenance.json). Public model-card checks during download reported MIT for Pixal3D, TRELLIS2, MoGe2, and BiRefNet. ComfyUI core is GPL-3.0. DINOv3's upstream license was not captured here and needs separate review before redistribution; do not interpret the MIT observations as a blanket license statement.

No paid API, cloud inference, API key, or upload of user art was used.

## Known fidelity limits

- Three-quarter bangs/fringe still obscure the eyes.
- Generated baking can duplicate or blur facial texture; the original-art projection only improves the bounded front face/neck region.
- Body hands/fingers remain fused or unsuitable for rigging.
- Cardigan/coat, rear bag, and accessories are inferred and may not match all source views.
- Geometry remains generated, unrigged draft topology. Retopology, seams, rigging, and production fidelity are unapproved.

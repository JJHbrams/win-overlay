# VRoid beta AvatarSample_4 - Victoria Rubin

The source is archived unchanged. An editable Face/Body duplicate may be adopted as Mia's anatomy basis; the original Hair and wardrobe are not adopted, and Mia likeness remains a separate quality gate.

## Source and checks

- Official guide: https://vroid.pixiv.help/hc/en-us/articles/360014900233
- Official Hub identity: https://hub.vroid.com/en/characters/2792872861023597723/models/5013769147837660446
- Public mirror: https://raw.githubusercontent.com/madjin/vrm-samples/master/vroid/beta/Victoria_Rubin.vrm
- Local file: D:/ai/Mia3DWork/anime-base-sources/Victoria_Rubin.vrm
- Size: 15,479,480 bytes
- SHA-256: b1372131bdbf233f46320146d565f342a7e4f6f4b8f2aefb301f1a283ec07e1e
- Git blob SHA-1: 3c59603eee2028756ed41ed4930dca6d99330f1e
- VRM title: Victoria Rubin; author/reference fields are empty
- VRM licenseName: CC0; allowedUserName=Everyone; commercial/violent/sexual usage are Allow in metadata

The official Hub identity and the empty native author field are kept distinct. The latest VRoid presets must not be assumed to have this sample's CC0 metadata.

## Structure confirmed

Direct GLB JSON inspection found 3 meshes, 16 materials, a 162-joint humanoid and 15 blendShapeGroups. The face has left/right blink, A/I/U/E/O mouth shapes, eye, brow and emotion morphs. The Blender import probe also packed MToon-related face, eye, lash, brow, mouth and hair textures.

Reference files:

- D:/ai/Mia3DWork/anime-base-sources/Victoria_Rubin.source.json
- D:/ai/Mia3DWork/anime-base-sources/Victoria_Rubin.inspect.json
- D:/ai/Mia3DWork/anime-base-sources/import-probe/Victoria_Rubin_imported.blend
- D:/ai/Mia3DWork/anime-base-sources/import-probe/inventory.json

## Blender import

The official VRM addon 4.10.3 package is copied to addon-runtime/io_scene_vrm. The companion script enables it in-memory with addon_utils.enable(..., persistent=False); it does not save preferences or install a global addon.

The imported Face/Body duplicate can serve as the editable anatomy basis. The original Hair and wardrobe remain reference-only; Mia likeness and all view/pose gates are still separate.

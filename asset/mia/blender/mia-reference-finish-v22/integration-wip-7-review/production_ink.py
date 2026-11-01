"""Small render-only contour layer, distinct from UV paint and viewport shading."""
import bpy


def configure_skin_ink(thickness=1.15):
    scene = bpy.context.scene
    scene.render.use_freestyle = True
    scene.render.line_thickness = 1
    coll = bpy.data.collections.get('MIA_REVIEW_SKIN_INK')
    if coll is None:
        coll = bpy.data.collections.new('MIA_REVIEW_SKIN_INK')
        scene.collection.children.link(coll)
    for name in ('MIA_V06_BODY_SKIN', 'MIA_V14_SculptedSkin'):
        obj = bpy.data.objects[name]
        if obj.name not in coll.objects:
            coll.objects.link(obj)
    fs = bpy.context.view_layer.freestyle_settings
    fs.mode = 'EDITOR'
    if hasattr(fs, 'use_smoothness'):
        fs.use_smoothness = True
    line = fs.linesets.get('MIA_V22_SkinContours') or fs.linesets.new('MIA_V22_SkinContours')
    # Leave unrelated line sets available, but disable their broad default selection.
    for other in fs.linesets:
        if other != line:
            other.show_render = False
    line.show_render = True
    line.select_by_collection = True
    line.collection = coll
    line.collection_negation = 'INCLUSIVE'
    line.select_by_edge_types = True
    line.select_by_visibility = True
    line.visibility = 'VISIBLE'
    for name in ('silhouette', 'border', 'crease', 'ridge_valley', 'suggestive_contour',
                 'material_boundary', 'edge_mark', 'external_contour', 'contour'):
        if hasattr(line, 'select_' + name):
            setattr(line, 'select_' + name, name == 'contour')
    style = line.linestyle
    style.color = (.018, .012, .014)
    style.alpha = .88
    style.thickness = thickness
    style.caps = 'ROUND'
    return {'technique': 'EEVEE camera render plus Freestyle visible skin object contours',
            'owners': [o.name for o in coll.objects], 'width_pixels': thickness,
            'color': list(style.color), 'alpha': style.alpha,
            'limits': 'Render pass only; viewport does not display these strokes. Internal silhouette selection rejected after nose bridge scratch artifacts. No crease or uniform seam selection. Animation stability untested.'}

"""Remove only the owned live trial actors and return original Main visibility."""
import json
import bpy
module=bpy.app.driver_namespace['MIA_RearPart01Module']
print(json.dumps(module.restore()))
del bpy.app.driver_namespace['MIA_RearPart01Module']

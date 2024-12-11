import bpy

bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'

#calling get_devices() first will populate the devices list
#otherwise the script might find it empty, even when compatible devices are present
bpy.context.preferences.addons['cycles'].preferences.get_devices()
bpy.context.preferences.addons['cycles'].preferences.devices[0].use = True
bpy.context.preferences.addons['cycles'].preferences.devices[2].use = True

bpy.context.scene.cycles.device = 'GPU'

#Use auto tile size to automatically set the tile size
#that better takes advantage of your GPU
bpy.ops.preferences.addon_enable(module="render_auto_tile_size")
bpy.context.scene.ats_settings.is_enabled = True

bpy.ops.render.render(animation=True)
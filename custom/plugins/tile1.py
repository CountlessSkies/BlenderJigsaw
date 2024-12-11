import bpy

render = bpy.context.scene.render

render.use_border = True
render.use_crop_to_border = True

render.border_min_x = 0.5
render.border_max_x = 1
render.border_min_y = 0
render.border_max_y = 0.5
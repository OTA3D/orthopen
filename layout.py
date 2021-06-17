import bpy


class Layout(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Layout Demo"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        # Large button
        layout.label(text="Simple operator")
        row = layout.row()
        row.scale_y = 3.0
        row.operator("object.simple_operator")

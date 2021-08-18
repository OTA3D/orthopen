import bpy

from . import operators

""" Setup layout for application
"""

TAB_NAME = "OrthOpen"


class PanelDefaults:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = TAB_NAME
    bl_options = {'DEFAULT_CLOSED'}

    @ classmethod
    def poll(cls, context):
        """
        Poll determines wether a control should be visible/enabled
        """
        return True


class COMMON_PT_panel(bpy.types.Panel, PanelDefaults):
    """
    Controls shown on top of UI that are always visible
    """
    bl_label = "This label is not visible"
    # This is what makes this visible all the time
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = True
        layout.label(text="Common controls")

        # Import button
        row = layout.row()
        row.scale_y = 1
        row.operator(operators.ORTHOPEN_OT_import_file.bl_idname)

        # Generate pad
        row = layout.row()
        row.scale_y = 1
        row.operator(operators.ORTHOPEN_OT_generate_pad.bl_idname)


class TAB_PT_foot_leg(bpy.types.Panel, PanelDefaults):
    bl_label = "Foot and leg"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = True

        layout.label(text="Adjust foot angle")
        row = layout.row()
        row.scale_y = 1.0
        row.operator(operators.ORTHOPEN_OT_set_foot_pivot.bl_idname)
        row = layout.row()
        row.scale_y = 1.0
        row.operator(operators.ORTHOPEN_OT_permanent_modifiers.bl_idname)

        layout.label(text="Prothesis cosmetics")
        row = layout.row()
        row.scale_y = 1.0
        row.operator(operators.ORTHOPEN_OT_leg_prosthesis_generate.bl_idname)

        layout.label(text="Foot splint")
        row = layout.row()
        row.scale_y = 1.0
        row.operator(operators.ORTHOPEN_OT_generate_toe_box.bl_idname)


class TAB_PT_help(bpy.types.Panel, PanelDefaults):
    bl_label = "Help"

    def draw(self, context):
        row = self.layout.row()
        row.operator("wm.url_open", text="Report an issue").url = "https://github.com/OTA3D/orthopen/issues"


classes = (
    COMMON_PT_panel,
    TAB_PT_foot_leg,
    TAB_PT_help,
)

register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()

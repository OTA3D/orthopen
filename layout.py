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

        # MeasureIt button      -- NO LONGER REQUIRED DUE TO NOT WORKING WITH OUR PURPOSE
        """ scene = context.scene
        box = layout.box()
        row = box.row()
        if context.window_manager.measureit_run_opengl is False:
            icon = 'PLAY'
            txt = 'Show measurements'
        else:
            icon = "PAUSE"
            txt = 'Hide measurements'

        row.operator("measureit.runopengl", text=txt, icon=icon) """


class TAB_PT_foot_leg(bpy.types.Panel, PanelDefaults):
    bl_label = "Foot and leg"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = True

        row = layout.row()
        row.scale_y = 1.0
        row.operator(operators.ORTHOPEN_OT_leg_prosthesis_mirror.bl_idname)
        row = layout.row()
        row.scale_y = 1.0
        row.operator(operators.ORTHOPEN_OT_model_transform_all.bl_idname)

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

        row = layout.row()
        row.scale_y = 1.0
        row.operator(operators.ORTHOPEN_OT_generate_foot_splint.bl_idname)

class TAB_PT_file_paths_asset_libraries(bpy.types.Panel, PanelDefaults):
    bl_label = "Asset Libraries"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        paths = context.preferences.filepaths

        box = layout.box()
        split = box.split(factor=0.35)
        name_col = split.column()
        path_col = split.column()

        row = name_col.row(align=True)  # Padding
        row.separator()
        row.label(text="Name")
        
        row = path_col.row(align=True)  # Padding
        row.separator()
        row.label(text="Path")

        for i, library in enumerate(paths.asset_libraries):
            row = name_col.row()
            row.alert = not library.name
            row.prop(library, "name", text="")

            row = path_col.row()
            subrow = row.row()
            subrow.alert = not library.path
            subrow.prop(library, "path", text="")
            row.operator("preferences.asset_library_remove", text="", icon='X', emboss=False).index = i

        row = box.row()
        row.alignment = 'RIGHT'
        #row.operator("preferences.asset_library_add", text="", icon='ADD', emboss=False)

        row = layout.row()
        row.scale_y = 1.0
        row.operator(operators.ORTHOPEN_OT_asset_library.bl_idname)

        """ row = layout.row()
        row.scale_y = 1.0
        row.operator(operators.ORTHOPEN_OT_asset_folders.bl_idname) """

class TAB_PT_help(bpy.types.Panel, PanelDefaults):
    bl_label = "Help"

    def draw(self, context):
        row = self.layout.row()
        row.operator("wm.url_open", text="Report an issue").url = "https://github.com/OTA3D/orthopen/issues"

        row = self.layout.row()
        row.operator("wm.url_open", text="User guide").url = "https://ota3d.github.io/orthopen/"


classes = (
    COMMON_PT_panel,
    TAB_PT_foot_leg,
    TAB_PT_help,
)

classes_3X = (
    COMMON_PT_panel,
    TAB_PT_foot_leg,
    TAB_PT_file_paths_asset_libraries,
    TAB_PT_help,
)

if (3, 0, 0) < bpy.app.version:
    register, unregister = bpy.utils.register_classes_factory(classes_3X)
else:
    register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()

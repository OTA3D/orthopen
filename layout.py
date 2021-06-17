import bpy

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


class COMMON_PT_Panel(bpy.types.Panel, PanelDefaults):
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
        row = layout.row()
        row.scale_y = 1

        # Import button
        row.operator("orthopen.import_file")


class TAB_PT_FootSplint(bpy.types.Panel, PanelDefaults):
    bl_label = "Footsplint"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = True

        # Big render button
        layout.label(text="Generate")
        row = layout.row()
        row.scale_y = 3.0
        row.operator("orthopen.foot_splint")


class TAB_PT_Prothesis(bpy.types.Panel, PanelDefaults):
    bl_label = "Prothesis"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = True


classes = (
    COMMON_PT_Panel,
    TAB_PT_FootSplint,
    TAB_PT_Prothesis
)

register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()

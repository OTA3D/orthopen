import bpy

""" Setup layout for application. The layout is basically tabs in the 
left side bar
"""

TAB_NAME = "OrthOpen"


class TabDefaults:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = TAB_NAME
    bl_options = {'DEFAULT_CLOSED'}


class ORTHOPEN_PT_FootSplint(bpy.types.Panel, TabDefaults):
    bl_label = "Footsplint"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = True

        # Big render button
        layout.label(text="Generate")
        row = layout.row()
        row.scale_y = 3.0
        row.operator("orthopen.foot_splint")


class ORTHOPEN_PT_Prothesis(bpy.types.Panel, TabDefaults):
    bl_label = "Prothesis"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = True


classes = (
    ORTHOPEN_PT_FootSplint,
    ORTHOPEN_PT_Prothesis
)

register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == "__main__":
    register()

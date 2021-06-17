import bpy


class ORTHOPEN_OT_FootSplint(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "orthopen.foot_splint"
    bl_label = "Generate"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        bpy.ops.mesh.primitive_monkey_add()
        return {'FINISHED'}


classes = (
    ORTHOPEN_OT_FootSplint,
)
register, unregister = bpy.utils.register_classes_factory(classes)


if __name__ == "__main__":
    register()

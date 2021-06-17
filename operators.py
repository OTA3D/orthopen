import bpy
import bpy_extras


class ORTHOPEN_OT_FootSplint(bpy.types.Operator):
    """
    To be implemented
    """
    bl_idname = "orthopen.foot_splint"
    bl_label = "Generate"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        bpy.ops.mesh.primitive_monkey_add()
        return {'FINISHED'}


class ORTHOPEN_OT_ImportFile(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """
    Opens a dialog for importing 3D scans
    """
    bl_idname = "orthopen.import_file"
    bl_label = "Import 3D scan"
    filter_glob: bpy.props.StringProperty(default='*.stl;*.STL', options={'HIDDEN'})

    def execute(self, context):
        bpy.ops.import_mesh.stl(filepath=self.filepath)
        print(f"Importing '{self.filepath}'")
        return {'FINISHED'}


classes = (
    ORTHOPEN_OT_ImportFile,
    ORTHOPEN_OT_FootSplint,
)
register, unregister = bpy.utils.register_classes_factory(classes)


if __name__ == "__main__":
    register()

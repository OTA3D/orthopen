import bpy
import bmesh
from bpy.types import POINTCLOUD_UL_attributes
import bpy_extras
import math
import mathutils
import numpy as np

from . import helpers


class ORTHOPEN_OT_FootSplint(bpy.types.Operator):
    """
    Generate a foot splint from a scanned foot. Select vertices to outline the footsplint first.
    """
    bl_idname = "orthopen.foot_splint"
    bl_label = "Generate"

    @classmethod
    def poll(cls, context):
        return bpy.context.active_object.data.total_vert_sel > 2

    def execute(self, context):

        # We need to switch from 'Edit mode' to 'Object mode' so the selection gets updated
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')

        # Extract selected points in the X-Z plane, sorted in in Z direction (from foot to knee)
        mesh = bmesh.from_edit_mesh(bpy.context.active_object.data)
        selected_verts = [(v.co.x, v.co.z) for v in mesh.verts if v.select]
        selected_verts.sort(key=lambda point: point[1])

        # Add vertices that will circumvent the left side of foot (heel and backwards). Now we have
        # polygon that outlines the vertice to be selected
        x_min = -10000
        selected_verts = [(x_min, selected_verts[0][1])] + selected_verts + [(x_min, selected_verts[-1][1])]

        for v in mesh.verts:
            v.select = helpers.inside_polygon(point=(v.co.x, v.co.z), polygon=selected_verts)

        bmesh.update_edit_mesh(bpy.context.active_object.data)
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
        # TODO: Rotate the leg
        # TODO: Flip to X-Z view
        return {'FINISHED'}


classes = (
    ORTHOPEN_OT_ImportFile,
    ORTHOPEN_OT_FootSplint,
)
register, unregister = bpy.utils.register_classes_factory(classes)


if __name__ == "__main__":
    register()

import copy
import math

import bmesh
import bpy
import bpy_extras
import mathutils
import numpy as np

from . import helpers

# If a bpy.types.Object contains this key, we know it is a scan we imported
_KEY_IMPORTED_SCAN = "imported_3d_scan"

# Key to identify armature managed by this add-on
_KEY_MANAGED_ARMATURE = "managed_armature"


def _clear_managed_armature(object: bpy.types.Object):
    """
    Identify and remove managed (automatically generated) armature attached to object
    """
    if object.parent is not None:
        if _KEY_MANAGED_ARMATURE in object.parent.keys():
            bpy.data.objects.remove(object.parent, do_unlink=True)


class ORTHOPEN_OT_permanent_modifiers(bpy.types.Operator):
    """
    Permanently apply modifiers (e.g. changed foot angle) to the selected object. Will
    try to automtically find relevant objects if no object is selected.
    """
    bl_idname = helpers.mangle_operator_name(__qualname__)
    bl_label = "Apply changes"

    @classmethod
    def poll(cls, context):
        try:
            return bpy.context.object.mode != 'EDIT'
        except AttributeError:
            return False

    def execute(self, context):
        # This is an original object, without modifiers, or an object without a mesh such as a bone
        if context.active_object is None or context.active_object.type != 'MESH':
            objects_to_permanent = [o for o in bpy.data.objects if _KEY_IMPORTED_SCAN in o.keys()]

            if(len(objects_to_permanent) == 0):
                self.report({'INFO'}, "Could not find a relevant object to permanent")
                return {'CANCELLED'}
        else:
            objects_to_permanent = [context.active_object]

        self.report(
            {'INFO'},
            f"Will permanently apply modifiers to '{','.join([o.name for o in objects_to_permanent])}'")

        # Apply all modifiers, such as ankle angle changed by bones
        # See: https://docs.blender.org/api/current/bpy.types.Depsgraph.html
        depedency_graph = bpy.context.evaluated_depsgraph_get()

        for object in objects_to_permanent:
            # Overwrite the old mesh with the mesh from modifiers
            object.data = bpy.data.meshes.new_from_object(object.evaluated_get(depedency_graph))

            # The modifiers are already applied implicitly now, so keeping them would apply them twice
            object.modifiers.clear()

            # If we tagged the parent, is likely an foot adjustment armature that will not work after the
            # modifiers are cleared, and it will probably only be confusing to a user to keep it
            _clear_managed_armature(object)

        context.collection.objects.update()

        return {'FINISHED'}


class ORTHOPEN_OT_set_foot_pivot(bpy.types.Operator):
    """
    When in edit mode, mark a vertex that will set a pivot point around which the foot angle can be adjusted.
    """
    bl_idname = helpers.mangle_operator_name(__qualname__)
    bl_label = "Set pivot point"

    # Used to keep track of the foot vertex group
    _FOOT_VERTEX_ID = "foot"

    @classmethod
    def poll(cls, context):
        try:
            return bpy.context.active_object.data.total_vert_sel == 1
        except AttributeError:
            return False

    def execute(self, context):
        # We need to switch from 'Edit mode' to 'Object mode' so the selection gets updated
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')

        for vertex_group in (context.active_object.vertex_groups):
            if self._FOOT_VERTEX_ID in vertex_group.name:
                context.active_object.vertex_groups.remove(vertex_group)

        foot = context.active_object.vertex_groups.new(name=self._FOOT_VERTEX_ID)

        # The foot will be rotated around the ankle, which we have asked the user to mark
        selected_verts = [v.co for v in bpy.context.active_object.data.vertices if v.select]
        assert len(selected_verts) == 1, "Only one vertex can be selected"
        ankle_point = copy.deepcopy(selected_verts[0])  # Deep copy here is important!

        self._weight_paint(foot, ankle_point)

        _clear_managed_armature(context.active_object)
        self._add_armature(ankle_point, foot.name)

        # The user probably wants to adjust the foot angle now and that has to be done in pose mode
        bpy.ops.object.mode_set(mode='POSE')

        return {'FINISHED'}

    def _weight_paint(self, foot: bpy.types.VertexGroup, ankle_point: mathutils.Vector):
        """
        Add weight paint to the foot vertex group.
        The weight paint defines how the mesh will deform when coupled with an armature.
        """
        bpy.ops.object.mode_set(mode='OBJECT')
        for vertex in bpy.context.active_object.data.vertices:
            def extract_xz(vector): return mathutils.Vector((vector.x, 0, vector.z))
            diff_from_ankle = (extract_xz(vertex.co) - extract_xz(ankle_point))

            X_LIM, Z_LIM = (0.06, 0.05)
            RADIUS = 0.15

            # Basically a circle around the ankle and then a box. It is imperative
            # that the mesh is properly aligned, i.e. toes in the X direction
            if diff_from_ankle.z > Z_LIM:
                weight = 0
            elif diff_from_ankle.x > X_LIM:
                weight = 1
            else:
                weight = 1 - (diff_from_ankle.length / RADIUS)**2

            foot.add(index=[vertex.index], weight=np.clip(weight, 0, 1), type='REPLACE')

    def _add_armature(self, ankle_point: mathutils.Vector, foot_name: str):
        """
        The armature is what enables us to rotate the foot around the ankle.
        """
        leg_name = bpy.context.active_object.name

        # Add a bone to the foot, keep track that this is something auto-generated
        old_objects = set(bpy.data.objects)
        bpy.ops.object.armature_add(enter_editmode=False,
                                    align='VIEW',
                                    location=bpy.context.active_object.matrix_world @ ankle_point,
                                    rotation=(0, math.degrees(70), 0))
        (list(set(bpy.data.objects) - old_objects))[0][_KEY_MANAGED_ARMATURE] = True

        armature_name = bpy.context.active_object.name
        bpy.data.objects[armature_name].scale = (0.1, 0.1, 0.1)

        # A bone is linked to a vertex group by having the same name
        assert len(bpy.data.objects[armature_name].data.bones) == 1
        bpy.data.objects[armature_name].data.bones[0].name = foot_name

        # Parenting the leg to the bone. Order of selection is imperative
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[armature_name].select_set(True)
        bpy.data.objects[leg_name].select_set(True)
        bpy.ops.object.parent_set(type='ARMATURE')

        # User is probably more interested in the armature at this point
        bpy.data.objects[leg_name].select_set(False)


class ORTHOPEN_OT_foot_splint(bpy.types.Operator):
    """
    Generate a foot splint from a scanned foot. Select vertices that should outline the footsplint first.
    """
    bl_idname = helpers.mangle_operator_name(__qualname__)
    bl_label = "Generate"

    @ classmethod
    def poll(cls, context):
        try:
            return bpy.context.active_object.data.total_vert_sel > 2
        except AttributeError:
            return False

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


class ORTHOPEN_OT_import_file(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """
    Opens a dialog for importing 3D scans. Use this instead of Blenders
    own import function, as this also does some important work behing the scenes.
    """
    bl_idname = helpers.mangle_operator_name(__qualname__)
    bl_label = "Import 3D scan"
    filter_glob: bpy.props.StringProperty(default='*.stl;*.STL', options={'HIDDEN'})

    def execute(self, context):
        # Import using a file opening dialog
        old_objects = set(context.scene.objects)
        bpy.ops.import_mesh.stl(filepath=self.filepath)
        print(f"Importing '{self.filepath}'")

        # Keep track of what objects we have imported
        imported_objects = set(context.scene.objects) - old_objects
        for object in imported_objects:
            object[_KEY_IMPORTED_SCAN] = True

        # TODO: Rotate the leg
        helpers.set_view_to_xz()
        return {'FINISHED'}


classes = (
    ORTHOPEN_OT_set_foot_pivot,
    ORTHOPEN_OT_permanent_modifiers,
    ORTHOPEN_OT_import_file,
    ORTHOPEN_OT_foot_splint,
)
register, unregister = bpy.utils.register_classes_factory(classes)


if __name__ == "__main__":
    register()

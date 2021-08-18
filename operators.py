import copy
import math
from pathlib import Path

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

    for modifier in object.modifiers:
        try:
            # The armature modifier is tied to an armature object
            if _KEY_MANAGED_ARMATURE in modifier.object.keys():
                object.modifiers.remove(modifier)
        except AttributeError:
            pass

    # Now remove the armature itself
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

        # Apply all modifiers, such as ankle angle changed by bones
        # See: https://docs.blender.org/api/current/bpy.types.Depsgraph.html
        depedency_graph = bpy.context.evaluated_depsgraph_get()

        for object in objects_to_permanent:
            # Overwrite the old mesh with the mesh from modifiers
            object.data = bpy.data.meshes.new_from_object(object.evaluated_get(depedency_graph))

            # If we tagged the parent, is likely an foot adjustment armature that will not work after the
            # modifiers are cleared, and it will probably only be confusing to a user to keep it
            _clear_managed_armature(object)

            # The modifiers are already applied implicitly now, so keeping them would apply them twice
            object.modifiers.clear()

        context.collection.objects.update()

        self.report(
            {'INFO'},
            f"Permanently applied modifiers to '{','.join([o.name for o in objects_to_permanent])}'")

        return {'FINISHED'}


class ORTHOPEN_OT_set_foot_pivot(bpy.types.Operator):
    """
    When in edit mode, mark a vertex that will set a pivot point around which the foot angle can be adjusted.
    """
    bl_idname = helpers.mangle_operator_name(__qualname__)
    bl_label = "Set pivot point"

    # Used to identify anything auto-generated by name. For bpy.types.Object we can use a hidden property,
    # however we do not have that option for modifiers, vertexgroups etc
    _FOOT_AUTOGEN_ID = "foot_auto_gen"

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

        leg = context.active_object

        # Identify the foot by a vertex group. First remove any
        # previously generated vertex groups
        for vertex_group in (leg.vertex_groups):
            if self._FOOT_AUTOGEN_ID in vertex_group.name:
                leg.vertex_groups.remove(vertex_group)
        foot = leg.vertex_groups.new(name=self._FOOT_AUTOGEN_ID)

        # The foot will be rotated around the ankle, which we have asked the user to mark
        selected_verts = [v.co for v in leg.data.vertices if v.select]
        assert len(selected_verts) == 1, "Only one vertex can be selected"
        ankle_point = copy.deepcopy(selected_verts[0])  # Deep copy here is important!

        self._weight_paint(foot, ankle_point)

        _clear_managed_armature(leg)
        armature = self._add_armature(ankle_point, foot.name)

        # Remove previous modifiers
        for modifier in leg.modifiers:
            if self._FOOT_AUTOGEN_ID in modifier.name:
                leg.modifiers.remove(modifier)

        # This might be the most important aspect for getting a realistic angle adjustment
        corrective_smooth = leg.modifiers.new(name=self._FOOT_AUTOGEN_ID, type="CORRECTIVE_SMOOTH")
        corrective_smooth.factor = 1
        corrective_smooth.iterations = 80

        # Select armature, this is probably what the user is interested in now
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        armature.select_set(True)

        # The user probably wants to adjust the foot angle now and that has to be done in pose mode
        bpy.ops.object.mode_set(mode='POSE')

        return {'FINISHED'}

    def _weight_paint(self, foot: bpy.types.VertexGroup, ankle_point: mathutils.Vector):
        """
        Add weight paint to the foot vertex group.
        The weight paint defines how the mesh will deform when coupled with an armature.
        """
        bpy.ops.object.mode_set(mode='OBJECT')

        # Set the default weight to zero
        foot.add(index=[v.index for v in bpy.context.active_object.data.vertices], weight=0, type='REPLACE')

        for vertex in bpy.context.active_object.data.vertices:
            diff_from_ankle = vertex.co - ankle_point

            if diff_from_ankle.z >= 0:
                # Create a deformation zone with linearly decreasing weight from 1 to 0 above the ankle
                DEFORM_ZONE = 0.02
                weight = np.clip(1 - diff_from_ankle.z / DEFORM_ZONE, 0, 1)
            else:
                # Move everyting below the ankle as a solid object
                weight = 1

            foot.add(index=[vertex.index], weight=weight, type='REPLACE')

    def _add_armature(self, ankle_point: mathutils.Vector, foot_name: str):
        """
        The armature is what enables us to rotate the foot around the ankle.
        """
        leg_name = bpy.context.active_object.name

        # Place the armature in the middle of the joint
        LEG_THICKNESS = 0.08
        position = mathutils.Vector((ankle_point.x, ankle_point.y + LEG_THICKNESS / 2, ankle_point.z))

        # Add a bone to the foot, keep track that this is something auto-generated
        old_objects = set(bpy.data.objects)
        bpy.ops.object.armature_add(enter_editmode=False,
                                    align='VIEW',
                                    location=bpy.context.active_object.matrix_world @ position,
                                    rotation=(0, math.radians(-90), 0))
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

        return bpy.data.objects[armature_name]


class ORTHOPEN_OT_leg_prosthesis_generate(bpy.types.Operator):
    """
    Generate a proposal for leg prosthesis cosmetics
    """
    bl_idname = helpers.mangle_operator_name(__qualname__)
    bl_label = "Generate cosmetics"

    set_max_circumference: bpy.props.FloatProperty(
        name="Calf circumference (max)",
        description="The largest circumference around the calf",
        unit="LENGTH",
        default=0.35)

    set_height: bpy.props.FloatProperty(name="Cosmetics total height",
                                        description="The extent of the cosmetics, "
                                        "from top to bottom",
                                        unit="LENGTH",
                                        default=0.2)

    set_clip_position_z: bpy.props.FloatProperty(name="Clip start height",
                                                 description="The center point of the fastening clip measured relative to"
                                                 " the lowest point of the prosthesis cosmetics",
                                                 unit="LENGTH",
                                                 default=0.1)

    use_interactive_placement: bpy.props.BoolProperty(name="Interactive clip placement",
                                                      description="After clicking 'OK' below, click a point on the prosthesis tube where"
                                                      " the fastening clip should be placed",
                                                      default=True)

    @ classmethod
    def poll(cls, context):
        try:
            return bpy.context.object.mode == 'OBJECT'
        except AttributeError:
            return False

    def execute(self, context):
        if self.use_interactive_placement:
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

        self._main()
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def modal(self, context, event):
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # Allow navigation
            return {'PASS_THROUGH'}
        elif event.type == 'LEFTMOUSE':
            clamp_origin = self._determine_clamp_origin(mouse_coords=(event.mouse_region_x, event.mouse_region_y))
            if clamp_origin is None:
                self.report(
                    {'INFO'},
                    "Could not find a tube for the fastening clamp. Will place prosthesis at default location.")
            self._main(clamp_origin)
            return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def _main(self, set_clamp_origin=None):
        cosmetics_main, fastening_clip = self._import_from_assets_folder()

        # The bounding box is defined in object coordinates, and defines the mesh size with no scale applied
        cosmetics_main_mesh_size = np.amax(np.array(cosmetics_main.bound_box), axis=0) - \
            np.amin(np.array(cosmetics_main.bound_box), axis=0)

        # Approximate the calf as as perfectly circular, and set the target bounding box
        # to a square that would circumvent this circle
        x_y_target_size = self.set_max_circumference / np.pi

        # The calf is a half circle along the X-axis, so halve that measurement
        cosmetics_main_target_scale = np.array([x_y_target_size / 2, x_y_target_size, self.set_height])\
            / cosmetics_main_mesh_size

        if set_clamp_origin is None:
            set_clamp_origin = np.array(fastening_clip.matrix_world.translation)
        fastening_clip.matrix_world.translation = mathutils.Vector(list(set_clamp_origin))

        # This is true if the body is not rotated, and no modifiers are applied
        cosmetics_main_origin_to_z_min = (np.amin(np.array(cosmetics_main.bound_box), axis=0))[2]\
            * cosmetics_main_target_scale[2]

        # Set the position of cosmetics main according to the user inputs. Other parts are parented and follow along
        cosmetics_main_translation = set_clamp_origin + \
            np.array([0, 0, -self.set_clip_position_z - cosmetics_main_origin_to_z_min])

        # By setting scale and position directly in matrix_world "atomically" there is less risk of
        # any of these properties getting lost between Blenders internal update cycles
        mat = np.eye(4)
        mat[:3, :3] = np.diag(cosmetics_main_target_scale)
        mat[:3, 3] = cosmetics_main_translation
        cosmetics_main.matrix_world = mathutils.Matrix(list(mat))

        # UI updates
        bpy.ops.object.select_all(action="DESELECT")
        cosmetics_main.select_set(True)
        helpers.set_view_to_xz()

    def _determine_clamp_origin(self, mouse_coords):
        """
        Determine an origin of the fastening clamp based on current mouse coordinates. This
        origin should make the clamp align well with the prosthesis tube.
        """
        ray = helpers.mouse_ray_cast(bpy.context, mouse_coords=mouse_coords)

        if ray.intersection_point is None:
            return None

        # Convert from object to world coordinates
        intersection_world = ray.object.matrix_world @ ray.intersection_point
        vertices_world = np.array([[v.co.x, v.co.y, v.co.z, 1]
                                   for v in ray.object.data.vertices]) @ np.array(list(ray.object.matrix_world)).T

        # Assume the prosthesis tube is perfectly cylindrical and parallel to the world Z-axis. Select
        # vertices symmetrically around the ray cast intersection.
        squared_distances_z = (vertices_world[:, 2] - intersection_world[2])**2
        Z_SELECTION_METERS = 0.015
        selected_vertices = vertices_world[squared_distances_z < Z_SELECTION_METERS**2, :3]

        # Likely to happen for a tube created in blender, these have few vertices along their length per default
        MINIMUM_VERTICES_FOR_VALID_RESULT = 5
        if selected_vertices.shape[0] < MINIMUM_VERTICES_FOR_VALID_RESULT:
            return None

        # This should be the center point of a vertical tube section
        return np.mean(selected_vertices, axis=0)

    def _import_from_assets_folder(self):
        assets = helpers.load_assets(filename="leg_prosthesis.blend", names=["clip", "cosmetics_main"])

        # In following code, it is assumed that these objects are not rotated
        def not_rotated(object): return np.linalg.norm(np.array(object.matrix_world.to_quaternion()) -
                                                       np.array(mathutils.Quaternion())) < 1.E-7
        assert not_rotated(assets["cosmetics_main"]) and not_rotated(
            assets["clip"]), "Parts in '{FILE_PATH}' must not be rotated prior to import"

        return assets["cosmetics_main"], assets["clip"]


class ORTHOPEN_OT_generate_pad(bpy.types.Operator):
    """
    Interactively generate a pad that sticks to surfaces. Hover the object where it should be centered and click left mouse button.
    Can be used e.g. for ensuring clearance between an ankle and a foot splint.
    """
    bl_idname = helpers.mangle_operator_name(__qualname__)
    bl_label = "Generate pad"

    @ classmethod
    def poll(cls, context):
        try:
            return bpy.context.object.mode == 'OBJECT'
        except AttributeError:
            return False

    def invoke(self, context, event):
        self.pad = (helpers.load_assets(filename="pad.blend", names=["pad"]))["pad"]

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # Allow navigation
            return {'PASS_THROUGH'}
        elif event.type in {'MOUSEMOVE'}:
            ray = helpers.mouse_ray_cast(
                bpy.context, (event.mouse_region_x, event.mouse_region_y), ignore=[self.pad.name])
            if ray.object is None:
                return {'RUNNING_MODAL'}

            # Snap pad at surface normal when the user moves the cursor around
            self.pad.matrix_world.translation = ray.object.matrix_world @ ray.intersection_point
            self.pad.rotation_mode = 'QUATERNION'
            self.pad.rotation_quaternion = ray.face_normal.to_track_quat('Z', 'Y')

            return {'RUNNING_MODAL'}

        elif event.type == 'LEFTMOUSE':
            # See if there is an object in front of the mouse cursor
            ray = helpers.mouse_ray_cast(
                bpy.context, (event.mouse_region_x, event.mouse_region_y), ignore=[
                    self.pad.name])
            if (ray.object is None):
                self.report({'INFO'}, "No object found in front of mouse cursor")
                return {'RUNNING_MODAL'}

            # This will make the pad wrap to surfaces
            for modifier in self.pad.modifiers:
                if modifier.type == "SHRINKWRAP":
                    modifier.target = ray.object

            # These tool settings will make the pad "hover" above the target surface.
            bpy.context.scene.tool_settings.use_snap = True
            bpy.context.scene.tool_settings.snap_elements = {'FACE'}
            bpy.context.scene.tool_settings.snap_target = 'CENTER'
            bpy.context.scene.tool_settings.use_snap_align_rotation = True

            return {'FINISHED'}
        if event.type == 'MOUSEMOVE':
            return {'PASS_THROUGH'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}


class ORTHOPEN_OT_generate_toe_box(bpy.types.Operator):
    """
    Generate a box around the toes. Used to ensure clearence between toes and the foot splint. Click
    around the toes to place it.
    """
    bl_idname = helpers.mangle_operator_name(__qualname__)
    bl_label = "Generate toe box"

    @ classmethod
    def poll(cls, context):
        try:
            return bpy.context.object.mode == 'OBJECT'
        except AttributeError:
            return False

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # Allow navigation
            return {'PASS_THROUGH'}
        elif event.type == 'LEFTMOUSE':
            # See if there is an object in front of the mouse cursor
            toes = helpers.mouse_ray_cast(bpy.context, (event.mouse_region_x, event.mouse_region_y))
            if toes.object is None:
                self.report({'INFO'}, "No object found in front of mouse cursor")
                return {'RUNNING_MODAL'}

            self._main(toes)
            return {'FINISHED'}
        if event.type == 'MOUSEMOVE':
            return {'PASS_THROUGH'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def _main(self, toes):
        toe_box = (helpers.load_assets(filename="toe_box.blend", names=["toe_box"]))["toe_box"]

        # The toes point in the x direction, so we easily find the toes by selecting all vertices
        # a bit behind the largest x coordinate.
        all_vertices = np.array([(v.co.x, v.co.y, v.co.z) for v in toes.object.data.vertices])
        SEL_RANGE_X = 0.09
        sel = all_vertices[:, 0] > (np.amax(all_vertices[:, 0]) - SEL_RANGE_X)
        toe_vertices = all_vertices[sel, :]

        toe_size = np.amax(toe_vertices, axis=0) - np.amin(toe_vertices, axis=0)
        toe_box_size = np.amax(np.array(toe_box.bound_box), axis=0) - np.amin(np.array(toe_box.bound_box), axis=0)

        # Largest x coordinate of object
        def x_max_world(object): return (np.amax(helpers.bound_box_world(object), axis=0))[0]

        # Assume the length of the toe box is fine, and scale up the Y and Z directions
        target_scale = np.array([1, toe_size[1] / toe_box_size[1], toe_size[2] / toe_box_size[2]])

        # Place toe box at center of toes, with the closed end a little bit in front of the toes
        target_position = np.array(toes.object.matrix_world) @ np.hstack([np.mean(toe_vertices, axis=0), 1])
        OFFSET_IN_FRONT_OF_TOES = 0.02
        target_position[0] = x_max_world(toes.object) - (x_max_world(toe_box) -
                                                         toe_box.matrix_world.translation[0]) + OFFSET_IN_FRONT_OF_TOES

        # Compose homog. transformation matrix
        mat = np.eye(4)
        mat[:3, :3] = np.diag(target_scale)
        mat[:, 3] = target_position
        toe_box.matrix_world = mathutils.Matrix(list(mat))

        # This will make the pad wrap to surfaces
        for modifier in toe_box.modifiers:
            if modifier.type == "SHRINKWRAP":
                modifier.target = toes.object


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
    ORTHOPEN_OT_generate_pad,
    ORTHOPEN_OT_generate_toe_box,
    ORTHOPEN_OT_import_file,
    ORTHOPEN_OT_leg_prosthesis_generate,
    ORTHOPEN_OT_permanent_modifiers,
    ORTHOPEN_OT_set_foot_pivot,
)
register, unregister = bpy.utils.register_classes_factory(classes)


if __name__ == "__main__":
    register()

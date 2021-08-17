"""
Functions that were needed but couldn't be found in Blender or numpy.
It is a bit awkward to install packages in Blender, so we avoid that.
"""
from collections import namedtuple
import math
from pathlib import Path

import bpy
from bpy_extras import view3d_utils
import mathutils
import numpy as np


def mangle_operator_name(class_name: str):
    """
    Blender does not use the class name directly to register operators but instead uses a complementary field
    "bl_idname" which can be different from the class name. To facilitate refactor and maintenance, the "bl_idname" field
    for all operators should be set using this function which output automatically complies to the naming rules:
    https://b3d.interplanety.org/en/class-naming-conventions-in-blender-2-8-python-api/

    Args:
        class_name (str): Class name, complying to Blender conventions. Hint: __qualname__ gives
        class name without the need to instantiate an object first

    Returns:
        str : Mangled name

      >>> mangle_operator_name("MYMODULE_OT_My_Operator")
    mymodule.my_operator
    """
    class_name_list = class_name.split("_")
    if "OT" in class_name_list:
        return class_name_list[0].lower() + "." + (class_name.split("OT_"))[-1].lower()
    else:
        raise ValueError("Only use this for operators, all other 'bl_idname' fields are set automatically")


def mouse_ray_cast(context: bpy.types.Context, mouse_coords):
    """
    Find the object that appears to be in front of the mouse cursor.

    Based on template 'Operator Modal View3D raycast'

    Args:
        context (bpy.types.Context): Current windowmanager context
        mouse_coords (tuple): Current mouse cursor position

    Returns:
        namedtuple: Data on the intersection, intersection_point is in object coordinates. All fields 'None' at no intersection.
    """
    # Get the ray from the viewport and mouse
    RayCastResult = namedtuple('RayCastResult', ['object', 'intersection_point', 'face_normal', 'face_index'])

    view_vector = view3d_utils.region_2d_to_vector_3d(context.region, context.region_data, mouse_coords)
    ray_origin_world = view3d_utils.region_2d_to_origin_3d(context.region, context.region_data, mouse_coords)
    ray_target_world = ray_origin_world + view_vector

    # Loop through all objects, cast the same ray, and see if the ray intersects the object
    best_length_squared = -1.0
    best_obj_data = RayCastResult(None, None, None, None)
    for object in context.evaluated_depsgraph_get().object_instances:
        # We have to treat instances and copies a bit differently
        if object.is_instance:
            obj, matrix_world = (object.instance_object, object.matrix_world.copy())
        else:
            obj, matrix_world = (object.object, object.object.matrix_world.copy())

        if obj.type == 'MESH':
            # Rays are cast in the object coordinate system, so we need to transform these vectors
            ray_origin_obj = matrix_world.inverted() @ ray_origin_world
            ray_target_obj = matrix_world.inverted() @ ray_target_world

            ray_direction_obj = ray_target_obj - ray_origin_obj
            hit, intersection_point, normal, index = obj.ray_cast(ray_origin_obj, ray_direction_obj)

            if hit:
                length_squared = (intersection_point - ray_origin_obj).length_squared
                # TODO(parlove@paxec.se): This criteria is not great, we sometimes
                # get objects not perceived to be directly in front of the mouse pointer
                if best_obj_data.object is None or length_squared < best_length_squared:
                    best_obj_data = RayCastResult(object=obj, intersection_point=intersection_point,
                                                  face_normal=normal, face_index=index)
                    best_length_squared = length_squared

    return best_obj_data


def set_view_to_xz():
    """
    Rotate viewport to show the X-Z plane (front orthographic), and set view to current object
    """
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            # Rotate so the Z axis points upwards (Y upwards, X rightwards is an identity rotation here)
            area.spaces.active.region_3d.view_matrix = mathutils.Matrix.Rotation(math.radians(-90), 4, 'X')

            # "Zoom" to the selected object
            bpy.ops.view3d.view_selected()

            # Set view to front orthograpic
            override = bpy.context.copy()
            override['area'] = area
            bpy.ops.view3d.view_axis(override, type='FRONT')


def object_size(object: bpy.types.Object):
    """
    Calculate the size of an object.

    Args:
        object (bpy.types.Object): Blender object

    Returns:
        np.array: Size in x,y,z direction
    """

    diff = np.amax(np.array(object.bound_box), axis=0) -\
        np.amin(np.array(object.bound_box), axis=0)

    # The bounding box has to be scaled
    return diff * np.array(object.scale)


def load_assets(filename: str, names: list) -> dict:
    """
    Import all assets from a *.blend file in the assets folder.

    Args:
        filename (str): Name of the *.blend file
        names (list): All objects in the assets file that are of special interest.
                      An explicit check is made to check that these objects are present

    Returns:
        assets (dict of str: bpy.types.Object):  Dictionary with the objects specified in names argument
    """
    # Import objects from file with assets
    FILE_PATH = Path(__file__).parent.joinpath("assets", filename)

    with bpy.data.libraries.load(str(FILE_PATH)) as (data_from, data_to):
        # Here .objects are strings, but then the "with" context is exited
        # they will be replaced by corresponding real objects
        data_to.objects = data_from.objects

    # Link objects to scene and save a reference
    assets = dict()
    for obj in data_to.objects:
        # Blender might already have renamed my_asset --> my_asset_001 etc, due to duplicates so we
        # cannot identify the assets by name directly
        for original_name in names:
            if original_name in obj.name:
                assets[original_name] = obj
        bpy.context.scene.collection.objects.link(obj)

    # Make sure we got it all
    missing_assets = [x for x in names if x not in assets.keys()]
    assert len(missing_assets) == 0, f"Sought assets '{missing_assets}' not found in '{FILE_PATH}'"

    return assets


def bound_box_world(object: bpy.types.Object):
    """
    Get the object bounding box in world coordinates. Note that this
    does not account for any modifiers applied.

    Args:
        object (bpy.types.Object): Blender object

    Returns:
        np.array: Corners of bounding box in world coordinates
    """
    # Row vectors, augmented with 1 as a column vector
    bound_box_augmented = np.hstack([np.array(object.bound_box), np.ones([8, 1])])

    # For order of multiplication, remember (A * B)^T = B^T * A^T
    return (bound_box_augmented @ np.array(object.matrix_world).T)[:, :3]

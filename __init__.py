bl_info = {
    "name": "Simple operator",
    "author": "",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh > New Object",
    "description": "Initial test",
    "warning": "",
    "doc_url": "",
    "category": "Add Mesh",
}

import bpy  # noqa
from . import simple_operator  # noqa
from . import layout  # noqa


def register():
    bpy.utils.register_class(layout.Layout)
    bpy.utils.register_class(simple_operator.SimpleOperator)


def unregister():
    bpy.utils.unregister_class(layout.Layout)
    bpy.utils.unregister_class(simple_operator.SimpleOperator)

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
from . import operators  # noqa
from . import layout  # noqa


def register():
    layout.register()
    operators.register()


def unregister():
    layout.unregister()
    operators.unregister()

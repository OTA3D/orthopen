bl_info = {
    "name": "OrthOpen",
    "author": "",
    "version": (0, 2),
    "blender": (2, 93, 0),
    "location": "View3D->Sidebar",
    "description": "Tools for facilitating the design of orthopaedic aids.",
    "warning": "This is a beta version",
    "doc_url": "https://github.com/OTA3D/orthopen",
    "category": "Object",
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

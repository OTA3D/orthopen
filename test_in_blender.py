"""
Unitests that are run from within Blender. Use for e.g. testing file import functions

Run as follows: blender --background -noaudio --python ./test_in_blender.py -- --verbose

See : https://wiki.blender.org/wiki/Tools/Tests/Python
"""
import unittest


# TODO(parlove@paxec.se): These statements import from the local git repository,
# would be better to call the operator as registered within Blender
from orthopen.operators import ORTHOPEN_OT_leg_prosthesis_generate


class TestFileImports(unittest.TestCase):
    def test_file_imports(self):
        # If these functions throw etc, unittest framework will report it
        ORTHOPEN_OT_leg_prosthesis_generate._import_from_assets_folder(None)


if __name__ == '__main__':
    import sys
    # Remove arguments from argv that unittest would complain about
    # See:
    # https://github.com/blender/blender/blob/8f94724f2246c9f4c2659f4380dc43fcda28d759/tests/python/bl_pyapi_mathutils.py#L551
    sys.argv = [__file__] + (sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    unittest.main()

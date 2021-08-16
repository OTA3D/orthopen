import random
import unittest

import numpy as np

import helpers


class TestPointInPolygon(unittest.TestCase):

    def test_rectangle(self):
        """
        Test that the function works for points generated in and outside of of a polygon
        forming a rectangle
        """
        X_MIN, X_MAX, Y_MIN, Y_MAX = 0, 20, 0, 10
        rectangle = [(X_MIN, Y_MIN), (X_MAX, Y_MIN), (X_MAX, Y_MAX), (X_MIN, Y_MAX)]

        for _ in range(100000):
            # Generate points inside and outside the rectangle border
            OVERLAP = 3
            x = random.uniform(X_MIN - OVERLAP, X_MAX + OVERLAP)
            y = random.uniform(Y_MIN - OVERLAP, Y_MAX + OVERLAP)

            # Compare to the the simple groundtruth
            ground_truth = ((x >= X_MIN and x <= X_MAX) and (y >= Y_MIN and y <= Y_MAX))
            self.assertTrue(helpers.inside_polygon(point=(x, y), polygon=rectangle) == ground_truth)


class FAKEMODULE_OT_fake_operator:
    """
    For testing the automatic operator naming function
    """
    # __qualname__ gives us the class name without having to create an instance
    bl_idname = helpers.mangle_operator_name(__qualname__)


class TestNaming(unittest.TestCase):

    def test_naming(self):
        """
        Blender does not use the class name directly to register operators, but instead polls field "bl_idname"
        and generates an instance from that. Blender seems to give us many options for naming "bl_idname"
        https://b3d.interplanety.org/en/class-naming-conventions-in-blender-2-8-python-api/
        We choose to automatically generate "bl_idname" from the class name, for easier refactor and hopefully less confusion
        """
        self.assertTrue(helpers.mangle_operator_name("MYMODULE_OT_My_Operator") == "mymodule.my_operator")
        self.assertTrue(FAKEMODULE_OT_fake_operator.bl_idname == "fakemodule.fake_operator")

        # We should not use this functions for menus etc as these can have their names set automatically:
        # https://wiki.blender.org/wiki/Reference/Release_Notes/2.80/Python_API/Addons
        with self.assertRaises(ValueError):
            helpers.mangle_operator_name("MYMODULE_MT_My_Menu")


if __name__ == '__main__':
    unittest.main()

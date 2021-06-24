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


if __name__ == '__main__':
    unittest.main()

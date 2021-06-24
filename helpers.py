"""
Functions that were needed but couldn't be found in Blender or numpy.
It is a bit awkward to install packages in Blender, so we avoid that.
"""

import numpy as np


def inside_polygon(point, polygon):
    """Check if point is inside polygon. The function will close the polygon,
    i.e. connect the last point to the first.

    Args:
        point (tuple): A point described as a tuple (size 2x1)
        polygon (list): List of tuples of points

    Returns:
        bool: True if the point is inside the polygon
    """

    point_x, point_y = point[0], point[1]

    # Edges of the polygon, connect end point to the start point
    polygon_edges = zip(polygon, polygon[1:] + [polygon[0]])

    # Loop through every edge of the polygon and check if point
    # extended to the right intersects the polygon edges an uneven number of times
    # See: Point inside polygon ray casting algorithm,
    # https://en.wikipedia.org/wiki/Point_in_polygon)
    inside = False
    for ((edge_x1, edge_y1), (edge_x2, edge_y2)) in polygon_edges:

        cannot_intersect = (point_y < min(edge_y1, edge_y2)) or \
            (point_y > max(edge_y1, edge_y2)) or \
            (point_x >= max(edge_x1, edge_x2))

        edge_is_horizontal = (edge_y1 == edge_y2)

        if (cannot_intersect or edge_is_horizontal):
            continue

        # Ray cast at [y = point_y] and see if ray intersects the edge to the left or right of point
        dx_dy = (edge_x2 - edge_x1) / (edge_y2 - edge_y1)
        intersection_x = dx_dy * (point_y - edge_y1) + edge_x1
        if point_x <= intersection_x:
            # This implicitly checks if we have an uneven number of intersections
            inside = not inside

    return inside


if __name__ == "__main__":
    # Demonstration
    import matplotlib.pyplot as plt
    BOX_SIZE = 1

    # Let first side slope rightwards
    DY_DX = 1
    polygon = [(x, DY_DX*x) for x in np.arange(start=0, stop=BOX_SIZE, step=0.1)]

    # Add rightside corners
    polygon += [(BOX_SIZE, BOX_SIZE), (BOX_SIZE, 0)]

    # Generate 2D point cloud
    N_POINTS = 1000
    CLOUD_SIZE = BOX_SIZE * 2
    points = np.random.rand(N_POINTS, 2) * CLOUD_SIZE - np.array([BOX_SIZE/2, BOX_SIZE/2])

    inside = np.array([inside_polygon(points[i, :], polygon) for i in range(N_POINTS)])

    # Plots
    polygon_closed = polygon + [polygon[0]]
    plt.plot([p[0] for p in polygon_closed], [p[1] for p in polygon_closed], c='k')
    plt.scatter(points[inside, 0], points[inside, 1], c='r')
    plt.scatter(points[~inside, 0], points[~inside, 1], c='b')
    plt.legend(["Polygon boundary", "Inside", "Outside"])
    plt.show()

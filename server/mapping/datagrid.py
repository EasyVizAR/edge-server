import collections
import heapq

import numpy as np
from PIL import Image


class DataGrid:
    """
    Generic data structure that stores values in a dense grid.
    """

    # Order of geometry attributes when exported to an array in numpy npz file.
    # If this changes, it will break file compatibility when loading old grid files.
    GEOMETRY_ATTRIBUTES = ["top", "left", "bottom", "right", "step"]

    SEARCH_DIRECTIONS = np.array([
        [-1, 0], # up
        [0, 1],  # right
        [1, 0],  # down
        [0, -1]  # left
    ], dtype=int)

    SEARCH_DIAGONALS = np.array([
        [-1, 1], # up + right
        [1, 1],  # right + down
        [1, -1], # down + left
        [-1, -1] # left + up
    ], dtype=int)

    def __init__(self, width=0.0, height=0.0, top=0.0, left=0.0, bottom=None, right=None, step=0.25, dtype=float, cell_shape=None):
        """
        Create a grid data structure.

        width, height, top, left: specify the extent of values required to
        be stored by the grid in physical units. For example, suppose we are
        mapping a room that is 10 meters wide, and the origin is in the center
        of the room such that the leftmost point is -5. The actual data
        structure will be slightly larger so that the origin can be centered in
        a grid cell and the most extreme points can still be contained in the
        grid.

        step: specify the size of grid cells in physical units. For example,
        if the grid is 10 meters wide and step size 0.25 meters, we will
        divide the space horizontally into 10/0.25=40 sections.

        dtype: data type to store, must be supported by numpy.

        cell_shape: shape of data to store for each grid cell, must be a tuple.
        The default shape stores one value for each grid cell.  Single or
        multi-dimensional arrays are also possible by setting a cell_shape as a
        tuple, but may be untested with some methods.  For example,
        cell_shape=(5,) would store five values for each cell.
        """
        self.cell_shape = cell_shape
        self.step = step

        if bottom is not None and right is not None:
            self.top = top
            self.bottom = bottom
            self.left = left
            self.right = right

            self.H = np.ceil((bottom - top) / step).astype(int)
            self.W = np.ceil((right - left) / step).astype(int)

        else:
            # Find smallest grid boundaries that enclose the required geometry.
            lower = np.floor(np.array([top, left]) / step)
            upper = np.ceil(np.array([top + height, left + width]) / step)

            # Height and width in grid cells.  Add 1 because we set the grid back a
            # half step size and still want to cover the required width and height.
            self.H, self.W = (upper - lower + 1).astype(int)

            # Top and left edge of the grid in world units. By setting it back a
            # half step, we ensure that the origin ends up centered in a grid cell.
            self.top, self.left = (lower - 0.5) * step
            self.bottom, self.right = (upper + 0.5) * step

        if cell_shape is None:
            shape = (self.H, self.W)
        elif isinstance(cell_shape, tuple):
            shape = (self.H, self.W) + cell_shape
        else:
            raise Exception("Only a tuple or None are accepted for cell_shape argument")

        self.data = np.zeros(shape, dtype=dtype)

    def __contains__(self, key):
        """
        Test if a cell is in bounds.
        """
        if isinstance(key, tuple) and len(key) == 2:
            return key[0] >= 0 and key[0] < self.H and key[1] >= 0 and key[1] < self.W
        elif len(key) == 3:
            return key[0] >= self.left and key[0] < self.right and key[-1] >= self.top and key[-1] < self.bottom

    def __getitem__(self, key):
        if isinstance(key, tuple) and len(key) == 2:
            return self.data[key]
        elif len(key) == 3:
            return self.data[self.xyz_to_index(key)]

    def __setitem__(self, key, value):
        if isinstance(key, tuple) and len(key) == 2:
            self.data[key] = value
        elif len(key) == 3:
            self.data[self.xyz_to_index(key)] = value

    def __str__(self):
        shape = "x".join(str(x) for x in self.data.shape)
        return f"DataGrid(top={self.top}, left={self.left}, bottom={self.bottom}, right={self.right}, shape={shape})"

    def add_segment(self, a, b, vspread=0):
        zz, xx, weights = self.line(a, b, vspread=vspread)
        keep = np.where((xx > self.left) & (xx < self.right) & (zz > self.top) & (zz < self.bottom))[0]

        xi = ((xx[keep] - self.left) / self.step).astype(int)
        zi = ((zz[keep] - self.top) / self.step).astype(int)
        weights = weights[keep]

        self.data[zi, xi] = np.maximum(self.data[zi, xi], weights)

    def check_segment(self, a, b):
        zz, xx, _ = self.line(a, b, vspread=0)
        keep = np.where((xx > self.left) & (xx < self.right) & (zz > self.top) & (zz < self.bottom))[0]

        xi = ((xx[keep] - self.left) / self.step).astype(int)
        zi = ((zz[keep] - self.top) / self.step).astype(int)

        return np.min(self.data[zi, xi])

    def a_star(self, a, b, cost=None, passable=None):
        if cost is None:
            cost = lambda cell, value: 0
        if passable is None:
            passable = self.ones_passable

        a = self.xyz_to_index(a)
        b = self.xyz_to_index(b)

        work = []

        # Current best distance from start to a given cell
        g_score = collections.defaultdict(lambda: np.inf)
        g_score[a] = 0.0

        came_from = dict()

        dist = lambda p, q: self.step * np.linalg.norm(np.subtract(p, q))

        def reconstruct_path():
            path = [self.index_to_xz(b)]
            current = b
            while current != a:
                current = came_from[current]
                path.append(self.index_to_xz(current))

            path.reverse()
            return self.douglas_peucker_path_smoothing(path)

        visited = set()
        heapq.heappush(work, (dist(a, b), a))
        while len(work) > 0:
            f_score, current = heapq.heappop(work)
            if current == b:
                return reconstruct_path()

            visited.add(current)

            neighbors = current + self.SEARCH_DIRECTIONS
            reachable = np.zeros(4, dtype=bool)

            # Grid cells are all the same size, so distance to any neighbor is
            # at most distance to the current cell plus a step.
            neighbors_g = g_score[current] + self.step

            for i, neigh in enumerate(neighbors):
                neigh = tuple(neigh)
                if neigh in self and neigh not in visited and passable(neigh, self.data[neigh]):
                    reachable[i] = True

                    tentative_g = neighbors_g + cost(neigh, self.data[neigh])
                    if tentative_g < g_score[neigh]:
                        g_score[neigh] = tentative_g
                        came_from[neigh] = current

                        f_score = tentative_g + dist(neigh, b)
                        heapq.heappush(work, (f_score, neigh))

            # Diagonal neighbors have a bit longer step size.
            neighbors_g = g_score[current] + np.sqrt(2) * self.step

            neighbors = current + self.SEARCH_DIAGONALS
            for i, neigh in enumerate(neighbors):
                neigh = tuple(neigh)
                if neigh in self and neigh not in visited and passable(neigh, self.data[neigh]):
                    # Only consider a diagonal neighbor if the two directly
                    # adjacent neighbors are reachable.  The directions and
                    # diagonals are ordered consistently so that we can check
                    # reachable[i] and reachable[i+1].  For example, to move up
                    # and right (diagonal entry 0), we need to check up
                    # (direction 0) and right (direction 1).
                    if reachable[i] and reachable[(i+1)%4]:
                        tentative_g = neighbors_g + cost(neigh, self.data[neigh])
                        if tentative_g < g_score[neigh]:
                            g_score[neigh] = tentative_g
                            came_from[neigh] = current

                            f_score = tentative_g + dist(neigh, b)
                            heapq.heappush(work, (f_score, neigh))

        return None

    def douglas_peucker_path_smoothing(self, points, epsilon=None):
        if points is None or len(points) < 3:
            return points

        if epsilon is None:
            epsilon = self.step

        points_arr = np.array(points)
        start2end = points_arr[-1,:] - points_arr[0,:]

        # This gives a array containing the perpendicular distance of each point to the line between start and end.
        distances = np.abs(np.cross(start2end, points_arr[0,:] - points_arr)) / np.linalg.norm(start2end)

        # Find the point farthest from the line and its distance.
        index = np.argmax(distances)
        dmax = distances[index]

        if dmax > epsilon:
            left = self.douglas_peucker_path_smoothing(points[:index+1], epsilon)
            right = self.douglas_peucker_path_smoothing(points[index:], epsilon)
            return left[:-1] + right
        else:
            return [points[0], points[-1]]

    def line(self, a, b, vspread=0):
        """
        Find grid cells hit by a line segment from point a to b.

        If vspread is greater than 0, then grid cells above and below the line
        will also be included.

        This is largely based on the solution by Marco Spinaci (https://stackoverflow.com/a/47381058).
        """
        diff = np.subtract(b, a)

        # The algorithm below works fine if c1 >= c0 and c1-c0 >= abs(r1-r0).
        # If either of these cases are violated, do some switches.
        if abs(diff[0]) < abs(diff[-1]):
            # Switch x and y, and switch again when returning.
            x, y, weights = self.line(np.flip(a), np.flip(b), vspread=vspread)
            return (y, x, weights)

        # At this point we know that the distance in columns (x) is greater
        # than that in rows (y). Possibly one more switch if c0 > c1.
        if a[0] > b[0]:
            return self.line(b, a, vspread=vspread)

        # The following is now always < 1 in abs
        slope = diff[-1] / diff[0]

        if np.isnan(slope):
            return np.array([a[1]]), np.array([a[0]]), np.array([1])

        # Axis intercept
        y0 = a[-1] - slope * a[0]

        half_step = 0.5 * self.step

        # We write y as a function of x, because the slope is always <= 1
        # (in absolute value)
        x = np.arange(a[0], b[0]+half_step, self.step, dtype=float)
        y = y0 + x * slope

        spread_steps = np.arange(-vspread, vspread+1)
        spread = self.step * spread_steps

        # Tent function that is 1 at the center and decreases to left and right.
        spread_weights = (vspread + 1 - np.abs(spread_steps)) / (vspread + 1)

        yy = y.reshape(-1, 1) + spread.reshape(1, -1)
        xx = np.repeat(x, yy.shape[1])
        yy = yy.flatten()
        weights = np.tile(spread_weights, x.shape[0])

        return yy, xx, weights

    def resize_to_other(self, other):
        """
        Create a new DataGrid with the same values but with the geometry from another DataGrid

        This effectively makes two grids aligned so that indexing is the same
        between them. Step size should be equal for this operation to make any
        sense.
        """
        new = DataGrid(top=other.top, left=other.left, bottom=other.bottom, right=other.right, step=other.step, dtype=self.data.dtype, cell_shape=self.cell_shape)

        from_i = 0
        from_j = 0
        to_i = 0
        to_j = 0

        if new.top < self.top:
            to_i = int(np.round((self.top - new.top) / self.step))
        else:
            from_i = int(np.round((new.top - self.top) / self.step))

        if new.left < self.left:
            to_j = int(np.round((self.left - new.left) / self.step))
        else:
            from_j = int(np.round((new.left - self.left) / self.step))

        copy_i = min(self.H - from_i, new.H - to_i)
        copy_j = min(self.W - from_j, new.W - to_j)

        new.data[to_i:to_i+copy_i, to_j:to_j+copy_j] = self.data[from_i:from_i+copy_i, from_j:from_j+copy_j]

        return new

    def save(self, path):
        """
        Save the grid to a numpy npz file
        """
        geometry = np.array([getattr(self, a) for a in self.GEOMETRY_ATTRIBUTES])
        np.savez(path, data=self.data, geometry=geometry)

    def save_image(self, path):
        grid = (255 * self.data).astype(np.uint8)
        grid = np.flipud(grid)
        img = Image.fromarray(grid)
        img.save(path)

    def to_ascii(self):
        symbols = [" ", ".", "o", "@"]

        # Divide the range between minimum and maximum value into equal size buckets
        breaks = np.linspace(self.data.min(), self.data.max(), len(symbols)+1)[1:]
        breaks[-1] = np.inf

        rows = []
        for i in range(self.H):
            cols = []
            for j in range(self.W):
                for k in range(len(symbols)):
                    if self.data[i,j] < breaks[k]:
                        cols.append(symbols[k])
                        break
            rows.append("".join(cols))
        return "\n".join(rows)

    def index_to_xz(self, p):
        # Add a half step to center the point in the grid cell.
        q = (np.array(p) + 0.5) * self.step + [self.top, self.left]
        return (q[1], q[0])

    def xyz_to_index(self, p):
        q = ([p[-1], p[0]] - np.array([self.top, self.left])) / self.step
        return tuple(np.floor(q).astype(int))

    @classmethod
    def load(cls, path):
        """
        Load grid object from a numpy npz file
        """
        npz = np.load(path)

        grid = cls()
        grid.data = npz['data']

        geom = npz['geometry']
        for i, a in enumerate(cls.GEOMETRY_ATTRIBUTES):
            setattr(grid, a, geom[i])

        shape = grid.data.shape
        grid.H = shape[0]
        grid.W = shape[1]

        return grid

    @staticmethod
    def ones_passable(cell, value):
        return value > 0.75

    @staticmethod
    def zero_passable(cell, value):
        return value < 0.25

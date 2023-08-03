import collections
import heapq

import numpy as np
from PIL import Image


def weighted_line(r0, c0, r1, c1, w=1, step=0.25):
    """
    Find pixels touched by a 2d numpy array along a thick line segment from point (r0, c0) to (r1, c1).

    This is based on the solution by Marco Spinaci (https://stackoverflow.com/a/47381058).
    """
    # The algorithm below works fine if c1 >= c0 and c1-c0 >= abs(r1-r0).
    # If either of these cases are violated, do some switches.
    if abs(c1-c0) < abs(r1-r0):
        # Switch x and y, and switch again when returning.
        xx, yy, weights = weighted_line(c0, r0, c1, r1, w, step)
        return (yy, xx, weights)

    # At this point we know that the distance in columns (x) is greater
    # than that in rows (y). Possibly one more switch if c0 > c1.
    if c0 > c1:
        return weighted_line(r1, c1, r0, c0, w, step)

    # The following is now always < 1 in abs
    slope = (r1-r0) / (c1-c0)

    if np.isnan(slope):
        return np.array([r0]), np.array([c0]), np.array([1])

    # Axis intercept
    y0 = r0 - slope * c0

    # Adjust weight by the slope
    #w *= np.sqrt(1+np.abs(slope)) / 2

    # We write y as a function of x, because the slope is always <= 1
    # (in absolute value)
    x = np.arange(c0, c1+1, dtype=float)
    y = y0 + x * slope

    # Now instead of 2 values for y, we have 2*np.ceil(w/2).
    # All values are 1 except the upmost and bottommost.
    #thickness = w / 2

    half_step = 0.5 * step
    spread = np.arange(-w+step, w, step)

    yy = y.reshape(-1, 1) + spread.reshape(1, -1)
    xx = np.repeat(x, yy.shape[1])
    yy = yy.flatten()
    weights = np.tile((w - np.abs(spread))**2, x.shape[0])

    return yy, xx, weights


class NavigationGrid:
    def __init__(self, geometry={}, step=0.25):
        self.step = step

        width = geometry.get("width", 20.0)
        height = geometry.get("height", 20.0)
        top = geometry.get("top", -10.0)
        left = geometry.get("left", -10.0)

        # Find smallest grid boundaries that enclose the required map geometry.
        lower = np.floor(np.array([top, left]) / step)
        upper = np.ceil(np.array([top + height, left + width]) / step)

        # Height and width in grid cells.  Add 1 because we set the grid back a
        # half step size and still want to cover the required width and height.
        self.H, self.W = (upper - lower + 1).astype(int)

        # Top and left edge of the grid in world units. By setting it back a
        # half step, we ensure that the origin ends up centered in a grid cell.
        self.top, self.left = (lower - 0.5) * step
        self.bottom, self.right = (upper + 0.5) * step

        self.grid = np.zeros((self.H, self.W))

        # Save starting points where headsets checked in for possible
        # reachability analysis.
        self.starting_points = []

    def __str__(self):
        return f"NavigationGrid(top={self.top}, left={self.left}, bottom={self.bottom}, right={self.right}, H={self.H}, W={self.W})"

    def add_trace(self, trace):
        points = []
        for pose in trace:
            point = np.array([float(pose['position'][i]) for i in ['x', 'y', 'z']])
            points.append(point)

        # Trace should either be in chronological or reversed chronological order.
        # Find and save the first point in the trace.
        if float(trace[0]['time']) < float(trace[-1]['time']):
            self.starting_points.append(points[0])
        else:
            self.starting_points.append(points[-1])

        for i in range(len(points) - 1):
            self.add_segment(points[i], points[i+1])

    def add_segment(self, a, b, weight=1):
        zz, xx, weights = weighted_line(a[-1], a[0], b[-1], b[0], 1, step=self.step)
        keep = np.where((xx > self.left) & (xx < self.right) & (zz > self.top) & (zz < self.bottom))[0]

        xi = ((xx[keep] - self.left) / self.step).astype(int)
        zi = ((zz[keep] - self.top) / self.step).astype(int)
        weights = weights[keep]

        self.grid[zi, xi] = np.maximum(self.grid[zi, xi], weights)

    def check_segment(self, a, b, weight=1):
        zz, xx, _ = weighted_line(a[-1], a[0], b[-1], b[0], 1, step=self.step)
        keep = np.where((xx > self.left) & (xx < self.right) & (zz > self.top) & (zz < self.bottom))[0]

        xi = ((xx[keep] - self.left) / self.step).astype(int)
        zi = ((zz[keep] - self.top) / self.step).astype(int)

        return np.min(self.grid[zi, xi])

    def a_star(self, a, b):
        a = self.xyz_to_index(a)
        b = self.xyz_to_index(b)

        work = []
        best_g = collections.defaultdict(lambda: np.inf)
        came_from = dict()

        directions = np.array([
            [1, 0],
            [-1, 0],
            [0, 1],
            [0, -1]
        ], dtype=int)

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
            current_g, current = heapq.heappop(work)
            if current == b:
                return reconstruct_path()

            visited.add(current)
            if len(visited) % 100 == 0:
                print("[A*] visited {}, work queue {}, current g {}".format(len(visited), len(work), current_g))

            neighbors = current + directions
            for neigh in neighbors:
                neigh = tuple(neigh)
                if np.min(neigh) >= 0 and neigh[0] < self.H and neigh[1] < self.W and neigh not in visited and self.grid[neigh] > 0.2:
                    tentative_g = current_g + self.step

                    penalty = 1.0 - self.grid[neigh]

                    if tentative_g < best_g[neigh]:
                        best_g[neigh] = tentative_g
                        came_from[neigh] = current
                        heapq.heappush(work, (dist(neigh, b) + penalty, neigh))

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

    def save_image(self, path):
        grid = (255 * self.grid).astype(np.uint8)
        grid = np.flipud(grid)
        img = Image.fromarray(grid)
        img.save(path)

    def index_to_xz(self, p):
        # Add a half step to center the point in the grid cell.
        q = (np.array(p) + 0.5) * self.step + [self.top, self.left]
        return (q[1], q[0])

    def xyz_to_index(self, p):
        q = ([p[-1], p[0]] - np.array([self.top, self.left])) / self.step
        return tuple(np.floor(q).astype(int))

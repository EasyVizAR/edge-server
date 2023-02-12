from xml.dom import minidom
import matplotlib.pyplot as plt
import math
import numpy as np
import time
import sys
# from searcher import Searcher
import heapq
import csv

import shapely
from shapely.geometry import LineString, Point

plt.rcParams['figure.dpi'] = 500
plt.rcParams['savefig.dpi'] = 500

GRANULARITY = 5


def fuzzy_equality(a, b):
	error = 0.00001
	return True if (math.abs(a - b) < error) else False


class Grid:
	def __init__(self, granularity):
		self.maxx = float('-inf')
		self.maxy = float('-inf')
		self.minx = float('inf')
		self.miny = float('inf')
		self.grid = {}
		self.granularity = granularity

	def put(self, point):
		# xgran = math.floor(point[0]*self.granularity)
		# ygran = math.floor(point[1]*self.granularity)
		xgran, ygran = self.getGridBoxCoordinates(point)

		if (xgran, ygran) in self.grid:
			self.grid[(xgran, ygran)] += 1
		else:
			self.grid[(xgran, ygran)] = 1
			if (xgran > self.maxx):
				maxx = xgran
			if (xgran < self.minx):
				minx = xgran
			if (ygran > self.maxy):
				maxy = ygran
			if (ygran < self.miny):
				miny = ygran

	def getValue(self, point):
		# xgran = math.floor(point[0]*self.granularity)
		# ygran = math.floor(point[1]*self.granularity)
		xgran, ygran = self.getGridBoxCoordinates(point)

		return self.grid[(xgran, ygran)] if (xgran, ygran) in self.grid else 0

	def getNeighbors(self, point):
		l = []
		for i in range(-1, 2):
			for j in range(-1, 2):
				if (i == 0 and j == 0):
					continue
				l.append((point[0] + i * (1 / self.granularity), point[1] + j * (1 / self.granularity)))
		return l

	def getUnOccupiedNeighbors(self, point):
		l = []
		point = self.getGridBoxCoordinates(point)
		for i in range(-1, 2):
			for j in range(-1, 2):
				if (i == 0 and j == 0):
					continue
				# neighbor = ( point[0] + i * (1/self.granularity), point[1] + j * (1/self.granularity) )
				neighbor = (point[0] + i, point[1] + j)
				if neighbor not in self.grid:
					l.append(self.getRealBoxCoordinates(neighbor))
		return l

	def getGridBoxCoordinates(self, point):
		nudge = 0.0000001
		return (
			math.floor(point[0] * self.granularity + nudge),
			math.floor(point[1] * self.granularity + nudge)
		)

	def getRealBoxCoordinates(self, point):
		nudge = 0.0000001
		return (
			math.floor(point[0] + nudge) / self.granularity,
			math.floor(point[1] + nudge) / self.granularity
		)

	def getAllBoxes(self):
		return [self.getRealBoxCoordinates(box) for box in self.grid]

	def nudge(self, value):
		nudge = 0.0000001
		return math.floor(value * self.granularity + nudge) / self.granularity

	def generous_floor(self, value):
		nudge = 0.0000001
		if (math.floor(value) != math.floor(value + nudge)):
			return math.floor(value + nudge)
		else:
			math.floor(value)

	def boxes_touching_line(self, line):
		# Good if it returned boxes in the order that they touched the line
		p1 = line[0]
		p2 = line[1]

		box1 = self.getGridBoxCoordinates(p1)
		box2 = self.getGridBoxCoordinates(p2)

		boxes = []
		intersections = []

		minx = min(box1[0], box2[0]) + 1
		maxx = max(box1[0], box2[0])
		miny = min(box1[1], box2[1]) + 1
		maxy = max(box1[1], box2[1])

	def __iter__(self):
		return iter(self.grid.keys())

	def getOccupiedBoxes(self):
		return [
			(box[0] / self.granularity, box[1] / self.granularity) for box in self.grid.keys()
		]

	def __contains__(self, point):
		return self.getGridBoxCoordinates(point) in self.grid


class Parser:
	def __init__(self):
		self.grid = Grid(GRANULARITY)  # Granularity of 5

	def parsePolylineStr(self, string):
		points = []
		for pstr in string.split(' '):
			point = pstr.split(',')
			points.append((float(point[0]), float(point[1])))
		return points

	def setPathsFromSvg(self, filename):
		doc = minidom.parse(filename)  # parseString also exists

		paths = [self.parsePolylineStr(line.getAttribute('points'))
				 for line in doc.getElementsByTagName('polyline')]
		# print(paths)

		doc.unlink()
		self.paths = paths
		return paths

	def setPaths(self, paths):
		self.paths = paths

	def getUserLocations(self, filepath):
		points = []
		with open(filepath, newline='') as csvFile:
			csvReader = csv.reader(csvFile, delimiter=',')
			headerRead = False
			for row in csvReader:
				# Skip heaer
				if not headerRead:
					headerRead = True
					continue
				points.append((float(row[1]), float(row[3])))
		return points

	def getGridOfBoxesWithPoints(self):
		for path in self.paths:
			for point in path:
				if (point[1] > 150):
					print("DEBUG: Point {} is unusually far from other points".format(point))

				self.grid.put(point)

	# return self.grid

	def create_grid_of_user_locations(self, user_locations_path):
		locations = self.getUserLocations(user_locations_path)
		grid = Grid(GRANULARITY)
		for point in locations:
			grid.put(point)
		return grid

	def getPathApproximations(self):
		approximatePaths = []
		for path in self.paths:
			numSegments = 2
			if len(path) <= numSegments:
				approximatePaths.append([path[0], path[-1]])
				continue

			# Path is longer than a single segment, break up path
			# approximatePaths.append([path[0], path[len(path)/2]])
			# approximatePaths.append([path[len(path)/2], path[-1]])

			previous = 0
			length = math.floor(len(path) / numSegments)
			for i in range(1, numSegments):
				approximatePaths.append([path[previous], path[length * i]])
				previous = length * i
			approximatePaths.append([path[previous], path[-1]])
		return approximatePaths

	# Line format = ( (x1, y1), (y1, y2) )
	def line_intersection(self, line1, line2):
		# What happens if the two lines are on top of each other? Does the code crash? How to handle?

		xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
		ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

		def det(a, b):
			return a[0] * b[1] - a[1] * b[0]

		div = det(xdiff, ydiff)
		if div == 0:
			return None

		d = (det(*line1), det(*line2))
		x = det(d, xdiff) / div
		y = det(d, ydiff) / div

		"""if x > 30:
			print("line1: {},\nline2: {},\nxdiff: {},\nydiff: {},\ndiv: {},\nd: {}"
			.format(line1, line2, xdiff, ydiff, div, d))"""

		return x, y

	def box_intersections(self, line):
		HORIZONTAL_GRIDLINE = 1
		VERTICAL_GRIDLINE = 2

		p1 = line[0]
		p2 = line[1]

		box1 = self.grid.getRealBoxCoordinates(p1)
		box2 = self.grid.getRealBoxCoordinates(p2)

		# print("box1: {}, box2: {}".format(box1, box2))
		# print("-----")

		# Common case: check if points are in the same line
		if (box1 == box2):
			return

		# points are not in same line, do multi-box check
		# num_horizontal_boxes = abs(box1[0] - box2[0]) + 1
		# num_vertical_boxes = abs(box1[1] - box2[1]) + 1

		minx = min(box1[0], box2[0]) + 1 / self.grid.granularity
		maxx = max(box1[0], box2[0])
		miny = min(box1[1], box2[1]) + 1 / self.grid.granularity
		maxy = max(box1[1], box2[1])

		# print("Minx: {}, Maxx: {}, Miny: {}, Maxy: {}".format(minx, maxx, miny, maxy))
		# print("-----")

		intersections = []

		# print("Vertical line intersections")
		# Check vertical line intersections (inclusive over grid lines)
		# for x in np.arange(minx, maxx + 1/self.grid.granularity, 1/self.grid.granularity):

		# These points are vertical intersections, keep track of this somehow
		for x in np.arange(minx, maxx, 1 / self.grid.granularity):
			grid_line = ((x, maxy), (x, miny))
			intersection = self.line_intersection(line, grid_line)
			if (intersection == None):
				continue
			# print("Line: {},\n\tGridline: {},\n\tIntersection: {}".format(line, grid_line, intersection))
			# intersections.append(intersection)
			intersections.append((VERTICAL_GRIDLINE, intersection))

		# print("-----")
		# print("Horizontal line intersections")
		# Check vertical line intersections (inclusive over grid lines)
		# for y in np.arange(miny, maxy + 1/self.grid.granularity, 1/self.grid.granularity):
		count = 0
		for y in np.arange(miny, maxy, 1 / self.grid.granularity):
			grid_line = ((maxx, y), (minx, y))
			intersection = self.line_intersection(line, grid_line)
			if (intersection == None):
				continue
			# print("Line: {},\n\tGridline: {},\n\tIntersection: {}".format(line, grid_line, intersection))
			# intersections.append((intersection))
			count += 1
			if (intersection[0] > 30):
				print("Gotem: {}, count: {}".format(intersection, count))
			intersections.append((HORIZONTAL_GRIDLINE, intersection))

		for intersection in intersections:
			# Check if intersection is none, why would this happen?
			if (intersection[1][0] > 30):
				print("Gotem: {}".format(intersection[1]))
			# continue

			if intersection[1] == None:
				print("What's goign on?")
				continue
			# Once we have intersections, then add boxes to grid
			intersection_x, intersection_y = intersection[1]

			# If not vertical or horizontal edge
			# if (intersection[0] != intersection_x and intersection[1] != intersection_y):
			#  print("error caught")
			if (intersection[0] != VERTICAL_GRIDLINE and intersection[0] != HORIZONTAL_GRIDLINE):
				print("ERROR: Intersection not on vertical or horizontal line")

			# If on vertical edge, add to boxes on either side of that vertical edge
			# if (intersection[0] == intersection_x and intersection[1] != intersection_y):
			if (intersection[0] == VERTICAL_GRIDLINE):
				# print("Point {} on vertical edge".format(intersection))
				self.grid.put((intersection_x, intersection_y))
				self.grid.put(
					(intersection_x - 1 / self.grid.granularity, intersection_y))
				continue

			# If on horizontal edge, add to boxes above and below that edge
			# if (intersection[0] != intersection_x and intersection[1] == intersection_y):
			if (intersection[0] == HORIZONTAL_GRIDLINE):
				# print("Point {} on horizontal edge".format(intersection))
				self.grid.put((intersection_x, intersection_y))
				self.grid.put(
					(intersection_x, intersection_y - 1 / self.grid.granularity))
				continue

			# If in the corner, then what?
			# Check direction
			if (intersection[0] == intersection_x and intersection[1] == intersection_y):
				# print("Point {} on corner".format(intersection))
				direction = (p2[0] - p1[0]) * (p2[1] - p1[1])
				# Line could be going through center, if so then detect direction
				# If diagonal (/ or \), mark corresponding boxes
				if (direction > 0):
					self.grid.put((intersection_x, intersection_y))
					self.grid.put((intersection_x - 1 / self.grid.granularity,
								   intersection_y - 1 / self.grid.granularity))
					continue
				elif (direction < 0):
					self.grid.put(
						(intersection_x - 1 / self.grid.granularity, intersection_y))
					self.grid.put(
						(intersection_x, intersection_y - 1 / self.grid.granularity))
					continue

	# If on axis (| or -), previous corner case of lines on top of each other

	# print("-----")

	def calculateOccupiedBoxes(self):
		# place line points into boxes
		self.getGridOfBoxesWithPoints()

		# place gridline intersections into boxes
		for path in self.paths:
			# If path is not a line, skip
			if len(path) < 2:
				continue

			for i in range(len(path) - 1):
				self.box_intersections((path[i], path[i + 1]))

		return self.grid

	def plotWallsAndBoxes(self, filename):
		# plot svg paths
		for path in self.paths:
			plt.plot([point[0] for point in path], [point[1]
													for point in path], 'k-')

		# plot boxes with points
		# """
		for box in self.grid.getOccupiedBoxes():
			# box_x = [box[0], box[0] + 1/granularity, box[0] + 1/granularity, box[0], box[0]]
			# box_y = [box[1], box[1], box[1] + 1/granularity, box[1] + 1/granularity, box[1]]

			box_x = [box[0] + 1 / (granularity * 2)]
			box_y = [box[1] + 1 / (granularity * 2)]

			# plt.plot(box_x, box_y, 'r-')
			plt.plot(box_x, box_y, marker="s",
					 markerfacecolor="red", markersize=1)
		# """

		# Plot wall path approximations
		approximatePaths = self.getPathApproximations()
		for path in approximatePaths:
			plt.plot([p[0] for p in path], [p[1] for p in path], 'b-', markersize=1)

		# Plot user positions
		locations = self.getUserLocations('samples/direct-route.csv')
		plt.plot([p[0] for p in locations], [p[1] for p in locations], 'r.', markersize=2)

		plt.savefig(filename)

	def plotWallsBoxesRoutes(self, filename, route):
		# plot svg paths
		for path in self.paths:
			plt.plot([point[0] for point in path], [point[1]
													for point in path], 'k-')

		# plot boxes with points
		# """
		for box in self.grid.getOccupiedBoxes():
			# box_x = [box[0], box[0] + 1/granularity, box[0] + 1/granularity, box[0], box[0]]
			# box_y = [box[1], box[1], box[1] + 1/granularity, box[1] + 1/granularity, box[1]]

			box_x = [box[0] + 1 / (granularity * 2)]
			box_y = [box[1] + 1 / (granularity * 2)]

			# plt.plot(box_x, box_y, 'r-')
			plt.plot(box_x, box_y, marker="s",
					 markerfacecolor="red", markersize=1)
		# """

		# plot route
		plt.plot([p[0] for p in route], [p[1] for p in route], 'b-', markersize=1)

		for point in route:
			plt.plot(point[0], point[1], 'r.', markersize=2)

		plt.savefig(filename)


# Line format = ( (x1, y1), (y1, y2) )
def line_intersection_alpha(line1, line2):
	# What happens if the two lines are on top of each other? Does the code crash? How to handle?
	xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
	ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

	def det(a, b):
		return a[0] * b[1] - a[1] * b[0]

	div = det(xdiff, ydiff)
	if div == 0:
		return None

	d = (det(*line1), det(*line2))
	x = det(d, xdiff) / div
	y = det(d, ydiff) / div

	"""if x > 30:
		print("line1: {},\nline2: {},\nxdiff: {},\nydiff: {},\ndiv: {},\nd: {}"
		.format(line1, line2, xdiff, ydiff, div, d))"""

	return x, y


# Check to see if a point is above or below an infinite line
# https://stackoverflow.com/questions/3838319/how-can-i-check-if-a-point-is-below-a-line-or-not
def halfplane(line, point):
	vector1 = (line[0][1] - line[0][0], line[1][1] - line[1][0])
	vector2 = (line[0][1] - point[0], line[1][1] - point[1])
	error_bound = 0.0000000001

	halfplane_side = vector1[0] * vector2[1] - vector1[1] * vector2[0]

	# Check to see if the point is approximately on the line
	if abs(halfplane_side) < error_bound:
		return 0
	else:
		return -1 if halfplane_side < 0 else 1


def lines_intersect_test(line1, line2):
	# Line 1, point 1 of l2 half plane
	l1p1 = halfplane(line1, line2[0])
	l1p2 = halfplane(line1, line2[1])
	l2p1 = halfplane(line2, line1[0])
	l2p2 = halfplane(line2, line1[1])

	# check if the points of each line are on different sides of the other line
	return l1p1 * -1 == l1p2 and l2p1 * -1 == l2p2


# intersection between line(p1, p2) and line(p3, p4)
def lines_intersect(line1, line2):
	x1, y1 = line1[0]
	x2, y2 = line1[1]
	x3, y3 = line2[0]
	x4, y4 = line2[1]
	denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
	if denom == 0:  # parallel
		return None
	ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
	if ua < 0 or ua > 1:  # out of range
		return None
	ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom
	if ub < 0 or ub > 1:  # out of range
		return None
	x = x1 + ua * (x2 - x1)
	y = y1 + ua * (y2 - y1)
	return (x, y)


def hEuclidean(start, destination):
	return math.sqrt(math.pow(start[0] - destination[0], 2) + math.pow(start[1] - destination[1], 2))


def inv_lerp(start, end, point):
	pass


class Map:
	def __init__(self, grid_walls: Grid, grid_user_locations: Grid):
		self.grid_walls = grid_walls
		self.grid_user_locations = grid_user_locations

	def calculatePath(self, start, destination):
		path = self.aStarSearch(start, destination, hEuclidean)
		return path

	def hDiagonal(self, start, destination):
		dx = abs(start[0] - destination[0])
		dy = abs(start[1] - destination[1])
		return (dx + dy) + (-1) * min(dx, dy)

	def naive_bloom(self):
		# Just create a square bloom effect around user locations
		weights = set()
		size = 21
		for location in self.grid_user_locations.getAllBoxes():
			for i in range(0, size):
				# for x in range(location[0] - 1, location[0] + 1 + 1/GRANULARITY, 1/GRANULARITY):
				for j in range(0, size):
					# for y in range(location[1] - 1, location[1] + 1 + 1/GRANULARITY, 1/GRANULARITY):
					x = location[0] + (-math.floor(size/2) + i) / self.grid_user_locations.granularity
					y = location[1] + (-math.floor(size/2) + j) / self.grid_user_locations.granularity
					weights.add((x, y))
		self.weights = weights

	def getGScore(self, gscore, point):
		if point in gscore and point not in self.weights:
			return gscore[point]
		else:
			return float('inf')

	def aStarSearch(self, start, destination, h):
		# First, is get neighbors implemented? Yes, although won't tell if neighbor is in the grid
		print(self.weights)

		# openSet = {start}
		openSet = []

		cameFrom = {}
		gscore = {start: 0}  # Default value of infinity
		fscore = {start: h(start, destination)}  # Default value of infinity



		heapq.heappush(openSet, (h(start, destination), start))

		while len(openSet) != 0:
			# Get node with lowest fscore value
			current_f, current = heapq.heappop(openSet)

			if current == destination:
				# print("YAHOOOO!!!")
				# print(cameFrom)
				return self.reconstructPath(cameFrom, current)

			# print("Length of OpenSet: {}".format(len(openSet)))
			neighbors = self.grid_walls.getUnOccupiedNeighbors(current)
			# print("{} -> {}".format(current, neighbors))
			for neighbor in neighbors:
				if neighbor not in self.grid_walls:
					tentativeGScore = self.getGScore(gscore, current) + 1

					# weight = 0.5 if self.grid_user_locations.getValue(neighbor) else 1
					# weight = self.weights[neighbor] if neighbor in self.weights[neighbor] else 2
					"""weight = 1000
					#print("-> Neighbor {}".format(neighbor))
					if neighbor in self.weights:
						weight = 0
						print("->-> Neighbor {} in visible area".format(neighbor))
					tentativeGScore += weight"""

					if tentativeGScore < self.getGScore(gscore, neighbor):
						# Better path to destination is found, record it
						#print(tentativeGScore)
						cameFrom[neighbor] = current
						gscore[neighbor] = tentativeGScore
						fscore[neighbor] = tentativeGScore + h(neighbor, destination)
						# print(" - neighbor {} in openSet? {}".format(neighbor, neighbor not in openSet))
						if (neighbor not in openSet):
							heapq.heappush(openSet, (h(neighbor, destination), neighbor))
				# print(len(openSet))

		print("No path found")
		return self.reconstructPath(cameFrom, current)

	def reconstructPath(self, cameFrom, current):
		# print("Current node {} in cameFrom? {}".format(current, current in cameFrom))
		total_path = [current]
		while current in cameFrom:
			current = cameFrom[current]
			total_path.append(current)
		total_path.reverse()
		self.route = total_path
		return total_path

	def plotWallsBoxesRoutes(self, filename):
		# plot boxes with points
		# """
		for box in self.grid_walls.getAllBoxes():
			# box_x = [box[0], box[0] + 1/granularity, box[0] + 1/granularity, box[0], box[0]]
			# box_y = [box[1], box[1], box[1] + 1/granularity, box[1] + 1/granularity, box[1]]

			box_x = [box[0] + 1 / (self.grid_walls.granularity * 2)]
			box_y = [box[1] + 1 / (self.grid_walls.granularity * 2)]

			# plt.plot(box_x, box_y, 'r-')
			plt.plot(box_x, box_y, marker="s", color="black", markersize=1)

		for w in self.weights:
			box_x = [w[0] + 1 / (self.grid_walls.granularity * 2)]
			box_y = [w[1] + 1 / (self.grid_walls.granularity * 2)]

			# plt.plot(box_x, box_y, 'r-')
			plt.plot(box_x, box_y, marker="s", color="blue", markersize=1)

		plt.plot([point[0] for point in self.route],
				 [point[1] for point in self.route], 'r-')

		plt.savefig(filename)


# def calculatePath(self, )

# Weighted A-star search
# Is this just multiplying the g-score by the weight?
# I can probably figure this out and intuit it if I watch more videos about how A-star works and
# just look it up

# What about something simpler, that might require less effort?
# I am talking about creating a graph between user locations as a web of waypoints
# I can whip up an implementation of this in like 10-15 minutes.

# If given a graph with distances, search through them (Dijkstra's should be good enough here)
# If given a start point and end point, identify closest waypoints in the graph and path plan


class Rectangle:
	def __init__(self, x, y, w, h):
		self.x = x
		self.y = y
		self.w = w
		self.h = h

	def intersects(self, rectangle):
		# First check intersection, then rect within rect?
		# check to see if sides overlap?
		# |  | |  | Here, r1's right side is in front of r2's left
		# |__|_|  | but r2's right side is behind r1's left
		#    |____| Same check for bottom and top
		# ^r1  ^r2
		thisleft = self.x - self.w
		thisright = self.x + self.w
		thisup = self.y - self.h
		thisdown = self.y + self.h

		rectleft = rectangle.x - rectangle.w
		rectright = rectangle.x + rectangle.w
		rectup = rectangle.y - rectangle.h
		rectdown = rectangle.y + rectangle.h

		return not (thisleft > rectright or
					thisright < rectleft or
					thisup > rectdown or
					thisdown < rectup)


class Node:
	def __init__(self):
		self.boundary = None


class QuadTree:
	def __init__(self):
		self.head = None


class RoadGraph:
	def __init__(self, vertices, boundaries):
		self.vertices = vertices
		self.boundaries = boundaries
		self.edges = {}

	def roadBoundaryIntersection(self, road):
		for boundary in self.boundaries:
			l1 = LineString(road)
			l2 = LineString(boundary)
			if l1.intersects(l2):
				return True

		# if lines_intersect(road, boundary):
		#	return True

		return False

	def calculateEdges(self):
		if len(self.vertices) < 2:
			return None

		# print(range(len(self.vertices)))

		# for each vertex
		for i in range(len(self.vertices)):
			print(i)
			v1 = self.vertices[i]
			# plt.plot(v1[0], v1[1], 'r.', markersize=2)
			# plt.show()
			# for every other vertex
			for j in range(i + 1, len(self.vertices)):

				# print(list(range(i+1, len(self.vertices))))

				v2 = self.vertices[j]
				# plt.plot(v1[0], v1[1], 'g.', markersize=1)
				# l1 = LineString([self.vertices[i], self.vertices[j]])
				# check if line between them intersects with boundary
				if not self.roadBoundaryIntersection([v1, v2]):
					# put edge between these points
					# print(" -> Edge created between vertices {} and {}".format(i, j))
					dist = hEuclidean(v1, v2)
					# self.edges[v1] = (v2, dist)
					# self.edges[v2] = (v1, dist)
					self.edges[i] = (j, dist)
					self.edges[j] = (i, dist)
		return self.edges

	def plotGraph(self, filename):
		# plot boundaries
		for boundary in self.boundaries:
			plt.plot([point[0] for point in boundary],
					 [point[1] for point in boundary], 'k-')

		# plot edges
		"""for v1 in self.edges:
			v2 = self.edges[v1][0]
			plt.plot([v[0] for v in [v1, v2]], [v[1] for v in [v1, v2]], 'r-', markersize = 1)"""

		for i in self.edges:
			j = self.edges[i][0]
			plt.plot(
				[v[0] for v in [self.vertices[i], self.vertices[j]]],
				[v[1] for v in [self.vertices[i], self.vertices[j]]], 'r-', markersize=1)

		# plt.plot([p[0] for p in route], [p[1] for p in route], 'r-', markersize = 1)

		for v in self.vertices:
			plt.plot(v[0], v[1], 'r.', markersize=2)

		plt.savefig(filename)


granularity = GRANULARITY

"""def plotPathsAndBoxes(paths, filled_spaces, filename):
	# plot svg paths
	for path in paths:
		plt.plot([point[0] for point in path], [point[1]
				 for point in path], 'k-')

	# plot boxes with points
	for box in filled_spaces:
		box_x = [box[0], box[0] + 1/granularity,
				 box[0] + 1/granularity, box[0], box[0]]
		box_y = [box[1], box[1], box[1] + 1 /
				 granularity, box[1] + 1/granularity, box[1]]
		#box_x = [ box[0] + 1/(granularity*2) ]
		#box_y = [ box[1] + 1/(granularity*2) ]
		plt.plot(box_x, box_y, 'r-')

	plt.savefig(filename)"""

"""
for i in range(math.floor(minx), math.floor(maxx), 1/granularity):
  for j in range(math.floor(miny), math.floor(maxy)):
"""

paths = [
	[(1.5, 1.5), (2.5, 2.5)],
	[(1.5, -1.5), (2.5, -2.5)]
]

"""paths set("image.svg")

t1 = time.time()

filled_spaces = getGridOfBoxesWithPoints(paths)

box_intersections(filled_spaces, paths[0])

t2 = time.time()

print("Calculations in {} ms".format(math.ceil((t2-t1)*1000)))

plotPathsAndBoxes(paths, filled_spaces, "test_intersections.png")"""

if __name__ == "__main__":
	parser = Parser()
	# s = Searcher()
	test = 0
	TEST_LINE_INTERSECTION = 1
	TEST_EXAMPLE_SVG = 2

	if (len(sys.argv) <= 2):
		test = 2
	elif (sys.argv[1] == "-t"):
		test = int(sys.argv[2])

	test = 3

	# test 0
	if (test == 1):
		parser.setPaths(paths)
		parser.getGridOfBoxesWithPoints()
		parser.box_intersections(paths[0])

	if (test == 2):
		print("Getting paths from svg...")
		boundaries = parser.setPathsFromSvg("image.svg")

		print("Creating grid...")
		parser.calculateOccupiedBoxes()

		# print("Plotting Grid...")
		# parser.plotWallsAndBoxes("test_grid.png")

		print("Getting user positions...")
		# points = parser.getUserLocations('samples/direct-route.csv')
		points = parser.getUserLocations('samples/rh-search.csv')

		print("Creating waypoint map...")
		# print(boundaries)
		approximate_boundaries = parser.getPathApproximations()
		graph = RoadGraph(points, boundaries)
		graphEdges = graph.calculateEdges()

		print("Plotting Graph...")
		graph.plotGraph("test_graph_rh_search_approx_bounds.png")
	# graph.plotGraph("test_graph.png")

	if (test == 3):
		parser.setPathsFromSvg("image.svg")
		parser.calculateOccupiedBoxes()
		user_locations = parser.create_grid_of_user_locations('samples/rh-search.csv')
		# parser.plotWallsBoxesRoutes("test_intersections.png", [(0, 0), (1, 1), (2, 2)])

		# neighbors = parser.grid.getUnOccupiedNeighbors((0, 0))
		# print(neighbors)
		map = Map(parser.grid, user_locations)
		map.naive_bloom()

		endpoint = (20, 10)
		#endpoint = (100, 55)
		path = map.calculatePath((0, -2.5), endpoint)
		print(path)
		parser.plotWallsBoxesRoutes("test_map_plotting.png", path)
		map.plotWallsBoxesRoutes("test_map_plotting_weights.png")

	# Test QuadTree
	if (test == 4):
		r1 = Rectangle(0, 0, 100, 100)
		r2 = Rectangle(0, 50, 100, 100)
		r3 = Rectangle(0, 150, 100, 100)

		print(r1.intersects(r2))
		print(r1.intersects(r3))
		print(r2.intersects(r3))

	# Test bloom graph, explored areas
	if (test == 5):
		# First, can we check if a
		grid = Grid(1)
		grid.put((0.5, 0.5))
		grid.put((0.7, 0.7))
		grid.put((5, 1.1))
		print("(0, 0) in grid: {}".format((0, 0) in grid))
		print("(0.5, 0.5) in grid: {}".format((0.5, 0.5) in grid))
		print(grid.grid)
		for item in grid:
			print(item)

		map = Map(None, grid)
		map.naive_bloom()
		print(map.weights)

# print(parser.grid.getOccupiedBoxes())

# 1). Fix buggy line intersection problem
# 2). Change grid structure to use ints instead of floats

# Hash points to grid value
# Num of boxes = ceil(maxx - minx) * ceil(maxy - miny)
# Can we hash tuple to

# Change from seeing point is in square to seeing if line intersects square
# Check if path line intersects with any of the square lines
# Fill in intersected cells with paths cutting through them if they are cut through walls

# Open cell coloring - Give open cells (without walls) a gaussian blur filter
# 1/4 1/2 1/4
# 1/2 [1] 1/2
# 1/4 1/2 1/4

# Professor Kevin Ponto - Graphics guy
#   associates might have resources for algorithms that find open areas around obstacles

# Use paths traveled through room to estimate open area

"""11/9/2022

Priority: test out an implementation of A star search

Ideas:
 - A star search with waypoints as priorities? Where the hololens has been
 - sparse raycasting to identify general wall boundaries?

"""

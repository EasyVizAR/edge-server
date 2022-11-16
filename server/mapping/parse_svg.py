from xml.dom import minidom
import matplotlib.pyplot as plt
import math
import numpy as np
import time
import sys

plt.rcParams['figure.dpi'] = 500
plt.rcParams['savefig.dpi'] = 500

GRANULARITY = 5


def fuzzy_equality(a, b):
	error = 0.00001
	return True if (math.abs(a-b) < error) else False


class Grid:
	def __init__(self, granularity):
		self.maxx = float('-inf')
		self.maxy = float('-inf')
		self.minx = float('inf')
		self.miny = float('inf')
		self.grid = {}
		self.granularity = granularity

	def put(self, point):
		#xgran = math.floor(point[0]*self.granularity)
		#ygran = math.floor(point[1]*self.granularity)
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
		#xgran = math.floor(point[0]*self.granularity)
		#ygran = math.floor(point[1]*self.granularity)
		xgran, ygran = self.getGridBoxCoordinates(point)

		return self.grid[(xgran, ygran)] if (xgran, ygran) in self.grid else 0

	def getNeighbors(self, point):
		l = []
		for i in range(-1, 2):
			for j in range(-1, 2):
				if (i == 0 and j == 0):
					continue
				l.append( ( point[0] + i * (1/self.granularity), point[1] + j * (1/self.granularity) ) )
		return l

	def getGridBoxCoordinates(self, point):
		nudge = 0.0000001
		return (
			math.floor(point[0]*self.granularity + nudge),
			math.floor(point[1]*self.granularity + nudge)
		)

	def getRealBoxCoordinates(self, point):
		nudge = 0.0000001
		return (
			math.floor(point[0]*self.granularity + nudge)/self.granularity,
			math.floor(point[1]*self.granularity + nudge)/self.granularity
		)

	def nudge(self, value):
		nudge = 0.0000001
		return math.floor(value*self.granularity + nudge)/self.granularity

	def generous_floor(self, value):
		nudge = 0.0000001
		if (math.floor(value) != math.floor(value + nudge)):
			return math.floor(value + nudge)
		else:
			math.floor(value)

	def __iter__(self):
		return iter(self.grid.keys())

	def getOccupiedBoxes(self):
		return [
			(box[0]/self.granularity, box[1]/self.granularity) for box in self.grid.keys()
		]
	
	def __contains__(self, point):
		return point in self.grid


class Parser:
	def __init__(self):
		self.grid = Grid(GRANULARITY)   # Granularity of 5

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

	def setPaths(self, paths):
		self.paths = paths

	def getGridOfBoxesWithPoints(self):
		for path in self.paths:
			for point in path:
				if (point[1] > 150):
					print("DEBUG: Point {} is unusually far from other points".format(point))

				self.grid.put(point)

		# return self.grid

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
		return x, y

	def box_intersections(self, line):
		HORIZONTAL_GRIDLINE = 1
		VERTICAL_GRIDLINE = 2

		p1 = line[0]
		p2 = line[1]

		box1 = self.grid.getRealBoxCoordinates(p1)
		box2 = self.grid.getRealBoxCoordinates(p2)

		#print("box1: {}, box2: {}".format(box1, box2))
		# print("-----")

		# Common case: check if points are in the same line
		if (box1 == box2):
			return

		# points are not in same line, do multi-box check
		#num_horizontal_boxes = abs(box1[0] - box2[0]) + 1
		#num_vertical_boxes = abs(box1[1] - box2[1]) + 1

		minx = min(box1[0], box2[0]) + 1/self.grid.granularity
		maxx = max(box1[0], box2[0])
		miny = min(box1[1], box2[1]) + 1/self.grid.granularity
		maxy = max(box1[1], box2[1])

		#print("Minx: {}, Maxx: {}, Miny: {}, Maxy: {}".format(minx, maxx, miny, maxy))
		# print("-----")

		intersections = []

		#print("Vertical line intersections")
		# Check vertical line intersections (inclusive over grid lines)
		# for x in np.arange(minx, maxx + 1/self.grid.granularity, 1/self.grid.granularity):

		# These points are vertical intersections, keep track of this somehow
		for x in np.arange(minx, maxx, 1/self.grid.granularity):
			grid_line = ((x, maxy), (x, miny))
			intersection = self.line_intersection(line, grid_line)
			if (intersection == None):
				continue
			#print("Line: {},\n\tGridline: {},\n\tIntersection: {}".format(line, grid_line, intersection))
			# intersections.append(intersection)
			intersections.append((VERTICAL_GRIDLINE, intersection))

		# print("-----")
		#print("Horizontal line intersections")
		# Check vertical line intersections (inclusive over grid lines)
		# for y in np.arange(miny, maxy + 1/self.grid.granularity, 1/self.grid.granularity):
		for y in np.arange(miny, maxy, 1/self.grid.granularity):
			grid_line = ((maxx, y), (minx, y))
			intersection = self.line_intersection(line, grid_line)
			if (intersection == None):
				continue
			#print("Line: {},\n\tGridline: {},\n\tIntersection: {}".format(line, grid_line, intersection))
			# intersections.append((intersection))
			intersections.append((HORIZONTAL_GRIDLINE, intersection))

		for intersection in intersections:
			# Check if intersection is none, why would this happen?
			if (intersection[1][1] > 150):
				print("Gotem: {}".format(intersection[1]))
				continue

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
				#print("Point {} on vertical edge".format(intersection))
				self.grid.put((intersection_x, intersection_y))
				self.grid.put(
					(intersection_x - 1/self.grid.granularity, intersection_y))
				continue

			# If on horizontal edge, add to boxes above and below that edge
			# if (intersection[0] != intersection_x and intersection[1] == intersection_y):
			if (intersection[0] == HORIZONTAL_GRIDLINE):
				#print("Point {} on horizontal edge".format(intersection))
				self.grid.put((intersection_x, intersection_y))
				self.grid.put(
					(intersection_x, intersection_y - 1/self.grid.granularity))
				continue

			# If in the corner, then what?
			# Check direction
			if (intersection[0] == intersection_x and intersection[1] == intersection_y):
				#print("Point {} on corner".format(intersection))
				direction = (p2[0] - p1[0]) * (p2[1] - p1[1])
				# Line could be going through center, if so then detect direction
				# If diagonal (/ or \), mark corresponding boxes
				if (direction > 0):
					self.grid.put((intersection_x, intersection_y))
					self.grid.put((intersection_x - 1/self.grid.granularity,
								  intersection_y - 1/self.grid.granularity))
					continue
				elif (direction < 0):
					self.grid.put(
						(intersection_x - 1/self.grid.granularity, intersection_y))
					self.grid.put(
						(intersection_x, intersection_y - 1/self.grid.granularity))
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
				self.box_intersections((path[i], path[i+1]))

	def plotPathsAndBoxes(self, filename):
		# plot svg paths
		for path in self.paths:
			plt.plot([point[0] for point in path], [point[1]
					 for point in path], 'k-')

		# plot boxes with points
		# """
		for box in self.grid.getOccupiedBoxes():
			#box_x = [box[0], box[0] + 1/granularity, box[0] + 1/granularity, box[0], box[0]]
			#box_y = [box[1], box[1], box[1] + 1/granularity, box[1] + 1/granularity, box[1]]

			box_x = [box[0] + 1/(granularity*2)]
			box_y = [box[1] + 1/(granularity*2)]

			#plt.plot(box_x, box_y, 'r-')
			plt.plot(box_x, box_y, marker="s",
					 markerfacecolor="red", markersize=1)
		# """
		plt.savefig(filename)


granularity = GRANULARITY


def plotPathsAndBoxes(paths, filled_spaces, filename):
	# plot svg paths
	for path in paths:
		plt.plot([point[0] for point in path], [point[1]
				 for point in path], 'k-')

	# plot boxes with points
	# """
	for box in filled_spaces:
		box_x = [box[0], box[0] + 1/granularity,
				 box[0] + 1/granularity, box[0], box[0]]
		box_y = [box[1], box[1], box[1] + 1 /
				 granularity, box[1] + 1/granularity, box[1]]
		#box_x = [ box[0] + 1/(granularity*2) ]
		#box_y = [ box[1] + 1/(granularity*2) ]
		plt.plot(box_x, box_y, 'r-')
	# """
	plt.savefig(filename)


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
	test = 0
	TEST_LINE_INTERSECTION = 1
	TEST_EXAMPLE_SVG = 2

	if (sys.argv[1] == "-t"):
		test = int(sys.argv[2])
	else:
		test = 2

	# test 0
	if (test == 1):
		parser.setPaths(paths)
		parser.getGridOfBoxesWithPoints()
		parser.box_intersections(paths[0])
		plotPathsAndBoxes(paths, parser.grid.getOccupiedBoxes(),
						  "test_line_intersection.png")

	if (test == 2):
		parser.setPathsFromSvg("image.svg")
		parser.calculateOccupiedBoxes()
		parser.plotPathsAndBoxes("test_intersections.png")

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

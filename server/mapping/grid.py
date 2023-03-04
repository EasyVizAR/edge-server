# Assuming we stick with the grid paradigm,
# We will need the grid data structure to be as solid as possible
import math
from collections import deque

try:
	import png
	have_pypng = True
except:
	have_pypng = False

try:
	import matplotlib.pyplot as plt
	have_matplotlib = True
except:
	have_matplotlib = False

import parse_data

class Grid:
	def __init__(self, boxes_per_meter):
		self.boxes_per_meter = boxes_per_meter
		self.grid = {}

	# Function mapping any real-world point to a grid box
	def point_to_box(self, point):
		nudge = 0.00000001
		boxx = math.floor(point[0] * self.boxes_per_meter + nudge)
		boxy = math.floor(point[1] * self.boxes_per_meter + nudge)
		return boxx, boxy

	# Function mapping grid box to real-world coordinates
	def box_to_point(self, box):
		nudge = 0.0000001
		return (math.floor(box[0] + nudge) / self.boxes_per_meter,
				math.floor(box[1] + nudge) / self.boxes_per_meter)

	# Put point into grid
	def put(self, point, private_input=False):
		box = point
		if not private_input:
			box = self.point_to_box(point)

		if box in self.grid:
			self.grid[box] += 1
		else:
			self.grid[box] = 1

	# Check if a grid box currently exists for a real-world point
	def __contains__(self, point):
		return self.point_to_box(point) in self.grid

	# Iterate through all real-world box coordinates
	def __iter__(self):
		return iter([self.box_to_point(box) for box in self.grid])

	# get value of box within grid
	def get_box_value(self, point):
		box = self.point_to_box(point)
		if box in self.grid:
			return self.grid[box]
		return 0

	# Return empty neighboring grid boxes? (needed by navigator)
	def unoccupied_neighbors(self, point):
		unoccupied = []
		box = self.point_to_box(point)
		for i in range(-1, 2):
			for j in range(-1, 2):
				if i == 0 and j == 0: continue
				neighbor = (box[0] + i, box[1] + j)
				if neighbor not in self.grid:
					unoccupied.append(neighbor)
		return [self.box_to_point(n) for n in unoccupied]
	
	def unoccupied_neighbors_with_weights(self, point):
		unoccupied = []
		box = self.point_to_box(point)
		for i in range(-1, 2):
			for j in range(-1, 2):
				if i == 0 and j == 0: continue
				neighbor = (box[0] + i, box[1] + j)
				if neighbor not in self.grid:
					weight = 1
					# Check for diagonal box to weight boxes differently based on distance
					if (i + j) % 2 == 0:
						weight = 1.4
					unoccupied.append((self.box_to_point(neighbor), weight))
		return unoccupied

	# What about all neighboring grid boxes or occupied neighboring grid boxes?

	def neighboring_box(self, point, direction):
		box = self.point_to_box(point)
		return self.box_to_point((box[0] + direction[0], box[1] + direction[1]))

	# How about a search algorithm to calculate the boxes that a line crosses
	# by just starting from a box on one endpoint, and moving vertically or horizontally
	# until you get to the endpoint box
	def boxes_touching_line(self, line, private_output=False):
		box_start = self.point_to_box(line[0])# if not private_usage else line[0]
		box_end = self.point_to_box(line[1])# if not private_usage else line[0]

		if box_start == box_end:
			return [box_start]

		def euclidean_sq(p1, p2):
			dx = (p2[0] - p1[0])
			dy = (p2[1] - p1[1])
			return dx * dx + dy * dy

		boxes_touching = [box_start]
		current = box_start

		while current != box_end:
			boxes = [(current[0], current[1] + 1), (current[0], current[1] - 1),
					 (current[0] - 1, current[1]), (current[0] + 1, current[1])]

			min_dist = 10000000
			min_box = None

			for box in boxes:
				if euclidean_sq(box, box_end) < min_dist:
					min_dist = euclidean_sq(box, box_end)
					min_box = box

			boxes_touching.append(min_box)
			current = min_box

		if not private_output:
			return [self.box_to_point(box) for box in boxes_touching]
		else:
			return boxes_touching

	def put_line(self, line):
		occupied_boxes = self.boxes_touching_line(line, private_output=True)
		for box in occupied_boxes:
			self.put(box, private_input=True)

	def put_lines(self, lines):
		if len(lines) < 1:
			return
		elif len(lines) < 2:
			self.put(self.point_to_box(lines[0]))
		for i in range(len(lines)-1):
			self.put_line([lines[i], lines[i+1]])
	
	def put_line_return_area(self, line, ttl):
		line_boxes = self.boxes_touching_line(line, private_output=True)
		
		#for box in line_boxes:
		#	self.put(box, private_input=True)

		"""
		# Do ttl bfs
		visited_nodes = set()
		ttl = {}
		open_queue = line_boxes

		for box in line_boxes:
			ttl[box] = time_to_live
		
		current = open_queue.pop()
		#visited_nodes.add(current)

		while len(open_queue) != 0:
			#print(len(open_queue))
			neighbors = self.unoccupied_neighbors(current)
			if len(neighbors) == 0:
				continue
			if ttl[current] == 0:
				visited_nodes.add(neighbor)
			else:
				for neighbor in neighbors:
					if neighbor not in visited_nodes and neighbor not in open_queue:
						open_queue.append(neighbor)
						ttl[neighbor] = ttl[current] - 1

			print("- Current: {}\n- Neighbors: {}\n- Open Queue: {}\n- Visited Nodes: {}\n====="
	 			.format(current, neighbors, open_queue, visited_nodes))
			plt.plot([box[0] for box in visited_nodes], [box[1] for box in visited_nodes],
				marker="s", color="blue", markersize=2, linestyle = '')
			plt.show()

			visited_nodes.add(current)
			current = open_queue.pop()
		"""

		visited = set()
		queue = deque((node, ttl) for node in line_boxes)

		# Explore neighbors until the queue is empty
		while queue:
			node, ttl = queue.popleft()

			# Check if the node has already been visited or if TTL is expired
			if node in visited or ttl < 0:
				continue

			# Add the node to the visited set
			visited.add(node)

			# Explore the neighbors of the node with a decremented TTL
			for neighbor in self.unoccupied_neighbors(node):
				queue.append((neighbor, ttl - 1))

		#return visited
		# Place boxes into grid
		for node in visited:
			self.put(node, private_input=True)


	def get_ranges(self):
		"""
		Find the minimum and maximum indices for each dimension of the grid.
		"""
		min_indices = tuple(min(dim) for dim in zip(*self.grid.keys()))
		max_indices = tuple(max(dim) for dim in zip(*self.grid.keys()))
		return min_indices, max_indices

	def write_png(self, path):
		if not have_pypng:
			raise Exception("Missing library pypng")

		min_indices, max_indices = self.get_ranges()
		
		width = 1 + max_indices[0] - min_indices[0]
		height = 1 + max_indices[1] - min_indices[1]

		max_value = max(self.grid.values())

		data = []
		for y in range(height):
			row = []
			for x in range(width):
				value = self.grid.get((x, y), 0)
				if value == 0:
					# Empty grid cells will be black (0)
					row.append(0)
				else:
					# Occupied cells will range from mid-gray to white (255)
					color = int(127 * value / (max_value + 1)) + 128
					row.append(color)
			data.append(row)

		with open(path, "wb") as output:
			writer = png.Writer(width, height, greyscale=True)
			writer.write(output, data)


def test_boxes_touching_line():
	# test boxes touching line
	grid = Grid(1)
	print("Getting boxes...")
	line = [(0.5, 0.5), (5.5, 7.5)]
	boxes = grid.boxes_touching_line(line)
	print(boxes)

	plt.plot([box[0] + 0.5 for box in boxes], [box[1] + 0.5 for box in boxes],
			 marker="s", color="red", markersize=20)
	plt.plot([p[0] for p in line], [p[1] for p in line], "k-")
	plt.xlim(-10, 10)
	plt.ylim(-10, 10)
	plt.show()

def test_neighbors():
	# test occupied neighbors?
	grid = Grid(5)
	line = [(-2, 1), (2, 1)]
	grid.put_line(line)
	point = (0, 0)
	neighbors = grid.unoccupied_neighbors(point)
	print("Neighbors of {} are {}".format(point, neighbors))
	print("Boxes in the grid:  {}".format([box for box in grid]))

	plt.plot([box[0] + 0.5 for box in grid], [box[1] + 0.5 for box in grid],
			 marker="s", color="red", markersize=20)
	plt.plot([box[0] + 0.5 for box in neighbors], [box[1] + 0.5 for box in neighbors],
			 marker="s", color="blue", markersize=18)
	plt.plot([p[0] for p in line], [p[1] for p in line], "k-")

	plt.xlim(-5, 5)
	plt.ylim(-5, 5)
	plt.show()

def test_image_import():
	print("Importing image...")
	boundaries = parse_data.get_paths_from_svg("image.svg")

	#print("Importing image...")
	#points = parser.getUserLocations("samples\\direct-route.csv")

	grid = Grid(5)
	print("Placing lines into grid...")
	for boundary in boundaries:
		grid.put_lines(boundary)
	
	print("Lines in grid...")
	plt.plot([box[0] + 0.5 for box in grid], [box[1] + 0.5 for box in grid],
			 marker="s", color="green", markersize=2, linestyle = '')
	plt.show()
	
def test_image_import():
	print("Importing image...")
	boundaries = parse_data.get_paths_from_svg("image.svg")

	#print("Importing image...")
	#points = parser.getUserLocations("samples\\direct-route.csv")

	grid_walls = Grid(5)
	print("Placing lines into grid...")
	for boundary in boundaries:
		grid_walls.put_lines(boundary)
	
	print("Lines in grid...")
	plt.plot([box[0] + 0.5 for box in grid_walls], [box[1] + 0.5 for box in grid_walls],
			 marker="s", color="green", markersize=2, linestyle = '')
	plt.show()

def test_put_line_weights():
	grid = Grid(1)
	line = [(0, 0), (5, 5)]
	grid.put_line_return_area(line, 2)

if __name__ == "__main__":
	print("Hello")
# Za Wardo (file initially named world.py)

# Global set of data structures
# Can have different threads of execution that can access all data threadsafe

# One thread for continuous updates

# How is this queried? Not sure
# Interprocess communication?
# Whatever, I will just implement all the base functions now without any structure

import math
from . import parse_data
from .grid import Grid
import heapq
from .geometry import lerp

class Floor():
	def __init__(self, boxes_per_meter=5):
		self.boxes_per_meter = boxes_per_meter
		self.walls = Grid(self.boxes_per_meter)
		self.user_locations = Grid(self.boxes_per_meter)
		self.explored_area = set()

	def update_walls_from_svg(self, filepath):
		boundaries = parse_data.get_paths_from_svg(filepath)
		for boundary in boundaries:
			self.walls.put_lines(boundary)
	
	def update_walls_from_list(self, boundary):
		self.walls.put_lines(boundary)
	
	def square_bloom_around_point(self, point, meters_wide):
		size = meters_wide * self.boxes_per_meter + 1
		for i in range(0, size):
				for j in range(0, size):
					x = point[0] + (-math.floor(size/2) + i) / self.user_locations.boxes_per_meter
					y = point[1] + (-math.floor(size/2) + j) / self.user_locations.boxes_per_meter
					self.explored_area.add((x, y))
	
	def place_line_of_blooms(self, line, meters_wide):
		# If distance is small, just do a bloom for each point?
		# Don't put a bloom for the last point, so that we can see the points later?
		
		# If lines[i] is the last point, then what happens? We just put it in
		# How do we know that this is the last point? Do we even need to handle that case here?
		#if i == len(lines)-1:
		#	self.square_bloom_around_point(weights, lines[i], meters_wide)
		#	return

		# Calculate distance between points
		p0, p1 = line
		distance = math.sqrt((p1[0]-p0[0])**2 + (p1[1] - p0[1])**2)

		# If points are too close together, just draw the first point and skip (draw the second point next round)
		if distance < meters_wide:
			self.square_bloom_around_point(p0, meters_wide)
			return
			
		# Points are too far, add some in between
		num_points = math.ceil(distance/meters_wide)
		num_segments = num_points - 1
		for j in range(num_segments):
			# lerp between p0 and p1 by j / segments
			pj = lerp(p0, p1, j/num_segments)
			self.square_bloom_around_point(pj, meters_wide)


	def generate_user_weighted_areas(self):
		# Naively weighting square areas
		meters_wide = 4
		
		#print("-Locations: {}".format(self.user_locations))
		for location in self.user_locations:
			self.square_bloom_around_point(location, meters_wide)

	def update_user_loations_from_csv(self, filepath):
		locations = parse_data.get_user_locations_csv_hololens(filepath)
		for point in locations:
			self.user_locations.put(point)
		self.generate_user_weighted_areas()
	
	def update_user_locations_from_list(self, locations: list):
		for point in locations:
			self.user_locations.put(point)
		self.generate_user_weighted_areas()
	
	def update_user_locations_as_lines(self, locations: list):
		len_locations = len(locations)
		line_width_score = 10
		for index in range(len_locations - 1):
			self.user_locations.put_line_return_area([locations[index], locations[index + 1]], line_width_score)

		# generate user weighted areas
		self.explored_area = set([point for point in self.user_locations])

	def h_euclidean_approx(self, start, end):
		score = math.sqrt((start[0] - end[0])**2 + (start[1] - end[1]) ** 2)
		return score if start in self.explored_area else score + 100

	def calculate_path(self, start, destination):
		path = self.a_star_search(start, destination, self.h_euclidean_approx)
		
		#return path
		
		smoothened_path = self.douglas_peucker_path_smoothening(path, 1/self.boxes_per_meter)
		return smoothened_path

	def points_close(self, a, b, tolerance=0.1):
		for i in range(len(a)):
			if not math.isclose(a[i], b[i], abs_tol=tolerance):
				return False
		return True

	def a_star_search(self, start, destination, h):
		# First, is get neighbors implemented? Yes, although won't tell if neighbor is in the grid
		openSet = []
		cameFrom = {}
		visited = set()
		gscore = {start: 0}			# Default value of infinity
		fscore = {start: h(start, destination)}	# Default value of infinity

		def getGScore(point):
			if point in gscore:
				return gscore[point]
			else:
				return float('inf')

		heapq.heappush(openSet, (h(start, destination), start))

		debug_x = []
		debug_y = []

		while len(openSet) != 0:
			current_f, current = heapq.heappop(openSet)

			# Efficiently check cells that have already been visited and avoid
			# duplicated effort.
			if current in visited:
				continue
			visited.add(current)

			# Fuzzy test if current cell matches destination.
			# Note that destination may contain arbitrary floating point values
			# such as (54.85721206665039, -12.640045166015625).
			if self.points_close(current, destination, tolerance=1.0/self.boxes_per_meter):
				return self.reconstruct_path(cameFrom, current)

			neighbors = self.walls.unoccupied_neighbors_with_weights(current)
			for neighbor_link in neighbors:
				neighbor = neighbor_link[0]
				weight = neighbor_link[1]
				if neighbor not in self.walls:
					if neighbor not in self.explored_area:
						weight = weight + 100

					tentative_neighbor_gscore = getGScore(current) + weight

					if tentative_neighbor_gscore < getGScore(neighbor):
						cameFrom[neighbor] = current
						gscore[neighbor] = tentative_neighbor_gscore
						fscore[neighbor] = tentative_neighbor_gscore + h(neighbor, destination)
						if (neighbor not in visited):
							heapq.heappush(openSet, (fscore[neighbor], neighbor))

	def reconstruct_path(self, cameFrom, current):
		total_path = [current]
		while current in cameFrom:
			current = cameFrom[current]
			total_path.append(current)
		total_path.reverse()
		return total_path
	
	def douglas_peucker_path_smoothening(self, points, epsilon):
		if points is None or len(points) < 3:
			return points
		
		def perpendicular_distance(point, line_start, line_end):
			if line_start == line_end:
				return distance(point, line_start)
			else:
				return abs((line_end[0] - line_start[0]) * (line_start[1] - point[1]) - (line_start[0] - point[0]) * (line_end[1] - line_start[1])) / distance(line_end, line_start)

		def distance(p, q):
			return ((p[0] - q[0])**2 + (p[1] - q[1])**2)**0.5

		dmax = 0
		index = 0
		end = len(points) - 1
		for i in range(1, end):
			d = perpendicular_distance(points[i], points[0], points[end])
			if d > dmax:
				index = i
				dmax = d
		if dmax > epsilon:
			left = self.douglas_peucker_path_smoothening(points[:index+1], epsilon)
			right = self.douglas_peucker_path_smoothening(points[index:], epsilon)
			return left[:-1] + right
		else:
			return [points[0], points[end]]


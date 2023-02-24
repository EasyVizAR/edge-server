# Za Wardo (file initially named world.py)

# Global set of data structures
# Can have different threads of execution that can access all data threadsafe

# One thread for continuous updates

# How is this queried? Not sure
# Interprocess communication?
# Whatever, I will just implement all the base functions now without any structure

import math
import parse_data
from grid import Grid
import heapq

class Floor():
	def __init__(self, boxes_per_meter=5):
		self.boxes_per_meter = boxes_per_meter
		self.walls = Grid(self.boxes_per_meter)
		self.user_locations = Grid(self.boxes_per_meter)
		self.explored_area = None

	def update_walls_from_svg(self, filepath):
		boundaries = parse_data.getPathsFromSvg(filepath)
		for boundary in boundaries:
			self.walls.put_lines(boundary)
	
	def update_walls_from_list(self, boundary):
		self.walls.put_lines(boundary)
	
	def generate_user_weighted_areas(self):
		weights = set()
		meters_wide = 4
		size = meters_wide * self.boxes_per_meter + 1
		for location in self.user_locations:
			for i in range(0, size):
				for j in range(0, size):
					x = location[0] + (-math.floor(size/2) + i) / self.user_locations.boxes_per_meter
					y = location[1] + (-math.floor(size/2) + j) / self.user_locations.boxes_per_meter
					weights.add((x, y))
		self.explored_area = weights
	
	def boundary_aware_bloom(self):
		radius = 4
		points = []
		for location in self.user_locations:
			for turn in range(0, 16):
				# calculate edge point
				degrees = math.pi * (turn / 8)
				edge_point = (location[0] + radius * math.cos(turn), location[1] + radius * math.sin(degrees))
				points.append(edge_point)

				# get boxes in that range
				# iterate through boxes to see which are filled, 
		
		return points

	def update_user_loations_from_csv(self, filepath):
		locations = parse_data.getUserLocations(filepath)
		for point in locations:
			self.user_locations.put(point)
	
	def update_user_locations_from_list(self, locations):
		for point in locations:
			self.user_locations.put(point)

	def h_euclidean_approx(self, start, end):
		score = math.sqrt((start[0] - end[0])**2 + (start[1] - end[1]) ** 2)
		return score if start in self.explored_area else score + 100

	def calculate_path(self, start, destination):
		self.generate_user_weighted_areas()
		path = self.a_star_search(start, destination, self.h_euclidean_approx)
		smoothened_path = self.douglas_peucker_path_smoothening(path, 1/self.boxes_per_meter)
		return smoothened_path

	def a_star_search(self, start, destination, h):
		# First, is get neighbors implemented? Yes, although won't tell if neighbor is in the grid
		openSet = []
		cameFrom = {}
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

			if current == destination:
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
						if (neighbor not in openSet):
							heapq.heappush(openSet, (fscore[neighbor], neighbor))

	def reconstruct_path(self, cameFrom, current):
		total_path = [current]
		while current in cameFrom:
			current = cameFrom[current]
			total_path.append(current)
		total_path.reverse()
		return total_path
	
	def douglas_peucker_path_smoothening(self, points, epsilon):
		if len(points) < 3:
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


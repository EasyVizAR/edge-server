# Za Wardo

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
import matplotlib.pyplot as plt

class Floor():
	def __init__(self, boxes_per_meter=5):
		self.boxes_per_meter = boxes_per_meter
		self.walls = Grid(self.boxes_per_meter)
		self.user_locations = Grid(self.boxes_per_meter)

	def update_walls_from_svg(self, filepath):
		boundaries = parse_data.getPathsFromSvg(filepath)
		for boundary in boundaries:
			self.walls.put_lines(boundary)
	
	def update_walls_from_list(self, boundary):
		self.walls.put_lines(boundary)
	
	def naive_bloom(self):
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

	def hEuclideanApprox(self, start, end):
		score = math.sqrt((start[0] - end[0])**2 + (start[1] - end[1]) ** 2)
		return score if start in self.explored_area else score + 100

	def calculatePath(self, start, destination):
		path = self.aStarSearch(start, destination, self.hEuclideanApprox)
		return path

	def aStarSearch(self, start, destination, h):
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
				return self.reconstructPath(cameFrom, current)

			#neighbors = self.walls.unoccupied_neighbors(current)
			neighbors = self.walls.unoccupied_neighbors_with_weights(current)
			#print("{} -> {}".format(current, [(neighbor, getGScore(neighbor)) for neighbor in neighbors]))
			for neighbor_link in neighbors:
				neighbor = neighbor_link[0]
				weight = neighbor_link[1]
				if neighbor not in self.walls:

					if neighbor not in self.explored_area:
						weight = weight + 100

					tentative_neighbor_gscore = getGScore(current) + weight

					if tentative_neighbor_gscore < getGScore(neighbor):
						# Better path to destination is found, record it
						cameFrom[neighbor] = current
						gscore[neighbor] = tentative_neighbor_gscore
						fscore[neighbor] = tentative_neighbor_gscore + h(neighbor, destination)
						#print(" - neighbor {} with fscore {}".format(neighbor, fscore[neighbor]))
						if (neighbor not in openSet):
							heapq.heappush(openSet, (fscore[neighbor], neighbor))
							#print(len(openSet))

	def reconstructPath(self, cameFrom, current):
		#print("Current node {} in cameFrom? {}".format(current, current in cameFrom))
		total_path = [current]
		while current in cameFrom:
			current = cameFrom[current]
			total_path.append(current)
		total_path.reverse()
		return total_path

##################
# Test functions #
##################

def test_boundary_aware_bloom():
	floor = Floor()
	floor.update_user_locations_from_list([(0, 0)])
	points = floor.boundary_aware_bloom()

	locations = floor.user_locations
	plt.plot([box[0] for box in locations], [box[1] for box in locations],
			 marker="s", color="blue", markersize=2, linestyle = '')
	
	plt.plot([p[0] for p in points], [p[1] for p in points], "r.")

	plt.show()

def test_map_explore_area():
	plt.rcParams['figure.dpi'] = 500
	plt.rcParams['savefig.dpi'] = 500

	floor = Floor()
	print("Updating walls...")
	floor.update_walls_from_svg("image.svg")

	print("Updating user locations...")
	#floor.update_user_loations_from_csv("samples\\direct-route.csv")
	floor.update_user_loations_from_csv("samples\\rh-search.csv")
	#print([p for p in floor.user_locations])
	
	print("Naive bloom...")
	floor.naive_bloom()

	print("Calculating path...")
	path = floor.calculatePath((0, -2), (20, 12))
	print(path)

	weights = floor.explored_area
	plt.plot([box[0] for box in weights], [box[1] for box in weights],
			 marker="s", color="green", markersize=2, linestyle = '')

	walls = floor.walls
	plt.plot([box[0] for box in walls], [box[1] for box in walls],
			 marker="s", color="black", markersize=2, linestyle = '')
	
	locations = floor.user_locations
	plt.plot([box[0] for box in locations], [box[1] for box in locations],
			 marker="s", color="blue", markersize=2, linestyle = '')

	plt.plot([p[0] for p in path], [p[1] for p in path], "r-")

	#plt.show()
	plt.savefig("images\\weighted_search_rh_search.png")

def test_easy_explore_area():
	floor = Floor(1)

	print("Updating walls...")
	boundary = []
	floor.update_walls_from_list(boundary)

	print("Updating user locations...")
	locations = [(0, 0)]
	floor.update_user_locations_from_list(locations)

	print("Calculate naive bloom...")
	floor.naive_bloom()

	print("Calculate path...")
	path = floor.calculatePath((-2, 2), (2, -4))

	weights = floor.explored_area
	plt.plot([box[0] for box in weights], [box[1] for box in weights],
			 marker="s", color="green", markersize=2, linestyle = '')

	walls = floor.walls
	plt.plot([box[0] for box in walls], [box[1] for box in walls],
			 marker="s", color="black", markersize=2, linestyle = '')

	locations = floor.user_locations
	plt.plot([box[0] for box in locations], [box[1] for box in locations],
			 marker="s", color="red", markersize=2, linestyle = '')
	
	plt.plot([p[0] for p in path], [p[1] for p in path], "b-")

	plt.show()





def test_walls_locations_path():
	floor = Floor()
	print("Updating walls...")
	floor.update_walls_from_svg("image.svg")

	print("Updating user locations...")
	floor.update_user_loations_from_csv("samples\\direct-route.csv")
	#print([p for p in floor.user_locations])
	
	print("Calculating path...")
	path = floor.calculatePath((0, -2), (20, 12))
	#print(path)

	walls = floor.walls
	plt.plot([box[0] + 0.5 for box in walls], [box[1] + 0.5 for box in walls],
			 marker="s", color="green", markersize=2, linestyle = '')
	
	locations = floor.user_locations
	plt.plot([box[0] + 0.5 for box in locations], [box[1] + 0.5 for box in locations],
			 marker="s", color="red", markersize=2, linestyle = '')

	plt.plot([p[0] for p in path], [p[1] for p in path], "r-")

	plt.show()

if __name__ == "__main__":
	test_map_explore_area()
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
	
	def calculate_bloom(self):
		weights = set()
		size_constant = 4
		size = size_constant * self.boxes_per_meter + 1
		for location in self.user_locations:
			for i in range(0, size):
				# for x in range(location[0] - 1, location[0] + 1 + 1/GRANULARITY, 1/GRANULARITY):
				for j in range(0, size):
					# for y in range(location[1] - 1, location[1] + 1 + 1/GRANULARITY, 1/GRANULARITY):
					x = location[0] + (-math.floor(size/2) + i) / self.user_locations.boxes_per_meter
					y = location[1] + (-math.floor(size/2) + j) / self.user_locations.boxes_per_meter
					weights.add((x, y))
		self.weights = weights

	def update_user_loations_from_csv(self, filepath):
		locations = parse_data.getUserLocations(filepath)
		for point in locations:
			self.user_locations.put(point)
	
	def update_user_locations_from_list(self, locations):
		for point in locations:
			self.user_locations.put(point)

	def hEuclideanApprox(self, start, end):
		score = (start[0] - end[0])**2 + (start[1] - end[1]) ** 2
		return score if start not in self.weights else score + 100

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

			neighbors = self.walls.unoccupied_neighbors(current)
			#print("{} -> {}".format(current, neighbors))
			for neighbor in neighbors:
				if neighbor not in self.walls:

					weight = 1 if neighbor not in self.weights else 100
					#if neighbor in self.weights:
					#	weight = 100
					#else:
					#	print("Neighbor {} is kinda far ngl", neighbor)

					tentativeGScore = getGScore(current) + weight

					if weight == 100:
						print("? {} vs {}".format(tentativeGScore, getGScore(neighbor)))

					if tentativeGScore < getGScore(neighbor):
						# Better path to destination is found, record it
						cameFrom[neighbor] = current
						gscore[neighbor] = tentativeGScore
						fscore[neighbor] = tentativeGScore + h(neighbor, destination)
						#print(" - neighbor {} in openSet? {}".format(neighbor, neighbor not in openSet))
						if (neighbor not in openSet):
							heapq.heappush(openSet, (h(neighbor, destination), neighbor))
							#print(len(openSet))

	def reconstructPath(self, cameFrom, current):
		#print("Current node {} in cameFrom? {}".format(current, current in cameFrom))
		total_path = [current]
		while current in cameFrom:
			current = cameFrom[current]
			total_path.append(current)
		total_path.reverse()
		return total_path

def test_easy_explore_area():
	floor = Floor(1)

	print("Updating walls...")
	boundary = [(0, 5), (5, 5), (5, -5), (0, -5)]
	floor.update_walls_from_list(boundary)

	print("Updating user locations...")
	locations = [(0, 0), (0, -3), (0, -6), (3, -6), (6, -6), (6, -3), (6, 0), (6, 3), (6, 6)]
	floor.update_user_locations_from_list(locations)

	print("Calculate naive bloom...")
	floor.calculate_bloom()

	print("Calculate path...")
	path = floor.calculatePath((0, 0), (6, 6))

	weights = floor.weights
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



if __name__ == "__main__":
	test_easy_explore_area()



def test_map_explore_area():
	floor = Floor()
	print("Updating walls...")
	floor.update_walls_from_svg("image.svg")

	print("Updating user locations...")
	floor.update_user_loations_from_csv("samples\\direct-route.csv")
	#print([p for p in floor.user_locations])
	
	print("Naive bloom...")
	floor.calculate_bloom()

	print("Calculating path...")
	path = floor.calculatePath((0, -2), (20, 12))
	#print(path)

	weights = floor.weights
	plt.plot([box[0] + 0.5 for box in weights], [box[1] + 0.5 for box in weights],
			 marker="s", color="green", markersize=2, linestyle = '')

	walls = floor.walls
	plt.plot([box[0] + 0.5 for box in walls], [box[1] + 0.5 for box in walls],
			 marker="s", color="blue", markersize=2, linestyle = '')
	
	locations = floor.user_locations
	plt.plot([box[0] + 0.5 for box in locations], [box[1] + 0.5 for box in locations],
			 marker="s", color="red", markersize=2, linestyle = '')

	plt.plot([p[0] for p in path], [p[1] for p in path], "r-")

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
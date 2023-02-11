# Za Wardo

# Global set of data structures
# Can have different threads of execution that can access all data threadsafe

# One thread for continuous updates

# How is this queried? Not sure
# Interprocess communication?
# Whatever, I will just implement all the base functions now without any structure

import parse_data
from grid import Grid
import heapq
import matplotlib.pyplot as plt

class Floor():
	def __init__(self):
		self.granularity = 5
		self.walls = Grid(self.granularity)

	def update_walls(self, filepath):
		boundaries = parse_data.getPathsFromSvg(filepath)
		for boundary in boundaries:
			self.walls.put_lines(boundary)

	def hEuclideanApprox(self, start, end):
		return (start[0] - end[0])**2 + (start[1] - end[1]) ** 2

	def calculatePath(self, start, destination):
		path = self.aStarSearch(start, destination, self.hEuclideanApprox)
		return path

	def aStarSearch(self, start, destination, h):
		# First, is get neighbors implemented? Yes, although won't tell if neighbor is in the grid

		#openSet = {start}
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

		while len(openSet) != 0:
			# Get node with lowest fscore value
			current_f, current = heapq.heappop(openSet)

			if current == destination:
				#print("YAHOOOO!!!")
				#print(cameFrom)
				return self.reconstructPath(cameFrom, current)
			
			#print("Length of OpenSet: {}".format(len(openSet)))
			neighbors = self.walls.unoccupied_neighbors(current)
			print("{} -> {}".format(current, neighbors))
			for neighbor in neighbors:
				if neighbor not in self.walls:
					tentativeGScore = getGScore(current) + 1
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

if __name__ == "__main__":
	floor = Floor()
	print("Updating walls...")
	floor.update_walls("image.svg")
	
	print("Calculating path...")
	path = floor.calculatePath((0, -2), (20, 12))
	print(path)

	walls = floor.walls
	plt.plot([box[0] + 0.5 for box in walls], [box[1] + 0.5 for box in walls],
			 marker="s", color="green", markersize=2, linestyle = '')
	plt.plot([p[0] for p in path], [p[1] for p in path], "r-")
	plt.show()
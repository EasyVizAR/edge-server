import matplotlib.pyplot as plt
import cProfile, pstats
from floor import Floor

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

def test_map_explore_timing(user_locations_filename):
	floor = Floor()
	profiler = cProfile.Profile()

	print("Starting timing analysis ...")
	profiler.enable()

	floor.update_walls_from_svg("image.svg")
	floor.update_user_loations_from_csv(user_locations_filename)
	floor.generate_user_weighted_areas()
	path = floor.calculate_path((0, -2), (20, 12))

	profiler.disable()
	print("Logging analysis to timing_logs.txt ...")

	with open('timing_logs.txt', 'w') as stream:
		stats = pstats.Stats(profiler, stream=stream).sort_stats('cumtime')
		stats.print_stats()

def test_map_explore_area(user_locations_filename, destination_plot_filename):
	floor = Floor()
	print("Updating walls...")
	floor.update_walls_from_svg("image.svg")

	print("Updating user locations...")
	#floor.update_user_loations_from_csv("samples\\direct-route.csv")
	floor.update_user_loations_from_csv(user_locations_filename)
	#print([p for p in floor.user_locations])
	
	print("Naive bloom...")
	floor.generate_user_weighted_areas()

	print("Calculating path...")
	path = floor.calculate_path((0, -2), (20, 12))

	print("Drawing map...")
	weights = floor.explored_area
	walls = floor.walls
	user_locations = floor.user_locations
	#draw_map(weights, walls, user_locations, path, destination_plot_filename)

def draw_map(weights, walls, user_locations, path, destination_plot_filename=None):
	plt.rcParams['figure.dpi'] = 500
	plt.rcParams['savefig.dpi'] = 500

	if weights is not None:
		plt.plot([box[0] for box in weights], [box[1] for box in weights],
			marker="s", color="green", markersize=2, linestyle = '')

	if walls is not None:
		plt.plot([box[0] for box in walls], [box[1] for box in walls],
			marker="s", color="black", markersize=2, linestyle = '')
	
	if user_locations is not None:
		plt.plot([box[0] for box in user_locations], [box[1] for box in user_locations],
			 marker="s", color="blue", markersize=2, linestyle = '')

	if path is not None:
		plt.plot([p[0] for p in path], [p[1] for p in path], "r-")

	if destination_plot_filename == None:
		plt.show()
	else:
		plt.savefig(destination_plot_filename)

def generate_images():
	test_map_explore_area("samples\\direct-route.csv", "images\\weighted_search_direct_route.png")
	test_map_explore_area("samples\\rh-search.csv", "images\\weighted_search_rh_search.png")
	test_map_explore_area("samples\\lh-search.csv", "images\\weighted_search_lh_search.png")

def test_easy_explore_area():
	floor = Floor(1)

	print("Updating walls...")
	boundary = []
	floor.update_walls_from_list(boundary)

	print("Updating user locations...")
	locations = [(0, 0)]
	floor.update_user_locations_from_list(locations)

	print("Calculate naive bloom...")
	floor.generate_user_weighted_areas()

	print("Calculate path...")
	path = floor.calculate_path((-2, 2), (2, -4))

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
	path = floor.calculate_path((0, -2), (20, 12))
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
	test_map_explore_timing("samples\\lh-search.csv")
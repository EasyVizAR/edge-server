import os
import matplotlib.pyplot as plt
import cProfile, pstats
from floor import Floor
from grid import Grid
import parse_data

##################
# Test functions #
##################

def test_map_timing(user_locations_filename):
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
	test_map_from_file("samples\\direct-route.csv", "images\\weighted_search_direct_route.png")
	test_map_from_file("samples\\rh-search.csv", "images\\weighted_search_rh_search.png")
	test_map_from_file("samples\\lh-search.csv", "images\\weighted_search_lh_search.png")


def test_easy_explore_area():
	floor = Floor(1)

	boundary = []
	floor.update_walls_from_list(boundary)

	locations = [(0, 0)]
	floor.update_user_locations_from_list(locations)
	path = floor.calculate_path((-2, 2), (2, -4))

	draw_map(floor.explored_area , floor.walls, floor.user_locations, path)

def test_medium_explore_area():
	floor = Floor(1)
	boundary = [(3, 3), (3, 2), (3, 1), (3, 0), (3, -1), (3, -2), (3, -3)]
	floor.update_walls_from_list(boundary)

	locations = [(0, 0), (3, 0), (5, 0)]
	floor.update_user_locations_from_list(locations)
	path = floor.calculate_path((0, 0), (5, 0))

	draw_map(floor.explored_area , floor.walls, floor.user_locations, path)

def test_map_user_path(user_locations_filename, destination_plot_filename=None):
	script_dir = os.path.dirname(os.path.abspath(__file__))
	walls_file_path = os.path.join(script_dir, "image.svg")

	floor = Floor()
	print("Updating walls...")
	floor.update_walls_from_svg(walls_file_path)
	
	#floor.update_user_loations_from_csv(user_locations_filename)
	locations_file_path = os.path.join(script_dir, user_locations_filename)
	locations = parse_data.get_user_locations_csv_hololens(locations_file_path)

	print("Updating user locations as lines...")
	floor.update_user_locations_as_lines(locations)
	
	print("Calculating path...")
	path = floor.calculate_path((0, -2), (20, 12))
	print("Path: {}", path)

	plot_file_path = None
	if destination_plot_filename != None:
		plot_file_path = os.path.join(script_dir, destination_plot_filename)
	draw_map(floor.explored_area, floor.walls, floor.user_locations, path, plot_file_path)

def test_if_douglas_peucker_runs():
	floor = Floor(1)
	path = [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)]
	smoothened_path = floor.douglas_peucker_path_smoothening(path, 0.2)
	print(smoothened_path)

def test_map_from_file(user_locations_filename, destination_plot_filename=None):
	floor = Floor()
	floor.update_walls_from_svg("image.svg")
	floor.update_user_loations_from_csv(user_locations_filename)
	path = floor.calculate_path((0, -2), (20, 12))
	print("Path: {}", path)

	weights = floor.explored_area
	walls = floor.walls
	user_locations = floor.user_locations
	draw_map(weights, walls, user_locations, path, destination_plot_filename)

def test_put_line_weights():
	grid = Grid(1)
	line = [(0, 0), (5, 5)]
	grid.put_line_return_area(line, 2)

	draw_map(None, None, grid.grid, None, None)

if __name__ == "__main__":
	#test_map_from_file("samples\\lh-search.csv")
	#test_map_timing("samples\\lh-search.csv")
	#test_medium_explore_area()
	#test_put_line_weights()
	test_map_user_path("samples\\lh-search.csv")
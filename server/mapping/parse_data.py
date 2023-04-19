# Parser object, handling all I/O?
# Only handling input at the time, how about output?
# Output usually handled by plt plotter?
# I can resolve that later, input matters the most right now

from xml.dom import minidom
import csv
import os

def get_paths_from_svg(filename):

	def parse_polyline_str(string):
		points = []
		for pstr in string.split(' '):
			point = pstr.split(',')
			points.append((float(point[0]), float(point[1])))
		return points

	doc = minidom.parse(filename)  # parseString also exists
	paths = [parse_polyline_str(line.getAttribute('points'))
			 for line in doc.getElementsByTagName('polyline')]

	doc.unlink()
	return paths

def get_user_locations_csv_hololens(filepath):
	points = []
	with open(filepath, newline='') as csvFile:
		csvReader = csv.reader(csvFile, delimiter=',')
		headerRead = False
		for row in csvReader:
			# Skip header
			if not headerRead:
				headerRead = True
				continue
			points.append((float(row[1]), float(row[3])))
	return points


def append_user_location_to_csv(filename, point):
    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create the full file path
    file_path = os.path.join(script_dir, filename)
    
    # Create the file if it doesn't exist
    if not os.path.isfile(file_path):
        with open(file_path, 'w', newline='') as csvfile:
            pass
    
    # Open the CSV file in append mode
    with open(file_path, 'a', newline='') as csvfile:
        # Create a CSV writer object
        csvwriter = csv.writer(csvfile)
        
        # Write the point to the CSV file
        csvwriter.writerow(point)

if __name__ == '__main__':
	append_user_location_to_csv("_test_csv_append.csv", (1, 1))
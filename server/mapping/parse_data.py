# Parser object, handling all I/O?
# Only handling input at the time, how about output?
# Output usually handled by plt plotter?
# I can resolve that later, input matters the most right now

from xml.dom import minidom
import csv

def getPathsFromSvg(filename):

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

def getUserLocations(self, filepath):
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
from server.headset.headsetrepository import get_headset_repository
from server.maps.maprepository import get_map_repository

mapRepo = get_map_repository()
headsetRepo = get_headset_repository()

mapRepo.add_map('cs-1', 'CS 1st Floor', '/uploads/firstfloor.svg')
mapRepo.create_image('maps', {'mapID': 'cs-1'}, 'image/svg+xml', [-35.44230853629791, -1.7768587228105028, 39.10819374001562, 52.83971533602437])
headsetRepo.add_headset('Headset-1', {
        "x": 1,
        "y": 0,
        "z": 0
    }, 'cs-1')

mapRepo.add_map('cs-2', 'CS 2nd Floor', '/uploads/secondfloor.svg')
mapRepo.create_image('maps', {'mapID': 'cs-2'}, 'image/svg+xml', [-35.44230853629791, -1.7768587228105028, 39.10819374001562, 52.83971533602437])
headsetRepo.add_headset('Headset-1', {
        "x": 0,
        "y": 0,
        "z": 0
    }, 'cs-2')
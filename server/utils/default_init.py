def create_dummy_objects():
    mapRepo = get_map_repository()
    headsetRepo = get_headset_repository()
    URL = 'https://pages.cs.wisc.edu/~hartung/easyvizar/seventhfloor.svg'

    mapRepo.add_map(id="cs-2", name="CS 2nd Floor", image="/uploads/secondfloor.svg", dummyData=False, viewBox=None)

    mapRepo.create_image("maps", data={"mapID": "cs-2"}, type="image/svg+xml",
                         viewBox=[-35.44230853629791, -1.7768587228105028, 39.10819374001562, 52.83971533602437])
    import urllib
    from pathlib import Path
    Path(f'server/frontend/build/uploads').mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(URL, f'server/frontend/build/uploads/secondfloor.svg')

    mapRepo.add_feature(None, "Fire-1", "fire", "cs-2", style={
        "leftOffset": "0",
        "placement": "point",
        "topOffset": "0"
    }, position={
        "x": -18.155353332377956,
        "y": 0,
        "z": 24.84940408323303
    })
    mapRepo.add_feature(None, "Fire-2", "fire", "cs-2", style={
        "leftOffset": "0",
        "placement": "point",
        "topOffset": "0"
    }, position={
        "x": -20.121572844333024,
      "y": 0,
      "z": 22.0459319977115
    })
    mapRepo.add_feature(None, "Fire-3", "fire", "cs-2", style={
        "leftOffset": "0",
        "placement": "floating",
        "topOffset": "0",
        "radius": "2"
    }, position={
        "x": -27.655278809303645,
        "y": 0,
        "z": 43.13419236018029
    })
    mapRepo.add_feature(None, "Fire-4", "fire", "cs-2", style={
        "leftOffset": "0",
        "placement": "floating",
        "topOffset": "0",
        "radius": "3"
    }, position={
        "x": -31.806898977366878,
        "y": 0,
        "z": 4.342902801868337
    })

    headsetRepo.add_headset("Headset-1", position={
        "x": -5,
        "y": 0,
        "z": 5
    }, mapId="cs-2", id=None)
    headsetRepo.add_headset("Headset-2", position={
        "x": -3,
        "y": 0,
        "z": 1
    }, mapId="cs-2", id=None)

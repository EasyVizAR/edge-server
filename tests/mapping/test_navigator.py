from unittest.mock import Mock
from unittest.mock import create_autospec
from server.mapping.navigator import Navigator
from server.location.models import Location

# TODO: Create mock objects (doesn't matter how correct they are)

# Website: https://easyvizar.wings.cs.wisc.edu/
# Get sample data from: https://easyvizar.wings.cs.wisc.edu/headsets/bab47744-89ea-4035-a157-7842b1391daa
# Sample location: https://easyvizar.wings.cs.wisc.edu/locations/1cc48e8d-890d-413a-aa66-cabaaa6e5458
# Sample routing: https://easyvizar.wings.cs.wisc.edu/locations/1cc48e8d-890d-413a-aa66-cabaaa6e5458/route?from=0,0,0&to=10,1,10

# Sample routing from running the server on my own machine: http://localhost:5000/locations/1cc48e8d-890d-413a-aa66-cabaaa6e5458/route?from=0,0,0&to=10,1,10

# Run test using: pytest .\tests\mapping\test_navigator.py

# FR-XR conference run by NTR International?
# NIST / 5x5 public safety innovation summit
# NIST / PSCR

# FUTURE: Store average height in grid for estimating floor

# TODO: Create test objects based on sample JSON data (From Lance's email)

# mock Layer object
"""
def test_navigator_find_path():
    headset = HeadsetModel("de8c33a6-efcd-41e8-81ea-1bd77102a758")
    print(headset)
    assert(False)
"""

# Test navigation with no headset
def test_navigator_find_path_no_headset():
    location = Location(id="1b06203d-0ef4-477d-bfb3-923ae0376c83",
                             name="Lance's House Remapped",
                             #model_path="data/incidents/82bf469a-6b48-42b0-aa7f-9365f5fa71e3/locations/1b06203d-0ef4-477d-bfb3-923ae0376c83/model.obj",
                             #model_url="/locations/1b06203d-0ef4-477d-bfb3-923ae0376c83/model"
                             )
    print(location)
    #layer = location.Layer.find(type="generated")
    #print(layer)

    #assert(False)
    #navigator = Navigator()
    #path = navigator.find_path(location, (0, 0), (10, 10))
    #assert(path == [(0, 0), (10, 10)])

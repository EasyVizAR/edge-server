import './Home.css';
import {Navbar, Container, Dropdown, DropdownButton, Form, Table, Nav, Button, Tab, Tabs} from 'react-bootstrap';
import NewLocation from './NewLocation.js';
import NewFeature from './NewFeature.js';
import NewIncidentModal from './NewIncidentModal.js';
import IncidentHistory from './IncidentHistory.js';
import AllHeadsets from './AllHeadsets.js';
import 'reactjs-popup/dist/index.css';
import React, {useState, useEffect} from 'react';
import moment from 'moment';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid, regular, brands} from '@fortawesome/fontawesome-svg-core/import.macro';
import {Helmet} from 'react-helmet';
import useStateSynchronous from './useStateSynchronous.js';

import fontawesome from '@fortawesome/fontawesome'
import {
    faBandage,
    faDoorClosed,
    faElevator,
    faExclamationTriangle,
    faFire,
    faFireExtinguisher,
    faHeadset,
    faMessage,
    faSquare,
    faStairs,
    faTruckMedical,
    faUser,
} from "@fortawesome/free-solid-svg-icons";

fontawesome.library.add(faBandage, faDoorClosed, faElevator,
    faExclamationTriangle, faFire, faFireExtinguisher, faHeadset, faMessage,
    faSquare, faStairs, faTruckMedical, faUser);

function Home(props) {
    const host = window.location.hostname;
    const port = props.port;

    // Map feature type -> FA icon
    const icons = {
        fire: solid('fire'),
        warning: solid('triangle-exclamation'),
        injury: solid('bandage'),
        door: solid('door-closed'),
        elevator: solid('elevator'),
        stairs: solid('stairs'),
        user: solid('user'),
        object: solid('square'),
        extinguisher: solid('fire-extinguisher'),
        message: solid('message'),
        headset: solid('headset'),
    }

    const buttonStyle = {
        marginBottom: "20px"
    }

    const mapIconSize = 7;
    const circleSvgIconSize = 11;

    const [selectedLocation, setSelectedLocation] = useState('');
    const [features, setFeatures] = useState([]);
    const [selectedImage, setSelectedImage] = useState('');
    const [headsets, setHeadsets] = useState([]);
    const [combinedMapObjects, setCombinedMapObjects] = useState([]);
    const [locations, setLocations] = useState([]);
    const [showNewFeature, displayNewFeature] = useState(false);
    const [locationLoaded, setLocationLoaded] = useState(false);
    const [crossHairIcon, setCrossHairIcon] = useState("/icons/headset16.png");
    const [inEditModeLocation, setInEditModeLocation] = useState({
        status: false,
        rowKey: null
    });
    const [pointCoordinates, setPointCoordinates] = useState([]);
    const [inEditModeHeadset, setInEditModeHeadset] = useState({
        status: false,
        rowKey: null
    });
    const [cursor, setCursor] = useState('auto');
    const [changedHeadsetName, setChangedHeadsetName] = useState(null);
    const [changedLocation, setChangedLocation] = useState(null);
    const [clickCount, setClickCount] = useState(0);
    const [iconIndex, setIconIndex] = useState(null);
    const [headsetsChecked, setHeadsetsChecked] = useState(false);
    const [featuresChecked, setFeaturesChecked] = useState(false);
    const [sliderValue, setSliderValue] = useState(0);
    const [currLocationName, setCurrLocationName] = useState('');
    const [placementType, setPlacementType] = useState('');
    const [tab, setTab] = useState('location-view');
    const [historyData, setHistoryData] = useState([]);

    const incidentInfo = useStateSynchronous(-1);
    const incidentName = useStateSynchronous('');
    const currentIncident = useStateSynchronous(-1);

    useEffect(() => {
        get_locations();
        getCurrentIncident();
        getHeadsets();
    }, []);

    useEffect(() => {
        combineMapObjects();
    }, [features, setFeatures]);

    useEffect(() => {
    }, [combinedMapObjects, setCombinedMapObjects]);

    useEffect(() => {
        combineMapObjects();
    }, [headsets, setHeadsets])

    useEffect(() => {
        if (selectedLocation == '' && locations.length > 0)
            setSelectedLocation(getDefaultLocationSelection());
    }, [locations, setLocations]);

    useEffect(() => {
        setSelectedImage(getMapImage(selectedLocation));
    }, [selectedLocation, setSelectedLocation]);


    // time goes off every 10 seconds to refresh headset data
    useEffect(() => {
        const timer = setTimeout(() => getHeadsets(), 1e4)
        return () => clearTimeout(timer)
    });

    useEffect(() => {
        const imgUrl = selectedImage.split("?")[0] + "?" + Math.floor(Math.random() * 100);
        const timer = setTimeout(() => {
            if (cursor != 'crosshair') // trigger only if not in on Location edit mode
                setSelectedImage(imgUrl)
        }, 6e4) // 60 secs
        return () => clearTimeout(timer)
    });

    useEffect(() => {
        combineMapObjects();
    }, [featuresChecked, setFeaturesChecked]);

    useEffect(() => {
        combineMapObjects();
    }, [headsetsChecked, setHeadsetsChecked]);

    const changeMapObjects = (e, v) => {

    };

    const changeMapObjectsContainer  = (e) => {
        if (e.target.id == 'features-switch') {
            setFeaturesChecked(e.target.checked);
        }
        if (e.target.id == 'headsets-switch') {
            setHeadsetsChecked(e.target.checked);
        }
        console.log(e);
    };

    const combineMapObjects = () => {
        if (!locationLoaded)
            return;
        var combinedMapObjectList = [];

        if (featuresChecked)
            for (const i in features) {
                const v = features[i];
                if (selectedLocation != v.mapId)
                    continue;
                combinedMapObjectList.push({
                    'id': v.id,
                    'mapId': v.mapId,
                    'name': v.name,
                    'scaledX': convertVector2Scaled(v.positionX, v.positionZ)[0],
                    'scaledY': convertVector2Scaled(v.positionX, v.positionZ)[1],
                    'iconValue': v.iconValue,
                    'radius': v.radius,
                    'placement': v.placement,
                    'editing': v.editing
                });
            }

        if (headsetsChecked)
            for (const i in headsets) {
                const v = headsets[i];
                if (selectedLocation != v.mapId)
                    continue;
                combinedMapObjectList.push({
                    'id': v.id,
                    'mapId': v.mapId,
                    'name': v.name,
                    'scaledX': convertVector2Scaled(v.positionX, v.positionZ)[0],
                    'scaledY': convertVector2Scaled(v.positionY, v.positionZ)[1],
                    'iconValue': 'headset',
                    'placement': 'headset'
                });
            }

        setCombinedMapObjects(combinedMapObjectList);
    }

    // function that sends request to server to get headset data
    function getHeadsets() {
        fetch(`http://${host}:${port}/headsets`)
            .then(response => {
                return response.json()
            }).then(data => {
              var fetchedHeadsets = []
              for (var k in data) {
                  var v = data[k];
                  if (selectedLocation === v.mapId) {
                    fetchedHeadsets.push({
                        'id': v.id,
                        'lastUpdate': v.lastUpdate,
                        'mapId': v.mapId,
                        'name': v.name,
                        'orientationX': v.orientation.x,
                        'orientationY': v.orientation.y,
                        'orientationZ': v.orientation.z,
                        'positionX': v.position.x,
                        'positionY': v.position.y,
                        'positionZ': v.position.z
                    });
                  }
              }
              setHeadsets(fetchedHeadsets);
            });
    }


    // gets list of locations from server
    function get_locations() {
        setLocations([]);

        fetch(`http://${host}:${port}/locations`)
            .then(response => response.json())
            .then(data => {
                var location_list = [];
                // var fetchedMaps = [];
                for (var key in data) {
                    // fetchedMaps.push({'id': data[key]['id'], 'name': data[key]['name'], 'image': data[key]['image'], 'viewBox': data[key]['viewBox']});
                    location_list.push({
                        'id': data[key]['id'],
                        'name': data[key]['name'],
                    });
                }
                setLocations(location_list);
                // setSelectedLocation(getDefaultLocationSelection());
            });
        // setSelectedLocation(getDefaultLocationSelection());
    }

    function updateIncidentInfo(){
      if (currentIncident.get() != -1 && (incidentName.get() == '' || incidentName.get() == null)){
        incidentInfo.set(currentIncident.get())
      }else{
        incidentInfo.set(incidentName.get());
      }
    }

    const onLocationLoad = () => {
        if (selectedLocation == 'NULL')
            return;

        setLocationLoaded(true);

        fetch(`http://${host}:${port}/locations/${selectedLocation}/features`)
            .then(response => {
                if (response.ok) {
                    return response.json();
                }
            }).then(data => {

            let fetchedFeatures = []
            if (data == undefined || data == null || data[0] === undefined) {
                console.log("NO DATA FOR MAP")
            } else {
                for (let i in data) {
                    let v = data[i];

                    fetchedFeatures.push({
                        'id': v.id,
                        'mapId': v.mapId,
                        'name': v.name,
                        'positionX': v.position.x,
                        'positionY': v.position.y,
                        'positionZ': v.position.z,
                        'iconValue': v.type,
                        'radius': v.style.radius,
                        'placement': v.style.placement
                    });
                }
            }
            setFeatures(fetchedFeatures);

            fetch(`http://${host}:${port}/headsets`)
                .then(response => {
                    return response.json()
                }).then(data => {
                let fetchedHeadsets = []
                for (let k in data) {
                    let v = data[k];
                    if (selectedLocation === v.mapId) {
                        fetchedHeadsets.push({
                            'id': v.id,
                            'lastUpdate': v.lastUpdate,
                            'mapId': v.mapId,
                            'name': v.name,
                            'orientationX': v.orientation.x,
                            'orientationY': v.orientation.y,
                            'orientationZ': v.orientation.z,
                            'positionX': v.position.x,
                            'positionY': v.position.y,
                            'positionZ': v.position.z,
                            'scaledX': convertVector2Scaled(v.position.x, v.position.z)[0],
                            'scaledY': convertVector2Scaled(v.position.x, v.position.z)[1],
                            'iconValue': 'user'
                        });
                    }
                }
                setHeadsets(fetchedHeadsets);
            });

        });

    }

    const getMapImage = (mapId) => {
        var map = null;
        for (var i = 0; i < locations.length; i++) {
            if (locations[i].id == mapId) {
                map = locations[i];
                break;
            }
        }
        if (map == null)
            return '';

        return `http://${host}:${port}/${map['image']}`;
        // return "http://pages.cs.wisc.edu/~hartung/easyvizar/seventhfloor.png";
        // if ("2e1a03e6-3d9d-11ec-a64a-0237d8a5e2fd" === mapId) {
        //     return `http://${host}:${port}/uploads/seventhfloor.png`;
        // } else if ("0a820028-3d9d-11ec-a64a-0237d8a5e2fd" === mapId) {
        //     return "https://media.istockphoto.com/photos/dramatic-sunset-over-a-quiet-lake-picture-id1192051826?k=20&m=1192051826&s=612x612&w=0&h=9HyN74dQTBcTZXB7g-BZp6mXV3upTgSvIav0x7hLm-I=";
        // } else {
        //     return "http://pages.cs.wisc.edu/~hartung/easyvizar/seventhfloor.png";
        // }
    }

    const handleLocationSelection = (e, o) => {
        setSelectedLocation(e);

        for (var x in locations){
          if (locations[x]['id'] == e){
            setCurrLocationName(locations[x]['name']);
          }
        }
        setFeaturesChecked(false);
        setHeadsetsChecked(false);
    }

    const getDefaultLocationSelection = () => {
        if (locations.length == 0)
            return 'NULL';
        setCurrLocationName(locations[0]['name']);
        return locations[0]['id'];
    }

    const getDefaultMapImage = () => {
        return getMapImage(getDefaultLocationSelection());
    }

    const convert2Pixel = (r) => {
        var map = {};
        for (var i = 0; i < locations.length; i++) {
            if (locations[i]['id'] == selectedLocation)
                map = locations[i];
        }
        if (Object.keys(map).length === 0 || !locationLoaded)
            return 0;
        const width = map['viewBox'][2];
        return document.getElementById('map-image').offsetWidth / width * r;
    }

    const convertVector2Scaled = (x, yy) => {
        var list = [];
        var map = {};
        for (var i = 0; i < locations.length; i++) {
            if (locations[i]['id'] == selectedLocation)
                map = locations[i];
        }
        if (Object.keys(map).length === 0 || !locationLoaded)
            return [0, 0];
        const xmin = map['viewBox'][0];
        const ymin = map['viewBox'][1];
        const width = map['viewBox'][2];
        const height = map['viewBox'][3];
        list.push(document.getElementById('map-image').offsetWidth / width * (x - xmin));
        list.push(document.getElementById('map-image').offsetHeight / height * (yy - ymin));

        return list;
    }

    const convertScaled2Vector = (px, py) => {
        var list = [];
        var map = {};
        for (var i = 0; i < locations.length; i++) {
            if (locations[i]['id'] == selectedLocation)
                map = locations[i];
        }
        if (Object.keys(map).length === 0 || !locationLoaded)
            return [0, 0];

        const xmin = map['viewBox'][0];
        const ymin = map['viewBox'][1];
        const width = map['viewBox'][2];
        const height = map['viewBox'][3];
        list.push((px * width / document.getElementById('map-image').offsetWidth + xmin));
        list.push((py * height / document.getElementById('map-image').offsetHeight + ymin));

        return list;
    }

    const changePointValue = (value, idx) => {
        var coordinates = pointCoordinates;
        coordinates[idx] = value;
        setPointCoordinates(coordinates);
    }

    const onMouseClick = (e) => {
        if (cursor != 'crosshair')
            return;

        let f = []
        for (let i in features) {
            f.push(features[i]);
        }
        if (clickCount > 0)
            f.pop();
        f.push({
            id: 'fire-1',
            LocationId: selectedLocation,
            name: 'Fire',
            positionX: convertScaled2Vector(e.clientX - e.target.getBoundingClientRect().left, e.clientY - e.target.getBoundingClientRect().top)[0],
            positionY: 0,
            positionZ: convertScaled2Vector(e.clientX - e.target.getBoundingClientRect().left, e.clientY - e.target.getBoundingClientRect().top)[1],
            scaledX: e.clientX - e.target.getBoundingClientRect().left,
            scaledY: e.clientY - e.target.getBoundingClientRect().top,
            icon: crossHairIcon,
            iconValue: icons[iconIndex].iconName,
            editing: 'true',
            placement: placementType
        });

        setFeatures(f);
        setPointCoordinates([convertScaled2Vector(e.clientX - e.target.getBoundingClientRect().left,
            e.clientY - e.target.getBoundingClientRect().top)[0],
            0,
            convertScaled2Vector(e.clientX - e.target.getBoundingClientRect().left,
                e.clientY - e.target.getBoundingClientRect().top)[1]]);

        setClickCount(clickCount + 1);
    }

    // shows the new feature popup
    const showFeature = (e) => {
        displayNewFeature(showNewFeature ? false : true);
    }

    function sort_list(arr){
       for(let i = 0; i < arr.length; i++){
          for(let j = 0; j < arr.length - i - 1; j++){
              if(parseInt(arr[j + 1]['created']) < parseInt(arr[j]['created'])){
                  [arr[j + 1],arr[j]] = [arr[j],arr[j + 1]]
              }
          }
      };
      return arr;
    }

    function getIncidentHistory(){
      const requestData = {
          method: 'GET',
          headers: {
              'Content-Type': 'application/json'
          }
      };

      fetch(`http://${host}:${port}/incidents`, requestData).then(response => {
        if (response.ok) {
          return response.json();
        }
      }).then(data => {
        var temp_data = [];
        for (var x in data){
          temp_data.push({
            'id': data[x]['id'],
            'name': data[x]['name'],
            'created': data[x]['created'],
          });
        }
        temp_data = sort_list(temp_data);
        setHistoryData(temp_data);
      });
    }

    // turns on Location editing
    const onEditLocation = (e, id) => {
        if (inEditModeLocation.status == true && inEditModeLocation.rowKey != null) {
            alert("Please save or cancel edit on other location before editing another location");
            return;
        }

        var location = {
          'name': locations[id]['name'],
        }
        setChangedLocation(location);

        setInEditModeLocation({
            status: true,
            rowKey: id
        });
    }

    // turns on headset editing
    const onEditHeadset = (e, id) => {
        if (inEditModeHeadset.status == true && inEditModeHeadset.rowKey != null) {
            alert("Please save or cancel edit on other headset before editing another headset");
            return;
        }

        setChangedHeadsetName(headsets[id]['name']);

        setInEditModeHeadset({
            status: true,
            rowKey: id,
            headset_name: headsets[id]['name']
        });
    }

    // saves the headset data
    const onSaveHeadsets = (e, index) => {
        const headset = null;
        const id = e.target.id.substring(7, e.target.id.length);
        const url = `http://${host}:${port}/headsets/${id}`;
        for (var x in headsets) {
            if (headsets[x]['id'] == id) {

                var dup = checkHeadsetName(headsets[x]['name'], headsets[x]['id']);
                if (dup) {
                    var conf = window.confirm('There is another headset with the same name. Are you sure you want to continue?');
                    if (!conf) {
                        return;
                    }
                }

                const requestData = {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(headsets[x])
                };

                fetch(url, requestData).then(response => {
                  setChangedHeadsetName(headsets[x]['name']);
                  onCancelHeadset(null, index);
                  getHeadsets();
                });
                break;
            }
        }
        console.log("headset updated");
    }

    // saves the Location data
    const saveLocation = (e, index) => {
        const id = e.target.id.substring(12, e.target.id.length);
        const url = `http://${host}:${port}/locations/${id}`;
        var i = 0;
        for (var x in locations) {
            if (locations[x]['id'] == id) {

                var dup_name = checkLocationName(locations[i]['name'], locations[x]['id']);
                if (dup_name) {
                    var conf = window.confirm('There is another location with the same name. Are you sure you want to continue?');
                    if (!conf) {
                        return;
                    }
                }

                const requestData = {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(locations[x])
                };
                fetch(url, requestData).then(response => {

                  var new_location = {
                    'name': locations[x]['name']
                  };
                  setChangedLocation(new_location);
                  onCancelLocation(index);
                  get_locations();
                });
                break;
            }
            i = i + 1
        }

    }

    // cancels Location editing
    const onCancelLocation = (index) => {
        for (var x in locations){
          if (x == index){
            locations[x]['name'] = changedLocation['name'];
            break;
          }
        }

        setChangedLocation(null);

        // reset the inEditMode state value
        setInEditModeLocation({
            status: false,
            rowKey: null
        });
    }

    // turns off headset editing
    const onCancelHeadset = (element, index) => {

        for (var x in headsets){
          if (x == index){
            headsets[x]['name'] = changedHeadsetName;
            break;
          }
        }

        setChangedHeadsetName(null);

        setInEditModeHeadset({
            status: false,
            rowKey: null
        });
    }

    // onchange handler for updating headset name
    const updateHeadsetName = (e) => {
        var newHeadsets = [];
        var prefix = "headsetName";
        var headset_id = e.target.id.substring(prefix.length, e.target.id.length);

        for (var x in headsets) {
            if (headsets[x]['id'] == headset_id) {
                headsets[x]['name'] = e.target.value;
            }
            newHeadsets.push(headsets[x]);
        }
        setHeadsets(newHeadsets);
    }

    // onchange handler for updating Location image
    const updateImage = (e) => {
        var newLocations = [];
        var prefix = "mapImage";
        var image_id = e.target.id.substring(prefix.length, e.target.id.length);
        for (var x in locations) {
            if (locations[x]['id'] == image_id) {
                //locations[x]['image'] = e.target.value;
                //inEditModeMap.map_image = e.target.value;
            }
            //newLocations.push(locations[x]);
        }
        //setLocations(newLocations);
    }

    // on change handler for updating Location name
    const updateLocationName = (e) => {
        var newLocations = [];
        var prefix = "locationName";
        var location_id = e.target.id.substring(prefix.length, e.target.id.length);

        for (var x in locations) {
            if (locations[x]['id'] == location_id) {
                locations[x]['name'] = e.target.value;
                inEditModeLocation.location_name = e.target.value;
            }
            newLocations.push(locations[x]);
        }
        setLocations(newLocations);
    }

    // checks if an image associated with a map already exists
    //function checkMapImage(image, id) {
        //for (var x in locations) {
            //if (locations[x]['image'] === image && locations[x]['id'] != id) {
                //return true;
            //}
        //}
        //return false;
    //}

    // checks if a Location name already exists
    function checkLocationName(name, id) {
        for (var x in locations) {
            if (locations[x]['name'] === name && locations[x]['id'] != id) {
                console.log(locations[x]['name'] + '.............' + locations[x]['id'])
                return true;
            }
        }
        return false;
    }

    // check if a headset name already exists
    function checkHeadsetName(name, id) {
        for (var x in headsets) {
            if (headsets[x]['name'] == name && headsets[x]['id'] != id) {
                return true;
            }
        }
        return false;
    }

    const toggleCursor = (e) => {
        if (cursor == 'crosshair') {
            setCursor('auto');
            if (clickCount > 0) {
                let f = []
                for (let i in features) {
                    f.push(features[i]);
                }
                f.pop();
                setFeatures(f);
                setClickCount(0);
            }
        } else {
            setCursor('crosshair');
            setClickCount(0);
        }
    }

    const changeIcon = (v) => {
        setCrossHairIcon(v);
    }

    // deletes headset with the id and name
    function deleteHeadset(id, name) {
        const del = window.confirm("Are you sure you want to delete headset '" + name + "'?");
        if (!del) {
            return;
        }

        const url = `http://${host}:${port}/headsets/${id}`;
        const requestData = {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        };

        fetch(url, requestData)
            .then(response => {
                for (var x in headsets) {
                    if (headsets[x]['id'] == id) {
                        headsets.pop(headsets[x]);
                    }
                }
                getHeadsets();
            });
    }

    function deleteLocation(id, name) {
        const del = window.confirm("Are you sure you want to delete Location '" + name + "'?");
        if (!del) {
            return;
        }

        const url = `http://${host}:${port}/locations/${id}`;
        const requestData = {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        };

        fetch(url, requestData)
            .then(response => {
                for (var x in locations) {
                    if (locations[x]['id'] == id) {
                        locations.pop(locations[x]);
                    }
                }
                get_locations();
            });
    }

    // code that creates the trash icons
    function TrashIcon(props) {
        const item = props.item;
        const itemId = props.id;
        const itemName = props.name;

        if (item == 'headset') {
            return (
                <Button style={{width: "30px", height: "30px"}} className='btn-danger table-btns'
                        onClick={(e) => deleteHeadset(itemId, itemName)} title="Delete Headset">
                    <FontAwesomeIcon icon={solid('trash-can')} size="lg"
                                     style={{position: 'relative', right: '0px', top: '-1px'}}/>
                </Button>
            );
        } else {
            return (
                <Button style={{width: "30px", height: "30px"}} className='btn-danger table-btns'
                        onClick={(e) => deleteLocation(itemId, itemName)} title="Delete Location">
                    <FontAwesomeIcon icon={solid('trash-can')} size="lg"
                                     style={{position: 'relative', right: '0px', top: '-1px'}}/>
                </Button>
            );
        }
    }

    function getCurrentIncident(){
      const requestData = {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json'
            }
      };
      fetch(`http://${host}:${port}/incidents/`, requestData)
        .then(response => {
          if (response.ok) {
            return response.json();
          }
        }).then(data => {
          if(data['incident_number'] != '' && data['incident_number'] != null){
            currentIncident.set(data['incident_number']);
          }
          if (data['incident_name'] != '' && data['incident_name'] != null){
            incidentName.set(data['incident_name']);
          }
          updateIncidentInfo();
        });
    }

    const getCircleSvgSize = (r) => {
        return Math.max(convert2Pixel(r) * 2, document.getElementById('map-image').offsetHeight / 100.0 * circleSvgIconSize);
    }

    const getCircleSvgShift = (r) => {
        return (Math.max(convert2Pixel(r) * 2, document.getElementById('map-image').offsetHeight / 100.0 * circleSvgIconSize)
            - document.getElementById('map-image').offsetHeight / 100.0 * mapIconSize) / 2.0;
    }

    return (
        <div className="Home">
            <Helmet>
              <title>EasyViz AR</title>
            </Helmet>
            <div className="home-body">
                <Tabs activeKey={tab} className="mb-3 tabs" onSelect={(t) => setTab(t)}>
                  <Tab eventKey="location-view" title="Location View">
                    <div className="location-nav">
                      <div className="dropdown-container">
                          <DropdownButton id="location-dropdown" title="Select Location" onSelect={handleLocationSelection}
                                          defaultValue={getDefaultLocationSelection}>
                              {
                                  locations.map((e, index) => {
                                      return <Dropdown.Item eventKey={e.id}>{e.name}</Dropdown.Item>
                                  })
                              }
                          </DropdownButton>
                      </div>

                      <div className="header-button">
                          <Button variant="secondary" title="Add Feature" value="Add Feature"
                                  onClick={(e) => showFeature(e)}>Add Feature</Button>
                      </div>

                      <div className="QR-code-btn header-button">
                        <Button title="Location QR Code" variant="secondary" href={"/locations/" + selectedLocation + "/qrcode.svg"} target="_blank">Location QR Code</Button>
                      </div>
                    </div>

                    <div className='home-content'>
                      <NewFeature port={port} showNewFeature={showNewFeature} changeCursor={toggleCursor} changeIcon={changeIcon}
                                  pointCoordinates={pointCoordinates} changePointValue={changePointValue} mapID={selectedLocation}
                                  setIconIndex={setIconIndex} sliderValue={sliderValue} setSliderValue={setSliderValue}
                                  setPlacementType={setPlacementType} placementType={placementType}/>

                      <div style={{textAlign: 'left', marginBottom: '15px'}}>
                        <div style={{display: 'inline-block'}}>
                          <p className="text-muted" style={{fontSize:'0.875em', marginBottom: '0px'}}>Location Name</p>
                          <h4 style={{marginTop: '0px'}}>{currLocationName != '' ? (currLocationName) : ('No Location Selected')}</h4>
                        </div>
                        <div style={{marginLeft: '15px', display: 'inline-block'}}>
                          <p className="text-muted" style={{fontSize:'0.875em', marginBottom: '0px'}}>Incident Name</p>
                          <h4 style={{marginTop: '0px'}}>{incidentInfo.get()}</h4>
                        </div>
                      </div>
                      <div className="location-image-container">
                          <img id="map-image" src={selectedImage} alt="Image of the environment" onLoad={onLocationLoad}
                               onClick={onMouseClick} style={{cursor: cursor}}/>
                          {combinedMapObjects.map((f, index) => {
                              return f.placement == 'floating' && f.editing == 'true'?
                                  <div>
                                      <FontAwesomeIcon icon={icons[f.iconValue]['iconName']} className="features" id={f.id}
                                                       alt={f.name} style={{
                                          left: combinedMapObjects[index].scaledX,
                                          top: combinedMapObjects[index].scaledY,
                                          height: mapIconSize + "%",
                                          pointerEvents: "none"
                                      }}/>
                                      <svg className="features"
                                           width={getCircleSvgSize(sliderValue)}
                                           height={getCircleSvgSize(sliderValue)}
                                           style={{
                                               left: combinedMapObjects[index].scaledX - getCircleSvgShift(sliderValue),
                                               top: combinedMapObjects[index].scaledY - getCircleSvgShift(sliderValue),
                                               pointerEvents: "none"
                                           }}>
                                    <circle style={{pointerEvents: "none"}} cx={getCircleSvgSize(sliderValue) / 2}
                                                  cy={getCircleSvgSize(sliderValue) / 2}
                                                  r={convert2Pixel(sliderValue)} fill-opacity="0.3" fill="#0000FF"/>
                                      </svg>
                                  </div>
                                  : f.placement == 'floating' ?
                                      <div>
                                          <FontAwesomeIcon icon={icons[f.iconValue]['iconName']} className="features" id={f.id}
                                                           alt={f.name} style={{
                                              left: combinedMapObjects[index].scaledX,
                                              top: combinedMapObjects[index].scaledY,
                                              height: mapIconSize + "%",
                                              pointerEvents: "none"
                                          }}/>
                                          <svg className="features"
                                               width={getCircleSvgSize(f.radius)}
                                               height={getCircleSvgSize(f.radius)}
                                               style={{
                                                   left: combinedMapObjects[index].scaledX - getCircleSvgShift(f.radius),
                                                   top: combinedMapObjects[index].scaledY - getCircleSvgShift(f.radius),
                                                   pointerEvents: "none"
                                               }}>
                                        <circle style={{pointerEvents: "none"}} cx={getCircleSvgSize(f.radius) / 2}
                                                      cy={getCircleSvgSize(f.radius) / 2}
                                                      r={convert2Pixel(f.radius)} fill-opacity="0.3" fill="#0000FF"/>
                                          </svg>
                                      </div>
                                      : <FontAwesomeIcon icon={icons[f.iconValue]['iconName']} className="features" id={f.id}
                                                   alt={f.name}
                                                      style={{
                                                          left: combinedMapObjects[index].scaledX,
                                                          top: combinedMapObjects[index].scaledY,
                                                    height: mapIconSize + "%",
                                                    pointerEvents: "none"
                                                      }}/>
                          })}
                      </div>
                      <div style={{width: 'max-content'}}>
                          <Form onChange={changeMapObjectsContainer}>
                              <Form.Check
                                  onClick={changeMapObjects(this, 'headsets')}
                                  type="switch"
                                  id="headsets-switch"
                                  label="Headsets"
                                  checked={headsetsChecked}
                              />
                              <Form.Check
                                  onChange={changeMapObjects(this, 'features')}
                                  type="switch"
                                  id="features-switch"
                                  label="Features"
                                  checked={featuresChecked}
                              />
                          </Form>
                      </div>
                      <div style={{marginTop: "20px"}}>
                          <div>
                            <h3 style={{textAlign: "left"}}>Headsets</h3>
                          </div>
                          <Table striped bordered hover>
                              <thead>
                              <tr>
                                  <th rowSpan='2'>Headset ID</th>
                                  <th rowSpan='2'>Name</th>
                                  <th rowSpan='2'>Location ID</th>
                                  <th rowSpan='2'>Last Update</th>
                                  <th colSpan='3'>Position</th>

                                  <th colSpan='3'>Orientation</th>
                                  <th colSpan='1'></th>
                              </tr>
                              <tr>
                                  <th>X</th>
                                  <th>Y</th>
                                  <th>Z</th>
                                  <th>X</th>
                                  <th>Y</th>
                                  <th>Z</th>
                                  <th></th>
                              </tr>
                              </thead>
                              <tbody>
                              {
                                  headsets.length > 0 ? (
                                    headsets.map((e, index) => (
                                        <tr>
                                          <td>{e.id}</td>
                                          <td id={"headsetName" + index}>
                                              {
                                                  inEditModeHeadset.status && inEditModeHeadset.rowKey === index ? (
                                                      <input
                                                          value={headsets[index]['name']}
                                                          placeholder="Edit Headset Name"
                                                          onChange={updateHeadsetName}
                                                          name={"headsetinput" + e.id}
                                                          type="text"
                                                          id={'headsetName' + e.id}/>
                                                  ) : (
                                                      e.name
                                                  )
                                              }
                                          </td>
                                          <td>{e.mapId}</td>
                                          <td>{moment.unix(e.lastUpdate).fromNow()}</td>
                                          <td>{e.positionX}</td>
                                          <td>{e.positionY}</td>
                                          <td>{e.positionZ}</td>
                                          <td>{e.orientationX}</td>
                                          <td>{e.orientationY}</td>
                                          <td>{e.orientationZ}</td>
                                          <td>
                                              {
                                                  (inEditModeHeadset.status && inEditModeHeadset.rowKey === index) ? (
                                                      <React.Fragment>
                                                          <Button
                                                              className={"btn-success table-btns"}
                                                              id={'savebtn' + e.id}
                                                              onClick={(e) => onSaveHeadsets(e, index)}
                                                              title='Save'>
                                                              Save
                                                          </Button>

                                                          <Button
                                                              className={"btn-secondary table-btns"}
                                                              style={{marginLeft: 8}}
                                                              onClick={(event) => onCancelHeadset(event, index)}
                                                              title='Cancel'>
                                                              Cancel
                                                          </Button>
                                                      </React.Fragment>
                                                  ) : (
                                                      <Button
                                                          className={"btn-primary table-btns"}
                                                          onClick={(e) => onEditHeadset(e, index)}
                                                          title='Edit'>
                                                          Edit
                                                      </Button>
                                                  )
                                              }
                                          </td>
                                          <td>
                                              <div>
                                                  <TrashIcon item='headset' id={e.id} name={e.name}/>
                                              </div>
                                          </td>
                                      </tr>
                                  ))
                                ) : (
                                  <tr><td colspan="100%">No Headsets</td></tr>
                                )
                              }
                              </tbody>
                          </Table>
                      </div>
                      <div style={{marginTop: "20px"}}>
                          <div>
                            <h3 style={{textAlign: "left"}}>Locations</h3>
                          </div>
                          <Table striped bordered hover>
                              <thead>
                              <tr>
                                  <th rowSpan='2'>Location ID</th>
                                  <th rowSpan='2'>Name</th>
                              </tr>
                              </thead>
                              <tbody>
                              {
                                  locations.length > 0 ? (
                                    locations.map((e, index) => {
                                        return <tr>
                                            <td>{e.id}</td>
                                            <td>
                                                {
                                                    inEditModeLocation.status && inEditModeLocation.rowKey === index ? (
                                                        <input
                                                            placeholder="Edit Location Name"
                                                            name="input"
                                                            type="text"
                                                            id={'locationName' + e.id}
                                                            onChange={updateLocationName}
                                                            value={locations[index]['name']}/>
                                                    ) : (
                                                        e.name
                                                    )
                                                }
                                            </td>
                                            <td>
                                                {
                                                    (inEditModeLocation.status && inEditModeLocation.rowKey === index) ? (
                                                        <React.Fragment>
                                                            <Button
                                                                className={"btn-success table-btns"}
                                                                id={'locationsbtn' + e.id}
                                                                onClick={(e) => saveLocation(e, index)}
                                                                title='Save'>
                                                                Save
                                                            </Button>

                                                            <Button
                                                                className={"btn-secondary table-btns"}
                                                                style={{marginLeft: 8}}
                                                                onClick={() => onCancelLocation(index)}
                                                                title='Cancel'>
                                                                Cancel
                                                            </Button>
                                                        </React.Fragment>
                                                    ) : (
                                                        <Button
                                                            className={"btn-primary table-btns"}
                                                            onClick={(e) => onEditLocation(e, index)}
                                                            title='Edit'>
                                                            Edit
                                                        </Button>
                                                    )
                                                }
                                            </td>
                                            <td>
                                                <div>
                                                    <TrashIcon item='location' id={e.id} name={e.name}/>
                                                </div>
                                            </td>
                                        </tr>
                                    })
                                  ) : (
                                    <tr><td colspan="100%">No Locations</td></tr>
                                  )
                              }
                              </tbody>
                          </Table>
                      </div>
                    </div>
                  </Tab>
                  <Tab eventKey="create-location" title="Create Location">
                    <NewLocation port={port} getHeadsets={getHeadsets} getLocations={get_locations} setTab={setTab}/>
                  </Tab>
                  <Tab eventKey="create-incident" title="Create Incident">
                    <NewIncidentModal port={port} getHeadsets={getHeadsets} setLocations={setLocations}
                                      getCurrentIncident={getCurrentIncident} currentIncident={currentIncident} incidentName={incidentName}
                                      updateIncidentInfo={updateIncidentInfo} setTab={setTab} getIncidentHistory={getIncidentHistory} />
                  </Tab>
                  <Tab eventKey="incident-history" title="Incident History">
                    <IncidentHistory port={port} currentIncident={currentIncident} incidentName={incidentName}
                                     updateIncidentInfo={updateIncidentInfo} historyData={historyData}
                                     setHistoryData={setHistoryData} getIncidentHistory={getIncidentHistory}
                                     getLocations={get_locations} getHeadsets={getHeadsets} getCurrentIncident={getCurrentIncident}/>
                  </Tab>
                  <Tab eventKey="all-headsets" title="All Headsets">
                    <AllHeadsets port={port} getLocationHeadsets={getHeadsets} />
                  </Tab>

                </Tabs>
            </div>
        </div>
    );
}

export default Home;

import './App.css';
import {Navbar, Container, Dropdown, DropdownButton, Form, Table, Nav, Button} from 'react-bootstrap';
import NewMap from './NewMap.js';
import NewFeature from './NewFeature.js'
import 'reactjs-popup/dist/index.css';
import React, {useState, useEffect} from 'react';
import moment from 'moment';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome'
import {solid, regular, brands} from '@fortawesome/fontawesome-svg-core/import.macro'

import fontawesome from '@fortawesome/fontawesome'
import {faCheckSquare, faCoffee, faFire} from '@fortawesome/fontawesome-free-solid'
import {
    faBandage,
    faDoorClosed,
    faExclamationTriangle,
    faHeadset,
    faTruckMedical
} from "@fortawesome/free-solid-svg-icons";

fontawesome.library.add(faCheckSquare, faCoffee, faFire, faTruckMedical, faExclamationTriangle, faBandage, faDoorClosed, faHeadset);

export const port = '5003'


function App() {
    const host = 'localhost';

    const icons = ['fire', 'truck-medical', 'triangle-exclamation', 'bandage', 'door-closed', 'headset'];
    const iconPaths = [];
    iconPaths.push(solid('fire'));
    iconPaths.push(solid('truck-medical'));
    iconPaths.push(solid('triangle-exclamation'));
    iconPaths.push(solid('bandage'));
    iconPaths.push(solid('door-closed'));
    iconPaths.push(solid('headset'));

    const buttonStyle = {
        marginBottom: "20px"
    }

    const [selectedMap, setSelectedMap] = useState('');
    const [features, setFeatures] = useState([]);
    const [selectedImage, setSelectedImage] = useState('');
    const [headsets, setHeadsets] = useState([]);
    const [combinedMapObjects, setCombinedMapObjects] = useState([]);
    const [maps, setMaps] = useState([]);
    const [popUpClass, displayModal] = useState(false);
    const [showNewMap, showMap] = useState(false);
    const [mapLoaded, setMapLoaded] = useState(false);
    const [crossHairIcon, setCrossHairIcon] = useState("/icons/headset16.png");
    const [inEditModeMap, setInEditModeMap] = useState({
        status: false,
        rowKey: null
    });
    const [pointCoordinates, setPointCoordinates] = useState([]);
    const [inEditModeHeadset, setInEditModeHeadset] = useState({
        status: false,
        rowKey: null
    });
    const [cursor, setCursor] = useState('auto');
    const [headsetNames, setHeadsetNames] = useState([]);
    const [mapNames, setMapNames] = useState([]);
    const [clickCount, setClickCount] = useState(0);
    const [iconIndex, setIconIndex] = useState(-1);
    const [headsetsChecked, setHeadsetsChecked] = useState(false);
    const [featuresChecked, setFeaturesChecked] = useState(false);

    useEffect(() => {
        get_maps();
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
        getHeadsets();
    }, []);

    useEffect(() => {
        setSelectedImage(getMapImage(selectedMap));
    }, [selectedMap, setSelectedMap]);


    // time goes off every 10 seconds to refresh headset data
    useEffect(() => {
        const timer = setTimeout(() => getHeadsets(), 1e4)
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
        if (!mapLoaded)
            return;
        var combinedMapObjectList = [];

        if (featuresChecked)
            for (const i in features) {
                const v = features[i];
                combinedMapObjectList.push({
                    'id': v.id,
                    'mapId': v.mapId,
                    'name': v.name,
                    'scaledX': convertVector2Scaled(v.positionX, v.positionZ)[0],
                    'scaledY': convertVector2Scaled(v.positionX, v.positionZ)[1],
                    'iconValue': v.iconValue
                });
            }

        if (headsetsChecked)
            for (const i in headsets) {
                const v = headsets[i];
                combinedMapObjectList.push({
                    'id': v.id,
                    'mapId': v.mapId,
                    'name': v.name,
                    'scaledX': convertVector2Scaled(v.positionX, v.positionZ)[0],
                    'scaledY': convertVector2Scaled(v.positionY, v.positionZ)[1],
                    'iconValue': 'headset'
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
            var headsetNamesList = []
            for (var k in data) {
                var v = data[k];
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
                headsetNamesList.push(v.name); // TODO: Question: why do we need this names list?
            }
            setHeadsets(fetchedHeadsets);
            setHeadsetNames(headsetNamesList); // TODO: Question: why do we need this names list?
        });
    }


    // gets list of maps from server
    function get_maps() {
        fetch(`http://${host}:${port}/maps`)
            .then(response => response.json())
            .then(data => {
                var map_names = []
                // var fetchedMaps = [];
                for (var key in data) {
                    // fetchedMaps.push({'id': data[key]['id'], 'name': data[key]['name'], 'image': data[key]['image'], 'viewBox': data[key]['viewBox']});
                    maps.push({
                        'id': data[key]['id'],
                        'name': data[key]['name'],
                        'image': data[key]['image'],
                        'viewBox': data[key]['viewBox']
                    });
                    var temp = {
                        'id': data[key]['id'],
                        'name': data[key]['name'],
                        'image': data[key]['image'],
                        'viewBox': data[key]['viewBox']
                    }
                    map_names.push(temp) // TODO: Question: why do we need this names list?
                }
                // setMaps(fetchedMaps); // TODO: Question: this is causing issues in  mapNames[index]['name'] in maps.map
                //  TODO: Question: because maps are refreshed but mapNames takes time. We should use the same state object in if-else in the HTML
                setMapNames(map_names) // TODO: Question: why do we need this names list?
                setSelectedMap(getDefaultMapSelection());
                setSelectedImage(getDefaultMapImage());
            });
        setSelectedMap(getDefaultMapSelection());
        setSelectedImage(getDefaultMapImage());
    }

    const onMapLoad = () => {
        if (selectedMap == 'NULL')
            return;

        setMapLoaded(true);

        fetch(`http://${host}:${port}/maps/${selectedMap}/features`)
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
                        'iconValue': v.style.icon
                    });
                }
            }
            setFeatures(fetchedFeatures);

            fetch(`http://${host}:${port}/headsets`)
                .then(response => {
                    return response.json()
                }).then(data => {
                let fetchedHeadsets = [] // TODO: Question: why do we need this names list?
                var headsetNamesList = []
                for (let k in data) {
                    let v = data[k];
                    if (selectedMap === v.mapId) {
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
                            'iconValue': 'headset'
                        });
                    }
                    headsetNamesList.push(v.name); // TODO: Question: why do we need this names list?
                }
                setHeadsets(fetchedHeadsets);
                setHeadsetNames(headsetNamesList); // TODO: Question: why do we need this names list?
            });

        });

    }

    const getMapImage = (mapId) => {
        var map = null;
        for (var i = 0; i < maps.length; i++) {
            if (maps[i].id == mapId) {
                map = maps[i];
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

    const handleMapSelection = (e, o) => {
        setSelectedMap(e);
        setFeaturesChecked(false);
        setHeadsetsChecked(false);
    }

    const getDefaultMapSelection = () => {
        if (maps.length == 0)
            return 'NULL';
        return maps[0]['id'];
    }

    const getDefaultMapImage = () => {
        return getMapImage(getDefaultMapSelection());
    }

    const convertVector2Scaled = (x, yy) => {
        var list = [];
        var map = {};
        for (var i = 0; i < maps.length; i++) {
            if (maps[i]['id'] == selectedMap)
                map = maps[i];
        }
        if (Object.keys(map).length === 0 || !mapLoaded)
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
        for (var i = 0; i < maps.length; i++) {
            if (maps[i]['id'] == selectedMap)
                map = maps[i];
        }
        if (Object.keys(map).length === 0 || !mapLoaded)
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
            mapId: selectedMap,
            name: 'Fire',
            positionX: convertScaled2Vector(e.clientX - e.target.getBoundingClientRect().left, e.clientY - e.target.getBoundingClientRect().top)[0],
            positionY: 0,
            positionZ: convertScaled2Vector(e.clientX - e.target.getBoundingClientRect().left, e.clientY - e.target.getBoundingClientRect().top)[1],
            scaledX: e.clientX - e.target.getBoundingClientRect().left,
            scaledY: e.clientY - e.target.getBoundingClientRect().top,
            icon: crossHairIcon,
            iconValue: iconPaths[iconIndex]
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
        if (showNewMap == false) {
            displayModal(popUpClass ? false : true)
        }
    }

    // shows the new map popup
    const showMapPopup = (e) => {
        if (popUpClass == false) {
            showMap(showNewMap ? false : true)
        }
    }

    // turns on map editing
    const onEditMap = (e, id) => {
        if (inEditModeMap.status == true && inEditModeMap.rowKey != null) {
            alert("Please save or cancel edit on other map before editing another map");
            return;
        }

        setInEditModeMap({
            status: true,
            rowKey: id,
            map_name: maps[id]['name'],
            map_image: maps[id]['image']
        });
    }

    // turns on headset editing
    const onEditHeadset = (e, id) => {
        if (inEditModeHeadset.status == true && inEditModeHeadset.rowKey != null) {
            alert("Please save or cancel edit on other headset before editing another headset");
            return;
        }

        setInEditModeHeadset({
            status: true,
            rowKey: id,
            headset_name: headsets[id]['name']
        });
    }

    // sends request to url, usually used for saving headset and map data. Reloads window on response
    const saveData = (url, requestData) => {
        console.log("Sending request to " + url);
        fetch(url, requestData)
            .then(response => {
                //window.location.reload(false);
            }).then(data => {
            console.log("data: " + data);
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
                saveData(url, requestData);
                headsetNames[x] = headsets[x]['name']
                break;
            }
        }
        onCancelHeadset(null, index);
        console.log("headset updated");
    }

    // saves the map data
    const saveMap = (e, index) => {
        console.log(e.target);
        const id = e.target.id.substring(7, e.target.id.length);
        const url = `http://${host}:${port}/maps/${id}`;
        var i = 0;
        for (var x in maps) {
            if (maps[x]['id'] == id) {

                var dup_name = checkMapName(mapNames[i]['name'], maps[x]['id']);
                if (dup_name) {
                    var conf = window.confirm('There is another map with the same name. Are you sure you want to continue?');
                    if (!conf) {
                        return;
                    }
                }

                var dup_image = checkMapImage(mapNames[i]['image'], maps[x]['id']);
                if (dup_image) {
                    var conf = window.confirm('There is another map with the same image. Are you sure you want to continue?');
                    if (!conf) {
                        return;
                    }
                }

                const requestData = {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(maps[x])
                };
                saveData(url, requestData);
                mapNames[x]['image'] = maps[x]['image']
                mapNames[x]['name'] = maps[x]['name']
                break;
            }
            i = i + 1
        }
        onCancelMap(index);
    }

    // cancels map editing
    const onCancelMap = (index) => {

        maps[index]['name'] = mapNames[index]['name']
        maps[index]['image'] = mapNames[index]['image']

        // reset the inEditMode state value
        setInEditModeMap({
            status: false,
            rowKey: null,
            map_name: null,
            map_image: null
        });
    }

    // turns off headset editing
    const onCancelHeadset = (element, index) => {

        headsets[index]['name'] = headsetNames[index];

        setInEditModeHeadset({
            status: false,
            rowKey: null,
            headset_name: null
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
                inEditModeHeadset.headset_name = e.target.value;
            }
            newHeadsets.push(headsets[x]);
        }
        setHeadsets(newHeadsets);
    }

    // onchange handler for updating map image
    const updateImage = (e) => {
        var newMaps = [];
        var prefix = "mapImage";
        var image_id = e.target.id.substring(prefix.length, e.target.id.length);
        for (var x in maps) {
            if (maps[x]['id'] == image_id) {
                maps[x]['image'] = e.target.value;
                inEditModeMap.map_image = e.target.value;
            }
            newMaps.push(maps[x]);
        }
        setMaps(newMaps);
    }

    // on change handler for updating map name
    const updateMapName = (e) => {
        var newMaps = [];
        var prefix = "mapName";
        var map_id = e.target.id.substring(prefix.length, e.target.id.length);

        for (var x in maps) {
            if (maps[x]['id'] == map_id) {
                maps[x]['name'] = e.target.value;
                inEditModeMap.map_name = e.target.value;
            }
            newMaps.push(maps[x]);
        }
        setMaps(newMaps);
    }

    // checks if an image associated with a map already exists
    function checkMapImage(image, id) {
        for (var x in maps) {
            if (maps[x]['image'] === image && maps[x]['id'] != id) {
                return true;
            }
        }
        return false;
    }

    // checks if a map name already exists
    function checkMapName(name, id) {
        for (var x in maps) {
            if (maps[x]['name'] === name && maps[x]['id'] != id) {
                console.log(maps[x]['name'] + '.............' + maps[x]['id'])
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
                window.location.reload(false);
            });
    }

    function deleteMap(id, name) {
        const del = window.confirm("Are you sure you want to delete map '" + name + "'?");
        if (!del) {
            return;
        }

        const url = `http://${host}:${port}/maps/${id}`;
        const requestData = {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        };

        fetch(url, requestData)
            .then(response => {
                for (var x in maps) {
                    if (maps[x]['id'] == id) {
                        maps.pop(maps[x]);
                    }
                }
                window.location.reload(false);
            });
    }

    // code that creates the trash icons
    function TrashIcon(props) {
        const item = props.item;
        const itemId = props.id;
        const itemName = props.name;

        if (item == 'headset') {
            return (
                <button style={{width: "30px", height: "30px"}} className='btn-danger'
                        onClick={(e) => deleteHeadset(itemId, itemName)} title="Delete Headset">
                    <FontAwesomeIcon icon={solid('trash-can')} size="lg"
                                     style={{position: 'relative', right: '1.5px', top: '-1px'}}/>
                </button>
            );
        } else {
            return (
                <button style={{width: "30px", height: "30px"}} className='btn-danger'
                        onClick={(e) => deleteMap(itemId, itemName)} title="Delete Map">
                    <FontAwesomeIcon icon={solid('trash-can')} size="lg"
                                     style={{position: 'relative', right: '1.5px', top: '-1px'}}/>
                </button>
            );
        }
    }

    function createNewIncident() {
        const requestData = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        };
        const url = `http://${host}:${port}/incidents/create`;
        fetch(url.toString(), requestData).then(response => {
            console.log("Incident created");
            alert('Starting new incident');
        });
    }

    return (
        <div className="App">
            <Navbar bg="dark" variant="dark">
                <Container>
                    <Navbar.Brand>Easy Viz AR Admin</Navbar.Brand>
                    <Navbar.Toggle aria-controls="basic-navbar-nav"/>
                </Container>
            </Navbar>
            <div className="app-body">
                <div className="nav">
                    <div className="dropdown-container">
                        <DropdownButton id="map-dropdown" title="Select Map" onSelect={handleMapSelection}
                                        defaultValue={getDefaultMapSelection}>
                            {
                                maps.map((e, index) => {
                                    return <Dropdown.Item eventKey={e.id}>{e.name}</Dropdown.Item>
                                })
                            }
                        </DropdownButton>
                    </div>
                    <div className="new-map-button header-button">
                        <Button variant="secondary" style={buttonStyle} onClick={(e) => showMapPopup(e)}>New
                            Map</Button>
                    </div>
                    <div className="add-feature-button header-button">
                        <Button variant="secondary" title="Add Feature" value="Add Feature"
                                onClick={(e) => showFeature(e)}>Add Feature</Button>
                    </div>

                    <div className="header-button new-incident-btn"
                         style={{position: "absolute", right: "0", paddingRight: "20px"}}>
                        <Button variant="primary" onClick={createNewIncident}>
                            New Incident
                        </Button>
                    </div>
                </div>
                <hr/>
                <NewFeature popUpClass={popUpClass} changeCursor={toggleCursor} changeIcon={changeIcon}
                            pointCoordinates={pointCoordinates} changePointValue={changePointValue} mapID={selectedMap}
                            setIconIndex={setIconIndex}/>
                <NewMap showNewMap={showNewMap}/>
                <div className="map-image-container">
                    <img id="map-image" src={selectedImage} alt="Map of the environment" onLoad={onMapLoad}
                         onClick={onMouseClick} style={{cursor: cursor}}/>
                    {combinedMapObjects.map((f, index) => {
                        return <FontAwesomeIcon icon={f.iconValue} className="features" id={f.id} alt={f.name}
                                                style={{
                                                    left: combinedMapObjects[index].scaledX,
                                                    top: combinedMapObjects[index].scaledY
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
                <div>
                    <Table striped bordered hover>
                        <thead>
                        <tr>
                            <th rowSpan='2'>Headset ID</th>
                            <th rowSpan='2'>Name</th>
                            <th rowSpan='2'>Map ID</th>
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
                            headsets.map((e, index) => {
                                return <tr>
                                    <td>{e.id}</td>
                                    <td id={"headsetName" + index}>
                                        {
                                            inEditModeHeadset.status && inEditModeHeadset.rowKey === index ? (
                                                <input
                                                    value={inEditModeHeadset.headset_name}
                                                    placeholder="Edit Headset Name"
                                                    onChange={updateHeadsetName}
                                                    name={"headsetinput" + e.id}
                                                    type="text"
                                                    id={'headsetName' + e.id}/>
                                            ) : (
                                                headsetNames[index]
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
                                                    <button
                                                        className={"btn-success"}
                                                        id={'savebtn' + e.id}
                                                        onClick={(e) => onSaveHeadsets(e, index)}
                                                        title='Save'>
                                                        Save
                                                    </button>

                                                    <button
                                                        className={"btn-secondary"}
                                                        style={{marginLeft: 8}}
                                                        onClick={(event) => onCancelHeadset(event, index)}
                                                        title='Cancel'>
                                                        Cancel
                                                    </button>
                                                </React.Fragment>
                                            ) : (
                                                <button
                                                    className={"btn-primary"}
                                                    onClick={(e) => onEditHeadset(e, index)}
                                                    title='Edit'>
                                                    Edit
                                                </button>
                                            )
                                        }
                                    </td>
                                    <td>
                                        <div>
                                            <TrashIcon item='headset' id={e.id} name={e.name}/>
                                        </div>
                                    </td>
                                </tr>
                            })
                        }
                        </tbody>
                    </Table>
                </div>
                <div>
                    <Table striped bordered hover>
                        <thead>
                        <tr>
                            <th rowSpan='2'>Map ID</th>
                            <th rowSpan='2'>Name</th>
                            <th rowSpan='2'>Image</th>
                        </tr>
                        </thead>
                        <tbody>
                        {
                            maps.map((e, index) => {
                                return <tr>
                                    <td>{e.id}</td>
                                    <td>
                                        {
                                            inEditModeMap.status && inEditModeMap.rowKey === index ? (
                                                <input
                                                    placeholder="Edit Map Name"
                                                    name="input"
                                                    type="text"
                                                    id={'mapName' + e.id}
                                                    onChange={updateMapName}
                                                    value={inEditModeMap.map_name}/>
                                            ) : (
                                                mapNames[index]['name']
                                            )
                                        }
                                    </td>
                                    <td>
                                        {
                                            inEditModeMap.status && inEditModeMap.rowKey === index ? (
                                                <input
                                                    placeholder="Edit Map Image"
                                                    name="input"
                                                    type="text"
                                                    id={'mapImage' + e.id}
                                                    onChange={updateImage}
                                                    value={inEditModeMap.map_image}/>
                                            ) : (
                                                mapNames[index]['image']
                                            )
                                        }
                                    </td>
                                    <td>
                                        {
                                            (inEditModeMap.status && inEditModeMap.rowKey === index) ? (
                                                <React.Fragment>
                                                    <button
                                                        className={"btn-success"}
                                                        id={'mapsbtn' + e.id}
                                                        onClick={(e) => saveMap(e, index)}
                                                        title='Save'>
                                                        Save
                                                    </button>

                                                    <button
                                                        className={"btn-secondary"}
                                                        style={{marginLeft: 8}}
                                                        onClick={() => onCancelMap(index)}
                                                        title='Cancel'>
                                                        Cancel
                                                    </button>
                                                </React.Fragment>
                                            ) : (
                                                <button
                                                    className={"btn-primary"}
                                                    onClick={(e) => onEditMap(e, index)}
                                                    title='Edit'>
                                                    Edit
                                                </button>
                                            )
                                        }
                                    </td>
                                    <td>
                                        <div>
                                            <TrashIcon item='map' id={e.id} name={e.name}/>
                                        </div>
                                    </td>
                                </tr>
                            })
                        }
                        </tbody>
                    </Table>
                </div>
            </div>
        </div>
    );
}

export default App;

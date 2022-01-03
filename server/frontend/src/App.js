import './App.css';
import {Navbar, Container, Dropdown, DropdownButton, Form, Table, Nav, Button} from 'react-bootstrap';
import NewMap from './NewMap.js';
import NewFeature from './NewFeature.js'
//import Save_Delete_Buttons from './Save_Delete_Buttons.js'
import 'reactjs-popup/dist/index.css';
import React, {useState, useEffect} from 'react';

export const port = '5000'

function App() {
  const host = window.location.hostname;

    const buttonStyle = {
        marginBottom: "20px"
    }

    const [selectedMap, setSelectedMap] = useState('');
    const [features, setFeatures] = useState([]);
    const [selectedImage, setSelectedImage] = useState('');
    const [headsets, setHeadsets] = useState([]);
    const [maps, setMaps] = useState([]);
    const [popUpClass, displayModal] = useState(false);
    const [showNewMap, showMap] = useState(false);
    const [crossHairIcon, setCrossHairIcon] = useState("/icons/headset16.png");
    const [inEditModeMap, setInEditModeMap] = useState({
        status: false,
        rowKey: null
    });
    const [inEditModeHeadset, setInEditModeHeadset] = useState({
        status: false,
        rowKey: null
    });
    const [cursor, setCursor] = useState('auto');

    useEffect(() => {
        fetch(`http://${host}:${port}/maps`)
            .then(response => response.json())
            .then(data => {
                for (var key in data) {
                    maps.push({'id': data[key]['id'], 'name': data[key]['name'], 'image': data[key]['image']});
                }
            });
        setSelectedMap(getDefaultMapSelection());
        setSelectedImage(getDefaultMapImage());
    }, []);

    useEffect(() => {
        console.log('Changes in features!!!');
    }, [features, setFeatures])


    useEffect(() => {
        fetch(`http://${host}:${port}/headsets`)
            .then(response => {
                return response.json()
            }).then(data => {
            console.log(data);
            var fetchedHeadsets = []
            for (var k in data) {
                var v = data[k];
                fetchedHeadsets.push({
                    'id': v.id, 'lastUpdate': v.lastUpdate, 'mapId': v.mapId, 'name': v.name,
                    'orientationX': v.orientation.x, 'orientationY': v.orientation.y, 'orientationZ': v.orientation.z,
                    'positionX': v.position.x, 'positionY': v.position.y, 'positionZ': v.position.z,
                    'pixelX': v.pixelPosition['x'], 'pixelY': v.pixelPosition['y']
                });
            }
            setHeadsets(fetchedHeadsets);
        });
    }, []);

    const onMapLoad = () => {
        var scaledWidth = document.getElementById('map-image').offsetWidth;
        var scaledHeight = document.getElementById('map-image').offsetHeight;
        var origWidth = document.getElementById('map-image').naturalWidth;
        var origHeight = document.getElementById('map-image').naturalHeight;

        var widthScaling = scaledWidth / origWidth;
        var heightScaling = scaledHeight / origHeight;

        console.log(`scaledWidth=${scaledWidth}, scaledHeight=${scaledHeight}, origWidth=${origWidth}, origHeight=${origHeight}, widthScaling=${widthScaling}, heightScaling=${heightScaling}`);
        console.log(`Fire: x=483=${(widthScaling * 483)}, y=836=${(heightScaling * 836)}`)
        console.log(`Office: x=1406=${(widthScaling * 1406)}, y=133=${(heightScaling * 133)}`)

        console.log("onMapLoad");
        for (var i = 0; i < features.length; i++) {
            features[i]['scaledX'] = features[i]['pixelX'] * widthScaling;
            features[i]['scaledY'] = features[i]['pixelY'] * heightScaling;
            var element = document.getElementById(features[i]['id'])
            element.style.left = features[i]['scaledX'];
            element.style.top = features[i]['scaledY'];
        }

        fetch(`http://${host}:${port}/maps/${selectedMap}/features`)
            .then(response => {
                return response.json()
            }).then(data => {

            let fetchedFeatures = []
            for (let i in data) {
                let v = data[i];
                fetchedFeatures.push({
                    'id': v.id,
                    'name': v.name,
                    'pixelX': v.pixelPosition['x'],
                    'pixelY': v.pixelPosition['y'],
                    'positionX': v.position.x,
                    'positionY': v.position.y,
                    'positionZ': v.position.z,
                    'icon': v.style.icon,
                    'scaledX': v.pixelPosition['x'] * widthScaling,
                    'scaledY': v.pixelPosition['y'] * heightScaling
                });
                console.log(`Headset: ${v.pixelPosition['x'] * widthScaling}, ${v.pixelPosition['x'] * widthScaling}`);
            }
            // setFeatures(fetchedFeatures);

            fetch(`http://${host}:${port}/headsets`)
                .then(response => {
                    return response.json()
                }).then(data => {
                let fetchedHeadsets = []
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
                            'scaledX': v.pixelPosition['x'] * widthScaling,
                            'scaledY': v.pixelPosition['y'] * heightScaling,
                            'icon': '/icons/headset24.png'
                        });
                    }
                }
                fetchedHeadsets = fetchedHeadsets.concat(fetchedFeatures);
                setFeatures(fetchedHeadsets);
            });


        });

    }

    const getMapImage = (mapId) => {
        if ("2e1a03e6-3d9d-11ec-a64a-0237d8a5e2fd" === mapId) {
            return `http://${host}:${port}/uploads/seventhfloor.png`;
        } else if ("0a820028-3d9d-11ec-a64a-0237d8a5e2fd" === mapId) {
            return "https://media.istockphoto.com/photos/dramatic-sunset-over-a-quiet-lake-picture-id1192051826?k=20&m=1192051826&s=612x612&w=0&h=9HyN74dQTBcTZXB7g-BZp6mXV3upTgSvIav0x7hLm-I=";
        } else {
            return "http://pages.cs.wisc.edu/~hartung/easyvizar/seventhfloor.png";
        }
    }

    const handleMapSelection = (e, o) => {
        console.log('e: ' + e);
        setSelectedMap(e);
        setSelectedImage(getMapImage(e));
        fetch(`http://${host}:${port}/maps`)
            .then(response => response.json())
            .then(data => {
                console.log(data);
            })
    }

    const getDefaultMapSelection = () => {
        if (maps.length == 0)
            return 'cs-5';
        return maps[0]['id'];
    }

    const getDefaultMapImage = () => {
        return getMapImage(getDefaultMapSelection());
    }

    const onMouseClick = (e) => {
        if (cursor != 'crosshair')
            return;
        console.log(`x=${e.clientX - e.target.x}, y=${e.clientY - e.target.y}`);
        let scaledWidth = document.getElementById('map-image').offsetWidth;
        let scaledHeight = document.getElementById('map-image').offsetHeight;
        let origWidth = document.getElementById('map-image').naturalWidth;
        let origHeight = document.getElementById('map-image').naturalHeight;

        let widthScaling = scaledWidth / origWidth;
        let heightScaling = scaledHeight / origHeight;

        console.log(`x=${(e.clientX - e.target.x) * widthScaling}, y=${(e.clientY - e.target.y) * heightScaling}`);

        let f = []
        for (let i in features) {
            f.push(features[i]);
        }
        f.push({
            id: 'fire-1',
            name: 'Fire',
            scaledX: (e.clientX - e.target.x),
            scaledY: (e.clientY - e.target.y),
            icon: crossHairIcon
        })
        setFeatures(f);
    }

    const showFeature = (e) => {
        if (showNewMap == false) {
            displayModal(popUpClass ? false : true)
        }
    }

    const showMapPopup = (e) => {
        if (popUpClass == false) {
            showMap(showNewMap ? false : true)
        }
    }

    const onEditMap = (e, id) => {
        setInEditModeMap({
            status: true,
            rowKey: id
        });
        console.log("edit mode set on row: " + id);
    }

    const onEditHeadset = (e, id) => {
        setInEditModeHeadset({
            status: true,
            rowKey: id
        });
        console.log("edit mode set on row: " + id);
    }

    const saveData = (url, requestData) => {
      fetch(url, requestData)
        .then(response => {
          console.log(response.json())
        }).then(data => {
          console.log(data);
        });

        console.log("Data saved to " + url);
    }

    const onSaveHeadsets = (e) => {
      console.log("saving headset...");
    }

    const saveMap = (e) => {
      const map = null;
      const id = e.target.id.substring(7,e.target.id.length);
      const url = `http://${host}:${port}/maps/${id}`;
      for (var x in maps) {
          if (maps[x]['id'] == id) {
              console.log("map: " + maps[x]['id']);

              const requestData = {
                method: 'PUT',
                headers: {
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify(maps[x])
              };

              console.log(requestData['body'])
              saveData(url, requestData);
              break;
          }
      }
      console.log("map saved");
    }

    const onCancelMap = () => {
        // reset the inEditMode state value
        setInEditModeMap({
            status: false,
            rowKey: null
        });
    }

    const onCancelHeadset = () => {
        // reset the inEditMode state value
        setInEditModeHeadset({
            status: false,
            rowKey: null
        });
    }

    const updateHeadsetName = (e) => {
        var newHeadsets = [];
        for (var x in headsets) {
            if (headsets[x]['id'] == e.target.id) {
                headsets[x]['name'] = e.target.value;
            }
            newHeadsets.push(headsets[x]);
        }
        setHeadsets(newHeadsets);
    }

    const updateImage = (e) => {
        var newMaps = [];
        for (var x in maps) {
            if (maps[x]['id'] == e.target.id) {
                maps[x]['image'] = e.target.value;
            }
            newMaps.push(maps[x]);
        }
        setMaps(newMaps);
    }

    const updateMapName = (e) => {
        var newMaps = [];
        for (var x in maps) {
            if (maps[x]['id'] == e.target.id) {
                maps[x]['name'] = e.target.value;
            }
            newMaps.push(maps[x]);
        }
        setMaps(newMaps);
    }

    const toggleCursor = (e) => {
        if (cursor == 'crosshair')
            setCursor('auto');
        else
            setCursor('crosshair');
    }

    const changeIcon = (v) => {
        setCrossHairIcon(v);
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
                </div>
                <hr/>
                <NewFeature popUpClass={popUpClass} changeCursor={toggleCursor} changeIcon={changeIcon}/>
                <NewMap showNewMap={showNewMap}/>
                <div className="map-image-container">
                    <img id="map-image" src={selectedImage} alt="Map of the environment" onLoad={onMapLoad}
                         onClick={onMouseClick} style={{cursor: cursor}}/>
                    {features.map((f, index) => {
                        return <img className="features" id={f.id} src={`http://${host}:${port}${f.icon}`} alt={f.name}
                                    style={{left: features[index].scaledX, top: features[index].scaledY}}/>
                    })}
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
                                    <td>
                                        {
                                            inEditModeHeadset.status && inEditModeHeadset.rowKey === index ? (
                                                <input
                                                  value={e.name}
                                                  placeholder="Edit Headset Name"
                                                  onChange={updateHeadsetName}
                                                  name={"headsetinput" + e.id}
                                                  type="text"
                                                  id={e.id}/>
                                            ) : (
                                                e.name
                                            )
                                        }
                                    </td>
                                    <td>{e.mapId}</td>
                                    <td>{e.lastUpdate}</td>
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
                                                        onClick={onSaveHeadsets}>
                                                        Save
                                                    </button>

                                                    <button
                                                        className={"btn-secondary"}
                                                        style={{marginLeft: 8}}
                                                        onClick={() => onCancelHeadset()}>
                                                        Cancel
                                                    </button>
                                                </React.Fragment>
                                            ) : (
                                                <button
                                                    className={"btn-primary"}
                                                    onClick={(e) => onEditHeadset(e, index)}>
                                                    Edit
                                                </button>
                                            )
                                        }
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
                                              id={e.id}
                                              onChange={updateMapName}
                                              value={e.name}/>
                                        ) : (
                                          e.name
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
                                            id={e.id}
                                            onChange={updateImage}
                                            value={e.image}/>
                                        ) : (
                                          e.image
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
                                                        onClick={saveMap}>
                                                        Save
                                                    </button>

                                                    <button
                                                        className={"btn-secondary"}
                                                        style={{marginLeft: 8}}
                                                        onClick={() => onCancelMap()}>
                                                        Cancel
                                                    </button>
                                                </React.Fragment>
                                            ) : (
                                                <button
                                                    className={"btn-primary"}
                                                    onClick={(e) => onEditMap(e, index)}>
                                                    Edit
                                                </button>
                                            )
                                        }
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

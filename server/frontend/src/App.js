import './App.css';
import {Navbar, Container, Dropdown, DropdownButton, Form, Table, Nav, Button} from 'react-bootstrap';
import NewMap from './NewMap.js';
import NewFeature from './NewFeature.js'
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
    const [headsetNames, setHeadsetNames] = useState([]);
    const [mapNames, setMapNames] = useState([]);

    useEffect(() => {
      get_maps();
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
            var headsetNamesList = []
            for (var k in data) {
                var v = data[k];
                fetchedHeadsets.push({
                    'id': v.id, 'lastUpdate': v.lastUpdate, 'mapId': v.mapId, 'name': v.name,
                    'orientationX': v.orientation.x, 'orientationY': v.orientation.y, 'orientationZ': v.orientation.z,
                    'positionX': v.position.x, 'positionY': v.position.y, 'positionZ': v.position.z,
                    'pixelX': v.pixelPosition['x'], 'pixelY': v.pixelPosition['y']
                });
                headsetNamesList.push(v.name);
            }
            setHeadsets(fetchedHeadsets);
            setHeadsetNames(headsetNamesList);
        });
    }, []);

    // gets list of maps from server
    function get_maps(){
      fetch(`http://${host}:${port}/maps`)
      .then(response => response.json())
      .then(data => {
        var map_names = []
        for (var key in data) {
           maps.push({'id': data[key]['id'], 'name': data[key]['name'], 'image': data[key]['image']});
           var temp = {
            'name': data[key]['name'],
            'image': data[key]['image']
           }
           map_names.push(temp)
        }
        setMapNames(map_names)
      });
      setSelectedMap(getDefaultMapSelection());
      setSelectedImage(getDefaultMapImage());
    }

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
                            'scaledX': v.pixelPosition['x'] * widthScaling,
                            'scaledY': v.pixelPosition['y'] * heightScaling,
                            'icon': '/icons/headset24.png'
                        });
                    }
                    headsetNamesList.push(v.name);
                }
                fetchedHeadsets = fetchedHeadsets.concat(fetchedFeatures);
                setFeatures(fetchedHeadsets);
                setHeadsetNames(headsetNamesList);
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
        if (inEditModeMap.status == true && inEditModeMap.rowKey != null){
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
        if (inEditModeHeadset.status == true && inEditModeHeadset.rowKey != null){
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
          window.location.reload(false);
        }).then(data => {
          console.log("data: " + data);
        });
    }

    // saves the headset data
    const onSaveHeadsets = (e, index) => {
      const headset = null;
      const id = e.target.id.substring(7,e.target.id.length);
      const url = `http://${host}:${port}/headsets/${id}`;
      for (var x in headsets) {
        if (headsets[x]['id'] == id) {

          var dup = checkHeadsetName(headsets[x]['name'], headsets[x]['id']);
          if (dup){
            var conf = window.confirm('There is another headset with the same name. Are you sure you want to continue?');
            if (!conf){
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
          break;
        }
      }
      onCancelHeadset(index);
      console.log("headset updated");
    }

    // saves the map data
    const saveMap = (e, index) => {
      console.log(e.target);
      const id = e.target.id.substring(7,e.target.id.length);
      const url = `http://${host}:${port}/maps/${id}`;
      var i = 0;
      for (var x in maps) {
        if (maps[x]['id'] == id) {

          var dup_name = checkMapName(mapNames[i]['name'], maps[x]['id']);
          if (dup_name){
            var conf = window.confirm('There is another map with the same name. Are you sure you want to continue?');
            if (!conf){
              return;
            }
          }

          var dup_image = checkMapImage(mapNames[i]['image'], maps[x]['id']);
          if (dup_image){
            var conf = window.confirm('There is another map with the same image. Are you sure you want to continue?');
            if (!conf){
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
    function checkMapImage(image, id){
      for (var x in maps) {
        if (maps[x]['image'] === image && maps[x]['id'] != id) {
          return true;
        }
      }
      return false;
    }

    // checks if a map name already exists
    function checkMapName(name, id){
      for (var x in maps) {
        if (maps[x]['name'] === name && maps[x]['id'] != id) {
          return true;
        }
      }
      return false;
    }

    // check if a headset name already exists
    function checkHeadsetName(name, id){
      for (var x in headsets) {
        if (headsets[x]['name'] == name && headsets[x]['id'] != id) {
          return true;
        }
      }
      return false;
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

    // deletes headset with the id and name
    function deleteHeadset(id, name){
      const del = window.confirm("Are you sure you want to delete headset '" + name + "'?");
      if (!del){
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
          if(headsets[x]['id'] == id){
            headsets.pop(headsets[x]);
          }
        }
        window.location.reload(false);
      });
    }

    function deleteMap(id, name){
      const del = window.confirm("Are you sure you want to delete map '" + name + "'?");
      if (!del){
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
          if(maps[x]['id'] == id){
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
      const src = `http://${host}:${port}/icons/temp/trash_can.png`;

      if (item == 'headset'){
        return (
          <button style={{width: "30px", height: "30px"}} className='btn-danger' onClick={(e) => deleteHeadset(itemId, itemName)} title="Delete Headset">
            <img style={{margin: 'auto', width: "20px", height: "20px", position: 'relative', right: '3.5px', top: '-3px'}} src={src}  alt="Delete Headset"/>
          </button>
        );
      }else{
        return (
          <button style={{width: "30px", height: "30px"}} className='btn-danger' onClick={(e) => deleteMap(itemId, itemName)} title="Delete Map">
            <img style={{margin: 'auto', width: "20px", height: "20px", position: 'relative', right: '3.5px', top: '-3px'}} src={src}  alt="Delete Map"/>
          </button>
        );
      }
    }

    function createNewIncident(){
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

                    <div className="header-button new-incident-btn" style={{position: "absolute", right: "0", paddingRight: "20px"}}>
                      <Button variant="primary" onClick={createNewIncident}>
                            New Incident
                      </Button>
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

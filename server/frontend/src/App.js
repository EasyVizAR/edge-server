import './App.css';
import { Navbar, Container, Dropdown, DropdownButton, Form, Table, Nav, Button } from 'react-bootstrap';
import NewMap from './NewMap.js';
import NewFeature from './NewFeature.js'
//import Save_Delete_Buttons from './Save_Delete_Buttons.js'
import 'reactjs-popup/dist/index.css';
import React, { useState, useEffect } from 'react';

function App() {
  const host = window.location.hostname;

  const buttonStyle = {
    marginBottom: "20px"
  }

  const [selectedMap, setSelectedMap] = useState('');
  const [selectedImage, setSelectedImage] = useState('');
  const [headsets, setHeadsets] = useState([]);
  const [maps, setMaps] = useState([]);
  const [popUpClass, displayModal] = useState(false);
  const [showNewMap, showMap] = useState(false);
  const [inEditMode, setInEditMode] = useState({
    status: false,
    rowKey: null
  });

  useEffect(() => {
    fetch(`http://${host}:5000/maps`)
      .then(response => response.json())
      .then(data => {
        console.log(data);
        var fetchedMaps = []
        for (var idx in data['maps']) {
          console.log(data['maps'][idx]['id']);
          fetchedMaps.push({'id': data['maps'][idx]['id'], 'name': data['maps'][idx]['name'], 'image': data['maps'][idx]['image']});
        }
        setMaps(fetchedMaps);
      });
      setSelectedMap(getDefaultMapSelection());
      setSelectedImage(getDefaultMapImage());
  }, []);

  useEffect(() => {
    fetch(`http://${host}:5000/headsets`)
      .then(response => response.json())
      .then(data => {
        console.log(data);
        var fetchedHeadsets = []
        for (var k in data) {
          var v = data[k];
          fetchedHeadsets.push({'id': v.id, 'lastUpdate': v.lastUpdate, 'mapId': v.mapId, 'name': v.name,
          'orientationX':v.orientation.x, 'orientationY':v.orientation.y, 'orientationZ':v.orientation.z,
          'positionX':v.position.x, 'positionY':v.position.y, 'positionZ':v.position.z});
        }
        setHeadsets(fetchedHeadsets);
        // for (var idx in data['maps']) {
        //   console.log(data['maps'][idx]['id']);
        //   fetchedHeadsets.push({'eventKey': data['maps'][idx]['id'], 'name': data['maps'][idx]['name'], 'image': data['maps'][idx]['image']});
        // }
        // setMaps(fetchedHeadsets);
      });
      // setSelectedImage(getDefaultMapImage());
  }, []);

  const getMapImage = (mapId) => {
    if ("2e1a03e6-3d9d-11ec-a64a-0237d8a5e2fd" === mapId) {
      return `http://${host}:5000/uploads/seventhfloor.png`;
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
    fetch(`http://${host}:5000/maps`)
      .then(response => response.json())
      .then(data => {
        console.log(data);
      })
  }

  const getDefaultMapSelection = () => {
    if (maps.length == 0)
      return 'current';
    console.log(`EventKey for mapImage: ${maps[0]['id']}`);
    return maps[0]['id'];
  }

  const getDefaultMapImage = () => {
    return getMapImage(getDefaultMapSelection());
  }

  const showFeature = (e) => {
    if (showNewMap == false){
      displayModal(popUpClass ? false : true)
    }
  }

  const showMapPopup = (e) => {
    if (popUpClass == false){
      showMap(showNewMap ? false : true)
    }
  }

  const onEdit = (e, id) => {
    setInEditMode({
        status: true,
        rowKey: id
    });
    console.log("edit mode set on row: " + id);
  }

  const onSave = (id) => {
    // TODO: save data
    console.log("save")
  }

  const onCancel = () => {
      // reset the inEditMode state value
      setInEditMode({
          status: false,
          rowKey: null
      });
  }

  function updateMapName(newMapName){
    console.log("New map name: " + newMapName);
  }

  return (
    <div className="App">
      <Navbar bg="dark" variant="dark">
        <Container>
          <Navbar.Brand>Easy Viz AR Admin</Navbar.Brand>
          <Navbar.Toggle aria-controls="basic-navbar-nav" />
        </Container>
      </Navbar>
      <div className="app-body">
        <div className="nav">
          <div className="dropdown-container">
            <DropdownButton id="map-dropdown" title="Select Map" onSelect={handleMapSelection} defaultValue={getDefaultMapSelection}>
              {
                maps.map((e, index) => {
                  return <Dropdown.Item eventKey={e.id}>{e.name}</Dropdown.Item>
                })
              }
            </DropdownButton>
          </div>
          <div className="new-map-button header-button">
            <Button variant="secondary" style={buttonStyle} onClick={(e) => showMapPopup(e)}>New Map</Button>
          </div>
          <div className="add-feature-button header-button">
            <Button variant="secondary" title="Add Feature" value="Add Feature" onClick={(e) => showFeature(e)}>Add Feature</Button>
          </div>
        </div>
        <hr/>
        <NewFeature popUpClass={popUpClass}/>
        <NewMap showNewMap={showNewMap}/>
        <div className="map-image-container">
          <img id="map-image" className="img-fluid" src={selectedImage} alt="Map of the environment" />
          <img id="map-qrcode" className="img-fluid" src={`http://${host}:5000/maps/${selectedMap}/qrcode`} alt="QR code to synchronize headsets" style={{width:400}}/>
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
                          inEditMode.status && inEditMode.rowKey === index ? (
                            <input value={e.name}
                                   onChange={(event) => updateMapName(event.target.value)}/>
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
      (inEditMode.status && inEditMode.rowKey === index) ? (
        <React.Fragment>
          <button
            className={"btn-success"}
            onClick={() => onSave({id: index})}>
            Save
          </button>

          <button
            className={"btn-secondary"}
            style={{marginLeft: 8}}
            onClick={() => onCancel()}>
            Cancel
          </button>
        </React.Fragment>
      ) : (
        <button
          className={"btn-primary"}
          onClick={(e) => onEdit(e, index)}>
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
                        <input
                          placeholder="type here"
                          name="input"
                          type="text"
                          value={e.name}/>
                      </td>
                      <td>
                        <input
                          placeholder="type here"
                          name="input"
                          type="text"
                          value={e.image}/>
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

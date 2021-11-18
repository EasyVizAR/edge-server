import './App.css';
import { Navbar, Container, Dropdown, DropdownButton, Form, Table, Nav, Button } from 'react-bootstrap';
import './forms/map_form.js';
import Popup from './Popup'
import 'reactjs-popup/dist/index.css';
import { useState, useEffect } from 'react';

function App() {
  const host = window.location.hostname;

  const [selectedMap, setSelectedMap] = useState('');
  const [selectedImage, setSelectedImage] = useState('');
  const [headsets, setHeadsets] = useState([]);
  const [maps, setMaps] = useState([]);
  const [popUpClass, displayModal] = useState(false);

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

  return (
    <div className="App">
      <Navbar bg="dark" variant="dark">
        <Container>
          <Navbar.Brand>Easy Viz AR Admin</Navbar.Brand>
          <Navbar.Toggle aria-controls="basic-navbar-nav" />
          <Nav className="me-auto">
            <Nav.Link href="/new_map">Create Map</Nav.Link>
          </Nav>
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
          <div className="add-feature-button">
            <Button variant="secondary" title="Add Feature" value="Add Feature" onClick={(e) => displayModal(popUpClass ? false : true)}>Add Feature</Button>
          </div>
        </div>
        <hr/>
        <Popup popUpClass={popUpClass}/>
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
                <th colSpan='3'>Position</th>b
                <th colSpan='3'>Orientation</th>
              </tr>
              <tr>
                <th>X</th>
                <th>Y</th>
                <th>Z</th>
                <th>X</th>
                <th>Y</th>
                <th>Z</th>
              </tr>
            </thead>
            <tbody>
              {
                headsets.map((e, index) => {
                  return <tr>
                      <td>{e.id}</td>
                      <td>{e.name}</td>
                      <td>{e.mapId}</td>
                      <td>{e.lastUpdate}</td>
                      <td>{e.positionX}</td>
                      <td>{e.positionY}</td>
                      <td>{e.positionZ}</td>
                      <td>{e.orientationX}</td>
                      <td>{e.orientationY}</td>
                      <td>{e.orientationZ}</td>
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
                      <td>{e.name}</td>
                      <td>{e.image}</td>
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

import './App.css';
import {Navbar, Container, Dropdown, DropdownButton, Form, Table, Nav, Button} from 'react-bootstrap';
import NewMap from './NewMap.js';
import NewFeature from './NewFeature.js'
import 'reactjs-popup/dist/index.css';
import {useState, useEffect} from 'react';

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
            return 'current';
        return maps[0]['id'];
    }

    const getDefaultMapImage = () => {
        return getMapImage(getDefaultMapSelection());
    }

    const onMouseClick = (e) => {
        console.log(`x=${e.clientX - e.target.x}, y=${e.clientY - e.target.y}`);
        var scaledWidth = document.getElementById('map-image').offsetWidth;
        var scaledHeight = document.getElementById('map-image').offsetHeight;
        var origWidth = document.getElementById('map-image').naturalWidth;
        var origHeight = document.getElementById('map-image').naturalHeight;

        var widthScaling = scaledWidth / origWidth;
        var heightScaling = scaledHeight / origHeight;

        console.log(`x=${(e.clientX - e.target.x) * widthScaling}, y=${(e.clientY - e.target.y) * heightScaling}`);

        var f = []
        for (var i in features) {
            f.push(features[i]);
        }
        f.push({
            id: 'fire-1',
            name: 'Fire',
            scaledX: (e.clientX - e.target.x),
            scaledY: (e.clientY - e.target.y),
            icon: "/icons/headset16.png"
        })
        console.log(f);
        setFeatures(f);
        console.log(features);
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
                <NewFeature popUpClass={popUpClass}/>
                <NewMap showNewMap={showNewMap}/>
                <div className="map-image-container">
                    <img id="map-image" src={selectedImage} alt="Map of the environment" onLoad={onMapLoad}
                         onClick={onMouseClick}/>
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
                            b
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

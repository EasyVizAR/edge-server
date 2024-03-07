import './Home.css';
import { Navbar, Container, Dropdown, DropdownButton, Form, Table, Nav, Button, Tab, Tabs, Row, Col } from 'react-bootstrap';
import NewLocation from './NewLocation.js';
import NewFeature from './NewFeature.js';
import NewIncidentModal from './NewIncidentModal.js';
import IncidentHistory from './IncidentHistory.js';
import AllHeadsets from './AllHeadsets.js';
import LocationTable from './LocationTable.js';
import LayerTable from './LayerTable.js';
import HeadsetTable from './HeadsetTable.js';
import HeadsetConfiguration from './HeadsetConfiguration.js';
import FeatureTable from './FeatureTable.js';
import PhotoTable from './PhotoTable.js';
import ClickToEdit from './ClickToEdit.js';
import 'reactjs-popup/dist/index.css';
import React, { useContext, useState, useEffect, useRef } from 'react';
import moment from 'moment';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { solid, regular, brands } from '@fortawesome/fontawesome-svg-core/import.macro';
import { Helmet } from 'react-helmet';
import useStateSynchronous from './useStateSynchronous.js';
import { Link } from "react-router-dom";
import { useParams } from "react-router";
import { ActiveIncidentContext, LocationsContext } from './Contexts.js';
import { WebSocketContext } from "./WSContext.js";


import fontawesome from '@fortawesome/fontawesome'
import {
  faBandage,
  faBiohazard,
  faBug,
  faCircle,
  faCirclePlay,
  faDoorClosed,
  faElevator,
  faExclamationTriangle,
  faFire,
  faFireExtinguisher,
  faHeadset,
  faImage,
  faLocationDot,
  faMessage,
  faPerson,
  faRadiation,
  faRightFromBracket,
  faSkull,
  faSquare,
  faStairs,
  faTruckMedical,
  faUser,
} from "@fortawesome/free-solid-svg-icons";
import NewLayer from "./NewLayer";
import MapContainer from "./MapContainer";

fontawesome.library.add(
  faBandage,
  faBiohazard,
  faBug,
  faCircle,
  faCirclePlay,
  faDoorClosed,
  faElevator,
  faExclamationTriangle,
  faFire,
  faFireExtinguisher,
  faHeadset,
  faImage,
  faLocationDot,
  faMessage,
  faPerson,
  faRadiation,
  faRightFromBracket,
  faSkull,
  faSquare,
  faStairs,
  faTruckMedical,
  faUser);

function Location(props) {
  const host = process.env.PUBLIC_URL;
  const { location_id } = useParams();

  // Map feature type -> FA icon
  const icons = {
    ambulance: solid('truck-medical'),
    audio: solid('circle-play'),
    'bad-person': solid('skull'),
    biohazard: solid('biohazard'),
    door: solid('door-closed'),
    elevator: solid('elevator'),
    exit: solid('right-from-bracket'),
    extinguisher: solid('fire-extinguisher'),
    fire: solid('fire'),
    headset: solid('headset'),
    injury: solid('bandage'),
    message: solid('message'),
    object: solid('square'),
    person: solid('person'),
    photo: solid('image'),
    point: solid('circle'),
    radiation: solid('radiation'),
    stairs: solid('stairs'),
    user: solid('user'),
    warning: solid('triangle-exclamation'),
    waypoint: solid('location-dot')
  }

  const buttonStyle = {
    marginBottom: "20px"
  }

  const mapIconSize = 7;
  const circleSvgIconSize = 11;

  const { activeIncident, setActiveIncident } = useContext(ActiveIncidentContext);
  const { locations, setLocations } = useContext(LocationsContext);
  const [subscribe, unsubscribe] = useContext(WebSocketContext);

  const [selectedLocation, setSelectedLocation] = useState(null);
  const [selectedLayer, setSelectedLayer] = useState(null);

  const [histories, setHistories] = useState({}); // position data
  const [features, setFeatures] = useState({}); // object indexed by feature.id
  const [headsets, setHeadsets] = useState({}); // object indexed by headset.id
  const [photos, setPhotos] = useState({});

  const [showNewFeature, setShowNewFeature] = useState(false);
  const [showNewLayer, setShowNewLayer] = useState(false);

  const [layers, setLayers] = useState([]);
  const [crossHairIcon, setCrossHairIcon] = useState("/icons/headset16.png");
  const [pointCoordinates, setPointCoordinates] = useState([]);
  const [cursor, setCursor] = useState('auto');
  const [editFeature, setEditFeature] = useState(null);

  const [iconIndex, setIconIndex] = useState(null);
  const [headsetsChecked, setHeadsetsChecked] = useState(true);
  const [featuresChecked, setFeaturesChecked] = useState(false);
  const [photosChecked, setPhotosChecked] = useState(false);
  const [sliderValue, setSliderValue] = useState(0);
  const [currentLocation, setCurrentLocation] = useState(null);
  const [placementType, setPlacementType] = useState('');
  const [tab, setTab] = useState('location-view');
  const [historyData, setHistoryData] = useState([]);

  // This triggers if a link causes the location_id URL parameter to change.
  useEffect(() => {
    setSelectedLocation(location_id);
  }, [location_id]);

  useEffect(() => {
    // If selected location changed, immediately reload list of headsets and
    // features at the new location.
    if (selectedLocation) {
      getHeadsets();
      getFeatures();
      getLayers();
      getPhotos();

      fetch(`${host}/locations/${selectedLocation}`)
        .then(response => response.json())
        .then(data => setCurrentLocation(data));
    } else {
      setCurrentLocation(null);
    }

    const uri_filter = `/locations/${selectedLocation}/*`;

    subscribe("location-headsets:created", uri_filter, (event, uri, message) => {
      if (message.current.location_id === selectedLocation) {
        setHeadsets(previous => {
          let tmp = Object.assign({}, previous);
          tmp[message.current.id] = message.current;
          return tmp;
        });
      }
    });

    subscribe("location-headsets:updated", uri_filter, (event, uri, message) => {
      if (message.current.location_id === selectedLocation) {
        setHeadsets(previous => {
          let tmp = Object.assign({}, previous);
          tmp[message.current.id] = message.current;
          return tmp;
        });
      }
    });

    subscribe("location-headsets:deleted", uri_filter, (event, uri, message) => {
      if (message.previous.location_id === selectedLocation) {
        setHeadsets(previous => {
          let tmp = Object.assign({}, previous);
          delete tmp[message.previous.id];
          return tmp;
        });
      }
    });

    subscribe("features:created", uri_filter, (event, uri, message) => {
      if (uri.includes(selectedLocation)) {
        setFeatures(previous => {
          let tmp = Object.assign({}, previous);
          tmp[message.current.id] = message.current;
          return tmp;
        });
      }
    });

    subscribe("features:updated", uri_filter, (event, uri, message) => {
      if (uri.includes(selectedLocation)) {
        setFeatures(previous => {
          let tmp = Object.assign({}, previous);
          tmp[message.current.id] = message.current;
          return tmp;
        });
      }
    });

    subscribe("features:deleted", uri_filter, (event, uri, message) => {
      if (uri.includes(selectedLocation)) {
        setFeatures(previous => {
          let tmp = Object.assign({}, previous);
          delete tmp[message.previous.id];
          return tmp;
        });
      }
    });

    subscribe("layers:updated", uri_filter, (event, uri, message) => {
      if (uri.includes(selectedLocation)) {
        setLayers(previous => {
          let tmp = [];
          for (var layer of previous) {
            if (layer.id === message.current.id) {
              tmp.push(message.current);
            } else {
              tmp.push(layer);
            }
          }
          return tmp;
        });
      }
    });

    subscribe("photos:created", "*", (event, uri, message) => {
      if (message.current.camera_location_id === selectedLocation) {
        setPhotos(previous => {
          let tmp = Object.assign({}, previous);
          tmp[message.current.id] = message.current;
          return tmp;
        });
      }
    });

    subscribe("photos:updated", "*", (event, uri, message) => {
      if (message.current.camera_location_id === selectedLocation) {
        setPhotos(previous => {
          let tmp = Object.assign({}, previous);
          tmp[message.current.id] = message.current;
          return tmp;
        });
      }
    });

    subscribe("photos:deleted", "*", (event, uri, message) => {
      if (message.previous.camera_location_id === selectedLocation) {
        setPhotos(previous => {
          let tmp = Object.assign({}, previous);
          delete tmp[message.previous.id];
          return tmp;
        });
      }
    });

    return () => {
      unsubscribe("location-headsets:created", uri_filter);
      unsubscribe("location-headsets:updated", uri_filter);
      unsubscribe("location-headsets:deleted", uri_filter);
      unsubscribe("features:created", uri_filter);
      unsubscribe("features:updated", uri_filter);
      unsubscribe("features:deleted", uri_filter);
      unsubscribe("layers:updated", uri_filter);
      unsubscribe("photos:created", "*");
      unsubscribe("photos:updated", "*");
      unsubscribe("photos:deleted", "*");
    }
  }, [selectedLocation]);

  // Change the cursor when entering or exiting a feature edit mode.
  useEffect(() => {
    if (showNewFeature || editFeature) {
      setCursor("crosshair");
    } else {
      setCursor("auto");
    }
  }, [showNewFeature, editFeature]);

  // If a feature is being edited and the user clicks on the map,
  // forward the clicked coordinate to the active feature.
  // Avoid overwriting the Y value because that could be surprising.
  useEffect(() => {
    setEditFeature(previous => {
      if (previous) {
        let newState = Object.assign({}, previous);
        newState.position.x = pointCoordinates[0];
        newState.position.z = pointCoordinates[2];
        return newState;
      } else {
        return previous;
      }
    });
  }, [pointCoordinates]);

  // function that sends request to server to get headset data
  function getHeadsets() {
    if (!selectedLocation)
      return;

    fetch(`${host}/headsets?location_id=${selectedLocation}`)
      .then(response => {
        return response.json()
      }).then(data => {
        let headsets = {};
        for (var h of data) {
          headsets[h.id] = h;
        }
        setHeadsets(headsets);
      });
  }

  function getFeatures() {
    if (!selectedLocation)
      return;

    fetch(`${host}/locations/${selectedLocation}/features`)
      .then(response => {
        return response.json()
      }).then(data => {
        let features = [];
        for (var f of data) {
          features[f.id] = f;
        }
        setFeatures(features);
      });
  }

  function getPhotos() {
    if (!selectedLocation)
      return;

    fetch(`${host}/photos?camera_location_id=${selectedLocation}`)
      .then(response => response.json())
      .then(data => {
        var temp = {};
        for (var photo of data) {
          if (photo.retention !== "temporary") {
            temp[photo.id] = photo;
          }
        }
        setPhotos(temp);
      })
  }

  const handleLocationSelection = (e, o) => {
    if (e) {
      window.location.href = `${host}/#/locations/${e}`;
    }
    setSelectedLocation(e);
    setFeaturesChecked(false);
    setHeadsetsChecked(true);
  }

  const changePointValue = (value, idx) => {
    var coordinates = [...pointCoordinates];
    coordinates[idx] = value;
    setPointCoordinates(coordinates);
  }

  const resetSurfaces = (e) => {
    const del = window.confirm("This will delete all surfaces that have been collected by headsets in the location. Are you sure?");
    if (!del) {
      return;
    }

    const requestData = {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    const surfaces_url = `${host}/locations/` + selectedLocation + "/surfaces";
    fetch(surfaces_url, requestData)
      .then(response => response.json())
      .then(data => {
        console.log("Deleted surfaces");
      });
  }

  // onchange handler for updating Location image
  const updateImage = (e) => {
    /*
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
    */
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

  const getLayers = () => {
    fetch(`${host}/locations/${selectedLocation}/layers`)
      .then(response => response.json())
      .then(data => {
        var layerList = [];
        for (const key in data) {
          if (data[key].ready)
            layerList.push(data[key]);
        }
        setLayers(layerList);
      });
  }

  const saveLocationFieldChange = (fieldName, newValue) => {
    if (!currentLocation)
      return;

    const url = `${host}/locations/${currentLocation.id}`;
    const requestData = {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        [fieldName]: newValue
      })
    };

    fetch(url, requestData)
      .then(response => {
        return response.json()
      }).then(data => {
        setCurrentLocation(data);

        setLocations(current => {
          const copy = {...current};
          copy[data.id] = data;
          return copy;
        });
      });
  }

  return (
    <div className="Home">
      <Helmet>
        <title>EasyVizAR Edge</title>
      </Helmet>
      <div className="home-body">
        <div className="location-nav">
          <div className="dropdown-container">
            <DropdownButton id="location-dropdown" title="Select Location" onSelect={handleLocationSelection}
              defaultValue={null}>
              {
                Object.entries(locations).map(([id, loc]) => {
                  return <Dropdown.Item eventKey={id}>{loc.name}</Dropdown.Item>
                })
              }
            </DropdownButton>
          </div>

          {
            selectedLocation &&
              <React.Fragment>
                <div className="header-button">
                  <Button variant="secondary" title="Add Feature" value="Add Feature"
                    onClick={() => setShowNewFeature(!showNewFeature)}>Add Feature</Button>
                </div>

                <div className="header-button">
                  <Button variant="secondary" title="Add Layer" value="Add Layer" onClick={() => setShowNewLayer(!showNewLayer)}>
                    Add Layer
                  </Button>
                </div>

                <div className="QR-code-btn header-button">
                  <Link className="btn btn-secondary" role="button" to={"/locations/" + selectedLocation + "/qrcode"}>Location QR Code</Link>
                </div>

                <div className="header-button">
                  <a class="btn btn-secondary" href={"/locations/" + selectedLocation + "/model"}>Location 3D Model</a>
                </div>

                <div className="header-button">
                  <Button variant="secondary" title="Reset Surfaces" value="Reset Surfaces"
                    onClick={(e) => resetSurfaces(e)}>Reset Surfaces</Button>
                </div>
              </React.Fragment>
          }
        </div>

        <Container fluid>
          {
            selectedLocation && showNewFeature &&
              <NewFeature icons={icons}
                showNewFeature={showNewFeature}
                pointCoordinates={pointCoordinates}
                changePointValue={changePointValue} mapID={selectedLocation}
                setIconIndex={setIconIndex} sliderValue={sliderValue}
                setSliderValue={setSliderValue} setPlacementType={setPlacementType}
                placementType={placementType} />
          }

          {
            selectedLocation && showNewLayer &&
              <NewLayer location={currentLocation} setLayers={setLayers} />
          }

          <Row className="location-header">
            <Col>
              <p className="text-muted" style={{ fontSize: '0.875em', marginBottom: '0px' }}>Current Incident</p>
              <h4 style={{ marginTop: '0px' }}>{activeIncident ? activeIncident.name : 'No Active Incident'}</h4>
              <h5>{activeIncident?.id}</h5>
            </Col>
            <Col>
              <p className="text-muted" style={{ fontSize: '0.875em', marginBottom: '0px' }}>Current Location</p>
              {
                currentLocation ? (
                  <>
                    <ClickToEdit
                      tag='h4'
                      initialValue={currentLocation.name}
                      placeholder='Location name'
                      onSave={(newValue) => saveLocationFieldChange('name', newValue)} />
                    <h5>{currentLocation ? selectedLocation : ''}</h5>
                  </>
                ) : (
                  <h4>No Location Selected</h4>
                )
              }
            </Col>
            <Col xs={5}>
              {
                currentLocation ? (
                  <>
                    <p className="text-muted" style={{ fontSize: '0.875em', marginBottom: '0px' }}>Description</p>
                    <ClickToEdit
                      textarea
                      tag='p'
                      initialValue={currentLocation.description}
                      placeholder='Description'
                      onSave={(newValue) => saveLocationFieldChange('description', newValue)} />
                  </>
                ) : (
                  null
                )
              }
            </Col>
          </Row>

          {
            currentLocation ? (
              <React.Fragment>
                <MapContainer id="map-container" locationId={selectedLocation}
                  layers={layers}
                  headsets={headsets} showHeadsets={headsetsChecked}
                  features={features} showFeatures={featuresChecked}
                  photos={photos} showPhotos={photosChecked}
                  cursor={cursor}
                  placementType={placementType} iconIndex={iconIndex}
                  setPointCoordinates={setPointCoordinates}
                  sliderValue={sliderValue}
                  crossHairIcon={crossHairIcon}
                />
                <div style={{ width: 'max-content' }}>
                  <Form>
                    <Form.Check
                      onChange={(e) => setHeadsetsChecked(e.target.checked)}
                      type="switch"
                      id="headsets-switch"
                      label="Headsets"
                      checked={headsetsChecked}
                    />
                    <Form.Check
                      onChange={(e) => setFeaturesChecked(e.target.checked)}
                      type="switch"
                      id="features-switch"
                      label="Features"
                      checked={featuresChecked}
                    />
                    <Form.Check
                      onChange={(e) => setPhotosChecked(e.target.checked)}
                      type="switch"
                      id="photos-switch"
                      label="Photos"
                      checked={photosChecked}
                    />
                  </Form>
                </div>

                <LayerTable locationId={selectedLocation} layers={layers} setLayers={setLayers} />

                <HeadsetTable headsets={headsets} getHeadsets={getHeadsets}
                  setHeadsets={setHeadsets} features={features} />
                <FeatureTable icons={icons} features={features} locationId={selectedLocation}
                  editFeature={editFeature} setEditFeature={setEditFeature} />

                <HeadsetConfiguration location={currentLocation} setLocation={setCurrentLocation} />

                <PhotoTable photos={photos} setPhotos={setPhotos} />
              </React.Fragment>
            ) : (
              <React.Fragment>
                <LocationTable />
                <NewLocation />
              </React.Fragment>
            )
          }
        </Container>
      </div>
    </div>
  );
}

export default Location;

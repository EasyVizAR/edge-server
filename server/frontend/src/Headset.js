import './Home.css';
import { Navbar, Container, Dropdown, DropdownButton, Form, Table, Nav, Button, Tab, Tabs } from 'react-bootstrap';
import NewLocation from './NewLocation.js';
import NewFeature from './NewFeature.js';
import NewIncidentModal from './NewIncidentModal.js';
import IncidentHistory from './IncidentHistory.js';
import AllHeadsets from './AllHeadsets.js';
import LocationTable from './LocationTable.js';
import CheckInTable from './CheckInTable.js';
import HeadsetTable from './HeadsetTable.js';
import FeatureTable from './FeatureTable.js';
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
import ReconnectingWebSocket from './ReconnectingWebSocket.js';


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
  faRobot,
  faMobileScreenButton,
  faLaptopCode
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
  faUser,
  faRobot,
  faLaptopCode,
  faMobileScreenButton
  );

function Headset(props) {
  const host = process.env.PUBLIC_URL;

  const { headset_id } = useParams();

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
    waypoint: solid('location-dot'),
    robot: solid('robot'),
    phone: solid('mobile-screen-button'),
    editor: solid('laptop-code')

  }

  const buttonStyle = {
    marginBottom: "20px"
  }

  const mapIconSize = 7;
  const circleSvgIconSize = 11;
  const historyLength = 4500;

  const { activeIncident, setActiveIncident } = useContext(ActiveIncidentContext);
  const { locations, setLocations } = useContext(LocationsContext);

  const [selectedLocation, setSelectedLocation] = useState(null);
  const [selectedLayer, setSelectedLayer] = useState(null);
  const selectedLocationRef = useRef(null);

  const [headset, setHeadset] = useState(null);

  const [histories, setHistories] = useState({}); // position data
  const [features, setFeatures] = useState({}); // object indexed by feature.id
  const [headsets, setHeadsets] = useState({}); // object indexed by headset.id
  const [positionHistory, setPositionHistory] = useState([]);
  const [showNewFeature, setShowNewFeature] = useState(false);
  const [layers, setLayers] = useState([]);

  const [crossHairIcon, setCrossHairIcon] = useState("/icons/headset16.png");
  const [pointCoordinates, setPointCoordinates] = useState([]);
  const [cursor, setCursor] = useState('auto');
  const [editFeature, setEditFeature] = useState(null);

  const [iconIndex, setIconIndex] = useState(null);
  const [sliderValue, setSliderValue] = useState(0);
  const [currLocationName, setCurrLocationName] = useState('');
  const [placementType, setPlacementType] = useState('');
  const [tab, setTab] = useState('location-view');
  const [historyData, setHistoryData] = useState([]);
  const [showDeviceQR, setShowDeviceQR] = useState(false);

  const [navigationTarget, setNavigationTarget] = useState(null);
  const [navigationRoute, setNavigationRoute] = useState(null);

  // Which user trace to show on the map
  const [displayedCheckInId, setDisplayedCheckInId] = useState(null);

  const [displayOptions, setDisplayOptions] = useState({
    headsets: true,
    features: false,
    history: false,
    navigation: false
  });

  const webSocket = useRef(null);

  useEffect(() => {
    openWebSocket();
  }, []);

  useEffect(() => {
    fetch(`${host}/headsets/${headset_id}`)
      .then(response => response.json())
      .then(data => {
        setHeadset(data)
        setSelectedLocation(data.location_id);
        setDisplayedCheckInId(data.last_check_in_id);
      });
  }, [headset_id]);

  useEffect(() => {
    getPositionHistory(headset);
  }, [displayedCheckInId]);

  useEffect(() => {
    setHeadset(headsets[headset_id]);
  }, [headset_id, headsets]);

  useEffect(() => {
    // If selected location changed, immediately reload list of headsets and
    // features at the new location.
    getHeadsets();
    getFeatures();

    if (selectedLocation) {
      getLayers();
    }

    changeSubscriptions(selectedLocationRef.current, selectedLocation);

    // Updated the reference variable. This is mainly for the websocket
    // event handler.
    selectedLocationRef.current = selectedLocation;
  }, [selectedLocation]);

  useEffect(() => {
    if (headset) {
      setPositionHistory(current => {
        // Drop the oldest point from history and append the new headset position.
        let newHistory = current.slice(1);
        newHistory.push({
          id: headset.id+headset.updated,
          time: headset.updated,
          type: "point",
          color: headset.color,
          position: headset.position
        });
        return newHistory;
      });
    }
  }, [headset]);

  useEffect(() => {
    if (displayOptions.navigation) {
      // Use a separate state variable to track the navigation target, and only
      // set it when we see the type or target_id change in the headset.
      // This reduces the number of times we request the route from the server.
      const new_target = headset.navigation_target;
      if (new_target?.type !== navigationTarget?.type || new_target?.target_id !== navigationTarget?.target_id) {
        setNavigationTarget(headset.navigation_target);
      }
    } else {
      setNavigationTarget(null);
    }
  }, [headset, displayOptions]);

  useEffect(() => {
    if (navigationTarget && navigationTarget.type !== "none") {
        const target = navigationTarget;
        const from = `${headset.position.x},${headset.position.y},${headset.position.z}`;
        const to = `${target.position.x},${target.position.y},${target.position.z}`;
        fetch(`${host}/locations/${headset.location_id}/route?from=${from}&to=${to}`)
          .then(response => response.json())
          .then(data => setNavigationRoute(data));
    } else {
      setNavigationRoute(null);
    }
  }, [navigationTarget]);

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

  // time goes off every 10 seconds to refresh headset data
  //    useEffect(() => {
  //        const timer = setTimeout(() => getHeadsets(), 1e4)
  //        return () => clearTimeout(timer)
  //    });

  const changeMapObjects = (e, v) => {

  };

  const changeMapObjectsContainer = (e) => {
    if (e.target.id == 'features-switch') {
      setDisplayOptions({
        ...displayOptions,
        features: e.target.checked
      });
    }
    if (e.target.id == 'headsets-switch') {
      setDisplayOptions({
        ...displayOptions,
        headsets: e.target.checked
      });
    }
    if (e.target.id == 'history-switch') {
      setDisplayOptions({
        ...displayOptions,
        history: e.target.checked
      });
    }
    if (e.target.id == 'navigation-switch') {
      setDisplayOptions({
        ...displayOptions,
        navigation: e.target.checked
      });
    }
  };

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
      })
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

  // gets pose changes from the server
  function getPositionHistory(hset) {
    const check_in_id = displayedCheckInId;
    fetch(`${host}/headsets/${headset_id}/check-ins/${check_in_id}/pose-changes?limit=${historyLength}`)
    .then(response => {
        return response.json()
    }).then(data => {
      let history = [];
      var i = 0;
      for (var pt of data) {
        i += 1;
        history.push({
          id: headset_id+pt.time,
          time: pt.time,
          type: "point",
          color: hset.color,
          position: pt.position
        });
      }
      setPositionHistory(history);
    });
  }

  const handleLocationSelection = (e, o) => {
    window.location.href = `${host}/#/locations/${e}`;
    setSelectedLocation(e);
    setCurrLocationName(locations[e]['name']);
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
    fetch(surfaces_url)
      .then(response => response.json())
      .then(data => {
        for (var key in data) {
          fetch(surfaces_url + "/" + data[key]['id'], requestData);
        }
      });
  }

  function sort_list(arr) {
    for (let i = 0; i < arr.length; i++) {
      for (let j = 0; j < arr.length - i - 1; j++) {
        if (parseInt(arr[j + 1]['created']) < parseInt(arr[j]['created'])) {
          [arr[j + 1], arr[j]] = [arr[j], arr[j + 1]]
        }
      }
    };
    return arr;
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

  function openWebSocket() {
    // I thought useEffect should only be called once, but this seems to be
    // called many times. Something is not quite right. The easy fix is to
    // back out of the function if webSocket.current is already initialized.
    if (webSocket.current) {
      return;
    }

    if (window.location.protocol === "https:") {
      webSocket.current = new ReconnectingWebSocket(`wss://${window.location.host}/ws`);
    } else {
      webSocket.current = new ReconnectingWebSocket(`ws://${window.location.host}/ws`);
    }

    const ws = webSocket.current;

    ws.connect();

    ws.onopen = (event) => {
      const selectedLocation = selectedLocationRef.current;
      if (selectedLocation) {
        changeSubscriptions(null, selectedLocation);
      }
    };

    ws.onmessage = (event) => {
      const selectedLocation = selectedLocationRef.current;

      const message = JSON.parse(event.data);
      if (message.event === "location-headsets:created") {
        if (message.current.location_id !== selectedLocation)
          return;
        setHeadsets(prevHeadsets => {
          let newHeadsets = Object.assign({}, prevHeadsets);
          newHeadsets[message.current.id] = message.current;
          return newHeadsets;
        });
      } else if (message.event === "location-headsets:updated") {
        if (message.current.location_id !== selectedLocation)
          return;
        setHeadsets(prevHeadsets => {
          let newHeadsets = Object.assign({}, prevHeadsets);
          newHeadsets[message.current.id] = message.current;
          return newHeadsets;
        });
      } else if (message.event === "location-headsets:deleted") {
        if (message.previous.location_id !== selectedLocation)
          return;
        setHeadsets(prevHeadsets => {
          let newHeadsets = Object.assign({}, prevHeadsets);
          delete newHeadsets[message.previous.id];
          return newHeadsets;
        });
      } else if (message.event === "features:created") {
        if (!message.uri.includes(selectedLocation))
          return;
        setFeatures(prevFeatures => {
          let newFeatures = Object.assign({}, prevFeatures);
          newFeatures[message.current.id] = message.current;
          return newFeatures;
        });
      } else if (message.event === "features:updated") {
        if (!message.uri.includes(selectedLocation))
          return;
        setFeatures(prevFeatures => {
          let newFeatures = Object.assign({}, prevFeatures);
          newFeatures[message.current.id] = message.current;
          return newFeatures;
        });
      } else if (message.event === "features:deleted") {
        if (!message.uri.includes(selectedLocation))
          return;
        setFeatures(prevFeatures => {
          let newFeatures = Object.assign({}, prevFeatures);
          delete newFeatures[message.previous.id];
          return newFeatures;
        });
      } else if (message.event === "layers:updated") {
        if (!message.uri.includes(selectedLocation))
          return;
        setLayers(prevLayers => {
          let newLayers = [];
          for (var layer of prevLayers) {
            if (layer.id === message.current.id) {
              newLayers.push(message.current);
            } else {
              newLayers.push(layer);
            }
          }
          return newLayers;
        });
      } else {
        console.log("Unhandled event: " + message);
      }
    };
  }

  function changeSubscriptions(previousLocation, currentLocation) {
    const ws = webSocket.current;
    if (!ws || ws.readyState === 0) {
      return;
    }

    const events = [
      "location-headsets:created",
      "location-headsets:updated",
      "location-headsets:deleted",
      "features:created",
      "features:updated",
      "features:deleted",
      "layers:updated",
      "locations:updated"
    ];

    if (previousLocation) {
      let filter1 = " /locations/" + previousLocation + "*";
      for (var ev of events) {
        ws.send("unsubscribe " + ev + filter1);
      }
    }

    let filter2 = " /locations/" + currentLocation + "*";
    for (var ev of events) {
      ws.send("subscribe " + ev + filter2);
    }
  }

  function DeviceQRCode(props) {
    return (
      headset !== null && showDeviceQR ? (
        <img src={`${host}/headsets/${headset.id}/qrcode`} />
      ) : (
        null
      )
    )
  }

  return (
    <div className="Home">
      <Helmet>
        <title>EasyVizAR Edge</title>
      </Helmet>
      <div className="home-body">
          <div className="location-nav">
            { /*
            <div className="dropdown-container">
              <DropdownButton id="location-dropdown" title="Select Location" onSelect={handleLocationSelection}
                defaultValue={getDefaultLocationSelection}>
                {
                  Object.entries(locations).map(([id, loc]) => {
                    return <Dropdown.Item eventKey={id}>{loc.name}</Dropdown.Item>
                  })
                }
              </DropdownButton>
            </div> */
            }

            <div className="header-button">
              <Button variant="secondary" title="Add Feature" value="Add Feature"
                onClick={() => setShowNewFeature(!showNewFeature)}>Add Feature</Button>
            </div>

            <div className="QR-code-btn header-button">
              <Button variant="secondary" title="Device QR Code"
                onClick={() => setShowDeviceQR(!showDeviceQR)}>
                Device QR Code
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
          </div>

          <div className='home-content'>
            {
              showNewFeature &&
                <NewFeature icons={icons}
                  pointCoordinates={pointCoordinates}
                  changePointValue={changePointValue} mapID={selectedLocation}
                  setIconIndex={setIconIndex} sliderValue={sliderValue}
                  setSliderValue={setSliderValue} setPlacementType={setPlacementType}
                  placementType={placementType} />
            }

            <DeviceQRCode />

            <div style={{ textAlign: 'left', marginBottom: '15px' }}>
              <div style={{ display: 'inline-block' }}>
                <p className="text-muted" style={{ fontSize: '0.875em', marginBottom: '0px' }}>Current Incident</p>
                <h4 style={{ marginTop: '0px' }}>{activeIncident ? activeIncident.name : "No Active Incident"}</h4>
                <h5>{activeIncident?.id}</h5>
              </div>
              <div style={{ marginLeft: '15px', display: 'inline-block' }}>
                <p className="text-muted" style={{ fontSize: '0.875em', marginBottom: '0px' }}>Current Location</p>
                <h4 style={{ marginTop: '0px' }}>{locations[selectedLocation] ? locations[selectedLocation].name : ('Unknown')}</h4>
                <h5>{selectedLocation}</h5>
              </div>
              <div style={{ marginLeft: '15px', display: 'inline-block' }}>
                <p className="text-muted" style={{ fontSize: '0.875em', marginBottom: '0px' }}>Headset</p>
                <h4 style={{ marginTop: '0px' }}>{headset ? (headset.name) : ('Unknown')}</h4>
                <h5>{headset_id}</h5>
              </div>
            </div>

            <MapContainer id="map-container" locationId={selectedLocation}
              layers={layers}
              headsets={headsets} showHeadsets={displayOptions.headsets}
              features={features} showFeatures={displayOptions.features}
              history={positionHistory} showHistory={displayOptions.history}
              navigationTarget={headset?.navigation_target}
              navigationRoute={navigationRoute}
              showNavigation={displayOptions.navigation}
              cursor={cursor}
              placementType={placementType} iconIndex={iconIndex}
              setPointCoordinates={setPointCoordinates}
              sliderValue={sliderValue}
              crossHairIcon={crossHairIcon}
            />

            <div style={{ width: 'max-content' }}>
              <Form onChange={changeMapObjectsContainer}>
                <Form.Check
                  onClick={changeMapObjects(this, 'headsets')}
                  type="switch"
                  id="headsets-switch"
                  label="Headsets"
                  checked={displayOptions.headsets}
                />
                <Form.Check
                  onChange={changeMapObjects(this, 'features')}
                  type="switch"
                  id="features-switch"
                  label="Features"
                  checked={displayOptions.features}
                />
                <Form.Check
                  onChange={changeMapObjects(this, 'history')}
                  type="switch"
                  id="history-switch"
                  label="History"
                  checked={displayOptions.history}
                />
                <Form.Check
                  onChange={changeMapObjects(this, 'navigation')}
                  type="switch"
                  id="navigation-switch"
                  label="Navigation"
                  checked={displayOptions.navigation}
                />
              </Form>
            </div>

            <CheckInTable locations={locations} headsetId={headset_id}
              selected={displayedCheckInId} setSelected={setDisplayedCheckInId} />

            <HeadsetTable headsets={headsets} getHeadsets={getHeadsets}
              setHeadsets={setHeadsets} locations={locations} features={features} />
            <FeatureTable icons={icons} features={features} locationId={selectedLocation}
              editFeature={editFeature} setEditFeature={setEditFeature} />
          </div>

      </div>
    </div>
  );
}

export default Headset;

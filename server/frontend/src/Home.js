import './Home.css';
import {Navbar, Container, Dropdown, DropdownButton, Form, Table, Nav, Button, Tab, Tabs} from 'react-bootstrap';
import NewLocation from './NewLocation.js';
import NewFeature from './NewFeature.js';
import NewIncidentModal from './NewIncidentModal.js';
import IncidentHistory from './IncidentHistory.js';
import AllHeadsets from './AllHeadsets.js';
import LocationTable from './LocationTable.js';
import HeadsetTable from './HeadsetTable.js';
import FeatureTable from './FeatureTable.js';
import 'reactjs-popup/dist/index.css';
import React, {useState, useEffect, useRef} from 'react';
import moment from 'moment';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid, regular, brands} from '@fortawesome/fontawesome-svg-core/import.macro';
import {Helmet} from 'react-helmet';
import useStateSynchronous from './useStateSynchronous.js';
import {Link} from "react-router-dom";

import fontawesome from '@fortawesome/fontawesome'
import {
    faBandage,
    faBug,
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
import LayerContainer from "./LayerContainer";
import NewLayer from "./NewLayer";

fontawesome.library.add(faBandage, faBug, faDoorClosed, faElevator,
    faExclamationTriangle, faFire, faFireExtinguisher, faHeadset, faMessage,
    faSquare, faStairs, faTruckMedical, faUser);

function Home(props) {
    const host = window.location.hostname;
    const port = props.port;

    // Map feature type -> FA icon
    const icons = {
        ambulance: solid('truck-medical'),
        door: solid('door-closed'),
        elevator: solid('elevator'),
        extinguisher: solid('fire-extinguisher'),
        fire: solid('fire'),
        headset: solid('headset'),
        injury: solid('bandage'),
        message: solid('message'),
        object: solid('square'),
        stairs: solid('stairs'),
        user: solid('user'),
        warning: solid('triangle-exclamation')
    }

    const buttonStyle = {
        marginBottom: "20px"
    }

    const mapIconSize = 7;
    const circleSvgIconSize = 11;

    const [selectedLocation, setSelectedLocation] = useState('');
    const [features, setFeatures] = useState([]);
    const [headsets, setHeadsets] = useState({}); // object indexed by headset.id
    const [combinedMapObjects, setCombinedMapObjects] = useState([]);
    const [locations, setLocations] = useState({}); // object indexed by locationId
    const [showNewFeature, displayNewFeature] = useState(false);
    const [layers, setLayers] = useState([]);
    const [selectedLayerId, setSelectedLayerId] = useState(-1);
    const [layerLoaded, setLayerLoaded] = useState(false);
    const [crossHairIcon, setCrossHairIcon] = useState("/icons/headset16.png");
    const [pointCoordinates, setPointCoordinates] = useState([]);
    const [cursor, setCursor] = useState('auto');
    const [clickCount, setClickCount] = useState(0);
    const [iconIndex, setIconIndex] = useState(null);
    const [headsetsChecked, setHeadsetsChecked] = useState(true);
    const [featuresChecked, setFeaturesChecked] = useState(false);
    const [sliderValue, setSliderValue] = useState(0);
    const [currLocationName, setCurrLocationName] = useState('');
    const [placementType, setPlacementType] = useState('');
    const [tab, setTab] = useState('location-view');
    const [historyData, setHistoryData] = useState([]);

    const incidentInfo = useStateSynchronous(-1);
    const incidentName = useStateSynchronous('');
    const currentIncident = useStateSynchronous(-1);

    const webSocket = useRef(null);

    useEffect(() => {
        get_locations();
        getCurrentIncident();
        openWebSocket();
    }, []);

    useEffect(() => {
        combineMapObjects();
    }, [features, setFeatures]);

    useEffect(() => {
    }, [combinedMapObjects, setCombinedMapObjects]);

    useEffect(() => {
        combineMapObjects();
    }, [headsets])

    useEffect(() => {
        if (selectedLocation == '' && Object.keys(locations).length > 0)
            setSelectedLocation(getDefaultLocationSelection());
    }, [locations, setLocations]);

    useEffect(() => {
        // If selectedLocation changed, immediately reload list of headsets at
        // the new location.
        getHeadsets();

        if (selectedLocation != '') {
            getLayers();
        }
    }, [selectedLocation]);

    // time goes off every 10 seconds to refresh headset data
//    useEffect(() => {
//        const timer = setTimeout(() => getHeadsets(), 1e4)
//        return () => clearTimeout(timer)
//    });

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
        if (!layerLoaded)
            return;
        var combinedMapObjectList = [];

        if (featuresChecked)
            for (const i in features) {
                const v = features[i];
                // if (selectedLocation != v.mapId)
                //     continue;
                combinedMapObjectList.push({
                    'id': v.id,
                    'locationId': v.locationId,
                    'name': v.name,
                    'color': v.color,
                    'scaledX': convertVector2Scaled(v.position.x, v.position.z)[0],
                    'scaledY': convertVector2Scaled(v.position.x, v.position.z)[1],
                    'type': v.type,
                    'radius': v.radius,
                    'placement': v.placement,
                    'editing': v.editing
                });
            }

        if (headsetsChecked)
            for (const id in headsets) {
                const headset = headsets[id];
                if (headset.location_id != selectedLocation)
                    continue;
                combinedMapObjectList.push({
                    'id': headset.id,
                    'locationId': headset.locationId,
                    'name': headset.name,
                    'color': headset.color,
                    'scaledX': convertVector2Scaled(headset.position.x, headset.position.z)[0],
                    'scaledY': convertVector2Scaled(headset.position.x, headset.position.z)[1],
                    'type': 'headset',
                    'placement': 'headset'
                });
            }

        setCombinedMapObjects(combinedMapObjectList);
    }

    // function that sends request to server to get headset data
    function getHeadsets() {
        fetch(`http://${host}:${port}/headsets?location_id=${selectedLocation}`)
            .then(response => {
                return response.json()
            }).then(data => {
              var headsets = {};
              for (var h of data) {
                headsets[h.id] = h;
              }
              setHeadsets(headsets);
            });
    }

    // gets list of locations from server
    function get_locations() {
        setLocations({});

        fetch(`http://${host}:${port}/locations`)
            .then(response => response.json())
            .then(data => {
                var temp_locations = {};
                for (var key in data) {
                    temp_locations[data[key]['id']] = data[key];
                }
                setLocations(temp_locations);
                // setSelectedLocation(getDefaultLocationSelection());
            });
        // setSelectedLocation(getDefaultLocationSelection());
    }

    function updateIncidentInfo() {
      if (currentIncident.get() != -1 && (incidentName.get() == '' || incidentName.get() == null)) {
        incidentInfo.set(currentIncident.get())
      } else {
        incidentInfo.set(incidentName.get());
      }
    }

    const handleLocationSelection = (e, o) => {
        setSelectedLocation(e);
        setCurrLocationName(locations[e]['name']);
        setFeaturesChecked(false);
        setHeadsetsChecked(true);
    }

    const getDefaultLocationSelection = () => {
        if (Object.keys(locations).length == 0)
            return 'NULL';
        var id = Object.keys(locations)[0];
        setCurrLocationName(locations[id]['name']);
        return id;
    }

    const convertVector2Scaled = (x, yy) => {
        var list = [];
        var map = {};
        for (var i = 0; i < layers.length; i++) {
            if (layers[i]['id'] == selectedLayerId)
                map = layers[i];
        }
        if (Object.keys(map).length === 0 || !layerLoaded)
            return [0, 0];
        const xmin = map['viewBox']['left'];
        const ymin = map['viewBox']['top'];
        const width = map['viewBox']['width'];
        const height = map['viewBox']['height'];
        list.push(document.getElementById('map-image').offsetWidth / width * (x - xmin));
        list.push(document.getElementById('map-image').offsetHeight / height * (yy - ymin));

        return list;
    }

    const changePointValue = (value, idx) => {
        var coordinates = pointCoordinates;
        coordinates[idx] = value;
        setPointCoordinates(coordinates);
    }

    // shows the new feature popup
    const showFeature = (e) => {
        displayNewFeature(showNewFeature ? false : true);
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

        const surfaces_url = `http://${host}:${port}/locations/` + selectedLocation + "/surfaces";
        fetch(surfaces_url)
            .then(response => response.json())
            .then(data => {
                for (var key in data) {
                    fetch(surfaces_url + "/" + data[key]['id'], requestData);
                }
            });
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

    function getCurrentIncident() {
      fetch(`http://${host}:${port}/incidents/active`)
        .then(response => response.json())
        .then(data => {
          currentIncident.set(data['id']);
          incidentName.set(data['name']);
          updateIncidentInfo();
        });
    }

    const getLayers = () => {
        fetch(`http://${host}:${port}/locations/${selectedLocation}/layers`)
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

      webSocket.current = new WebSocket(`ws://${host}:${port}/ws`);

      const ws = webSocket.current;

      ws.onopen = (event) => {
          ws.send("subscribe headsets:created");
          ws.send("subscribe headsets:updated");
          ws.send("subscribe headsets:deleted");
          ws.send("subscribe features:created");
          ws.send("subscribe features:updated");
          ws.send("subscribe features:deleted");
      };

      ws.onmessage = (event) => {
          const message = JSON.parse(event.data);
          if (message.event === "headsets:created") {
            let newHeadsets = { ...headsets };
            newHeadsets[message.current.id] = message.current;
            setHeadsets(newHeadsets);
          } else if (message.event === "headsets:updated") {
            let newHeadsets = { ...headsets };
            newHeadsets[message.current.id] = message.current;
            setHeadsets(newHeadsets);
          } else if (message.event === "headsets:deleted") {
            let newHeadsets = { ...headsets };
            delete newHeadsets[message.previous.id];
            setHeadsets(newHeadsets);
          } else if (message.event === "features:created") {

          } else if (message.event === "features:updated") {

          } else if (message.event === "features:deleted") {

          }
      };
    }

    return (
        <div className="Home">
            <Helmet>
              <title>EasyVizAR Edge</title>
            </Helmet>
            <div className="home-body">
                <Tabs activeKey={tab} className="mb-3 tabs" onSelect={(t) => setTab(t)}>
                  <Tab eventKey="location-view" title="Location View">
                    <div className="location-nav">
                      <div className="dropdown-container">
                          <DropdownButton id="location-dropdown" title="Select Location" onSelect={handleLocationSelection}
                                          defaultValue={getDefaultLocationSelection}>
                              {
                                  Object.entries(locations).map(([id, loc]) => {
                                      return <Dropdown.Item eventKey={id}>{loc.name}</Dropdown.Item>
                                  })
                              }
                          </DropdownButton>
                      </div>

                      <div className="header-button">
                          <Button variant="secondary" title="Add Feature" value="Add Feature"
                                  onClick={(e) => showFeature(e)}>Add Feature</Button>
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
                      <NewFeature port={port} showNewFeature={showNewFeature} changeCursor={toggleCursor} changeIcon={changeIcon}
                                  pointCoordinates={pointCoordinates} changePointValue={changePointValue} mapID={selectedLocation}
                                  setIconIndex={setIconIndex} sliderValue={sliderValue} setSliderValue={setSliderValue}
                                  setPlacementType={setPlacementType} placementType={placementType}/>

                      <div style={{textAlign: 'left', marginBottom: '15px'}}>
                        <div style={{display: 'inline-block'}}>
                          <p className="text-muted" style={{fontSize:'0.875em', marginBottom: '0px'}}>Current Incident</p>
                          <h4 style={{marginTop: '0px'}}>{incidentInfo.get()}</h4>
                          <h5>{currentIncident.get()}</h5>
                        </div>
                        <div style={{marginLeft: '15px', display: 'inline-block'}}>
                          <p className="text-muted" style={{fontSize:'0.875em', marginBottom: '0px'}}>Current Location</p>
                          <h4 style={{marginTop: '0px'}}>{currLocationName != '' ? (currLocationName) : ('No Location Selected')}</h4>
                          <h5>{currLocationName != '' ? selectedLocation : ''}</h5>
                        </div>
                      </div>
                        <LayerContainer id="map-container" port={port} features={features}
                                        setFeatures={setFeatures} setHeadsets={setHeadsets} cursor={cursor} setClickCount={setClickCount}
                                        clickCount={clickCount} placementType={placementType} iconIndex={iconIndex}
                                        setPointCoordinates={setPointCoordinates} headsetsChecked={headsetsChecked}
                                        featuresChecked={featuresChecked} sliderValue={sliderValue}
                                        combinedMapObjects={combinedMapObjects} selectedLocation={selectedLocation}
                                        convertVector2Scaled = {convertVector2Scaled} crossHairIcon={crossHairIcon}
                                        layerLoaded={layerLoaded} setLayerLoaded={setLayerLoaded}
                                        layers={layers} setLayers={setLayers} selectedLayerId={selectedLayerId}
                                        setSelectedLayerId={setSelectedLayerId}
                                      // selectedMap={selectedMap} maps={maps} setMapLoaded={setMapLoaded} mapLoaded ={mapLoaded} selectedImage={selectedImage}
                        />
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

                      <HeadsetTable port={port} headsets={headsets} getHeadsets={getHeadsets}
                                    setHeadsets={setHeadsets} locations={locations}/>
                      <FeatureTable port={port} features={features} locationId={selectedLocation}/>
                      <LocationTable port={port} locations={locations} getLocations={get_locations}
                                     setLocations={setLocations}/>
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
                    <AllHeadsets port={port} getLocationHeadsets={getHeadsets} locations={locations}/>
                  </Tab>
                    <Tab eventKey="create-layer" title="Create Layer">
                        <NewLayer port={port} getHeadsets={getHeadsets} getLayers={getLayers} setTab={setTab} locations={locations}/>
                    </Tab>
                </Tabs>
            </div>
        </div>
    );
}

export default Home;

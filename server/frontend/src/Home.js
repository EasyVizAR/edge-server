import './Home.css';
import {Navbar, Container, Dropdown, DropdownButton, Form, Table, Nav, Button, Tab, Tabs} from 'react-bootstrap';
import NewLocation from './NewLocation.js';
import NewFeature from './NewFeature.js';
import NewIncidentModal from './NewIncidentModal.js';
import IncidentHistory from './IncidentHistory.js';
import AllHeadsets from './AllHeadsets.js';
import LocationTable from './LocationTable.js';
import HeadsetTable from './HeadsetTable.js';
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
import LayerContainer from "./LayerContainer";
import NewLayer from "./NewLayer";

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
    const [headsets, setHeadsets] = useState([]);
    const [combinedMapObjects, setCombinedMapObjects] = useState([]);
    const [locations, setLocations] = useState([]);
    const [showNewFeature, displayNewFeature] = useState(false);
    const [layers, setLayers] = useState([]);
    const [selectedLayerId, setSelectedLayerId] = useState(-1);
    const [layerLoaded, setLayerLoaded] = useState(false);
    const [crossHairIcon, setCrossHairIcon] = useState("/icons/headset16.png");
    const [pointCoordinates, setPointCoordinates] = useState([]);
    const [cursor, setCursor] = useState('auto');
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
        if (selectedLocation != '') {
            getLayers();
        }
    }, [selectedLocation]);

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
                        'updated': v.updated,
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
                        <Button title="Location QR Code" variant="secondary" href={"/locations/" + selectedLocation + "/qrcode"} target="_blank">Location QR Code</Button>
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
                                    setHeadsets={setHeadsets}/>
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
                    <AllHeadsets port={port} getLocationHeadsets={getHeadsets} />
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

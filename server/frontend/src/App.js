import React, {createContext, useState, useEffect} from 'react';
import {HashRouter, Link, Route, Routes} from 'react-router-dom';
import AllHeadsets from './AllHeadsets.js';
import WorkItems from './WorkItems.js';
import Location from './Location.js';
import Headset from './Headset.js';
import IncidentHistory from './IncidentHistory.js';
import LocationQrCodeWrapper from './LocationQrCodeWrapper.js';
import PhotoWrapper from './PhotoWrapper.js';
import VideoStreams from './VideoStreams.js';
import VideoPlayer from './VideoPlayer.js';
import WebsocketConnections from './WebsocketConnections.js';
import { WebSocketProvider } from './WSContext.js';
import Users from './Users.js';
import NavBar from './NavBar.js';
import { ActiveIncidentContext, LocationsContext, UsersContext } from './Contexts.js';

function App() {
    const [activeIncident, setActiveIncident] = useState(null);
    const activeIncidentContextValue = { activeIncident, setActiveIncident };

    const [locations, setLocations] = useState({});
    const locationsContextValue = { locations, setLocations };

    const [users, setUsers] = useState({});
    const usersContextValue = { users, setUsers };

    useEffect(() => {
      fetch(`${process.env.PUBLIC_URL}/incidents/active`)
        .then(response => response.json())
        .then(data => setActiveIncident(data));

      fetch(`${process.env.PUBLIC_URL}/users`)
        .then(response => response.json())
        .then(data => {
          var new_users = {};
          for (var key in data) {
            new_users[data[key]['id']] = data[key];
          }
          setUsers(new_users);
        });
    }, []);

    useEffect(() => {
      fetch(`${process.env.PUBLIC_URL}/locations`)
        .then(response => response.json())
        .then(data => {
          var new_locations = {};
          for (var key in data) {
            new_locations[data[key]['id']] = data[key];
          }
          setLocations(new_locations);
        });
    }, [activeIncident]);

    return (
        <div className="App">
            <HashRouter>
                <NavBar />
                <div className="content">
                  <ActiveIncidentContext.Provider value={activeIncidentContextValue}>
                  <LocationsContext.Provider value={locationsContextValue}>
                  <UsersContext.Provider value={usersContextValue}>
                  <WebSocketProvider>
                    <Routes>
                        <Route exact path="/" element={<Location />}/>
                        <Route path="/headsets" element={<AllHeadsets />}/>
                        <Route path="/headsets/:headset_id" element={<Headset />}/>
                        <Route path="/incidents" element={<IncidentHistory />}/>
                        <Route path="/streams" element={<VideoStreams />}/>
                        <Route path="/streams/:stream_id" element={<VideoPlayer />}/>
                        <Route path="/websockets" element={<WebsocketConnections />}/>
                        <Route path="/locations/:location_id/qrcode" element={<LocationQrCodeWrapper />}/>
                        <Route path="/locations/:location_id" element={<Location />}/>
                        <Route path="/photos" element={<WorkItems />}/>
                        <Route path="/photos/:photo_id" element={<PhotoWrapper />} />
                        <Route path="/users" element={<Users />} />
                    </Routes>
                  </WebSocketProvider>
                  </UsersContext.Provider>
                  </LocationsContext.Provider>
                  </ActiveIncidentContext.Provider>
                </div>
            </HashRouter>
        </div>
    );
}

export default App;

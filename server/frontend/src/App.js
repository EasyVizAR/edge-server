import React, {createContext, useState, useEffect} from 'react';
import {HashRouter, Link, Route, Routes} from 'react-router-dom';
import Home from './Home.js';
import WorkItems from './WorkItems.js';
import Location from './Location.js';
import Headset from './Headset.js';
import LocationQrCodeWrapper from './LocationQrCodeWrapper.js';
import PhotoWrapper from './PhotoWrapper.js';
import NavBar from './NavBar.js';
import { LocationsContext } from './Contexts.js';

function App() {
    const [locations, setLocations] = useState({});
    const locationsContextValue = { locations, setLocations };

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
    }, []);

    return (
        <div className="App">
            <HashRouter>
                <NavBar />
                <div className="content">
                  <LocationsContext.Provider value={locationsContextValue}>
                    <Routes>
                        <Route exact path="/" element={<Home />}/>
                        <Route path="/workitems" element={<WorkItems />}/>
                        <Route path="/locations/:location_id/qrcode" element={<LocationQrCodeWrapper />}/>
                        <Route path="/locations/:location_id" element={<Location />}/>
                        <Route path="/locations/:location_id/:headset_id" element={<Headset />}/>
                        <Route path="/photos/:photo_id" element={<PhotoWrapper />} />
                    </Routes>
                  </LocationsContext.Provider>
                </div>
            </HashRouter>
        </div>
    );
}

export default App;

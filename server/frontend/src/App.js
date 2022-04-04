import React, {useState, useEffect} from 'react';
import {BrowserRouter as Router, Route, Routes} from 'react-router-dom';
import Home from './Home.js';
import WorkItems from './WorkItems.js';
import MapQrCodeWrapper from './MapQrCodeWrapper.js'
import NavBar from './NavBar.js'

function App() {
    const port = '5000';

    return (
      <Router>
        <div className="App">
          <NavBar/>
          <div className="content">
            <Routes>
              <Route path="/" element={<Home port={port}/>} />
              <Route path="/workitems" element={<WorkItems port={port} />} />
              <Route path="/maps/:map_id/qrcode.svg" element={<MapQrCodeWrapper port={port}/>} />
            </Routes>
          </div>
        </div>
      </Router>
    );
}

export default App;

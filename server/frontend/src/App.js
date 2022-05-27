import React, {useState, useEffect} from 'react';
import {HashRouter, Link, Route, Routes} from 'react-router-dom';
import Home from './Home.js';
import WorkItems from './WorkItems.js';
import LocationQrCodeWrapper from './LocationQrCodeWrapper.js'
import NavBar from './NavBar.js'

function App() {
    const port = '5000';

    return (
        <div className="App">
            <HashRouter>
                <NavBar port={port}/>
                <div className="content">
                    <Routes>
                        <Route exact path="/" element={<Home port={port}/>}/>
                        <Route path="/workitems" element={<WorkItems port={port}/>}/>
                        <Route path="/locations/:location_id/qrcode" element={<LocationQrCodeWrapper port={port}/>}/>
                    </Routes>
                </div>
            </HashRouter>
        </div>
    );
}

export default App;

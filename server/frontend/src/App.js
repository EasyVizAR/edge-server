import React, {useState, useEffect} from 'react';
import {BrowserRouter, Link, Route, Routes} from 'react-router-dom';
import Home from './Home.js';
import WorkItems from './WorkItems.js';
import LocationQrCodeWrapper from './LocationQrCodeWrapper.js'
import NavBar from './NavBar.js'

function App() {
    const port = '5000';

    return (
        <div className="App">
            <BrowserRouter>
                <NavBar port={port}/>
                <div className="content">
                    <Routes>
                        <Route path="/" element={<Home port={port}/>}/>
                        <Route path="/workitems" element={<WorkItems port={port}/>}/>
                        <Route path="/locations/:map_id/qrcode" element={<LocationQrCodeWrapper port={port}/>}/>
                    </Routes>
                </div>
            </BrowserRouter>
        </div>
    );
}

export default App;

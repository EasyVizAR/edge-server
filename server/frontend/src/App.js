import React, {useState, useEffect} from 'react';
import {BrowserRouter as Router, Route, Routes} from 'react-router-dom';
import Home from './Home.js';
import WorkItems from './WorkItems.js';
import NavBar from './NavBar.js'

function App() {
    return (
      <Router>
        <div className="App">
          <NavBar/>
          <div className="content">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/workitems" element={<WorkItems />} />
            </Routes>
          </div>
        </div>
      </Router>
    );
}

export default App;

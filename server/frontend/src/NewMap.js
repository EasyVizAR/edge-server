import './NewMap.css';
import App from './App.js';
import { Form, Button, FloatingLabel } from 'react-bootstrap';
import React from "react";
import { useState } from 'react';

function NewMap(props){
    const host = window.location.hostname;
    const port = '5000';
    const[mapName, setMapName] = useState(null);

    if (!props.showNewMap){
      return null;
    }

    const handleSubmit = (event) => {

      const new_map = {
        name: mapName,
      }

      const requestData = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(new_map)
      };

      let url = `http://${host}:${port}/maps`;
      fetch(url, requestData)
      .then(response => response.json())
      .then(data => {
        console.log(data);
      });
    }

    function updateState(e, type){
      let val = e.target.value;
      switch(type){
        case "map-name":
          setMapName(val);
          break;
        default:
          console.log('bad type');
          break;
      }
    }

    return (
      <div className="NewMapForm">
        <div>
          <h2>Create A Map</h2>
          <Form onSubmit={handleSubmit}>
            <Form.Group style={{width: '50%', margin: 'auto'}} className="mb-3" controlId="map-name">
              <FloatingLabel controlId="floating-name" label="Map Name">
                <Form.Control type="text" placeholder="Map Name" name="mapName" onChange={(e) => updateState(e, "map-name")}/>
              </FloatingLabel>
            </Form.Group>
            <Button variant="primary" onClick={handleSubmit}>
              Create
            </Button>
          </Form>
        </div>
        <hr/>
      </div>
    );
}

export default NewMap;
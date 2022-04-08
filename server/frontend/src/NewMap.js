import './NewMap.css';
import App from './App.js';
import { Form, Button, FloatingLabel } from 'react-bootstrap';
import React from "react";
import { useState } from 'react';

function NewMap(props){
    const host = window.location.hostname;
    const port = props.port;
    const[mapName, setMapName] = useState(null);
    const[initDummy, setInitDummy] = useState(false);

    const handleSubmit = (event) => {

      const new_map = {
        name: mapName,
          dummyData: initDummy
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
        props.getMaps();
        props.getHeadsets();
        window.location.reload(false);
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
      <div className="new-map">
        <div className='new-map-content'>
          <h2>Create A Map</h2>
          <Form onSubmit={handleSubmit} className='new-map-form'>
            <Form.Group style={{width: '50%', margin: 'auto', display:'flex', flexFlow:'column'}} className="mb-3" controlId="map-name">
              <FloatingLabel controlId="floating-name" label="Map Name">
                <Form.Control type="text" placeholder="Map Name" name="mapName" onChange={(e) => updateState(e, "map-name")}/>
              </FloatingLabel>
                <label style={{display: 'flex'}}>Initialize with dummy data</label>
                <input type='checkbox' id='dummy-data-checkbox' value={initDummy} onChange={(e) => setInitDummy(e.target.checked)}/>
            </Form.Group>
            <Button variant="primary" onClick={handleSubmit}>
              Create
            </Button>
          </Form>
        </div>
      </div>
    );
}

export default NewMap;
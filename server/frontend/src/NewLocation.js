import './NewLocation.css';
import App from './App.js';
import { Form, Button, FloatingLabel } from 'react-bootstrap';
import React from "react";
import { useState } from 'react';

function NewLocation(props){
    const host = window.location.hostname;
    const port = props.port;
    const[locationName, setLocationName] = useState(null);
    const[initDummy, setInitDummy] = useState(false);

    function handleSubmit(e) {

      const new_location = {
        name: locationName,
          dummyData: initDummy
      }

      const requestData = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(new_location)
      };

      let url = `http://${host}:${port}/locations`;
      fetch(url, requestData)
      .then(response => response.json())
      .then(data => {
        props.getLocations();
        props.getHeadsets();
        e.target.form.elements.formLocationName.value = ""
        props.setTab('location-view');
      });
    }

    function updateState(e, type){
      let val = e.target.value;
      switch(type){
        case "location-name":
          setLocationName(val);
          break;
        default:
          console.log('bad type');
          break;
      }
    }

    return (
      <div className="new-location">
        <div className='new-location-content'>
          <h2>Create A Location</h2>
          <Form onSubmit={handleSubmit} className='new-location-form'>
            <Form.Group style={{width: '50%', margin: 'auto', display:'flex', flexFlow:'column'}} className="mb-3" controlId="location-name">
              <FloatingLabel controlId="floating-name" label="Location Name">
                <Form.Control type="text" placeholder="Location Name" name="formLocationName" onChange={(e) => updateState(e, "location-name")}/>
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

export default NewLocation;
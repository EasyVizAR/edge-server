import './NewLocation.css';
import App from './App.js';
import { Form, Button, FloatingLabel, Row, Col } from 'react-bootstrap';
import React from "react";
import { useContext, useState } from 'react';
import { LocationsContext } from './Contexts.js';


function NewLocation(props) {
    const host = process.env.PUBLIC_URL;

    const { locations, setLocations } = useContext(LocationsContext);

    const formReferences = {
      name: React.createRef()
    }

    function handleSubmit(e) {
      const name = formReferences.name.current.value;

      const requestData = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({name})
      };

      fetch(`${host}/locations`, requestData)
        .then(response => response.json())
        .then(data => {
          setLocations(prevLocations => {
            const newLocations = Object.assign({}, prevLocations);
            newLocations[data.id] = data;
            return newLocations;
          });
        });
    }

    return (
      <div className="new-location">
        <div className='new-location-content'>
          <h3 style={{textAlign: "left"}}>New Location</h3>
          <Form onSubmit={handleSubmit} className='new-location-form'>
            <Row className="align-items-center">
              <Col xs="auto">
                <Form.Group style={{width: '50%', margin: 'auto', display:'flex', flexFlow:'column'}} className="mb-3" controlId="location-name">
                  <FloatingLabel controlId="floating-name" label="Location Name">
                    <Form.Control type="text" placeholder="Location Name" name="formLocationName" ref={formReferences.name}/>
                  </FloatingLabel>
                </Form.Group>
              </Col>
              <Col xs="auto">
                <Button variant="primary" onClick={handleSubmit}>
                  Create
                </Button>
              </Col>
            </Row>
          </Form>
        </div>
      </div>
    );
}

export default NewLocation;

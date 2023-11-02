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
        <h3 style={{textAlign: "left"}}>New Location</h3>
        <Form className='table-new-item-form'>
          <Row className="align-items-center">
            <Col xs="auto">
              <Form.Label htmlFor="new-location-name" visuallyHidden>
                Name
              </Form.Label>
              <Form.Control
                className="mb-2"
                id="new-location-name"
                placeholder="Name"
                ref={formReferences.name}
              />
            </Col>
            <Col xs="auto" className="my-1">
              <Button onClick={handleSubmit}>Create</Button>
            </Col>
          </Row>
        </Form>
      </div>
    );
}

export default NewLocation;

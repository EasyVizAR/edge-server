import './NewLocation.css';
import App from './App.js';
import { Form, Button, FloatingLabel, Row, Col } from 'react-bootstrap';
import React from "react";
import { useContext, useState } from 'react';
import { LocationsContext } from './Contexts.js';


function NewDevice(props) {
    const host = process.env.PUBLIC_URL;

    const formReferences = {
      name: React.createRef(),
      type: React.createRef()
    }

    function handleSubmit(e) {
      const requestData = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: formReferences.name.current.value,
          type: formReferences.type.current.value,
        })
      };

      fetch(`${host}/headsets`, requestData)
        .then(response => response.json())
        .then(data => {
          if (props.setDevices) {
            props.setDevices(previous => {
              let newDevices = Object.assign({}, previous);
              newDevices[data.id] = data;
              return newDevices;
            });
          }
        });
    }

    return (
      <div className="new-device">
        <h3 style={{textAlign: "left"}}>New Device</h3>
        <Form className='table-new-item-form'>
          <Row className="align-items-center">
            <Col xs="auto">
              <Form.Label htmlFor="new-device-name" visuallyHidden>
                Name
              </Form.Label>
              <Form.Control
                className="mb-2"
                id="new-device-name"
                placeholder="Name"
                ref={formReferences.name}
              />
            </Col>
            <Col xs="auto">
              <Form.Select aria-label="Type" ref={formReferences.type}>
                <option value="headset">Headset</option>
                <option value="phone">Phone</option>
                <option value="editor">Editor (testing)</option>
                <option value="robot">Robot</option>
                <option value="drone">Drone</option>
              </Form.Select>
            </Col>
            <Col xs="auto" className="my-1">
              <Button onClick={handleSubmit}>Create</Button>
            </Col>
          </Row>
        </Form>
      </div>
    );
}

export default NewDevice;

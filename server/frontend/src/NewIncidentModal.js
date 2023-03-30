import App from './App.js';
import { Form, Button, FloatingLabel, Row, Col } from 'react-bootstrap';
import React from "react";
import { useContext, useState } from 'react';
import { ActiveIncidentContext, LocationsContext } from './Contexts.js';

function NewIncidentModal(props) {
  const host = process.env.PUBLIC_URL;

  const { activeIncident, setActiveIncident } = useContext(ActiveIncidentContext);
  const { locations, setLocations } = useContext(LocationsContext);

  const formReferences = {
    name: React.createRef()
  }

  function createNewIncident(e) {
      const newName = formReferences.name.current.value;

      const requestData = {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json'
          },
          body: JSON.stringify({'name': newName})
      };

      fetch(`${host}/incidents`, requestData).then(async response => {
        if (response.ok) {
          return response.json();
        }
      }).then(async data => {
        setActiveIncident(data);
        props.setIncidents(prevIncidents => {
          let newIncidents = [...prevIncidents];
          newIncidents.push(data);
          return newIncidents;
        });
        //props.setTab('location-view');
      });
  }

  return (
    <div className="newIncidentForm">
      <div>
        <h3 style={{textAlign: "left"}}>New Incident</h3>
        <Form onSubmit={createNewIncident}>
          <Row className="align-items-center">
            <Col xs="auto">
              <Form.Group controlId="incident-name">
                <FloatingLabel controlId="incident-floating-name" label="Incident Name">
                  <Form.Control
                    type="text"
                    placeholder="Incident Name"
                    name="incidentName"
                    ref={formReferences.name}/>
                </FloatingLabel>
              </Form.Group>
            </Col>
            <Col xs="auto">
              <Button variant="primary" onClick={createNewIncident}>
                Create
              </Button>
            </Col>
          </Row>
        </Form>
      </div>
    </div>
  );
}

export default NewIncidentModal;

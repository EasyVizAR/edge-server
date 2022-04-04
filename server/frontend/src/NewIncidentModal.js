import App from './App.js';
import { Form, Button, FloatingLabel } from 'react-bootstrap';
import React from "react";
import { useState } from 'react';

function NewIncidentModal(props){
  const[incidentName, setIncidentName] = useState('');
  const host = window.location.hostname;
  const port = props.port;

  function updateState(e){
    setIncidentName(e.target.value);
  }

  function createNewIncident() {
      const requestData = {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json'
          },
          body: JSON.stringify({'incident_name': incidentName})
      };

      fetch(`http://${host}:${port}/incidents/create`, requestData).then(async response => {
      }).then(async data => {
        props.setMaps([]);
        props.getHeadsets();
        window.location.reload(false);
      });
  }

  return (
    <div className="newIncidentForm">
      <div>
        <h2>Create New Incident</h2>
        <Form onSubmit={createNewIncident}>
          <Form.Group style={{width: '50%', margin: 'auto'}} className="mb-3" controlId="incident-name">
            <FloatingLabel controlId="incident-floating-name" label="Incident Name">
              <Form.Control type="text" placeholder="Incident Name" name="incidentName" onChange={(e) => updateState(e)}/>
            </FloatingLabel>
          </Form.Group>
          <Button variant="primary" onClick={createNewIncident}>
            Create
          </Button>
        </Form>
      </div>
    </div>
  );
}

export default NewIncidentModal;
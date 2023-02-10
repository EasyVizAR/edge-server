import App from './App.js';
import { Form, Button, FloatingLabel } from 'react-bootstrap';
import React from "react";
import { useState } from 'react';

function NewIncidentModal(props){
  const[incidentName, setIncidentName] = useState('');
  const host = process.env.PUBLIC_URL;

  function updateState(e){
    setIncidentName(e.target.value);
  }

  function createNewIncident(e) {
      const requestData = {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json'
          },
          body: JSON.stringify({'name': incidentName})
      };

      fetch(`${host}/incidents`, requestData).then(async response => {
        if (response.ok) {
          return response.json();
        }
      }).then(async data => {
        props.currentIncident.set(data['current incident']);
        props.incidentName.set(incidentName);
        props.updateIncidentInfo();
        props.setLocations([]);
        props.getHeadsets();
        props.getIncidentHistory();
        e.target.form.elements.incidentName.value = ""
        props.setTab('location-view');
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

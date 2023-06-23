import {Container, Form, Table, Row, Col, Button} from 'react-bootstrap';
import React, {useContext, useState, useEffect} from 'react';

function HeadsetConfiguration(props) {
  const host = process.env.PUBLIC_URL;

  // Only one row can be open for editing at a time. A reference is used to
  // query the value of the input field when the user clicks Save. The
  // performance is much better than using an onChange handler for every
  // key press.
  const formReferences = {
    enable_mesh_capture: React.createRef(),
    enable_photo_capture: React.createRef(),
    enable_extended_capture: React.createRef()
  };

  function saveConfiguration() {
    const requestData = {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        "headset_configuration.enable_mesh_capture": formReferences.enable_mesh_capture.current.checked,
        "headset_configuration.enable_photo_capture": formReferences.enable_photo_capture.current.checked,
        "headset_configuration.enable_extended_capture": formReferences.enable_extended_capture.current.checked
      })
    };

    const url = `${host}/locations/${props.location.id}`;

    fetch(url, requestData)
      .then(response => response.json())
      .then(data => {
        props.setLocation(data);
      });
  }

  return (
    <div>
      <h3>Headset Configuration</h3>
      <p>These settings will be sent to headsets when they check in at the location.</p>
      <Form key={props.location.id}>
        <Form.Group as={Row} className="mb-3">
          <Form.Label column sm={6} for="enable_mesh_capture">
            Enable mesh capture
          </Form.Label>
          <Col sm={6}>
            <Form.Check
              id="enable_mesh_capture"
              label="Enable automatic mesh capturing for map construction"
              type="checkbox"
              defaultChecked={props.location.headset_configuration.enable_mesh_capture}
              ref={formReferences.enable_mesh_capture}
            />
          </Col>
        </Form.Group>

        <Form.Group as={Row} className="mb-3">
          <Form.Label column sm={6} for="enable_photo_capture">
            Enable photo capture
          </Form.Label>
          <Col sm={6}>
            <Form.Check
              id="enable_photo_capture"
              label="Enable automatic (high resolution) photo capture, which may be resource intensive"
              type="checkbox"
              defaultChecked={props.location.headset_configuration.enable_photo_capture}
              ref={formReferences.enable_photo_capture}
            />
          </Col>
        </Form.Group>

        <Form.Group as={Row} className="mb-3">
          <Form.Label column sm={6} for="enable_extended_capture">
            Enable extended capture
          </Form.Label>
          <Col sm={6}>
            <Form.Check
              id="enable_extended_capture"
              label="Enable automatic capture of photos, depth, geometry, and intensity images"
              type="checkbox"
              defaultChecked={props.location.headset_configuration.enable_extended_capture}
              ref={formReferences.enable_extended_capture}
            />
          </Col>
        </Form.Group>

        <Form.Group as={Row} className="mb-3">
          <Col sm={{ span: 10, offset: 2 }}>
            <Button onClick={() => saveConfiguration()}>Save</Button>
          </Col>
        </Form.Group>
      </Form>
    </div>
  );
}

export default HeadsetConfiguration;

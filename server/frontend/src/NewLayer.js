import './NewLayer.css';
import App from './App.js';
import {Form, Button, FloatingLabel, FormText, FormControl, Dropdown, DropdownButton, Row, Col} from 'react-bootstrap';
import React from "react";
import { useContext, useState } from 'react';
import { LocationsContext } from './Contexts.js';


function NewLayer(props) {
    const host = process.env.PUBLIC_URL;

    const { locations, setLocations } = useContext(LocationsContext);

    const formReferences = {
      name: React.createRef(),
      cutting_height: React.createRef(),
    }

    const [layerType, setLayerType] = useState("generated");
    const [file, setFile] = useState('');

    const handleSubmit = (e) => {
        const new_layer = {
            name: formReferences.name.current.value,
            type: layerType
        }

        if (new_layer.type === "generated") {
          new_layer.cutting_height = formReferences.cutting_height.current.value;
        }

        const requestData = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(new_layer)
        };

        let url = `${host}/locations/${props.location.id}/layers`;
        fetch(url, requestData)
            .then(response => response.json())
            .then(data => {
                if (props.setLayers) {
                  props.setLayers(prevLayers => {
                    let newLayers = [...prevLayers];
                    newLayers.push(data);
                    return newLayers;
                  });
                }

                if (layerType === "uploaded") {
                  const url =  `${host}/locations/${props.location.id}/layers/${data.id}/image`;
                  const formData = new FormData();
                  formData.append('image', file);
                  const config = {
                      method: 'PUT',
                      body: formData
                  };
                  fetch(url, config)
                      .then(response => response.json());
                }
            });
    }

    const onFileSelect = (e) => {
        setFile(e.target.files[0])
    }

    return (
      <div className="new-layer">
        <h3 style={{textAlign: "left"}}>New Layer</h3>
        <Form className='table-new-item-form new-layer-form'>
          <Form.Group as={Row} className="mb-3">
            <Form.Label column sm="2">
              Name
            </Form.Label>
            <Col sm="10">
              <Form.Control
                className="mb-2"
                id="new-layer-name"
                placeholder="Name"
                ref={formReferences.name}
              />
            </Col>
          </Form.Group>

          <Form.Group as={Row} className="mb-3">
            <Form.Label column sm="2">
              Layer Type
            </Form.Label>
            <Col sm="10">
              <select
                id="layer-type-dropdown"
                title="Select Layer Type"
                defaultValue="generated"
                onChange={e => setLayerType(e.target.value)}
                value={layerType}>
                <option value="generated">Generated</option>
                <option value="uploaded">Uploaded</option>
              </select>
            </Col>
          </Form.Group>

          <Form.Group as={Row} className="mb-3">
            <Form.Label column sm="2">
              Cutting Plane Height
            </Form.Label>
            <Col sm="10">
              <Form.Control
                className="mb-2"
                type="number"
                id="new-layer-cutting-heightt"
                disabled={layerType !== "generated"}
                placeholder="Cutting Height"
                defaultValue="0"
                ref={formReferences.cutting_height}
              />
            </Col>
          </Form.Group>

          <Form.Group as={Row} className="mb-3">
            <Form.Label column sm="2">
              Image File
            </Form.Label>
            <Col sm="10">
              <Form.Control type="file" name="file" disabled={layerType !== 'uploaded'} onChange={onFileSelect} />
            </Col>
          </Form.Group>

          <Button variant="primary" onClick={handleSubmit}>
            Create Layer
          </Button>
        </Form>
      </div>
    );
}

export default NewLayer;

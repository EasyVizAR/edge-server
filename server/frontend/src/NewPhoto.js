import './NewLayer.css';
import App from './App.js';
import {Form, Button, FloatingLabel, FormText, FormControl, Dropdown, DropdownButton, Row, Col} from 'react-bootstrap';
import React from "react";
import { useContext, useState } from 'react';


function NewPhoto(props) {
    const host = process.env.PUBLIC_URL;

    const [file, setFile] = useState(null);

    const handleSubmit = (e) => {
      if (file === null) {
        return;
      }

      const requestData = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          camera_location_id: props.location?.id
        })
      };

      const url = `${host}/photos`;
      fetch(url, requestData)
        .then(response => response.json())
        .then(data => {
          const photo_url = `${host}/photos/${data.id}/image`;
          const formData = new FormData();
          formData.append('image', file);
          const requestData = {
            method: 'PUT',
            body: formData
          }
          fetch(photo_url, requestData)
            .then(response => response.json())
            .then(data => {
              setFile(null);
            });
        });
    }

    const onFileSelect = (e) => {
        setFile(e.target.files[0])
    }

    return (
      <div className="new-photo">
        <h3 style={{textAlign: "left"}}>Upload Photo</h3>
        <Form className='table-new-item-form new-layer-form'>
          <Form.Group as={Row} className="mb-3">
            <Form.Label column sm="2">
              Image File
            </Form.Label>
            <Col sm="10">
              <Form.Control type="file" name="file" onChange={onFileSelect} />
            </Col>
          </Form.Group>

          <Button variant="primary" onClick={handleSubmit}>
            Upload Photo
          </Button>
        </Form>
      </div>
    );
}

export default NewPhoto;

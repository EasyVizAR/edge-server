import { Button, Form, FloatingLabel } from 'react-bootstrap';
import './Popup.css';
import React from "react";
import { useState } from 'react';

function Popup(props){
    const state = {
      feature_name: "",
      placement_type: "",
    }
    const[formVal, updateForm] = useState(state);
    const[feature_name, setName] = useState('');
    const[placement_type, setPlacement] = useState('');

    if (!props.popUpClass){
      return null;
    }

    const host = window.location.hostname;

    function updateState(e, type){
      let val = e.target.value;
      switch(type){
        case "feature-name":
          setName(val);
          //console.log("feature-name: " + feature_name);
          break;
        case "placement-type":
          setPlacement(val);
          break;
      }
      updateForm({feature_name:feature_name, placement_type:placement_type});
      //console.log(formVal);
    }

    const handleSubmit = (event) => {
      let formData = formVal;
      const new_feature = {
        new_feature: formData,
      }
      let mapID = "2e1a03e6-3d9d-11ec-a64a-0237d8a5e2fd";
      let url = `http://${host}:5000/maps/${mapID}/features`;
      const requestData = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(new_feature)
      };
      fetch(url, requestData)
      .then(response => response.json())
      .then(data => {
        console.log(data);
      });
    }

    return (

        <div className="popUpClassShow">
          <div className="inner-modal">
            <h2>Add a Feature</h2>
            <div id="form-div">
              <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-3" controlId="feature-name">
                  <FloatingLabel controlId="floating-name" label="Feature Name">
                    <Form.Control type="text" placeholder="Feature Name" name="mapName" onChange={(e) => updateState(e, "feature-name")}/>
                  </FloatingLabel>
                </Form.Group>

                <Form.Group className="mb-3" controlId="placement-type">
                  <FloatingLabel controlId="floating-placement-type" label="Placement Type">
                    <Form.Select aria-label="Placement Type" onChange={(e) => updateState(e, "placement-type")}>
                      <option>--Select--</option>
                      <option value="floating">Floating</option>
                      <option value="surface">Surface</option>
                      <option value="point">Point</option>
                    </Form.Select>
                  </FloatingLabel>
                </Form.Group>

                <Button variant="primary" onClick={handleSubmit}>
                  Submit
                </Button>
              </Form>
            </div>
          </div>
          <hr/>
        </div>
    );
}

export default Popup;
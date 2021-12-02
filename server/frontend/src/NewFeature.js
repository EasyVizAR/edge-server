import { Button, Form, FloatingLabel, Row, Col } from 'react-bootstrap';
import './NewFeature.css';
import React from "react";
import { useState, useEffect } from 'react';
import {port} from "./App";

function NewFeature(props){
    const state = {
      feature_name: "",
      placement_type: "",
      x: null,
      y: null,
      z: null,
      offset: null,
      placement_location: null,
      coord_location: null,
      icon: -1,
    }

    const hideDisplay = {
      display: "none"
    }

    const showDisplay = {
      display: "block"
    }

    const displayflex = {
      display: "flex"
    }

    const host = window.location.hostname;

    const[formVal, updateForm] = useState(state);
    const[feature_name, setName] = useState('');
    const[placement_type, setPlacement] = useState('');
    const[x_pos, setX] = useState(null);
    const[y_pos, setY] = useState(null);
    const[z_pos, setZ] = useState(null);
    const[offset_percent, setOffPer] = useState("0");
    const[placement_location, setPlacementLoc] = useState(null);
    const[coord_location, setCoordLocation] = useState(null);
    const[posStyle, setPosStyle] = useState(hideDisplay);
    const[coordStyle, setCoordStyle] = useState(hideDisplay);
    const[offsetPerStyle, setOffsetPerStyle] = useState(hideDisplay);
    const[iconPaths, setIconPaths] = useState(null);
    const[iconIndex, changeIcon] = useState(-1);

    useEffect(() => {
      const url = `http://${host}:${port}/icon_urls`;
      fetch(url)
      .then(response => response.json())
      .then(data => {
        data['file_paths'].map((path, index) => {
          const url = `http://${host}:${port}/` + path;
          data['file_paths'][index] = url;
        });
        setPaths(data['file_paths']);
      });
      //const temp = [fire.png`, `http://${host}:${port}/icons/medical.png`, `http://${host}:${port}/icons/obstacle.png`, `http://${host}:${port}/icons/target.png`];
      //setIconPaths(temp);
    }, []);

    if (!props.popUpClass){
      return null;
    }

    function setPaths(paths){

      // TODO: bug here. Does not update iconPaths

      setIconPaths("hi");
      console.log("here1");
      console.log(iconPaths);
      console.log(paths);
      setIconPaths(paths);
      console.log("here2");
      console.log(iconPaths);
    }

    function setIcon(index){
      changeIcon(index);
      console.log(iconIndex);

      // TODO: set css of selected icon

      updateForm({feature_name:feature_name, placement_type:placement_type, x:x_pos, y:y_pos, z:z_pos, offset:offset_percent, placement_location:placement_location, coord_location: coord_location, icon: iconIndex});
    }

    function Icons(props){
      const iconPaths = props.iconPaths;

      if(iconPaths != null){
        const marginCss = {
          marginBottom: "10px",
          marginLeft: "10px"
        }

        const listItems = iconPaths.map((icon, index) =>
          <Col>
            <img onClick={(e) => setIcon(index)} src={icon} className="iconImg" alt="Icon"/>
          </Col>
        );
        return (
          <Row style={marginCss}>{listItems}</Row>
        );
      }

    }

    function updateState(e, type){

      // TODO: bug here. lags when updating variables

      let val = e.target.value;
      switch(type){
        case "feature-name":
          setName(val);
          //console.log("feature-name: " + feature_name);
          break;
        case "placement-type":
          setPlacement(val);
          hideAllSections();
          if (val === "point"){
            console.log("point");
            setPosStyle(displayflex);
            setCoordStyle(showDisplay);
          }else if(val == "floating" || val == "surface"){
            console.log("not point");
            setOffsetPerStyle(showDisplay);
          }
          break;
        case "offset-percent":
          setOffPer(val);
          break;
        case "point-x":
          setX(val);
          break;
        case "point-y":
          setY(val);
          break;
        case "point-z":
          setZ(val);
          break;
        case "placement-location":
          setPlacementLoc(val);
          break;
        case "coord-location":
          setCoordLocation(val);
          break;
        default:
          console.warn('Bad type');
          return null;
      }
      updateForm({feature_name:feature_name, placement_type:placement_type, x:x_pos, y:y_pos, z:z_pos, offset:offset_percent, placement_location:placement_location, coord_location: coord_location, icon: iconIndex});
      console.log(formVal);
    }

    function hideAllSections(){
      setCoordStyle(hideDisplay);
      setOffsetPerStyle(hideDisplay);
      setPosStyle(hideDisplay);
      console.log("resetting sections " + coordStyle.display);
    }

    const handleSubmit = (event) => {
      let formData = formVal;
      const new_feature = {
        new_feature: formData,
      }
      let mapID = "2e1a03e6-3d9d-11ec-a64a-0237d8a5e2fd";
      let url = `http://${host}:${port}/maps/${mapID}/features`;
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

                <Form.Group className="mb-3" controlId="placement-location" style={offsetPerStyle}>
                  <FloatingLabel controlId="placement-location" label="Placement Location">
                    <Form.Select aria-label="Placement Location" onChange={(e) => updateState(e, "placement-location")}>
                      <option>--Select--</option>
                      <option value="ceiling">Ceiling</option>
                      <option value="floor">Floor</option>
                    </Form.Select>
                  </FloatingLabel>
                </Form.Group>

                <Form.Group className="mb-3" controlId="offset-percent" style={offsetPerStyle}>
                  <FloatingLabel controlId="offset-percent" label="Offset (%)">
                    <Form.Control type="number" max="100" min="0" defaultValue="0" placeholder="Offset (%)" name="offset-percent" onChange={(e) => updateState(e, "offset-percent")}/>
                  </FloatingLabel>
                </Form.Group>

                <Form.Group className="mb-3" controlId="coord-location" style={coordStyle}>
                  <FloatingLabel controlId="coord-location" label="Placement Location">
                    <Form.Select aria-label="coord Location" onChange={(e) => updateState(e, "coord-location")}>
                      <option>--Select--</option>
                      <option value="world">World</option>
                      <option value="image">Image</option>
                    </Form.Select>
                  </FloatingLabel>
                </Form.Group>

                <Row className="mb-3" style={posStyle}>
                  <Col>
                    <Form.Group className="mb-3" controlId="point-pos-x">
                      <FloatingLabel controlId="floating-x-position" label="X Position">
                        <Form.Control type="number" placeholder="X Position" name="x_pos" onChange={(e) => updateState(e, "point-x")}/>
                      </FloatingLabel>
                    </Form.Group>
                  </Col>
                  <Col>
                    <Form.Group className="mb-3" controlId="point-pos-y">
                      <FloatingLabel controlId="floating-y-position" label="Y Position">
                        <Form.Control type="number" placeholder="Y Position" name="y_pos" onChange={(e) => updateState(e, "point-y")}/>
                      </FloatingLabel>
                    </Form.Group>
                  </Col>
                  <Col>
                    <Form.Group className="mb-3" controlId="point-pos-z">
                      <FloatingLabel controlId="floating-z-position" label="Z Position">
                        <Form.Control type="number" placeholder="Z Position" name="z_pos" onChange={(e) => updateState(e, "point-z")}/>
                      </FloatingLabel>
                    </Form.Group>
                  </Col>
                </Row>

                <p className="icon-select-label">Select an icon:</p>
                <div className="icon-select" style={displayflex}>
                  <Icons iconPaths={iconPaths}/>
                </div>
                <br/>
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

export default NewFeature;
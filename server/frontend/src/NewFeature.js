import {Button, Form, FloatingLabel, Row, Col, ButtonGroup} from 'react-bootstrap';
import './NewFeature.css';
import React from "react";
import {useState, useEffect} from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { solid, regular, brands } from '@fortawesome/fontawesome-svg-core/import.macro'
import RangeSlider from 'react-bootstrap-range-slider';

function NewFeature(props) {
    const icons = props.icons;

    const state = {
        feature_name: "",
        placement_type: "",
        x: null,
        y: null,
        z: null,
        offset: null,
        placement_location: null,
        coord_location: null,
        icon: null,
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

    const host = process.env.PUBLIC_URL;

    const formReferences = {
      name: React.createRef(),
    }

    const [formVal, updateForm] = useState(state);
    const [feature_name, setName] = useState('');
    const [x_pos, setX] = useState(null);
    const [y_pos, setY] = useState(null);
    const [z_pos, setZ] = useState(null);
    const [top_offset_percent, setTopOffPer] = useState("0");
    const [left_offset_percent, setLeftOffPer] = useState("0");
    const [placement_location, setPlacementLoc] = useState(null);
    const [coord_location, setCoordLocation] = useState(null);
    const [posStyle, setPosStyle] = useState(hideDisplay);
    const [coordStyle, setCoordStyle] = useState(hideDisplay);
    const [offsetPerStyle, setOffsetPerStyle] = useState(hideDisplay);
    const [feature_type, changeIcon] = useState(null);
    const [rangeSliderVisibility, setRangeSliderVisibility] = useState("none")

    const [mapMode, setMapMode] = useState(false);
    const [featureType, setFeatureType] = useState("point")

    if (!props.showNewFeature) {
        return null;
    }

    function setIcon(type) {
        //changeIcon(type);
        //props.setIconIndex(type);
        // TODO: set css of selected icon
    }

    function Icons() {
        // update icons here

        const marginCss = {
            marginBottom: "10px",
            marginLeft: "10px"
        }

        const listItems = Object.keys(icons).map((name, index) =>
            <Col style={{display:"flex", flexDirection:"row"}}>
                <input checked={featureType===name} onClick={(e) => setFeatureType(name)} type='radio' name='feature-icon' style={{marginRight: '5px'}}/>
                <FontAwesomeIcon icon={icons[name]} size="lg"/>
            </Col>
        );
        return (
            <Row style={marginCss}>{listItems}</Row>
        );
    }

    function hideAllSections() {
        setCoordStyle(hideDisplay);
        setOffsetPerStyle(hideDisplay);
        setPosStyle(hideDisplay);
        setRangeSliderVisibility("none")
        console.log("resetting sections " + coordStyle.display);
    }

    const changeInputMode = (e) => {
        setMapMode(!mapMode);
        props.changeCursor();
    };

    const handleSubmit = (event) => {
        let formData = formVal;
        const new_feature = {
            "name": formReferences.name.current.value,
            "type": featureType,
            "position": {
                "x": props.pointCoordinates[0],
                "y": props.pointCoordinates[1],
                "z": props.pointCoordinates[2]
            }
        }

        let url = `${host}/locations/${props.mapID}/features`
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
      <div className="new-feature">
        <h3 style={{textAlign: "left"}}>New Feature</h3>
        <Form className='table-new-item-form new-feature-form'>
          <Form.Group as={Row} className="mb-3">
            <Form.Label column sm="2">
              Name
            </Form.Label>
            <Col sm="10">
              <Form.Control
                className="mb-2"
                id="new-feature-name"
                placeholder="Name"
                ref={formReferences.name}
              />
            </Col>
          </Form.Group>

          <Form.Group as={Row} className="mb-3">
            <Form.Label column sm="2">
              Position
            </Form.Label>

            <Col sm="1">
              <Form.Group>
                <input checked={mapMode} onClick={(e) => changeInputMode(e)} type='checkbox' name='map-mode' />
                <Form.Label>choose on map</Form.Label>
              </Form.Group>
            </Col>

            <Col sm="3">
              <Form.Control type="number" disabled={mapMode} placeholder="X"
                value={props.pointCoordinates[0]} defaultValue='0'
                name="x_pos" onChange={e => props.changePointValue(e.target.value, 0)}/>
            </Col>

            <Col sm="3">
              <Form.Control type="number" disabled={mapMode} placeholder="Y"
                value={props.pointCoordinates[1]} defaultValue='0'
                name="y_pos" onChange={e => props.changePointValue(e.target.value, 1)}/>
            </Col>

            <Col sm="3">
              <Form.Control type="number" disabled={mapMode} placeholder="Z"
                value={props.pointCoordinates[2]} defaultValue='0'
                name="z_pos" onChange={e => props.changePointValue(e.target.value, 2)}/>
            </Col>
          </Form.Group>

          <Form.Group as={Row} className="mb-3">
            <Form.Label column sm="2">
              Icon
            </Form.Label>
            <Col sm="10">
              <Icons/>
            </Col>
          </Form.Group>

          <Button variant="primary" onClick={handleSubmit}>
            Create Feature
          </Button>
        </Form>
      </div>
    );
}

export default NewFeature;

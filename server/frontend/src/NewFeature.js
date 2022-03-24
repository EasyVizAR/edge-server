import {Button, Form, FloatingLabel, Row, Col, ButtonGroup} from 'react-bootstrap';
import './NewFeature.css';
import React from "react";
import {useState, useEffect} from 'react';
import App, {port} from "./App";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { solid, regular, brands } from '@fortawesome/fontawesome-svg-core/import.macro'
import RangeSlider from 'react-bootstrap-range-slider';

function NewFeature(props) {
    // Map feature type -> FA icon
    const icons = {
        fire: solid('fire'),
        warning: solid('triangle-exclamation'),
        injury: solid('bandage'),
        door: solid('door-closed'),
        elevator: solid('elevator'),
        stairs: solid('stairs'),
        user: solid('user'),
        object: solid('square'),
        extinguisher: solid('fire-extinguisher'),
        message: solid('message'),
        headset: solid('headset'),
        ambulance: solid('truck-medical'),
    }

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

    const host = window.location.hostname;

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

    if (!props.popUpClass) {
        return null;
    }

    function setIcon(index) {
        changeIcon(index);
        props.setIconIndex(index);
        // TODO: set css of selected icon

        updateForm({
            feature_name: feature_name,
            placement_type: props.placementType,
            x: x_pos,
            y: y_pos,
            z: z_pos,
            top_offset: top_offset_percent,
            left_offset: left_offset_percent,
            placement_location: placement_location,
            coord_location: coord_location,
            icon: feature_type
        });
    }

    function Icons() {

        // update icons here

        const marginCss = {
            marginBottom: "10px",
            marginLeft: "10px"
        }

        const listItems = Object.keys(icons).map((name, index) =>
            <Col style={{display:"flex", flexDirection:"row"}}>
                <input checked={feature_type==name} onClick={(e) => setIcon(name)} type='radio' name='feature-icon' style={{marginRight: '5px'}}/>
                <FontAwesomeIcon icon={icons[name]} size="lg"/>
            </Col>
        );
        return (
            <Row style={marginCss}>{listItems}</Row>
        );

    }

    function updateState(e, type) {

        // TODO: bug here. lags when updating variables


        let val = e.target.value;
        switch (type) {
          case "feature-name":
            setName(val);
            break;
          case "placement-type":
              props.setPlacementType(val);
            hideAllSections();
            if (val === "point") {
                console.log("point");
                setPosStyle(displayflex);
                setCoordStyle(showDisplay);
            } else if (val == "floating" || val == "surface") {
                console.log("not point");
                setOffsetPerStyle(showDisplay);
                if (val == "floating") {
                    setPosStyle(displayflex);
                    setRangeSliderVisibility("flex");
                } else {
                    setRangeSliderVisibility("none");
                }
            } else {
                setRangeSliderVisibility("none");
            }
            break;
          case "left-offset-percent":
            setLeftOffPer(val);
            break;
          case "top-offset-percent":
            setTopOffPer(val);
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
        updateForm({
            feature_name: feature_name,
            placement_type: props.placementType,
            x: x_pos,
            y: y_pos,
            z: z_pos,
            top_offset: top_offset_percent,
            left_offset: left_offset_percent,
            placement_location: placement_location,
            coord_location: coord_location,
            icon: feature_type
        });
        console.log(formVal);
    }

    function hideAllSections() {
        setCoordStyle(hideDisplay);
        setOffsetPerStyle(hideDisplay);
        setPosStyle(hideDisplay);
        console.log("resetting sections " + coordStyle.display);
    }

    const changeInputMode = (e) => {
        setMapMode(!mapMode);
        props.changeCursor();
    };

    const handleSubmit = (event) => {
        let formData = formVal;
        const new_feature = {
            "name": feature_name,
            "type": feature_type,
            "position": {
                "x": props.pointCoordinates[0],
                "y": props.pointCoordinates[1],
                "z": props.pointCoordinates[2]
            },
            "mapID": props.mapID,
            "style": {
                "placement": props.placementType,
                "topOffset": top_offset_percent,
                "leftOffset": left_offset_percent
            }
        }

        if (props.placementType == 'floating') {
            new_feature.style.radius = props.sliderValue;
        }

        console.log(new_feature)
        let url = `http://${host}:${port}/maps/${props.mapID}/features`;
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
                                <Form.Control type="text" placeholder="Feature Name" name="mapName" value={feature_name}
                                              onChange={(e) => updateState(e, "feature-name")}/>
                            </FloatingLabel>
                        </Form.Group>

                        <Form.Group className="mb-3" controlId="placement-type">
                            <FloatingLabel controlId="floating-placement-type" label="Placement Type">
                                <Form.Select aria-label="Placement Type"
                                             onChange={(e) => updateState(e, "placement-type")}>
                                    <option>--Select--</option>
                                    <option value="floating">Floating</option>
                                    <option value="surface">Surface</option>
                                    <option value="point">Point</option>
                                </Form.Select>
                            </FloatingLabel>
                        </Form.Group>

                        <Form.Group className="mb-3" controlId="placement-location" style={offsetPerStyle}>
                            <FloatingLabel controlId="placement-location" label="Placement Location">
                                <Form.Select aria-label="Placement Location"
                                             onChange={(e) => updateState(e, "placement-location")}>
                                    <option>--Select--</option>
                                    <option value="ceiling">Ceiling</option>
                                    <option value="floor">Floor</option>
                                </Form.Select>
                            </FloatingLabel>
                        </Form.Group>
                        <div style={{display: "flex", width: "100%"}}>
                            <Form.Group className="mb-3" controlId="top-offset-percent" style={{width: "50%"}}>
                              <FloatingLabel controlId="top-offset-percent" label="Top Offset (%)">
                                <Form.Control type="number" max="100" min="0" defaultValue="0" placeholder="Top Offset (%)"
                                              name="top-offset-percent" onChange={(e) => updateState(e, "top-offset-percent")}/>
                              </FloatingLabel>
                            </Form.Group>
                            <Form.Group className="mb-3" controlId="left-offset-percent" style={{width: "50%"}}>
                              <FloatingLabel controlId="left-offset-percent" label="Left Offset (%)">
                                <Form.Control type="number" max="100" min="0" defaultValue="0" placeholder="Left Offset (%)"
                                              name="left-offset-percent" onChange={(e) => updateState(e, "left-offset-percent")}/>
                              </FloatingLabel>
                            </Form.Group>
                        </div>
                        <div style={{display: rangeSliderVisibility, height: 'contentMax'}}>
                            <RangeSlider
                                value={props.sliderValue}
                                onChange={e => props.setSliderValue(e.target.value)}
                                tooltipLabel={currentValue => `${currentValue}`}
                                tooltip='on'
                                min={1}
                                max={15}
                            />
                        </div>
                        <Form.Group className="mb-3" controlId="coord-location" style={coordStyle}>
                            <FloatingLabel controlId="coord-location" label="Placement Location">
                                <Form.Select aria-label="coord Location"
                                             onChange={(e) => updateState(e, "coord-location")}>
                                    <option>--Select--</option>
                                    <option value="world">World</option>
                                    <option value="image">Image</option>
                                </Form.Select>
                            </FloatingLabel>
                        </Form.Group>

                        <input style={posStyle} checked={!mapMode} type='radio' value='coordinates' onClick={changeInputMode} name='input-mode-radio'/>
                        <label style={posStyle} htmlFor="coordinates">Input Coordinates</label>
                        <Row className="mb-3" style={posStyle}>
                            <Col>
                                <Form.Group className="mb-3" controlId="point-pos-x">
                                    <FloatingLabel controlId="floating-x-position" label="X Position">
                                        <Form.Control type="number" disabled={mapMode} placeholder="X Position"
                                                      value={props.pointCoordinates[0]} defaultValue=''
                                                      name="x_pos" onChange={e => props.changePointValue(e.target.value, 0)}/>
                                    </FloatingLabel>
                                </Form.Group>
                            </Col>
                            <Col>
                                <Form.Group className="mb-3" controlId="point-pos-y">
                                    <FloatingLabel controlId="floating-y-position" label="Y Position">
                                        <Form.Control type="number" disabled={mapMode} placeholder="Y Position"
                                                      value={props.pointCoordinates[1]} defaultValue=''
                                                      name="y_pos" onChange={e => props.changePointValue(e.target.value, 1)}/>
                                    </FloatingLabel>
                                </Form.Group>
                            </Col>
                            <Col>
                                <Form.Group className="mb-3" controlId="point-pos-z">
                                    <FloatingLabel controlId="floating-z-position" label="Z Position">
                                        <Form.Control type="number" disabled={mapMode} placeholder="Z Position"
                                                      value={props.pointCoordinates[2]} defaultValue=''
                                                      name="z_pos" onChange={e => props.changePointValue(e.target.value, 2)}/>
                                    </FloatingLabel>
                                </Form.Group>
                            </Col>
                        </Row>

                        <input style={posStyle} type='radio' value='onmap' onClick={changeInputMode} name='input-mode-radio'/>
                        <label htmlFor="onmap" style={posStyle}>Select on Map</label>

                        <p className="icon-select-label">Select an icon:</p>
                        <div className="icon-select" style={posStyle}>
                            <Icons/>
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

import {Badge, Button, Form, FloatingLabel, Row, Col, ButtonGroup} from 'react-bootstrap';
import './NewFeature.css';
import React from "react";
import {useState, useEffect} from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { solid, regular, brands } from '@fortawesome/fontawesome-svg-core/import.macro'
import RangeSlider from 'react-bootstrap-range-slider';

function NewMapPath(props) {
    const host = process.env.PUBLIC_URL;

    const icons = props.icons;

    const formReferences = {
      mobile_device_id: React.createRef(),
      target_marker_id: React.createRef(),
      type: React.createRef(),
      color: React.createRef(),
      label: React.createRef(),
    }

    const setMobileDevice = (device_id) => {
      if (device_id && props.headsets[device_id]) {
        formReferences.color.current.value = props.headsets[device_id].color;
      }
    }

    const handleSubmit = (event) => {
        let points = [...props.pointList];

        // If mobile_device_id is set, get the starting position from the device's position.
        // However, adjust the Y coordinate to be consistent with the first path point.
        if (formReferences.mobile_device_id.current.value) {
          const device = props.headsets[formReferences.mobile_device_id.current.value];
          let start = {...device.position};
          if (points.length > 0) {
            start.y = points[0][1];
          }
          points.splice(0, 0, start);
        }

        // If target_marker_id is set, get the ending position from the target marker.
        // However, adjust the Y coordinate to be consistent with the last path point.
        if (formReferences.target_marker_id.current.value) {
          const marker = props.features[formReferences.target_marker_id.current.value];
          let end = {...marker.position};
          if (points.length > 0) {
            end.y = points[points.length-1][1];
          }
          points.push(end);
        }

        const new_path = {
          mobile_device_id: formReferences.mobile_device_id.current.value || null,
          target_marker_id: formReferences.target_marker_id.current.value || null,
          type: formReferences.type.current.value,
          color: formReferences.color.current.value,
          label: formReferences.label.current.value,
          points: points,
        }

        let url = `${host}/locations/${props.locationId}/map-paths`
        const requestData = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(new_path)
        };

        // If mobile_device_id is set, change method to PUT.
        // This ensures that only one navigation path exists for the device.
        if (formReferences.mobile_device_id.current.value) {
          url = `${url}?mobile_device_id=${formReferences.mobile_device_id.current.value}&type=navigation`;
          requestData.method = "PUT"
        }

        fetch(url, requestData)
            .then(response => response.json());
    }

    return (
      <div className="new-feature">
        <h3 style={{textAlign: "left"}}>New Path</h3>
        <Form className='table-new-item-form new-feature-form'>

          <Form.Group as={Row} className="mb-3">
            <Form.Label column sm="2">
              Mobile Device
            </Form.Label>
            <Col sm="10">
              <select
                title="Select Mobile Device"
                onChange={e => setMobileDevice(e.target.value)}
                defaultValue=""
                ref={formReferences.mobile_device_id} >
                <option value=''>All</option>
                {
                  Object.entries(props.headsets).map(([id, headset]) => {
                    return <option value={id}>{headset.name}</option>
                  })
                }
              </select>
            </Col>
          </Form.Group>

          <Form.Group as={Row} className="mb-3">
            <Form.Label column sm="2">
              Target
            </Form.Label>
            <Col sm="10">
              <select
                title="Select Target"
                defaultValue=""
                ref={formReferences.target_marker_id} >
                <option value=''>None</option>
                {
                  Object.entries(props.features).map(([id, feature]) => {
                    return <option value={id}>{`${id}: ${feature.name}`}</option>
                  })
                }
              </select>
            </Col>
          </Form.Group>

          <Form.Group as={Row} className="mb-3">
            <Form.Label column sm="2">
              Path Type
            </Form.Label>
            <Col sm="10">
              <select
                title="Select Type"
                defaultValue="navigation"
                ref={formReferences.type} >
                <option value="drawing">Drawing</option>
                <option value="navigation">Navigation</option>
                <option value="object">Object</option>
              </select>
            </Col>
          </Form.Group>

          <Form.Group as={Row} className="mb-3">
            <Form.Label column sm="2">
              Color
            </Form.Label>
            <Col sm="10">
              <input
                defaultValue="#0000ff"
                placeholder="Edit Color"
                type="color"
                ref={formReferences.color} />
            </Col>
          </Form.Group>

          <Form.Group as={Row} className="mb-3">
            <Form.Label column sm="2">
              Label
            </Form.Label>
            <Col sm="10">
              <Form.Control
                className="mb-2"
                placeholder="Label"
                ref={formReferences.label} />
            </Col>
          </Form.Group>

          <Form.Group as={Row} className="mb-3">
            <Form.Label column sm="2">
              Points
            </Form.Label>
            <Col sm="10">
              {
                props.pointList.map((point, index) => {
                  return <Badge bg="secondary">{point[0].toFixed(3)}, {point[1].toFixed(3)}, {point[2].toFixed(3)}</Badge>
                })
              }
            </Col>
          </Form.Group>

          <Button variant="primary" onClick={handleSubmit}>
            Create Path
          </Button>
        </Form>
      </div>
    );
}

export default NewMapPath;

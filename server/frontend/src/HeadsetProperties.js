import {Container, Form, Table, Row, Col, Button} from 'react-bootstrap';
import React, {useContext, useState, useEffect} from 'react';
import { LocationsContext } from './Contexts.js';


const deviceTypeOptions = [
  "unknown",
  "headset",
  "phone",
  "editor",
  "robot",
  "drone",
];


function HeadsetProperties(props) {
  const host = process.env.PUBLIC_URL;
  const config_url = `${host}/headsets/${props.headset.id}`;

  const { locations, setLocations } = useContext(LocationsContext);

  const formReferences = {
    name: React.createRef(),
    color: React.createRef(),
    location_id: React.createRef(),
    type: React.createRef(),
    "offset.x": React.createRef(),
    "offset.y": React.createRef(),
    "offset.z": React.createRef(),
    "rotation.x": React.createRef(),
    "rotation.y": React.createRef(),
    "rotation.z": React.createRef(),
  };

//  useEffect(() => {
//    fetch(config_url)
//      .then(response => response.json())
//      .then(data => setConfiguration(data));
//  }, []);

  function save() {
    const requestData = {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(
        // Map the formReferences object to one we can send to the server by
        // keeping the field names but fetching the reference values.  We do
        // need to fetch checkboxes differently from other input types.  As
        // long as the checkbox fields are all named with "enable_", this will
        // work.
        Object.fromEntries(
          Object.entries(formReferences).map(
            ([k, v], i) => [k, k.startsWith("enable_") ? v.current.checked : v.current.value]
          )
        )
      )
    };

    fetch(config_url, requestData)
      .then(response => response.json())
      .then(data => props.setHeadset(data));
  }

  return (
    <div>
      <h3>Headset</h3>
      <Form>
        <Table striped bordered hover>
          <tbody>
            <tr>
              <td>
                <Form.Label for="name">
                  Name
                </Form.Label>
              </td>
              <td>
                <Form.Control
                  className="mb-2"
                  id="name"
                  defaultValue={props.headset.name}
                  placeholder="Name"
                  ref={formReferences.name}
                />
              </td>
              <td>
                <Form.Label for="name">
                  Device name
                </Form.Label>
              </td>
            </tr>

            <tr>
              <td>
                <Form.Label for="color">
                  Color
                </Form.Label>
              </td>
              <td>
                <input
                  defaultValue={props.headset.color}
                  placeholder="Color"
                  type="color"
                  ref={formReferences.color}
                  id="color"
                />
              </td>
              <td>
                <Form.Label for="color">
                  Color for device icon on map
                </Form.Label>
              </td>
            </tr>

            <tr>
              <td>
                <Form.Label for="location_id">
                  Device location
                </Form.Label>
              </td>
              <td>
                {
                  Object.keys(locations).length > 0 ?
                  (
                    <select
                      id="location_id"
                      title="Location"
                      defaultValue={props.headset.location_id}
                      ref={formReferences.location_id}>
                      {
                        Object.entries(locations).map(([location_id, loc]) => {
                          return <option value={location_id}>{loc.name}</option>
                        })
                      }
                    </select>
                  ) : (
                    <p>None available</p>
                  )
                }
              </td>
              <td>
                <Form.Label for="location_id">
                  Current location of the device - determines on which map the device icon appears
                </Form.Label>
              </td>
            </tr>

            <tr>
              <td>
                <Form.Label for="type">
                  Device type
                </Form.Label>
              </td>
              <td>
                <select
                  id="type"
                  title="Device Type"
                  defaultValue={props.headset.type}
                  ref={formReferences.type}>
                  {
                    deviceTypeOptions.map((type) => {
                      return <option value={type}>{type}</option>
                    })
                  }
                </select>
              </td>
              <td>
                <Form.Label for="type">
                  Device type - changes icon style and other behaviors
                </Form.Label>
              </td>
            </tr>

            <tr>
              <td>
                <Form.Label>
                  Position offset
                </Form.Label>
              </td>
              <td>
                <input
                  defaultValue={props.headset.offset.x}
                  label="X"
                  placeholder="X"
                  type="number"
                  ref={formReferences['offset.x']}
                />
                <input
                  defaultValue={props.headset.offset.y}
                  label="Y"
                  placeholder="Y"
                  type="number"
                  ref={formReferences['offset.y']}
                />
                <input
                  defaultValue={props.headset.offset.z}
                  label="Z"
                  placeholder="Z"
                  type="number"
                  ref={formReferences['offset.z']}
                />
              </td>
              <td>
                <Form.Label>
                  Position offset from location origin point (x, y, z)
                </Form.Label>
              </td>
            </tr>

            <tr>
              <td>
                <Form.Label>
                  Rotation
                </Form.Label>
              </td>
              <td>
                <input
                  defaultValue={props.headset.rotation.x}
                  label="X"
                  placeholder="X"
                  type="number"
                  ref={formReferences['rotation.x']}
                />
                <input
                  defaultValue={props.headset.rotation.y}
                  label="Y"
                  placeholder="Y"
                  type="number"
                  ref={formReferences['rotation.y']}
                />
                <input
                  defaultValue={props.headset.rotation.z}
                  label="Z"
                  placeholder="Z"
                  type="number"
                  ref={formReferences['rotation.z']}
                />
              </td>
              <td>
                <Form.Label>
                  Rotation from location origin (degrees for x, y, z axes)
                </Form.Label>
              </td>
            </tr>
          </tbody>
        </Table>

        <Form.Group as={Row} className="mb-3">
          <Col sm={{ span: 10, offset: 2 }}>
            <Button onClick={() => save()}>Save</Button>
          </Col>
        </Form.Group>
      </Form>
    </div>
  );
}

export default HeadsetProperties;

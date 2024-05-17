import {Container, Form, Table, Row, Col, Button} from 'react-bootstrap';
import React, {useContext, useState, useEffect} from 'react';

function CameraConfiguration(props) {
  const host = process.env.PUBLIC_URL;
  const config_url = `${host}/headsets/${props.headset.id}/camera`;

  const [configuration, setConfiguration] = useState({__empty: true});

  // Only one row can be open for editing at a time. A reference is used to
  // query the value of the input field when the user clicks Save. The
  // performance is much better than using an onChange handler for every
  // key press.
  const formReferences = {
    type: React.createRef(),
    width: React.createRef(),
    height: React.createRef(),
    fx: React.createRef(),
    fy: React.createRef(),
    cx: React.createRef(),
    cy: React.createRef(),
  };

  useEffect(() => {
    fetch(config_url)
      .then(response => response.json())
      .then(data => setConfiguration(data));
  }, []);

  function saveConfiguration() {
    const requestData = {
      method: 'PUT',
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
      .then(data => setConfiguration(data));
  }

  return (
    <div>
      <h3>Camera Configuration</h3>
      <Form>
        <Table striped bordered hover>
          <tbody>
            <tr>
              <td>
                <Form.Label column sm={6} for="type">
                  Type
                </Form.Label>
              </td>
              <td>
                {
                  !(configuration.__empty) && <select
                    id="type"
                    title="Type"
                    defaultValue={configuration.type || "color"}
                    ref={formReferences.type}>
                    <option value="color">Color</option>
                    <option value="thermal">Thermal</option>
                  </select>
                }
              </td>
              <td>
                <p>Camera type</p>
              </td>
            </tr>

            <tr>
              <td>
                <Form.Label column sm={6} for="width">
                  Width
                </Form.Label>
              </td>
              <td>
                <input
                  defaultValue={configuration.width}
                  placeholder="Width"
                  name={"width"}
                  type="number"
                  ref={formReferences.width} />
              </td>
              <td>
                <p>Calibration image width</p>
              </td>
            </tr>

            <tr>
              <td>
                <Form.Label column sm={6} for="height">
                  Height
                </Form.Label>
              </td>
              <td>
                <input
                  defaultValue={configuration.height}
                  placeholder="Height"
                  name={"height"}
                  type="number"
                  ref={formReferences.height} />
              </td>
              <td>
                <p>Calibration image height</p>
              </td>
            </tr>

            <tr>
              <td>
                <Form.Label column sm={6} for="fx">
                  FX
                </Form.Label>
              </td>
              <td>
                <input
                  defaultValue={configuration.fx}
                  placeholder="FX"
                  name={"fx"}
                  type="number"
                  ref={formReferences.fx} />
              </td>
              <td>
                <p>Calibration FX</p>
              </td>
            </tr>

            <tr>
              <td>
                <Form.Label column sm={6} for="fy">
                  FY
                </Form.Label>
              </td>
              <td>
                <input
                  defaultValue={configuration.fy}
                  placeholder="FY"
                  name={"fy"}
                  type="number"
                  ref={formReferences.fy} />
              </td>
              <td>
                <p>Calibration FY</p>
              </td>
            </tr>

            <tr>
              <td>
                <Form.Label column sm={6} for="cx">
                  CX
                </Form.Label>
              </td>
              <td>
                <input
                  defaultValue={configuration.cx}
                  placeholder="CX"
                  name={"cx"}
                  type="number"
                  ref={formReferences.cx} />
              </td>
              <td>
                <p>Calibration CX</p>
              </td>
            </tr>

            <tr>
              <td>
                <Form.Label column sm={6} for="cy">
                  CY
                </Form.Label>
              </td>
              <td>
                <input
                  defaultValue={configuration.cy}
                  placeholder="CY"
                  name={"cy"}
                  type="number"
                  ref={formReferences.cy} />
              </td>
              <td>
                <p>Calibration CY</p>
              </td>
            </tr>
          </tbody>
        </Table>

        <Form.Group as={Row} className="mb-3">
          <Col sm={{ span: 10, offset: 2 }}>
            <Button onClick={() => saveConfiguration()}>Save</Button>
          </Col>
        </Form.Group>
      </Form>
    </div>
  );
}

export default CameraConfiguration;

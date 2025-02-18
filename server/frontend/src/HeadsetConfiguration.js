import {Container, Form, Table, Row, Col, Button} from 'react-bootstrap';
import React, {useContext, useState, useEffect} from 'react';

function HeadsetConfiguration(props) {
  const host = process.env.PUBLIC_URL;
  const config_url = props.headset ?
    `${host}/headsets/${props.headset.id}/configuration` :
    `${host}/locations/${props.location.id}/device_configuration`;

  const [configuration, setConfiguration] = useState({});

  // Only one row can be open for editing at a time. A reference is used to
  // query the value of the input field when the user clicks Save. The
  // performance is much better than using an onChange handler for every
  // key press.
  const formReferences = {
    enable_mesh_capture: React.createRef(),
    enable_photo_capture: React.createRef(),
    enable_extended_capture: React.createRef(),
    photo_capture_mode: React.createRef(),
    photo_detection_threshold: React.createRef(),
    photo_target_interval: React.createRef(),
    enable_gesture_recognition: React.createRef(),
    enable_marker_placement: React.createRef(),
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
      <h3>Device Configuration</h3>
      <Form>
        <Table striped bordered hover>
          <tbody>
            <tr>
              <td>
                <Form.Label for="enable_mesh_capture">
                  Enable mesh capture
                </Form.Label>
              </td>
              <td>
                <Form.Check
                  id="enable_mesh_capture"
                  type="checkbox"
                  defaultChecked={configuration.enable_mesh_capture}
                  ref={formReferences.enable_mesh_capture}
                />
              </td>
              <td>
                <Form.Label for="enable_mesh_capture">
                  Enable automatic mesh capturing for map construction
                </Form.Label>
              </td>
            </tr>

            <tr>
              <td>
                <Form.Label for="enable_photo_capture">
                  Enable photo capture
                </Form.Label>
              </td>
              <td>
                <Form.Check
                  id="enable_photo_capture"
                  type="checkbox"
                  defaultChecked={configuration.enable_photo_capture}
                  ref={formReferences.enable_photo_capture}
                />
              </td>
              <td>
                <Form.Label for="enable_photo_capture">
                  Enable automatic (high resolution) photo capture, which may be resource intensive
                </Form.Label>
              </td>
            </tr>

            <tr>
              <td>
                <Form.Label for="enable_extended_capture">
                  Enable extended capture
                </Form.Label>
              </td>
              <td>
                <Form.Check
                  id="enable_extended_capture"
                  type="checkbox"
                  defaultChecked={configuration.enable_extended_capture}
                  ref={formReferences.enable_extended_capture}
                />
              </td>
              <td>
                <Form.Label for="enable_extended_capture">
                  Enable automatic capture of photos, depth, geometry, and intensity images
                </Form.Label>
              </td>
            </tr>

            <tr>
              <td>
                <Form.Label for="photo_capture_mode">
                  Photo capture mode
                </Form.Label>
              </td>
              <td>
                {
                  configuration.photo_capture_mode && <select
                    id="photo_capture_mode"
                    title="Photo capture mode"
                    defaultValue={configuration.photo_capture_mode}
                    ref={formReferences.photo_capture_mode}>
                    <option value="off">Off</option>
                    <option value="objects">Objects</option>
                    <option value="people">People</option>
                    <option value="anonymize">Anonymize</option>
                    <option value="continuous">Continuous</option>
                  </select>
                }
              </td>
              <td>
                <p>Conditions for automatic upload of camera images</p>
              </td>
            </tr>

            <tr>
              <td>
                <Form.Label for="photo_detection_threshold">
                  Photo detection threshold
                </Form.Label>
              </td>
              <td>
                <input
                  defaultValue={configuration.photo_detection_threshold}
                  placeholder="Threshold (0-1)"
                  name={"photo_detection_threshold"}
                  type="number"
                  ref={formReferences.photo_detection_threshold} />
              </td>
              <td>
                <p>Threshold applied in object or person detection</p>
              </td>
            </tr>

            <tr>
              <td>
                <Form.Label for="photo_target_interval">
                  Photo target interval
                </Form.Label>
              </td>
              <td>
                <input
                  defaultValue={configuration.photo_target_interval}
                  placeholder="Interval (seconds)"
                  name={"photo_target_interval"}
                  type="number"
                  ref={formReferences.photo_target_interval} />
              </td>
              <td>
                <p>Target upload interval (seconds) for automatic camera capture</p>
              </td>
            </tr>

            <tr>
              <td>
                <Form.Label for="enable_gesture_recognition">
                  Enable gesture recognition
                </Form.Label>
              </td>
              <td>
                <Form.Check
                  id="enable_gesture_recognition"
                  type="checkbox"
                  defaultChecked={configuration.enable_gesture_recognition}
                  ref={formReferences.enable_gesture_recognition}
                />
              </td>
              <td>
                <Form.Label for="enable_gesture_recognition">
                  Enable experimental gesture recognition actions
                </Form.Label>
              </td>
            </tr>

            <tr>
              <td>
                <Form.Label for="enable_marker_placement">
                  Enable marker placement
                </Form.Label>
              </td>
              <td>
                <Form.Check
                  id="enable_marker_placement"
                  type="checkbox"
                  defaultChecked={configuration.enable_marker_placement}
                  ref={formReferences.enable_marker_placement}
                />
              </td>
              <td>
                <Form.Label for="enable_marker_placement">
                  Whether marker placement panel should be visible in headset
                </Form.Label>
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

export default HeadsetConfiguration;

import { Button, Form, FloatingLabel } from 'react-bootstrap';
import './Popup.css';

function Popup(props){

    if (!props.popUpClass){
      return null;
    }

    return (
        <div className="popUpClassShow">
          <div className="inner-modal">
            <h2>Add a Feature</h2>
            <div id="form-div">
              <Form>
                <Form.Group className="mb-3" controlId="feature-name">
                  <FloatingLabel controlId="floating-name" label="Feature Name">
                    <Form.Control type="text" placeholder="Feature Name" />
                  </FloatingLabel>
                </Form.Group>


                <Form.Group className="mb-3" controlId="placement-type">
                  <Form.Label>Placement Type</Form.Label>
                  <Form.Select aria-label="Placement Type">
                    <option>--Select--</option>
                    <option value="floating">Floating</option>
                    <option value="surface">Surface</option>
                    <option value="point">Point</option>
                  </Form.Select>
                </Form.Group>

                <Button variant="primary" type="submit">
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
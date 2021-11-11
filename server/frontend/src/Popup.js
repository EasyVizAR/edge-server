import { Button, Form } from 'react-bootstrap';
import './Popup.css';
import {useState, useEffect } from 'react';

function Popup(props){
    /*const[popUpClass, changeClass] = useState(props.PopupClass ? 'popUpClassShow' : 'popUpClassHide');

    useEffect(() => {
      console.log(popUpClass);
    });*/

    if (!props.popUpClass){
      return null;
    }

    return (
        <div className="popUpClassShow">
          <div className="inner-modal">
            <h2>Add a Feature</h2>
            <div id="form-div">
              <Form>
                <Form.Group className="mb-3" controlId="featureName">
                  <Form.Label>Feature Name</Form.Label>
                  <Form.Control type="text" placeholder="Feature Name" />
                </Form.Group>

                <Form.Group className="mb-3" controlId="formBasicPassword">
                  <Form.Label>Password</Form.Label>
                  <Form.Control type="password" placeholder="Password" />
                </Form.Group>
                <Button variant="primary" type="submit">
                  Submit
                </Button>
              </Form>
            </div>
          </div>
        </div>
    );
}

export default Popup;
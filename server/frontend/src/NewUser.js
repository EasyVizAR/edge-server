import './NewLocation.css';
import App from './App.js';
import { Form, Button, FloatingLabel, Row, Col } from 'react-bootstrap';
import React from "react";
import { useContext, useState } from 'react';
import { LocationsContext } from './Contexts.js';


function NewUser(props) {
    const host = process.env.PUBLIC_URL;

    const formReferences = {
      name: React.createRef(),
      password: React.createRef()
    }

    function handleSubmit(e) {
      const name = formReferences.name.current.value;
      const password = formReferences.password.current.value;

      const requestData = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name,
          password,
          display_name: name,
          type: 'user'
        })
      };

      fetch(`${host}/users`, requestData)
        .then(response => response.json())
        .then(data => {
          props.setUsers(previous => {
            const newObject = Object.assign({}, previous);
            newObject[data.id] = data;
            return newObject;
          });
        });
    }

    return (
      <div className="new-user">
        <h3 style={{textAlign: "left"}}>New User</h3>
        <Form className='table-new-item-form'>
          <Row className="align-items-center">
            <Col xs="auto">
              <Form.Label htmlFor="new-user-name" visuallyHidden>
                Name
              </Form.Label>
              <Form.Control
                className="mb-2"
                id="new-user-name"
                placeholder="Name"
                ref={formReferences.name}
              />
            </Col>
            <Col xs="auto">
              <Form.Label htmlFor="new-user-password" visuallyHidden>
                Password
              </Form.Label>
              <Form.Control
                className="mb-2"
                id="new-user-password"
                placeholder="Password"
                type="password"
                ref={formReferences.password}
              />
            </Col>
            <Col xs="auto" className="my-1">
              <Button onClick={handleSubmit}>Create</Button>
            </Col>
          </Row>
        </Form>
      </div>
    );
}

export default NewUser;

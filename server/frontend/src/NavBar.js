import {Navbar, Container, Dropdown, DropdownButton, Form, Table, Nav, Button} from 'react-bootstrap';
import React, {useState, useEffect} from 'react';
import UserInfo from './UserInfo.js';
import './NavBar.css';
import {Link} from "react-router-dom";

function NavBar(props){
  const port = props.port;

  return (
    <Navbar bg="dark" variant="dark">
        <div className="nav">
          <Container className="header">
              <Navbar.Brand>EasyVizAR Edge</Navbar.Brand>
              <Navbar.Toggle aria-controls="basic-navbar-nav"/>
          </Container>
          <div class="vl"></div>
          <Link className="links" to="/">Home</Link>
          <Link className="links" to="/workitems">Image Processing</Link>
        </div>
        <UserInfo port={port}/>
    </Navbar>
  );
}

export default NavBar;

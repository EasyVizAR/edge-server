import {Navbar, Container, Dropdown, DropdownButton, Form, Table, Nav, Button} from 'react-bootstrap';
import React, {useState, useEffect} from 'react';
import './NavBar.css';

function NavBar(props){
  return (
    <Navbar bg="dark" variant="dark">
        <div className="nav">
          <Container className="header">
              <Navbar.Brand>Easy Viz AR Admin</Navbar.Brand>
              <Navbar.Toggle aria-controls="basic-navbar-nav"/>
          </Container>
          <div class="vl"></div>
          <a className="links" href="/">Home</a>
          <a className="links" href="/workitems">Work Items</a>
        </div>
    </Navbar>
  );
}

export default NavBar;
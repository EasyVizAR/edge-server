import {Navbar, Container, Dropdown, DropdownButton, Form, Table, Nav, Button} from 'react-bootstrap';
import React, {useState, useEffect} from 'react';
import './NavBar.css';
import {Link} from "react-router-dom";

function NavBar(props){
  return (
    <Navbar bg="dark" variant="dark">
        <div className="nav">
          <Container className="header">
              <Navbar.Brand>Easy Viz AR Admin</Navbar.Brand>
              <Navbar.Toggle aria-controls="basic-navbar-nav"/>
          </Container>
          <div class="vl"></div>
            <Link className="links" to="/">Home</Link>
            <Link className="links" to="/workitems">WorkItems</Link>
        </div>
    </Navbar>
  );
}

export default NavBar;
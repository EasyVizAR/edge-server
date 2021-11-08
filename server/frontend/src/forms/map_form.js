import '../App.css';
import { Navbar, Container, Dropdown, DropdownButton, Form, Table, Nav } from 'react-bootstrap';

function map_form(){
    return (
        <div className="map-form">
            <Navbar bg="dark" variant="dark">
                <Container>
                    <Navbar.Brand>Easy Viz AR Admin</Navbar.Brand>
                    <Navbar.Toggle aria-controls="basic-navbar-nav" />
                    <Nav className="me-auto">
                        <Nav.Link href="/map_form">Create Map</Nav.Link>
                    </Nav>
                </Container>

                <a class="navbar-brand" href="/map_form">Create Map</a>
            </Navbar>

            <div className="app-body">
                <form method="POST" action="/maps/create">
                    <input type="text" placeholder="Map Name" id="map_name" name="map_name"/>
                    <input type="submit"/>
                </form>
            </div>
        </div>
    );
}

export default map_form;
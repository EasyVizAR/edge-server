import logo from './logo.svg';
import './App.css';
import { Navbar, Container, Dropdown, DropdownButton, Form, Table } from 'react-bootstrap';
import { useState } from 'react';

function App() {

  const [selectedImage, setSelectedImage] = useState("https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885_960_720.jpg");

  const handleMapSelection = (e, o) => {
    if ("map-1" == e) {
      setSelectedImage("https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885_960_720.jpg");
    } else if ("map-2" == e) {
      setSelectedImage("https://media.istockphoto.com/photos/dramatic-sunset-over-a-quiet-lake-picture-id1192051826?k=20&m=1192051826&s=612x612&w=0&h=9HyN74dQTBcTZXB7g-BZp6mXV3upTgSvIav0x7hLm-I=");
    } else {
      setSelectedImage("https://media.istockphoto.com/photos/sycamore-tree-in-summer-field-at-sunset-england-uk-picture-id476116580?k=20&m=476116580&s=612x612&w=0&h=tZL4WDfgtV-0ko0nxidANitYB2bv2tCPDLhgYWYEnC4=");
    }
    fetch("http://localhost:5000/headsets")
      .then(response => response.json())
      .then(data => {
        console.log(data);
      })
  }

  return (
    <div className="App">
      <Navbar bg="dark" variant="dark">
        <Container>
          <Navbar.Brand>Easy Viz AR Admin</Navbar.Brand>
        </Container>
      </Navbar>
      <div className="app-body">
        <div className="dropdown-container">
          <DropdownButton id="map-dropdown" title="Select Map" onSelect={handleMapSelection} defaultValue="map-1">
            <Dropdown.Item eventKey="map-1">Map-1</Dropdown.Item>
            <Dropdown.Item eventKey="map-2">Map-2</Dropdown.Item>
            <Dropdown.Item eventKey="map-3">Map-3</Dropdown.Item>
          </DropdownButton>
        </div>
        <div className="map-image-container">
          <img id="map-image" src={selectedImage} />
        </div>
        <div>
          <Table striped bordered hover>
            <thead>
              <tr>
                <th>Headset ID</th>
                <th>Name</th>
                <th>Position - X</th>
                <th>Position - Y</th>
                <th>Position - Z</th>
                <th>Map ID</th>
                <th>Last Update</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>1</td>
                <td>Headset 1</td>
                <td>22</td>
                <td>88</td>
                <td>4</td>
                <td>b5c6fc5a-e5f7-4c7e-9e8e-d1d5276a54b6</td>
                <td>2021-09-21 14:06:39</td>
              </tr>
              <tr>
                <td>2</td>
                <td>Headset 2</td>
                <td>22</td>
                <td>88</td>
                <td>4</td>
                <td>b5c6fc5a-e5f7-4c7e-9e8e-d1d5276a54b6</td>
                <td>2021-09-21 14:06:39</td>
              </tr>
              <tr>
                <td>3</td>
                <td>Headset 2</td>
                <td>22</td>
                <td>88</td>
                <td>4</td>
                <td>b5c6fc5a-e5f7-4c7e-9e8e-d1d5276a54b6</td>
                <td>2021-09-21 14:06:39</td>
              </tr>
            </tbody>
          </Table>
        </div>
      </div>
    </div>
  );
}

export default App;

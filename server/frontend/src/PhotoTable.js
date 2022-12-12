import './Tables.css';
import {Badge, Container, Table, Button} from 'react-bootstrap';
import React, {useState, useEffect} from 'react';
import {Link} from "react-router-dom";
import moment from 'moment';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid, regular, brands} from '@fortawesome/fontawesome-svg-core/import.macro';

function PhotoTable(props) {
  const host = window.location.hostname;
  const port = props.port;

  function handleDeleteClicked(id) {
    const del = window.confirm(`Delete photo ${id}?`);
    if (!del) {
      return;
    }

    const url = `http://${host}:${port}/photos/${id}`;
    const requestData = {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    fetch(url, requestData).then(response => {
      props.setPhotos(current => {
        const copy = {...current};
        delete copy[id];
        return copy;
      });
    });
  }

  function Photo(props) {
    var url = '';
    if (props.url) {
      if (props.url.startsWith('http')) {
        url = props.url;
      } else {
        url = `http://${host}:${port}${props.url}`;
      }
    } else {
      return <p style={{color: 'black'}}>No image</p>;
    }

    return (
      <div className="image-parent">
        <Link to={"/photos/" + props.id}>
          <img className="work-items-images" src={url} alt="Photo" />
        </Link>
      </div>
    );
  }

  function Detections(props) {
    const annotations = props.photo.annotations || [];
    return (
      <div class="detections">
        {
          annotations.map((item) => {
            return <Badge className="detection" bg="info">{item.label}</Badge>
          })
        }
      </div>
    );
  }

  return (
    <div style={{marginTop: "20px"}}>
      <div>
        <h3 style={{textAlign: "left"}}>Photos</h3>
      </div>
      <Table striped bordered hover>
        <thead>
          <tr>
            <th>ID</th>
            <th>Date Created</th>
            <th>Content Type</th>
            <th>Status</th>
            <th>Detections</th>
            <th>Image</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {
            Object.keys(props.photos).length > 0 ? (
              Object.entries(props.photos).map(([id, photo]) => {
                return <tr>
                  <td>{id}</td>
                  <td>{moment.unix(photo.created).fromNow()}</td>
                  <td>{photo.contentType}</td>
                  <td>{photo.status}</td>
                  <td>
                    <Detections photo={photo} />
                  </td>
                  <td>
                    <div>
                      <Photo id={id} url={photo.imageUrl} />
                    </div>
                  </td>
                  <td>
                    <Button
                      variant="danger" size="sm"
                      onClick={() => handleDeleteClicked(id)}
                      title="Delete photo">
                      Delete
                    </Button>
                  </td>
                </tr>
              })
            ) : (
              <tr><td colspan="100%">No photos to display.</td></tr>
            )
          }
        </tbody>
      </Table>
    </div>
  );
}

export default PhotoTable;

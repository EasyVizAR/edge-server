import './Tables.css';
import {Badge, Container, Table, Button} from 'react-bootstrap';
import React, {useState, useEffect} from 'react';
import {Link} from "react-router-dom";
import moment from 'moment';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid, regular, brands} from '@fortawesome/fontawesome-svg-core/import.macro';

function PhotoTable(props) {
  const host = process.env.PUBLIC_URL;

  const [sortBy, setSortBy] = useState({
    attr: "created",
    direction: -1,
  });

  function handleDeleteClicked(id) {
    const del = window.confirm(`Delete photo ${id}?`);
    if (!del) {
      return;
    }

    const url = `${host}/photos/${id}`;
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

  function SortByLink(props) {
    if (sortBy.attr === props.attr) {
      return (
        <Button className="column-sort" variant="link" onClick={() => setSortBy({attr: props.attr, direction: -sortBy.direction})}>
          {props.text} <FontAwesomeIcon icon={sortBy.direction > 0 ? solid('sort-up') : solid('sort-down')} />
        </Button>
      )
    } else {
      return <Button className="column-sort" variant="link" onClick={() => setSortBy({attr: props.attr, direction: 1})}>{props.text}</Button>
    }
  }

  function Photo(props) {
    var url = '';
    if (props.url) {
      if (props.url.startsWith('http')) {
        url = props.url;
      } else {
        url = `${host}/photos/${props.id}/thumbnail`;
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
            <th><SortByLink attr="id" text="ID" /></th>
            <th><SortByLink attr="created" text="Date Created" /></th>
            <th><SortByLink attr="contentType" text="Content Type" /></th>
            <th><SortByLink attr="status" text="Status" /></th>
            <th>Detections</th>
            <th>Image</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {
            Object.keys(props.photos).length > 0 ? (
              Object.entries(props.photos).sort((a, b) => a[1][sortBy.attr] > b[1][sortBy.attr] ? sortBy.direction : -sortBy.direction).map(([id, photo]) => {
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

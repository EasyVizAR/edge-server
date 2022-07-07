import React, { useState, useEffect } from 'react';
import {Table} from 'react-bootstrap';
import { useParams } from 'react-router';
import {Helmet} from 'react-helmet';
import './PhotoWrapper.css';

function PhotoWrapper(props) {
  const host = window.location.hostname;
  const port = props.port;

  const {photo_id} = useParams();

  const [photo, setPhoto] = useState(null);
  const [selectedBox, setSelectedBox] = useState(null);

  useEffect(() => {
    function getPhotoInfo() {
      const url = `http://${host}:${port}/photos/${photo_id}`;
      fetch(url).then(response => {
        if (response.ok) {
          return response.json();
        }
      }).then(data => {
        setPhoto(data);
      }).catch(err => {
        // Do something for an error here
        console.log("Error Reading data " + err);
      });
    }

    getPhotoInfo();
  }, [host, port, photo_id]);

  function Photo() {
    return (
      <div className="photo-wrapper">
        <img src={photo?.imageUrl} alt="something" />
        {
          photo?.annotations && photo.annotations.length > 0 &&
            photo.annotations.map((annotation, index) => {
              if (selectedBox === null || selectedBox === index) {
                const style = {
                  left: 100 * annotation.boundary.left + "%",
                  top: 100 * annotation.boundary.top + "%",
                  width: 100 * annotation.boundary.width + "%",
                  height: 100 * annotation.boundary.height + "%"
                };
                return <div className="object-bounding-box" style={style}></div>
              } else {
                return null;
              }
            })
        }
      </div>
    );
  }

  function PhotoInfo() {
    if (!photo) {
      return <p>The photo information is not ready or could not be found.</p>;
    }

    if (!photo.annotations || !(photo.annotations.length > 0)) {
      return <p>The photo has no annotations to show.</p>;
    }

    return (
      <div>
        <Table striped bordered hover>
          <thead>
            <tr>
              <th>Category</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {
              photo.annotations.map((annotation, index) => {
                return <tr onMouseEnter={() => setSelectedBox(index)} onMouseLeave={() => setSelectedBox(null)}>
                  <td>{ annotation.label }</td>
                  <td>{ annotation.confidence }</td>
                </tr>
              })
            }
          </tbody>
        </Table>
        <p>Mouse over a row to highlight that object in the image.</p>
      </div>
    );
  }

  return (
    <div>
      <Helmet>
        <title>Photo</title>
      </Helmet>

      <div className="container-lg">
        <div className="row align-items-center">
          <div className="col-lg-8">
            <Photo />
          </div>
          <div className="col-lg-4">
            <PhotoInfo />
          </div>
        </div>

        <div className="row">
          <div className="col">
            <p>{ photo?.imageUrl }</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PhotoWrapper;

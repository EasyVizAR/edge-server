import React, { useState, useEffect } from 'react';
import {ListGroup, Table} from 'react-bootstrap';
import { useParams } from 'react-router';
import {Helmet} from 'react-helmet';
import './PhotoWrapper.css';

function PhotoWrapper(props) {
  const host = process.env.PUBLIC_URL;

  const {photo_id} = useParams();

  const [photo, setPhoto] = useState(null);
  const [selectedBox, setSelectedBox] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);
  const [imageSource, setImageSource] = useState(null);

  useEffect(() => {
    function getPhotoInfo() {
      const url = `${host}/photos/${photo_id}`;
      fetch(url).then(response => {
        if (response.ok) {
          return response.json();
        }
      }).then(data => {
        setPhoto(data);
        setImageSource(data.imageUrl);
      }).catch(err => {
        // Do something for an error here
        console.log("Error Reading data " + err);
      });
    }

    getPhotoInfo();
  }, [host, photo_id]);

  function Photo() {
    return (
      <div className="photo-wrapper">
        <img src={imageSource} alt="something" />
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

  function ImageSelector() {
    const base_url = `${host}/photos/${photo_id}/`;
    var photo_found = false;
    return (
      <>
        <h2>Select Image</h2>
        <ListGroup defaultActiveKey="photo">
          {
            photo?.files && photo.files.length > 0 &&
              photo.files.map((file, index) => {
                if (file.purpose === "photo") {
                  photo_found = true;
                }
                return <ListGroup.Item action key={ file.purpose } onClick={() => setImageSource(base_url + file.name)}>{ file.purpose }</ListGroup.Item>
              })
          }
          {
            photo_found || <ListGroup.Item action key="photo" onClick={() => setImageSource(photo.imageUrl)}>Photo</ListGroup.Item>
          }
        </ListGroup>
      </>
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

  function DetectorInfo() {
    if (!photo) {
      return <p>The photo information is not ready or could not be found.</p>;
    }

    if (!photo.detector) {
      return <p>The photo has no detector information to show.</p>;
    }

    return (
      <div>
        <Table striped bordered hover>
          <tbody>
            <tr>
              <td>Model Repo</td>
              <td>{ photo.detector.model_repo }</td>
            </tr>
            <tr>
              <td>Model Name</td>
              <td>{ photo.detector.model_name }</td>
            </tr>
            <tr>
              <td>Engine Name</td>
              <td>{ photo.detector.engine_name }</td>
            </tr>
            <tr>
              <td>Engine Version</td>
              <td>{ photo.detector.engine_version }</td>
            </tr>
            <tr>
              <td>Cuda Enabled</td>
              <td>{ photo.detector.cuda_enabled }</td>
            </tr>
            <tr>
              <td>Preprocessing Duration (s)</td>
              <td>{ photo.detector.preprocess_duration }</td>
            </tr>
            <tr>
              <td>Inference Duration (s)</td>
              <td>{ photo.detector.inference_duration }</td>
            </tr>
            <tr>
              <td>Postprocessing Duration (s)</td>
              <td>{ photo.detector.postprocess_duration }</td>
            </tr>
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
          <div className="col-lg-9">
            <Photo />
          </div>
          <div className="col-lg-3">
            <ImageSelector />
          </div>
        </div>

        <div className="row align-items-center">
          <div className="col-lg-6">
            <PhotoInfo />
          </div>
          <div className="col-lg-6">
            <DetectorInfo />
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

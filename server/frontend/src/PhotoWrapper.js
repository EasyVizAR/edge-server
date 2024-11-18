import React, { useContext, useState, useEffect } from 'react';
import {Link} from "react-router-dom";
import {ListGroup, Table} from 'react-bootstrap';
import { useParams } from 'react-router';
import {Helmet} from 'react-helmet';
import MapContainer from "./MapContainer";
import { LocationsContext } from './Contexts.js';
import { UsersContext } from './Contexts.js';
import TrashIcon from './TrashIcon.js';
import './PhotoWrapper.css';

function PhotoWrapper(props) {
  const host = process.env.PUBLIC_URL;

  const {photo_id} = useParams();

  const [captureDevice, setCaptureDevice] = useState(null);
  const [photo, setPhoto] = useState(null);
  const [selectedBox, setSelectedBox] = useState(null);
  const [selectedImage, setSelectedImage] = useState("photo");
  const [imageSource, setImageSource] = useState(null);

  const { locations, setLocations } = useContext(LocationsContext);
  const { users, setUsers } = useContext(UsersContext);

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
        getCaptureDevice(data);
      }).catch(err => {
        // Do something for an error here
        console.log("Error Reading data " + err);
      });
    }

    getPhotoInfo();
  }, [host, photo_id]);

  function getCaptureDevice(photo) {
    if (photo.created_by) {
      const url = `${host}/headsets/${photo.created_by}`;
      fetch(url)
        .then(response => response.json())
        .then(data => setCaptureDevice(data));
    }
  }

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

    const changeImage = (purpose, url) => {
      setImageSource(url);
      setSelectedImage(purpose);
    }

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
                return <ListGroup.Item action key={ file.purpose }
                  onClick={() => changeImage(file.purpose, base_url + file.name)}
                  active={ selectedImage === file.purpose }>
                    { file.purpose }
                </ListGroup.Item>
              })
          }
          {
            photo_found || <ListGroup.Item action key="photo"
                            onClick={() => changeImage("photo", photo.imageUrl)}
                            active={ selectedImage === "photo" }>Photo</ListGroup.Item>
          }
        </ListGroup>
      </>
    );
  }

  function patchPhotoAnnotation(id, patch) {
    const url = `${host}/photos/annotations/${id}`;
    const requestData = {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(patch)
    };

    fetch(url, requestData)
      .then(response => response.json())
      .then(data => {
        setPhoto(current => {
          const copy = {...current};
          for (var i = 0; i < copy.annotations.length; i++) {
            if (copy.annotations[i].id == id) {
              copy.annotations[i] = data;
              break;
            }
          }
          return copy;
        });
      });
  }

  function Identity(props) {
    const id = props.annotation.id;
    const label = props.annotation.label;
    const identified_user_id = props.annotation.identified_user_id;

    if (label === "person") {
      return <select
        value={identified_user_id}
        onChange={e => patchPhotoAnnotation(id, {
          identified_user_id: e.target.value,
          sublabel: users[e.target.value]?.display_name || ""
        })} >
        <option value={null}>None</option>
        {
          Object.entries(users).map(([user_id, user]) => {
            return <option value={user_id}>{user.display_name}</option>
          })
        }
      </select>
    }

    return null;
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
              <th>Sublabel</th>
              <th>Confidence</th>
              <th>Identity</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {
              photo.annotations.map((annotation, index) => {
                return <tr onMouseEnter={() => setSelectedBox(index)}>
                  <td>{ annotation.label }</td>
                  <td>{ annotation.sublabel }</td>
                  <td>{ annotation.confidence }</td>
                  <td>
                    <Identity annotation={annotation} />
                  </td>
                  <td><TrashIcon name={annotation.label} uri={`/photos/annotations/${annotation.id}`} /></td>
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
      </div>
    );
  }

  function PhotoMap(props) {
    const photo = props.photo;

    return (
        photo?.camera_location_id ? (
          <MapContainer id="map-container"
                locationId={props.photo.camera_location_id}
                photos={[photo]} showPhotos={true}
                defaultIconColor="#aa0000" />
        ) : (
          <p>The photo location is unknown.</p>
        )
    )
  }

  return (
    <div>
      <Helmet>
        <title>Photo</title>
      </Helmet>

      <div className="container-lg">
        {
          photo &&
          <div className="row location-header">
            <div className="col-lg-4">
              <p className="text-muted" style={{ fontSize: '0.875em', marginBottom: '0px' }}>Location</p>
              <h4 style={{ marginTop: '0px' }}>{locations[photo.camera_location_id]?.name || 'Unknown'}</h4>
              {
                photo.camera_location_id &&
                <h5>
                  <Link to={`/locations/${photo.camera_location_id}`}>{photo.camera_location_id}</Link>
                </h5>
              }
            </div>
            <div className="col-lg-4">
              <p className="text-muted" style={{ fontSize: '0.875em', marginBottom: '0px' }}>Capture Device</p>
              <h4 style={{ marginTop: '0px' }}>{captureDevice?.name || 'Unknown'}</h4>
              {
                photo.created_by &&
                <h5>
                  <Link to={`/headsets/${photo.created_by}`}>{photo.created_by}</Link>
                </h5>
              }
            </div>
            <div className="col-lg-4">
              <p className="text-muted" style={{ fontSize: '0.875em', marginBottom: '0px' }}>Queue</p>
              <h4 style={{ marginTop: '0px' }}>{photo.queue_name}</h4>
            </div>
          </div>
        }

        <div className="row align-items-center">
          <div className="col-lg-9">
            <Photo />
          </div>
          <div className="col-lg-3">
            <ImageSelector />
          </div>
        </div>

        <div className="row align-items-center">
          <div className="col">
            <PhotoInfo />
          </div>
        </div>

        <div className="row align-items-center">
          <div className="col-lg-9">
            <PhotoMap photo={photo} />
          </div>
          <div className="col-lg-3">
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

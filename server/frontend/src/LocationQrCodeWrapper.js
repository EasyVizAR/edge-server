import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router';
import {Helmet} from 'react-helmet';
import './LocationQrCodeWrapper.css';

function LocationQrCodeWrapper(props){
  const {location_id} = useParams();
  const host = window.location.hostname;
  const port = props.port;
  const [qr, setQrCode] = useState(null);
  const[location, setLocation] = useState(null);

  useEffect(() => {
    getQrCode();
    getLocationInfo();
  }, []);

  function getLocationInfo(){
    const requestData = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    };

    fetch(`http://${host}:${port}/locations/` + location_id, requestData).then(response => {
      if(response.ok){
        return response.json();
      }
    }).then(data => {
      setLocation(data);
    }).catch(err => {
      // Do something for an error here
      console.log("Error Reading data " + err);
    });
  }

  function getQrCode(){
    const requestData = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'text/svg'
        }
    };

    fetch(`http://${host}:${port}/locations/` + location_id + `/qrcode.svg`, requestData).then(response => {
      if(response.ok){
        return response.json();
      }
    }).then(data => {
      setQrCode(data['image'])
    }).catch(err => {
      // Do something for an error here
      console.log("Error Reading data " + err);
    });
  }

  function LocationInfo(){
    if (location == null){
      return (<p>Cannot Load Location Data</p>);
    }

    return (
      <div>
        <h1>{location['name'] != null ? location['name'] : ''}</h1>
        <h3>{location['id'] != null ? location['id'] : ''}</h3>
      </div>
    );
  }

  return (
    <div className="LocationQrCodeWrapper">
      <Helmet>
        <title>Location QR Code</title>
      </Helmet>

      <div className="data">
        <div className="svg-image">
          {qr != null ? (
            <p dangerouslySetInnerHTML={{ __html: qr }} />
          ) : (
            <p>Could not load location QR code. Make sure there is a location selected on the home page.</p>
          )}
        </div>
        <div className="location-info">
          <LocationInfo/>
        </div>
      </div>
    </div>
  );
}

export default LocationQrCodeWrapper;
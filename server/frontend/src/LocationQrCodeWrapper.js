import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router';
import {Helmet} from 'react-helmet';
import './LocationQrCodeWrapper.css';

function LocationQrCodeWrapper(props){
  const {location_id} = useParams();
  const host = process.env.PUBLIC_URL;
  const [qr, setQrCode] = useState(null);
  const[location, setLocation] = useState(null);

  useEffect(() => {
    getLocationInfo();
  }, []);

  function getLocationInfo(){
    const requestData = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    };

    fetch(`${host}/locations/` + location_id, requestData).then(response => {
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

      <div className="container-lg">
        <div className="row align-items-center">
          <div className="col-lg-8">
            <img src={`${host}/locations/` + location_id + "/qrcode"}/>
          </div>
          <div className="col-lg-4">
            <LocationInfo/>
          </div>
        </div>

        <div className="row">
          <div className="col">
            <p>{"vizar://" + window.location.host + "/locations/" + location_id}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LocationQrCodeWrapper;

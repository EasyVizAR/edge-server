import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router';
import {Helmet} from 'react-helmet';
import './MapQrCodeWrapper.css';

function MapQrCodeWrapper(props){
  const {map_id} = useParams();
  const host = window.location.hostname;
  const port = props.port;
  const [qr, setQrCode] = useState(null);
  const[map, setMap] = useState(null);

  useEffect(() => {
    getQrCode();
    getMapInfo();
  }, []);

  function getMapInfo(){
    const requestData = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    };

    fetch(`http://${host}:${port}/maps/` + map_id, requestData).then(response => {
      if(response.ok){
        return response.json();
      }
    }).then(data => {
      setMap(data);
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

    fetch(`http://${host}:${port}/maps/` + map_id + `/qrcode.svg`, requestData).then(response => {
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

  function MapInfo(){
    if (map == null){
      return (<p>Cannot Load Map Data</p>);
    }

    return (
      <div>
        <h1>{map['name'] != null ? map['name'] : ''}</h1>
        <h3>{map['id'] != null ? map['id'] : ''}</h3>
      </div>
    );
  }

  return (
    <div className="MapQrCodeWrapper">
      <Helmet>
        <title>Map QR Code</title>
      </Helmet>

      <div className="data">
        <div className="svg-image">
          {qr != null ? (
            <p dangerouslySetInnerHTML={{ __html: qr }} />
          ) : (
            <p>Could not load map QR code. Make sure there is a map selected on the home page.</p>
          )}
        </div>
        <div className="map-info">
          <MapInfo/>
        </div>
      </div>
    </div>
  );
}

export default MapQrCodeWrapper;
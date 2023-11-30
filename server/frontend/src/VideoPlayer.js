import React, { useContext, useState, useEffect } from 'react';
import { Row, Col } from 'react-bootstrap';
import {Helmet} from 'react-helmet';
import { useParams } from 'react-router';
import Hls from 'hls.js';

import ClickToEdit from './ClickToEdit.js';


function VideoPlayer(props) {
  const host = process.env.PUBLIC_URL;
  const {stream_id} = useParams();
  const [stream, setStream] = useState(null);

  useEffect(() => {
    getStream();
  }, []);

  useEffect(() => {
    if (stream && Hls.isSupported()) {
      var video = document.getElementById('video');

      var hls = new Hls();
      hls.on(Hls.Events.MANIFEST_PARSED, function(event, data) {
        console.log(`manifest loaded, found ${data.levels.length} quality level`);
      });
      hls.on(Hls.Events.ERROR, function(event, data) {
        console.log(`video error type ${data.type}, ${data.details}, is fatal ${data.fatal}`);
      });

      const url = host + stream.hls_path;
      hls.loadSource(url);
      hls.attachMedia(video);
    }
  }, [stream]);

  function getStream() {
    const url = `${host}/streams/${stream_id}`;
    fetch(url)
      .then((response) => response.json())
      .then((data) => setStream(data));
  }

  function updateDescription(desc) {
    const url = `${host}/streams/${stream_id}`;
    const requestData = {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        description: desc
      })
    };

    fetch(url, requestData)
      .then((response) => response.json())
      .then((data) => setStream(data));
  }

  return (
    <div className="video-player">
      <Helmet>
        <title>Stream</title>
      </Helmet>

      <div className="container-lg">
        <Row>
          <video id="video" controls></video>
        </Row>

        {
          stream &&
            <Row>
              <Col sm="2"><p>Description</p></Col>
              <Col sm="10">
                <ClickToEdit
                  tag="p" initialValue={stream.description} placeholder='Description'
                  onSave={(desc) => updateDescription(desc)} />
              </Col>
            </Row>
        }

        {
          stream &&
            <Row>
              <Col sm="2"><p>Source</p></Col>
              <Col sm="10"><p>{stream.publisher_addr | 'Unavailable'}</p></Col>
            </Row>
        }
    	</div>
		</div>
  );
}

export default VideoPlayer;

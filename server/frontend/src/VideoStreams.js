import { Button, Table } from 'react-bootstrap';
import React, { useContext, useState, useEffect } from 'react';
import { Link } from "react-router-dom";
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid} from '@fortawesome/fontawesome-svg-core/import.macro';
import moment from 'moment';
import { LocationsContext } from './Contexts.js';


function VideoStreams(props) {
  const host = process.env.PUBLIC_URL;

  const [streams, setStreams] = useState({});

  const [sortBy, setSortBy] = useState({
    attr: "id",
    direction: -1,
  });

  useEffect(() => {
      getStreams();
  }, []);

  function deleteStream(id) {
      const del = window.confirm("Are you sure you want to delete stream '" + id + "'?");
      if (!del) {
          return;
      }

      const url = `${host}/streams/${id}`;
      const requestData = {
          method: 'DELETE',
          headers: {
              'Content-Type': 'application/json'
          }
      };

      fetch(url, requestData)
        .then(response => response.json())
        .then(data => {
          setStreams(current => {
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

  // code that creates the trash icons
  function TrashIcon(props) {
      const itemId = props.id;
      const itemName = props.name;

      return (
          <Button style={{width: "30px", height: "30px"}} className='btn-danger table-btns'
                  onClick={(e) => deleteStream(itemId)} title="Delete Stream">
              <FontAwesomeIcon icon={solid('trash-can')} size="lg"
                               style={{position: 'relative', right: '0px', top: '-1px'}}/>
          </Button>
      );
  }

  function getStreams() {
    fetch(`${host}/streams`)
      .then(response => response.json())
      .then(data => {
        var streams = {};
        for (var w of data) {
          streams[w.id] = w;
        }
        setStreams(streams);
      })
  }

  return (
    <div>
      <Table striped bordered hover>
        <thead>
          <tr>
            <th><SortByLink attr="id" text="ID" /></th>
            <th><SortByLink attr="description" text="Description" /></th>
            <th><SortByLink attr="publisher_addr" text="Source Address" /></th>
            <th><SortByLink attr="updated_time" text="Updated Time" /></th>
            <th><SortByLink attr="stream_url" text="Stream URL" /></th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {
            Object.keys(streams).length > 0 ? (
              Object.entries(streams).sort((a, b) => a[1][sortBy.attr] > b[1][sortBy.attr] ? sortBy.direction : -sortBy.direction).map(([id, stream]) => {
                return <tr>
                  <td><Link to={`/streams/${id}`}>{id}</Link></td>
                  <td>{stream.description}</td>
                  <td>{stream.publisher_addr || "N/A"}</td>
                  <td>{moment(stream.updated_time).fromNow()}</td>
                  <td><small>{stream.stream_url}</small></td>
                  <td>
                    <div>
                      <TrashIcon item='stream' id={id} name={stream.id}/>
                    </div>
                  </td>
                </tr>
              })
            ) : (
              <tr><td colspan="100%">No streams</td></tr>
            )
          }
        </tbody>
      </Table>
    </div>
  );
}

export default VideoStreams;

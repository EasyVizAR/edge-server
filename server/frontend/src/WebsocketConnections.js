import { Button, Table } from 'react-bootstrap';
import React, { useContext, useState, useEffect } from 'react';
import { Link } from "react-router-dom";
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid} from '@fortawesome/fontawesome-svg-core/import.macro';
import moment from 'moment';
import { LocationsContext } from './Contexts.js';


function WebsocketConnections(props) {
  const host = process.env.PUBLIC_URL;

  const { locations, setLocations } = useContext(LocationsContext);

  const [websockets, setWebsockets] = useState({});

  const [sortBy, setSortBy] = useState({
    attr: "id",
    direction: -1,
  });

  useEffect(() => {
      getWebsockets();
  }, []);

  function deleteWebsocket(id, name) {
      const del = window.confirm("Are you sure you want to close websocket connection '" + name + "'?");
      if (!del) {
          return;
      }

      const url = `${host}/websockets/${id}`;
      const requestData = {
          method: 'DELETE',
          headers: {
              'Content-Type': 'application/json'
          }
      };

      fetch(url, requestData)
        .then(response => response.json())
        .then(data => {
          setWebsockets(current => {
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
                  onClick={(e) => deleteWebsocket(itemId, itemName)} title="Close Websocket">
              <FontAwesomeIcon icon={solid('trash-can')} size="lg"
                               style={{position: 'relative', right: '0px', top: '-1px'}}/>
          </Button>
      );
  }

  function getWebsockets() {
    fetch(`${host}/websockets`)
      .then(response => response.json())
      .then(data => {
        var websockets = {};
        for (var w of data) {
          websockets[w.id] = w;
        }
        setWebsockets(websockets);
      })
  }

  return (
    <div>
      <Table striped bordered hover>
        <thead>
          <tr>
            <th rowSpan='2'><SortByLink attr="id" text="ID" /></th>
            <th rowSpan='2'><SortByLink attr="client" text="Client" /></th>
            <th rowSpan='2'><SortByLink attr="user_id" text="User" /></th>
            <th rowSpan='2'><SortByLink attr="start_time" text="Start Time" /></th>
            <th colSpan='5'>Received (from client)</th>
            <th colSpan='5'>Sent (to client)</th>
            <th rowSpan='2'>Subscriptions</th>
            <th rowSpan='2'></th>
          </tr>
          <tr>
            <th><SortByLink attr="messages_received" text="Messages" /></th>
            <th><SortByLink attr="messages_received_per_second" text="Msg / Sec" /></th>
            <th><SortByLink attr="bytes_received" text="Bytes" /></th>
            <th><SortByLink attr="bytes_received_per_second" text="Bytes / Sec" /></th>
            <th><SortByLink attr="last_received_time" text="Last" /></th>
            <th><SortByLink attr="messages_sent" text="Messages" /></th>
            <th><SortByLink attr="messages_sent_per_second" text="Msg / Sec" /></th>
            <th><SortByLink attr="bytes_sent" text="Bytes" /></th>
            <th><SortByLink attr="bytes_sent_per_second" text="Bytes / Sec" /></th>
            <th><SortByLink attr="last_sent_time" text="Last" /></th>
          </tr>
        </thead>
        <tbody>
          {
            Object.keys(websockets).length > 0 ? (
              Object.entries(websockets).sort((a, b) => a[1][sortBy.attr] > b[1][sortBy.attr] ? sortBy.direction : -sortBy.direction).map(([id, websocket]) => {
                return <tr>
                  <td>{id}</td>
                  <td>{websocket.client}</td>
                  <td>
                    { websocket.user_id ? <Link to={`/headsets/${websocket.user_id}`}>{ websocket.user_id }</Link> : "N/A" }
                  </td>
                  <td>{moment.unix(websocket.start_time).fromNow()}</td>
                  <td>{websocket.messages_received}</td>
                  <td>{websocket.messages_received_per_second.toFixed(2)}</td>
                  <td>{websocket.bytes_received}</td>
                  <td>{websocket.bytes_received_per_second.toFixed(2)}</td>
                  <td>{moment.unix(websocket.last_received_time).fromNow()}</td>
                  <td>{websocket.messages_sent}</td>
                  <td>{websocket.messages_sent_per_second.toFixed(2)}</td>
                  <td>{websocket.bytes_sent}</td>
                  <td>{websocket.bytes_sent_per_second.toFixed(2)}</td>
                  <td>{moment.unix(websocket.last_sent_time).fromNow()}</td>
                  <td>{websocket.subscriptions.length}</td>
                  <td>
                    <div>
                      <TrashIcon item='websocket' id={id} name={websocket.id}/>
                    </div>
                  </td>
                </tr>
              })
            ) : (
              <tr><td colspan="100%">No open websocket connections</td></tr>
            )
          }
        </tbody>
      </Table>
    </div>
  );
}

export default WebsocketConnections;

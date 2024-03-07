import { Button, Table } from 'react-bootstrap';
import React, { useContext, useState, useEffect } from 'react';
import { Link } from "react-router-dom";
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid} from '@fortawesome/fontawesome-svg-core/import.macro';
import moment from 'moment';
import { LocationsContext } from './Contexts.js';
import NewDevice from './NewDevice.js';
import { WebSocketContext } from "./WSContext.js";


const deviceTypeOptions = [
  "unknown",
  "headset",
  "phone",
  "editor",
  "robot"
];


function AllHeadsets(props) {
  const host = process.env.PUBLIC_URL;

  const { locations, setLocations } = useContext(LocationsContext);
  const [subscribe, unsubscribe] = useContext(WebSocketContext);

  const [headsets, setHeadsets] = useState({});

  // Only one row can be open for editing at a time. A reference is used to
  // query the value of the input field when the user clicks Save. The
  // performance is much better than using an onChange handler for every
  // key press.
  const formReferences = {
    name: React.createRef(),
    type: React.createRef(),
    location_id: React.createRef()
  }

  const [inEditModeHeadset, setInEditModeHeadset] = useState({
      status: false,
      rowKey: null
  });
  const [sortBy, setSortBy] = useState({
    attr: "updated",
    direction: -1,
  });

  useEffect(() => {
    getAllHeadsets();

    subscribe("headsets:created", "*", (event, uri, message) => {
      setHeadsets(previous => {
        let tmp = Object.assign({}, previous);
        tmp[message.current.id] = message.current;
        return tmp;
      });
    });

    subscribe("headsets:updated", "*", (event, uri, message) => {
      setHeadsets(previous => {
        let tmp = Object.assign({}, previous);
        tmp[message.current.id] = message.current;
        return tmp;
      });
    });

    subscribe("headsets:deleted", "*", (event, uri, message) => {
      setHeadsets(previous => {
        let tmp = Object.assign({}, previous);
        delete tmp[message.previous.id];
        return tmp;
      });
    });

    return () => {
      unsubscribe("headsets:created", "*");
      unsubscribe("headsets:updated", "*");
      unsubscribe("headsets:deleted", "*");
    }
  }, []);

  // check if a headset name already exists
  function checkHeadsetName(name, id) {
      for (var i in headsets) {
          if (headsets[i].name === name && i !== id) {
              return true;
          }
      }
      return false;
  }

  // deletes headset with the id and name
  function deleteHeadset(id, name) {
      const del = window.confirm("Are you sure you want to delete headset '" + name + "'?");
      if (!del) {
          return;
      }

      const url = `${host}/headsets/${id}`;
      const requestData = {
          method: 'DELETE',
          headers: {
              'Content-Type': 'application/json'
          }
      };

      fetch(url, requestData)
          .then(response => {
              delete headsets[id];
              getAllHeadsets();
              props.getLocationHeadsets();
          });
  }

  // turns on headset editing
  const onEditHeadset = (e, id) => {
      if (inEditModeHeadset.status === true && inEditModeHeadset.rowKey != null) {
          alert("Please save or cancel edit on other headset before editing another headset");
          return;
      }

      setInEditModeHeadset({
          status: true,
          rowKey: id
      });
  }

  // saves the headset data
  const onSaveHeadsets = (e, id) => {
      const headset = headsets[id];
      const url = `${host}/headsets/${id}`;

      const newName = formReferences.name.current.value;
      const newLocationId = formReferences.location_id.current.value;

      var dup = checkHeadsetName(newName, id);
      if (dup) {
        var conf = window.confirm('There is another headset with the same name. Are you sure you want to continue?');
        if (!conf) {
          return;
        }
      }

      const requestData = {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          'name': newName,
          'type': formReferences.type.current.value,
          'location_id': newLocationId
        })
      };

      fetch(url, requestData).then(response => {
        headset.name = newName;
        headset.location_id = newLocationId;

        onCancelHeadset(null, id);
        getAllHeadsets();
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
                  onClick={(e) => deleteHeadset(itemId, itemName)} title="Delete Headset">
              <FontAwesomeIcon icon={solid('trash-can')} size="lg"
                               style={{position: 'relative', right: '0px', top: '-1px'}}/>
          </Button>
      );
  }

  // turns off headset editing
  const onCancelHeadset = (element, id) => {
      setInEditModeHeadset({
          status: false,
          rowKey: null
      });
  }

  function getAllHeadsets(){
    fetch(`${host}/headsets`)
    .then(response => {
      return response.json()
    }).then(data => {
      var headsets = {};
      for (var h of data) {
        headsets[h.id] = h;
      }
      setHeadsets(headsets);
    });
  }

  return (
    <div>
      <Table striped bordered hover>
        <thead>
          <tr>
            <th rowSpan='2'><SortByLink attr="id" text="Headset ID" /></th>
            <th rowSpan='2'><SortByLink attr="name" text="Name" /></th>
            <th rowSpan='2'><SortByLink attr="type" text="Type" /></th>
            <th rowSpan='2'><SortByLink attr="location_id" text="Location" /></th>
            <th rowSpan='2'><SortByLink attr="updated" text="Last Update" /></th>
            <th colSpan='3'>Position</th>
            <th colSpan='4'>Orientation</th>
            <th colSpan='1'></th>
          </tr>
          <tr>
            <th>X</th>
            <th>Y</th>
            <th>Z</th>
            <th>X</th>
            <th>Y</th>
            <th>Z</th>
            <th>W</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {
            Object.keys(headsets).length > 0 ? (
              Object.entries(headsets).sort((a, b) => a[1][sortBy.attr] > b[1][sortBy.attr] ? sortBy.direction : -sortBy.direction).map(([id, headset]) => {
                return <tr>
                  <td><Link to={`/headsets/${id}`}>{id}</Link></td>
                  <td id={"headsetName" + id}>
                    {
                      inEditModeHeadset.status && inEditModeHeadset.rowKey === id ? (
                        <input
                          defaultValue={headset.name}
                          placeholder="Edit Headset Name"
                          name={"headsetinput" + id}
                          type="text"
                          ref={formReferences.name}
                          id={'headsetName' + id}/>
                      ) : (
                        headset.name
                      )
                    }
                  </td>
                  <td>
                    {
                      inEditModeHeadset.status && inEditModeHeadset.rowKey === id ? (
                        <select
                          id="device-type-dropdown"
                          title="Change Device Type"
                          defaultValue={headset.type}
                          ref={formReferences.type}>
                          {
                            deviceTypeOptions.map((type) => {
                              return <option value={type}>{type}</option>
                            })
                          }
                        </select>
                      ) : (
                        headset.type
                      )
                    }
                  </td>
                  <td>
                    {
                      (inEditModeHeadset.rowKey === id) ? (
                        <select
                          id="headset-location-dropdown"
                          title="Change Location"
                          defaultValue={headset.location_id}
                          ref={formReferences.location_id}>
                          {
                            Object.entries(locations).map(([location_id, loc]) => {
                              return <option value={location_id}>{loc.name}</option>
                            })
                          }
                          </select>
                      ) : (
                        locations[headset.location_id] ? (
                          <Link to={`/locations/${headset.location_id}`}>{locations[headset.location_id]['name']}</Link>
                        ) : (
                          "Unknown"
                        )
                      )
                    }
                  </td>
                  <td>{moment.unix(headset.updated).fromNow()}</td>
                  <td>{headset.position.x.toFixed(3)}</td>
                  <td>{headset.position.y.toFixed(3)}</td>
                  <td>{headset.position.z.toFixed(3)}</td>
                  <td>{headset.orientation.x.toFixed(3)}</td>
                  <td>{headset.orientation.y.toFixed(3)}</td>
                  <td>{headset.orientation.z.toFixed(3)}</td>
                  <td>{headset.orientation.w.toFixed(3)}</td>
                  <td>
                    {
                      (inEditModeHeadset.status && inEditModeHeadset.rowKey === id) ? (
                        <React.Fragment>
                          <Button
                            className={"btn-success table-btns"}
                            id={'savebtn' + id}
                            onClick={(e) => onSaveHeadsets(e, id)}
                            title='Save'>
                              Save
                          </Button>

                          <Button
                            className={"btn-secondary table-btns"}
                            style={{marginLeft: 8}}
                            onClick={(event) => onCancelHeadset(event, id)}
                            title='Cancel'>
                              Cancel
                          </Button>
                        </React.Fragment>
                      ) : (
                        <Button
                          className={"btn-primary table-btns"}
                          onClick={(e) => onEditHeadset(e, id)}
                          title='Edit'>
                            Edit
                          </Button>
                      )
                    }
                  </td>
                  <td>
                    <div>
                      <TrashIcon item='headset' id={id} name={headset.name}/>
                    </div>
                  </td>
                </tr>
              })
            ) : (
              <tr><td colspan="100%">No Headsets</td></tr>
            )
          }
        </tbody>
      </Table>

      <NewDevice setDevices={setHeadsets} />
    </div>
  );
}

export default AllHeadsets;

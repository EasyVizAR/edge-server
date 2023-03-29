import './Tables.css';
import {Container, Table, Button} from 'react-bootstrap';
import React, {useContext, useState, useEffect} from 'react';
import moment from 'moment';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid, regular, brands} from '@fortawesome/fontawesome-svg-core/import.macro';
import { LocationsContext } from './Contexts.js';


function LocationTable(props) {
  const host = process.env.PUBLIC_URL;

  const { locations, setLocations } = useContext(LocationsContext);

  // Only one row can be open for editing at a time. A reference is used to
  // query the value of the input field when the user clicks Save. The
  // performance is much better than using an onChange handler for every
  // key press.
  const formReferences = {
    locationName: React.createRef()
  }

  const [changedLocation, setChangedLocation] = useState(null);
  const [inEditModeLocation, setInEditModeLocation] = useState({
    status: false,
    locationId: null
  });

  // checks if a Location name already exists
  function checkLocationName(name, targetId) {
    for (const [id, loc] of Object.entries(locations)) {
      if (id != targetId && loc['name'] === name) {
        return true;
      }
    }
    return false;
  }

  // turns on Location editing
  const onEditLocation = (e, id) => {
    if (inEditModeLocation.status == true && inEditModeLocation.locationId != null) {
      alert("Please save or cancel edit on other location before editing another location");
      return;
    }

    setChangedLocation(locations[id]['name']);

    setInEditModeLocation({
      status: true,
      locationId: id
    });
  }

  // saves the Location data
  const saveLocation = (e, id) => {
    const url = `${host}/locations/${id}`;
    const targetLocation = locations[id];
    console.log(e.target);
    const newName = formReferences.locationName.current.value;

    const is_dup = checkLocationName(newName, id);
    if (is_dup) {
      var conf = window.confirm('There is another location with the same name. Are you sure you want to continue?');
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
        'name': newName
      })
    };

    fetch(url, requestData)
      .then(response => {
        return response.json()
      }).then(data => {
        setChangedLocation(newName);

        setLocations(current => {
          const copy = {...current};
          copy[data.id] = data;
          return copy;
        });

        onCancelLocation(id);
      });
  }

  // cancels Location editing
  const onCancelLocation = (id) => {
    locations[id]['name'] = changedLocation;
    setChangedLocation(null);

    // reset the inEditMode state value
    setInEditModeLocation({
      status: false,
      locationId: null
    });
  }

  // on change handler for updating Location name
  const updateLocationName = (ev, id) => {
    locations[id]['name'] = ev.target.value;
  }

  function deleteLocation(id, name) {
    const del = window.confirm("Are you sure you want to delete Location '" + name + "'?");
    if (!del) {
      return;
    }

    const url = `${host}/locations/${id}`;
    const requestData = {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    fetch(url, requestData).then(response => {
      setLocations(current => {
        const copy = {...current};
        delete copy[id];
        return copy;
      });
    });
  }

  // code that creates the trash icons
  function TrashIcon(props) {
    const itemId = props.id;
    const itemName = props.name;

    return (
      <Button style={{width: "30px", height: "30px"}} className='btn-danger table-btns'
        onClick={(e) => deleteLocation(itemId, itemName)} title="Delete Location">

        <FontAwesomeIcon icon={solid('trash-can')} size="lg" style={{position: 'relative', right: '0px', top: '-1px'}}/>
      </Button>
    );
  }

  return (
    <div style={{marginTop: "20px"}}>
      <div>
        <h3 style={{textAlign: "left"}}>Locations</h3>
      </div>
      <Table striped bordered hover>
        <thead>
          <tr>
            <th rowSpan='2'>Location ID</th>
            <th rowSpan='2'>Name</th>
          </tr>
        </thead>
        <tbody>
          {
            Object.keys(locations).length > 0 ? (
              Object.entries(locations).map(([id, loc]) => {
                return <tr>
                  <td>{id}</td>
                  <td>
                    {
                      (inEditModeLocation.locationId === id) ? (
                        <input
                          placeholder="Edit Location Name"
                          name="input"
                          type="text"
                          id={'locationName' + id}
                          defaultValue={loc.name}
                          ref={formReferences.locationName}/>
                      ) : (
                        loc.name
                      )
                    }
                  </td>
                  <td>
                    {
                      (inEditModeLocation.locationId === id) ? (
                        <React.Fragment>
                          <Button
                            className={"btn-success table-btns"}
                            id={'locationsbtn' + id}
                            onClick={(e) => saveLocation(e, id)}
                            title='Save'>
                            Save
                          </Button>
                          <Button
                            className={"btn-secondary table-btns"}
                            style={{marginLeft: 8}}
                            onClick={() => onCancelLocation(id)}
                            title='Cancel'>
                            Cancel
                          </Button>
                        </React.Fragment>
                      ) : (
                        <Button
                          className={"btn-primary table-btns"}
                          onClick={(e) => onEditLocation(e, id)}
                          title='Edit'>
                          Edit
                        </Button>
                      )
                    }
                  </td>
                  <td>
                    <div>
                      <TrashIcon item='location' id={id} name={loc.name}/>
                    </div>
                  </td>
                </tr>
              })
            ) : (
              <tr><td colspan="100%">No Locations</td></tr>
            )
          }
        </tbody>
      </Table>
    </div>
  );
}

export default LocationTable;

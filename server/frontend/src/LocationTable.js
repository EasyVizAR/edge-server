import './Tables.css';
import {Container, Table, Button} from 'react-bootstrap';
import React, {useState, useEffect} from 'react';
import moment from 'moment';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid, regular, brands} from '@fortawesome/fontawesome-svg-core/import.macro';

function LocationTable(props){
  const host = window.location.hostname;
  const port = props.port;
  const [changedLocation, setChangedLocation] = useState(null);
  const [inEditModeLocation, setInEditModeLocation] = useState({
    status: false,
    rowKey: null
  });

  // checks if a Location name already exists
  function checkLocationName(name, id) {
    for (var x in props.locations) {
      if (props.locations[x]['name'] === name && props.locations[x]['id'] != id) {
        return true;
      }
    }
    return false;
  }

  // turns on Location editing
  const onEditLocation = (e, id) => {
    if (inEditModeLocation.status == true && inEditModeLocation.rowKey != null) {
      alert("Please save or cancel edit on other location before editing another location");
      return;
    }

    setChangedLocation(props.locations[id]['name']);

    setInEditModeLocation({
      status: true,
      rowKey: id
    });
  }

  // saves the Location data
  const saveLocation = (e, index) => {
    const id = e.target.id.substring(12, e.target.id.length);
    const url = `http://${host}:${port}/locations/${id}`;
    var i = 0;
    for (var x in props.locations) {
      if (props.locations[x]['id'] == id) {
        var dup_name = checkLocationName(props.locations[i]['name'], props.locations[x]['id']);
        if (dup_name) {
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
            'name': props.locations[x]['name']
          })
        };

        fetch(url, requestData).then(response => {
          setChangedLocation(props.locations[x]['name']);
          onCancelLocation(index);
          props.getLocations();
        });
        break;
      }
      i = i + 1
    }
  }

  // cancels Location editing
  const onCancelLocation = (index) => {
    for (var x in props.locations){
      if (x == index){
        props.locations[x]['name'] = changedLocation;
        break;
      }
    }

    setChangedLocation(null);

    // reset the inEditMode state value
    setInEditModeLocation({
      status: false,
      rowKey: null
    });
  }

  // on change handler for updating Location name
  const updateLocationName = (e) => {
    var newLocations = [];
    var prefix = "locationName";
    var location_id = e.target.id.substring(prefix.length, e.target.id.length);

    for (var x in props.locations) {
      if (props.locations[x]['id'] == location_id) {
        props.locations[x]['name'] = e.target.value;
      }
      newLocations.push(props.locations[x]);
    }
    props.setLocations(newLocations);
  }

  function deleteLocation(id, name) {
    const del = window.confirm("Are you sure you want to delete Location '" + name + "'?");
    if (!del) {
      return;
    }

    const url = `http://${host}:${port}/locations/${id}`;
    const requestData = {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    fetch(url, requestData).then(response => {
      for (var x in props.locations) {
        if (props.locations[x]['id'] == id) {
          props.locations.pop(props.locations[x]);
        }
      }
      props.getLocations();
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
            props.locations.length > 0 ? (
              props.locations.map((e, index) => {
                return <tr>
                  <td>{e.id}</td>
                  <td>
                    {
                      inEditModeLocation.status && inEditModeLocation.rowKey === index ? (
                        <input
                          placeholder="Edit Location Name"
                          name="input"
                          type="text"
                          id={'locationName' + e.id}
                          onChange={updateLocationName}
                          value={props.locations[index]['name']}/>
                      ) : (
                        e.name
                      )
                    }
                  </td>
                  <td>
                    {
                      (inEditModeLocation.status && inEditModeLocation.rowKey === index) ? (
                        <React.Fragment>
                          <Button
                            className={"btn-success table-btns"}
                            id={'locationsbtn' + e.id}
                            onClick={(e) => saveLocation(e, index)}
                            title='Save'>
                            Save
                          </Button>
                          <Button
                            className={"btn-secondary table-btns"}
                            style={{marginLeft: 8}}
                            onClick={() => onCancelLocation(index)}
                            title='Cancel'>
                            Cancel
                          </Button>
                        </React.Fragment>
                      ) : (
                        <Button
                          className={"btn-primary table-btns"}
                          onClick={(e) => onEditLocation(e, index)}
                          title='Edit'>
                          Edit
                        </Button>
                      )
                    }
                  </td>
                  <td>
                    <div>
                      <TrashIcon item='location' id={e.id} name={e.name}/>
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
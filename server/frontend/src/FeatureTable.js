import './Tables.css';
import {Container, Table, Button} from 'react-bootstrap';
import React, {useState, useEffect} from 'react';
import moment from 'moment';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid, regular, brands} from '@fortawesome/fontawesome-svg-core/import.macro';

const featureTypes = [
  "ambulance",
  "door",
  "elevator",
  "extinguisher",
  "fire",
  "headset",
  "injury",
  "message",
  "object",
  "stairs",
  "user",
  "warning"
]

const placementTypes = [
  "point",
  "floating",
  "surface"
]

function FeatureTable(props){
  const host = window.location.hostname;
  const port = props.port;

  // Only one row can be open for editing at a time. A reference is used to
  // query the value of the input field when the user clicks Save. The
  // performance is much better than using an onChange handler for every
  // key press.
  const formReferences = {
    name: React.createRef(),
    type: React.createRef(),
    placement: React.createRef()
  };

  const [editMode, setEditMode] = useState({
    enabled: false,
    rowIndex: null
  });

  const enableEditMode = (e, index) => {
    if (editMode.status) {
      alert("Only one row can be open for editing at a time. Please save or cancel the currently open row.");
      return;
    }

    setEditMode({
      status: true,
      rowIndex: index
    });
  }

  const cancelEditMode = (e, index) => {
    setEditMode({
      status: false,
      rowIndex: null
    });
  }

  // saves the headset data
  const saveFeature = (e, index) => {
    const id = props.features[index]['id'];
    const url = `http://${host}:${port}/locations/${props.locationId}/features/${id}`;

    const newName = formReferences.name.current.value;
    const newType = formReferences.type.current.value;
    const newPlacement = formReferences.placement.current.value;

    const requestData = {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        'name': newName,
        'type': newType,
        'style.placement': newPlacement
      })
    };

    fetch(url, requestData).then(response => {
      props.features[index]['name'] = newName;
      props.features[index]['iconValue'] = newType;
      props.features[index]['placement'] = newPlacement;
      cancelEditMode(null, index);
      props.getFeatures();
    });
  }

  // deletes item with the id and name
  function deleteFeature(index, id, name) {
    const del = window.confirm("Are you sure you want to delete '" + name + "'?");
    if (!del) {
      return;
    }

    const url = `http://${host}:${port}/locations/${props.locationId}/features/${id}`;
    const requestData = {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    fetch(url, requestData).then(response => {
      props.features.pop(id);
    });
  }

  // code that creates the trash icons
  function TrashIcon(props) {
    const index = props.index;
    const itemId = props.id;
    const itemName = props.name;

    return (
      <Button style={{width: "30px", height: "30px"}} className='btn-danger table-btns'
        onClick={(e) => deleteFeature(index, itemId, itemName)} title="Delete Feature">

        <FontAwesomeIcon icon={solid('trash-can')} size="lg" style={{position: 'relative', right: '0px', top: '-1px'}}/>
      </Button>
    );
  }

  return(
    <div style={{marginTop: "20px"}}>
      <div>
        <h3 style={{textAlign: "left"}}>Features</h3>
      </div>
      <Table striped bordered hover>
        <thead>
          <tr>
            <th rowSpan='2'>Feature ID</th>
            <th rowSpan='2'>Name</th>
            <th rowSpan='2'>Type</th>
            <th rowSpan='2'>Last Update</th>
            <th colSpan='3'>Position</th>
            <th colSpan='4'>Style</th>
            <th colSpan='1'></th>
          </tr>
          <tr>
            <th>X</th>
            <th>Y</th>
            <th>Z</th>
            <th>Placement</th>
            <th>Radius</th>
            <th>Left Offset</th>
            <th>Top Offset</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {
            props.features.length > 0 ? (
              props.features.map((e, index) => (
                <tr>
                  <td>{e.id}</td>
                  <td id={"headsetName" + index}>
                    {
                      editMode.status && editMode.rowIndex === index ? (
                        <input
                          defaultValue={props.features[index]['name']}
                          placeholder="Edit Feature Name"
                          name={"headsetinput" + e.id}
                          type="text"
                          ref={formReferences.name}
                          id={'headsetName' + e.id}/>
                      ) : (
                        e.name
                      )
                    }
                  </td>
                  <td>
                    {
                      editMode.status && editMode.rowIndex === index ? (
                        <select
                          id="feature-type-dropdown"
                          title="Change Type"
                          defaultValue={e.iconValue}
                          ref={formReferences.type}>
                          {
                            featureTypes.map((name, index) => {
                              return <option style={{textTransform: 'capitalize'}} value={name}>{name}</option>
                            })
                          }
                          </select>
                      ) : (
                        e.iconValue
                      )
                    }
                  </td>
                  <td>{moment.unix(e.updated).fromNow()}</td>
                  <td>{e.positionX.toFixed(3)}</td>
                  <td>{e.positionY.toFixed(3)}</td>
                  <td>{e.positionZ.toFixed(3)}</td>
                  <td>
                    {
                      editMode.status && editMode.rowIndex === index ? (
                        <select
                          id="feature-placement-dropdown"
                          title="Change Placement"
                          defaultValue={e.placement}
                          ref={formReferences.placement}>
                          {
                            placementTypes.map((name, index) => {
                              return <option style={{textTransform: 'capitalize'}} value={name}>{name}</option>
                            })
                          }
                          </select>
                      ) : (
                        e.placement
                      )
                    }
                  </td>
                  <td>{e.radius}</td>
                  <td>N/A</td>
                  <td>N/A</td>
                  <td>
                    {
                      (editMode.status && editMode.rowIndex === index) ? (
                        <React.Fragment>
                          <Button
                            className={"btn-success table-btns"}
                            id={'savebtn' + e.id}
                            onClick={(e) => saveFeature(e, index)}
                            title='Save'>
                            Save
                          </Button>
                          <Button
                            className={"btn-secondary table-btns"}
                            style={{marginLeft: 8}}
                            onClick={(event) => cancelEditMode(event, index)}
                            title='Cancel'>
                            Cancel
                          </Button>
                        </React.Fragment>
                      ) : (
                        <Button
                          className={"btn-primary table-btns"}
                          onClick={(e) => enableEditMode(e, index)}
                          title='Edit'>
                          Edit
                        </Button>
                      )
                    }
                  </td>
                  <td>
                    <div>
                      <TrashIcon index={index} id={e.id} name={e.name}/>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr><td colspan="100%">No Features</td></tr>
            )
          }
        </tbody>
      </Table>
    </div>
  );
}

export default FeatureTable;

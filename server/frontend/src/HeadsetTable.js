import './Tables.css';
import {Container, Table, Button} from 'react-bootstrap';
import React, {useState, useEffect} from 'react';
import moment from 'moment';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid, regular, brands} from '@fortawesome/fontawesome-svg-core/import.macro';

function HeadsetTable(props){
  const host = window.location.hostname;
  const port = props.port;

  // Only one row can be open for editing at a time. A reference is used to
  // query the value of the input field when the user clicks Save. The
  // performance is much better than using an onChange handler for every
  // key press.
  const formReferences = {
    name: React.createRef(),
    color: React.createRef()
  };

  const [inEditModeHeadset, setInEditModeHeadset] = useState({
    status: false,
    rowKey: null
  });

  // check if a headset name already exists
  function checkHeadsetName(name, id) {
    for (var x in props.headsets) {
      if (props.headsets[x]['name'] == name && props.headsets[x]['id'] != id) {
        return true;
      }
    }
    return false;
  }

  // turns on headset editing
  const onEditHeadset = (e, id) => {
    if (inEditModeHeadset.status == true && inEditModeHeadset.rowKey != null) {
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
    const headset = props.headsets[id];
    const url = `http://${host}:${port}/headsets/${id}`;

    const newName = formReferences.name.current.value;
    const newColor = formReferences.color.current.value;

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
        'color': newColor
      })
    };

    fetch(url, requestData).then(response => {
      headset.name = newName;
      headset.color = newColor;
      onCancelHeadset(null, id);
      props.getHeadsets();
    });
  }

  // turns off headset editing
  const onCancelHeadset = (element, id) => {
    setInEditModeHeadset({
      status: false,
      rowKey: null
    });
  }

  // deletes headset with the id and name
  function deleteHeadset(id, name) {
    const del = window.confirm("Are you sure you want to delete headset '" + name + "'?");
    if (!del) {
      return;
    }

    const url = `http://${host}:${port}/headsets/${id}`;
    const requestData = {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    fetch(url, requestData).then(response => {
      delete props.headsets[id];
      props.getHeadsets();
    });
  }

  // code that creates the trash icons
  function TrashIcon(props) {
    const itemId = props.id;
    const itemName = props.name;

    return (
      <Button style={{width: "30px", height: "30px"}} className='btn-danger table-btns'
        onClick={(e) => deleteHeadset(itemId, itemName)} title="Delete Headset">

        <FontAwesomeIcon icon={solid('trash-can')} size="lg" style={{position: 'relative', right: '0px', top: '-1px'}}/>
      </Button>
    );
  }

  return(
    <div style={{marginTop: "20px"}}>
      <div>
        <h3 style={{textAlign: "left"}}>Headsets</h3>
      </div>
      <Table striped bordered hover>
        <thead>
          <tr>
            <th rowSpan='2'>Headset ID</th>
            <th rowSpan='2'>Name</th>
            <th rowSpan='2'>Icon / Color</th>
            <th rowSpan='2'>Location</th>
            <th rowSpan='2'>Last Update</th>
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
            Object.keys(props.headsets).length > 0 ? (
              Object.entries(props.headsets).map(([id, headset]) => {
                return <tr>
                  <td>{id}</td>
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
                        <input
                          defaultValue={headset.color}
                          placeholder="Edit Headset Color"
                          name={"headset-color-" + id}
                          type="color"
                          ref={formReferences.color}
                          id={"headset-color-" + id}/>
                      ) : (
                        <FontAwesomeIcon icon={solid('headset')} size="lg" color={headset.color}/>
                      )
                    }
                  </td>
                  <td>{props.locations[headset.location_id] ? props.locations[headset.location_id]['name'] : 'Unknown'}</td>
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
                      <TrashIcon id={id} name={headset.name}/>
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
    </div>
  );
}

export default HeadsetTable;

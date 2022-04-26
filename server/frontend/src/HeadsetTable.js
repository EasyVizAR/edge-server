import './Tables.css';
import {Container, Table, Button} from 'react-bootstrap';
import React, {useState, useEffect} from 'react';
import moment from 'moment';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid, regular, brands} from '@fortawesome/fontawesome-svg-core/import.macro';

function HeadsetTable(props){
  const host = window.location.hostname;
  const port = props.port;
  const [changedHeadsetName, setChangedHeadsetName] = useState(null);
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

    setChangedHeadsetName(props.headsets[id]['name']);

    setInEditModeHeadset({
        status: true,
        rowKey: id
    });
  }

  // saves the headset data
  const onSaveHeadsets = (e, index) => {
    const headset = null;
    const id = e.target.id.substring(7, e.target.id.length);
    const url = `http://${host}:${port}/headsets/${id}`;
    for (var x in props.headsets) {
      if (props.headsets[x]['id'] == id) {

        var dup = checkHeadsetName(props.headsets[x]['name'], props.headsets[x]['id']);
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
            'name': props.headsets[x]['name']
          })
        };

        fetch(url, requestData).then(response => {
          setChangedHeadsetName(props.headsets[x]['name']);
          onCancelHeadset(null, index);
          props.getHeadsets();
        });
        break;
      }
    }
    console.log("headset updated");
  }

  // turns off headset editing
  const onCancelHeadset = (element, index) => {

    for (var x in props.headsets){
      if (x == index){
        props.headsets[x]['name'] = changedHeadsetName;
        break;
      }
    }

    setChangedHeadsetName(null);

    setInEditModeHeadset({
      status: false,
      rowKey: null
    });
  }

  // onchange handler for updating headset name
  const updateHeadsetName = (e) => {
    var newHeadsets = [];
    var prefix = "headsetName";
    var headset_id = e.target.id.substring(prefix.length, e.target.id.length);

    for (var x in props.headsets) {
      if (props.headsets[x]['id'] == headset_id) {
        props.headsets[x]['name'] = e.target.value;
      }
      newHeadsets.push(props.headsets[x]);
    }
    props.setHeadsets(newHeadsets);
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
      for (var x in props.headsets) {
        if (props.headsets[x]['id'] == id) {
          props.headsets.pop(props.headsets[x]);
        }
      }
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
            <th rowSpan='2'>Location ID</th>
            <th rowSpan='2'>Last Update</th>
            <th colSpan='3'>Position</th>
            <th colSpan='3'>Orientation</th>
            <th colSpan='1'></th>
          </tr>
          <tr>
            <th>X</th>
            <th>Y</th>
            <th>Z</th>
            <th>X</th>
            <th>Y</th>
            <th>Z</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {
            props.headsets.length > 0 ? (
              props.headsets.map((e, index) => (
                <tr>
                  <td>{e.id}</td>
                  <td id={"headsetName" + index}>
                    {
                      inEditModeHeadset.status && inEditModeHeadset.rowKey === index ? (
                        <input
                          value={props.headsets[index]['name']}
                          placeholder="Edit Headset Name"
                          onChange={updateHeadsetName}
                          name={"headsetinput" + e.id}
                          type="text"
                          id={'headsetName' + e.id}/>
                      ) : (
                        e.name
                      )
                    }
                  </td>
                  <td>{e.mapId}</td>
                  <td>{moment.unix(e.lastUpdate).fromNow()}</td>
                  <td>{e.positionX}</td>
                  <td>{e.positionY}</td>
                  <td>{e.positionZ}</td>
                  <td>{e.orientationX}</td>
                  <td>{e.orientationY}</td>
                  <td>{e.orientationZ}</td>
                  <td>
                    {
                      (inEditModeHeadset.status && inEditModeHeadset.rowKey === index) ? (
                        <React.Fragment>
                          <Button
                            className={"btn-success table-btns"}
                            id={'savebtn' + e.id}
                            onClick={(e) => onSaveHeadsets(e, index)}
                            title='Save'>
                            Save
                          </Button>
                          <Button
                            className={"btn-secondary table-btns"}
                            style={{marginLeft: 8}}
                            onClick={(event) => onCancelHeadset(event, index)}
                            title='Cancel'>
                            Cancel
                          </Button>
                        </React.Fragment>
                      ) : (
                        <Button
                          className={"btn-primary table-btns"}
                          onClick={(e) => onEditHeadset(e, index)}
                          title='Edit'>
                          Edit
                        </Button>
                      )
                    }
                  </td>
                  <td>
                    <div>
                      <TrashIcon id={e.id} name={e.name}/>
                    </div>
                  </td>
                </tr>
              ))
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
import { Button, Table } from 'react-bootstrap';
import React, { useState, useEffect } from 'react';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid} from '@fortawesome/fontawesome-svg-core/import.macro';
import useStateSynchronous from './useStateSynchronous.js';
import moment from 'moment';

function AllHeadsets(props){
  const host = window.location.hostname;
  const port = props.port;
  const headsets = useStateSynchronous([]);
  const [changedHeadsetName, setChangedHeadsetName] = useState(null);
  const [inEditModeHeadset, setInEditModeHeadset] = useState({
      status: false,
      rowKey: null
  });

  useEffect(() => {
      getAllHeadsets();
  }, []);

  // onchange handler for updating headset name
  const updateHeadsetName = (e) => {
      var newHeadsets = [];
      var prefix = "headsetName";
      var headset_id = e.target.id.substring(prefix.length, e.target.id.length);
      for (var x in headsets.get()) {
          if (headsets.get()[x]['id'] === headset_id) {
              headsets.get()[x]['name'] = e.target.value;
          }
          newHeadsets.push(headsets.get()[x]);
      }
      headsets.set(newHeadsets);
  }

  // check if a headset name already exists
  function checkHeadsetName(name, id) {
      for (var x in headsets.get()) {
          if (headsets.get()[x]['name'] === name && headsets.get()[x]['id'] !== id) {
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

      const url = `http://${host}:${port}/headsets/${id}`;
      const requestData = {
          method: 'DELETE',
          headers: {
              'Content-Type': 'application/json'
          }
      };

      fetch(url, requestData)
          .then(response => {
              for (var x in headsets.get()) {
                  if (headsets.get()[x]['id'] === id) {
                      headsets.get().pop(headsets.get()[x]);
                  }
              }
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

      setChangedHeadsetName(headsets.get()[id]['name']);

      setInEditModeHeadset({
          status: true,
          rowKey: id,
          headset_name: headsets.get()[id]['name']
      });
  }

  // saves the headset data
  const onSaveHeadsets = (e, index) => {
      const headset = null;
      const id = e.target.id.substring(7, e.target.id.length);
      const url = `http://${host}:${port}/headsets/${id}`;
      for (var x in headsets.get()) {
          if (headsets.get()[x]['id'] === id) {

              var dup = checkHeadsetName(headsets.get()[x]['name'], headsets.get()[x]['id']);
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
                      'name': headsets.get()[x]['name']
                  })
              };

              fetch(url, requestData).then(response => {
                setChangedHeadsetName(headsets.get()[x]['name']);
                onCancelHeadset(null, index);
                getAllHeadsets();
              });
              break;
          }
      }
  }

  // code that creates the trash icons
  function TrashIcon(props) {
      const item = props.item;
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
  const onCancelHeadset = (element, index) => {
      for (var x in headsets.get()){
        if (x == index){
          headsets.get()[x]['name'] = changedHeadsetName;
          break;
        }
      }
      setChangedHeadsetName(null);

      setInEditModeHeadset({
          status: false,
          rowKey: null
      });
  }

  function getAllHeadsets(){
    fetch(`http://${host}:${port}/headsets`)
    .then(response => {
      return response.json()
    }).then(data => {
      var fetchedHeadsets = []
      for (var k in data) {
        var v = data[k];
        fetchedHeadsets.push({
          'id': v.id,
          'lastUpdate': v.lastUpdate,
          'mapId': v.mapId,
          'name': v.name,
          'orientationX': v.orientation.x,
          'orientationY': v.orientation.y,
          'orientationZ': v.orientation.z,
          'positionX': v.position.x,
          'positionY': v.position.y,
          'positionZ': v.position.z
        });
      }
      headsets.set(fetchedHeadsets);
    });
  }

  return (
    <div>
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
            headsets.get().length > 0 ? (
              headsets.get().map((e, index) => (
                <tr>
                  <td>{e.id}</td>
                  <td id={"headsetName" + index}>
                    {
                      inEditModeHeadset.status && inEditModeHeadset.rowKey === index ? (
                        <input
                          value={headsets.get()[index]['name']}
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
                      <TrashIcon item='headset' id={e.id} name={e.name}/>
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

export default AllHeadsets;

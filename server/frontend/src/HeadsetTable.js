import './Tables.css';
import {Container, Table, Button} from 'react-bootstrap';
import React, {useContext, useState, useEffect} from 'react';
import { Link } from "react-router-dom";
import moment from 'moment';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid, regular, brands} from '@fortawesome/fontawesome-svg-core/import.macro';
import { LocationsContext } from './Contexts.js';
import { icon } from '@fortawesome/fontawesome-svg-core';
import IconMap from './Icons.js';

const deviceTypeOptions = [
  "unknown",
  "headset",
  "phone",
  "robot",
  "editor",
  "drone",
];


function HeadsetTable(props) {
  const host = process.env.PUBLIC_URL;

  const { locations, setLocations } = useContext(LocationsContext);

  // Only one row can be open for editing at a time. A reference is used to
  // query the value of the input field when the user clicks Save. The
  // performance is much better than using an onChange handler for every
  // key press.
  const formReferences = {
    name: React.createRef(),
    color: React.createRef(),
    type: React.createRef(),
  };

  const [checkedItems, setCheckedItems] = useState({});
  const [navigationTargetIndex, setNavigationTargetIndex] = useState(0);
  const [inEditModeHeadset, setInEditModeHeadset] = useState({
    status: false,
    rowKey: null
  });

  const navigationTargetOptions = ((props) => {
    const options = [
      {
        id: null,
        name: "None",
      }
    ];

    if (Object.keys(props.features).length > 0) {
      Object.entries(props.features).map(([id, feature]) => {
        options.push({
          id: feature.id,
          name: feature.id + " - " + feature.name,
          position: feature.position,
        });
      });
    }

    return options;
  })(props);

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
  const onEditHeadset = (headset, id) => {
    if (inEditModeHeadset.status == true && inEditModeHeadset.rowKey != null) {
      alert("Please save or cancel edit on other headset before editing another headset");
      return;
    }

    setInEditModeHeadset({
        status: true,
        rowKey: id
    });

    // Find the current navigation target as an index in our list of options.
    var target_index = 0;
    if (headset.navigation_target_id) {
      const target_id = headset.navigation_target.target_id;

      navigationTargetOptions.forEach((option, index) => {
        if (target_id === option.id) {
          target_index = index;
        }
      });
    }
    setNavigationTargetIndex(target_index);
  }

  // saves the headset data
  const onSaveHeadsets = (e, id) => {
    const headset = props.headsets[id];
    const url = `${host}/headsets/${id}`;

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
        'color': newColor,
        'type': formReferences.type.current.value,
        'navigation_target_id': navigationTargetOptions[navigationTargetIndex].id
      })
    };

    fetch(url, requestData)
      .then(response => response.json())
      .then(data => {
        props.setHeadsets(prevHeadsets => {
          let newHeadsets = Object.assign({}, prevHeadsets);
          newHeadsets[id] = data;
          return newHeadsets;
        });
        onCancelHeadset(null, id);
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

    const url = `${host}/headsets/${id}`;
    const requestData = {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    fetch(url, requestData).then(response => {
      props.setHeadsets(current => {
        const copy = {...current};
        delete copy[id];
        return copy;
      });
    });
  }

  const toggleCheckAll = () => {
    if (Object.keys(checkedItems).length > 0) {
      setCheckedItems({});
    } else {
      var result = {};
      for (const [id, feature] of Object.entries(props.headsets)) {
        result[id] = true;
      }
      setCheckedItems(result);
    }
  }

  const deleteCheckedItems = async () => {
    const del = window.confirm("Are you sure you want to delete the checked items?");
    if (!del) {
      return;
    }

    await Object.entries(checkedItems)
      .filter(([id, checked]) => checked)
      .reduce((chain, [id]) => {
        const url = `${host}/headsets/${id}`;
        const requestData = {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json'
          }
        };

        return chain.then(() => new Promise(resolve => {
          setTimeout(() => {
            fetch(url, requestData)
              .then(response => {
                props.features.pop(id);
                resolve();
              })
              .catch(error => {
                console.error(`Error deleting headset ${id}: ${error.message}`);
                resolve();
              });
          }, 100); // Delay by 100ms to avoid triggering rate limit
        }));
      }, Promise.resolve());

    setCheckedItems({});
  }

  const toggleCheck = (id) => {
    checkedItems[id] = !checkedItems[id];
    setCheckedItems({...checkedItems});
  }

  const handleRemoveClicked = (id) => {
    const url = `${host}/headsets/${id}`;

    const requestData = {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        'location_id': null
      })
    };

    fetch(url, requestData).then(response => {
      onCancelHeadset(null, id);

      props.setHeadsets(current => {
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
        onClick={(e) => deleteHeadset(itemId, itemName)} title="Delete Headset">

        <FontAwesomeIcon icon={solid('trash-can')} size="lg" style={{position: 'relative', right: '0px', top: '-1px'}}/>
      </Button>
    );
  }

  function NavigationTarget(child_props) {
    const target_id = child_props.target_id;

    if (target_id) {
      return <p>{props.features[target_id]?.name || "invalid"}</p>;
    } else {
      return <p>None</p>;
    }
  }

  return(
    <div style={{marginTop: "20px"}}>
      <div>
        <h3 style={{textAlign: "left"}}>Headsets</h3>
      </div>
      <Table striped bordered hover>
        <thead>
          <tr>
            <th rowSpan='2'><input type="checkbox" checked={Object.keys(checkedItems).length > 0} onChange={toggleCheckAll} /></th>
            <th rowSpan='2'>Headset ID</th>
            <th rowSpan='2'>Name</th>
            <th rowSpan='2'>Color</th>
            <th rowSpan='2'>Location</th>
            <th rowSpan='2'>Last Update</th>
            <th rowSpan='2'>Type</th>
            <th colSpan='3'>Position</th>
            <th colSpan='4'>Orientation</th>
            <th colSpan='2'>Target</th>
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
            <th>ID</th>
            <th>Name</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {
            Object.keys(props.headsets).length > 0 ? (
              Object.entries(props.headsets).map(([id, headset]) => {
                return <tr>
                  <td><input type="checkbox" id={"check-"+id} checked={checkedItems[id]} onChange={() => toggleCheck(id)} /></td>
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
                        <input
                          defaultValue={headset.color}
                          placeholder="Edit Headset Color"
                          name={"headset-color-" + id}
                          type="color"
                          ref={formReferences.color}
                          id={"headset-color-" + id}/>
                      ) : ( deviceTypeOptions.includes(headset.type) ?
                        <FontAwesomeIcon
                          icon={IconMap?.[headset.type]?.['iconName'] || "bug"}
                          size="lg"
                          color={headset.color}
                        /> : null
                      )
                    }
                  </td>
                  <td>{locations[headset.location_id] ? locations[headset.location_id]['name'] : 'Unknown'}</td>
                  <td>{moment.unix(headset.updated).fromNow()}</td>
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
                  <td>{headset.position.x.toFixed(3)}</td>
                  <td>{headset.position.y.toFixed(3)}</td>
                  <td>{headset.position.z.toFixed(3)}</td>
                  <td>{headset.orientation.x.toFixed(3)}</td>
                  <td>{headset.orientation.y.toFixed(3)}</td>
                  <td>{headset.orientation.z.toFixed(3)}</td>
                  <td>{headset.orientation.w.toFixed(3)}</td>
                  {
                    (inEditModeHeadset.status && inEditModeHeadset.rowKey === id) ? (
                      <td colSpan='2'>
                        <select
                          id="navigation-target-dropdown"
                          title="Change Target"
                          value={navigationTargetIndex}
                          onChange={(e) => setNavigationTargetIndex(e.target.value)}>
                          {
                            navigationTargetOptions.map((option, index) => {
                              return <option value={index}>{option.name}</option>
                            })
                          }
                        </select>
                      </td>
                    ) : (
                      <React.Fragment>
                        <td>{headset.navigation_target_id}</td>
                        <td><NavigationTarget target_id={headset.navigation_target_id} /></td>
                      </React.Fragment>
                    )
                  }
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
                        <React.Fragment>
                          <Button
                            variant="primary" size="sm"
                            onClick={(e) => onEditHeadset(headset, id)}
                            title='Edit'>
                            Edit
                          </Button>
                          <Button
                            variant="warning" size="sm"
                            onClick={() => handleRemoveClicked(id)}
                            title="Remove headset from location (does not delete its history)">
                            Remove
                          </Button>
                        </React.Fragment>
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

      {
        Object.keys(checkedItems).length > 0 ? (
          <Button variant="danger" onClick={deleteCheckedItems}>Delete Checked</Button>
        ) : (null)
      }
    </div>
  );
}

export default HeadsetTable;

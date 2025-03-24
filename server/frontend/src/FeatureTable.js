import './Tables.css';
import {Table, Button} from 'react-bootstrap';
import React, {useState} from 'react';
import moment from 'moment';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid} from '@fortawesome/fontawesome-svg-core/import.macro';

function FeatureTable(props){
  const host = process.env.PUBLIC_URL;
  const icons = props.icons;

  // Only one row can be open for editing at a time. A reference is used to
  // query the value of the input field when the user clicks Save. The
  // performance is much better than using an onChange handler for every
  // key press.
  const formReferences = {
    name: React.createRef(),
    color: React.createRef(),
    type: React.createRef(),
    enabled: React.createRef(),
  };

  const [checkedItems, setCheckedItems] = useState({});

  const enableEditMode = (e, id, feature) => {
    if (props.editFeature?.status) {
      alert("Only one row can be open for editing at a time. Please save or cancel the currently open row.");
      return;
    }

    props.setEditFeature({
      status: true,
      featureId: id,
      position: Object.assign({}, feature.position),
    });
  }

  const cancelEditMode = (e, id) => {
    props.setEditFeature(null);
  }

  // saves the headset data
  const saveFeature = (e, id) => {
    const url = `${host}/locations/${props.locationId}/features/${id}`;

    const newName = formReferences.name.current.value;
    const newColor = formReferences.color.current.value;
    const newType = formReferences.type.current.value;

    const requestData = {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        'name': newName,
        'color': newColor,
        'type': newType,
        'enabled': formReferences.enabled.current.checked,
        'position.x': props.editFeature.position.x,
        'position.y': props.editFeature.position.y,
        'position.z': props.editFeature.position.z,
      })
    };

    fetch(url, requestData).then(response => {
      cancelEditMode(null, id);
      props.getFeatures();
    });
  }

  // deletes item with the id and name
  function deleteFeature(id, name) {
    const del = window.confirm("Are you sure you want to delete '" + name + "'?");
    if (!del) {
      return;
    }

    const url = `${host}/locations/${props.locationId}/features/${id}`;
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

  const toggleCheckAll = () => {
    if (Object.keys(checkedItems).length > 0) {
      setCheckedItems({});
    } else {
      var result = {};
      for (const [id, feature] of Object.entries(props.features)) {
        result[id] = true;
      }
      setCheckedItems(result);
    }
  }

  const toggleCheck = (id) => {
    checkedItems[id] = !checkedItems[id];
    setCheckedItems({...checkedItems});
  }

  const deleteCheckedItems = async () => {
    const del = window.confirm("Are you sure you want to delete the checked items?");
    if (!del) {
      return;
    }

    await Object.entries(checkedItems)
      .filter(([id, checked]) => checked)
      .reduce((chain, [id]) => {
        const url = `${host}/locations/${props.locationId}/features/${id}`;
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
                console.error(`Error deleting feature ${id}: ${error.message}`);
                resolve();
              });
          }, 100); // Delay by 100ms to avoid triggering rate limit
        }));
      }, Promise.resolve());

    setCheckedItems({});
  }

  // code that creates the trash icons
  function TrashIcon(props) {
    const itemId = props.id;
    const itemName = props.name;

    return (
      <Button style={{width: "30px", height: "30px"}} className='btn-danger table-btns'
        onClick={(e) => deleteFeature(itemId, itemName)} title="Delete Feature">

        <FontAwesomeIcon icon={solid('trash-can')} size="lg" style={{position: 'relative', right: '0px', top: '-1px'}}/>
      </Button>
    );
  }

  function setPositionValue(k, value) {
    props.setEditFeature(previous => {
      let newState = Object.assign({}, previous);
      newState.position[k] = value;
      return newState;
    });
  }

  return(
    <div style={{marginTop: "20px"}}>
      <div>
        <h3 style={{textAlign: "left"}}>Features</h3>
      </div>
      <Table striped bordered hover>
        <thead>
          <tr>
            <th rowSpan='2'><input type="checkbox" checked={Object.keys(checkedItems).length > 0} onChange={toggleCheckAll} /></th>
            <th rowSpan='2'>Feature ID</th>
            <th rowSpan='2'>Name</th>
            <th rowSpan='2'>Icon / Color</th>
            <th rowSpan='2'>Type</th>
            <th rowSpan='2'>Last Update</th>
            <th colSpan='3'>Position</th>
            <th colSpan='2' rowSpan='2'></th>
          </tr>
          <tr>
            <th>X</th>
            <th>Y</th>
            <th>Z</th>
          </tr>
        </thead>
        <tbody>
          {
            Object.keys(props.features).length > 0 ? (
              Object.entries(props.features).map(([id, feature]) => {
                return <tr>
                  <td><input type="checkbox" id={"check-"+id} checked={checkedItems[id]} onChange={() => toggleCheck(id)} /></td>
                  <td>{id}</td>
                  <td id={"featureName" + id}>
                    {
                      props.editFeature?.featureId === id ? (
                        <>
                          <input
                            defaultValue={feature.name}
                            placeholder="Edit Feature Name"
                            name={"feature-name-input" + id}
                            type="text"
                            ref={formReferences.name}
                            id={'feature-name-input' + id}/>
                          <input
                            type="checkbox"
                            defaultChecked={feature.enabled}
                            title="Enabled"
                            ref={formReferences.enabled} />
                        </>
                      ) : (
                        <>
                          {feature.name}
                          { !feature.enabled && <i>(disabled)</i> }
                        </>
                      )
                    }
                  </td>
                  <td>
                    {
                      props.editFeature?.featureId === id ? (
                        <input
                          defaultValue={feature.color}
                          placeholder="Edit Feature Color"
                          name={"feature-color-" + id}
                          type="color"
                          ref={formReferences.color}
                          id={"feature-color-" + id}/>
                      ) : (
                        /* If the feature type is missing or unrecognized, show a bug icon. */
                        icons?.[feature.type]?.['iconName'] ?
                          <FontAwesomeIcon icon={icons[feature.type]['iconName']} size="lg" color={feature.color}/> :
                          <FontAwesomeIcon icon="bug" size="lg" color={feature.color}/>
                      )
                    }
                  </td>
                  <td>
                    {
                      props.editFeature?.featureId === id ? (
                        <select
                          id="feature-type-dropdown"
                          title="Change Type"
                          defaultValue={feature.type || "fire"}
                          ref={formReferences.type}>
                          {
                            Object.entries(props.icons).map(([name, icon]) => {
                              return <option style={{textTransform: 'capitalize'}} value={name}>{name}</option>
                            })
                          }
                          </select>
                      ) : (
                        feature.type
                      )
                    }
                  </td>
                  <td>{moment.unix(feature.updated).fromNow()}</td>
                  <td>
                    {
                      props.editFeature?.featureId === id ? (
                        <input
                          value={props.editFeature.position.x}
                          placeholder="X"
                          name={"feature-position-x"}
                          type="number"
                          onChange={(e) => setPositionValue("x", e.target.value)}
                          id={"feature-position-x"} />
                      ) : (
                        feature.position.x.toFixed(3)
                      )
                    }
                  </td>
                  <td>
                    {
                      props.editFeature?.featureId === id ? (
                        <input
                          value={props.editFeature.position.y}
                          placeholder="Y"
                          name={"feature-position-y"}
                          type="number"
                          onChange={(e) => setPositionValue("y", e.target.value)}
                          id={"feature-position-y"} />
                      ) : (
                        feature.position.y.toFixed(3)
                      )
                    }
                  </td>
                  <td>
                    {
                      props.editFeature?.featureId === id ? (
                        <input
                          value={props.editFeature.position.z}
                          placeholder="Z"
                          name={"feature-position-z"}
                          type="number"
                          onChange={(e) => setPositionValue("z", e.target.value)}
                          id={"feature-position-z"} />
                      ) : (
                        feature.position.z.toFixed(3)
                      )
                    }
                  </td>
                  <td>
                    {
                      (props.editFeature?.featureId === id) ? (
                        <React.Fragment>
                          <Button
                            className={"btn-success table-btns"}
                            id={'savebtn' + id}
                            onClick={(e) => saveFeature(e, id)}
                            title='Save'>
                            Save
                          </Button>
                          <Button
                            className={"btn-secondary table-btns"}
                            style={{marginLeft: 8}}
                            onClick={(event) => cancelEditMode(event, id)}
                            title='Cancel'>
                            Cancel
                          </Button>
                        </React.Fragment>
                      ) : (
                        <>
                          <Button
                            className={"btn-primary table-btns"}
                            onClick={(e) => enableEditMode(e, id, feature)}
                            title='Edit'>
                            Edit
                          </Button>
                          {
                            props.onCalibrate &&
                              <Button
                                className={"btn-warning table-btns"}
                                style={{marginLeft: 8}}
                                onClick={(event) => props.onCalibrate(event, feature)}
                                title='Calibrate'>
                                Calibrate
                              </Button>
                          }
                        </>
                      )
                    }
                  </td>
                  <td>
                    <div>
                      <TrashIcon id={id} name={feature.name}/>
                    </div>
                  </td>
                </tr>
              })
            ) : (
              <tr><td colspan="100%">No Features</td></tr>
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

export default FeatureTable;

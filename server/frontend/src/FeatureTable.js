import './Tables.css';
import {Table, Button} from 'react-bootstrap';
import React, {useState} from 'react';
import moment from 'moment';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid} from '@fortawesome/fontawesome-svg-core/import.macro';

const placementTypes = [
  "point",
  "floating",
  "surface"
]

function FeatureTable(props){
  const host = window.location.hostname;
  const port = props.port;
  const icons = props.icons;

  // Only one row can be open for editing at a time. A reference is used to
  // query the value of the input field when the user clicks Save. The
  // performance is much better than using an onChange handler for every
  // key press.
  const formReferences = {
    name: React.createRef(),
    color: React.createRef(),
    type: React.createRef(),
    placement: React.createRef()
  };

  const [editMode, setEditMode] = useState({
    enabled: false,
    featureId: null
  });

  const [checkedItems, setCheckedItems] = useState({});

  const enableEditMode = (e, id) => {
    if (editMode.status) {
      alert("Only one row can be open for editing at a time. Please save or cancel the currently open row.");
      return;
    }

    setEditMode({
      status: true,
      featureId: id
    });
  }

  const cancelEditMode = (e, id) => {
    setEditMode({
      status: false,
      featureId: null
    });
  }

  // saves the headset data
  const saveFeature = (e, id) => {
    const url = `http://${host}:${port}/locations/${props.locationId}/features/${id}`;

    const newName = formReferences.name.current.value;
    const newColor = formReferences.color.current.value;
    const newType = formReferences.type.current.value;
    const newPlacement = formReferences.placement.current.value;

    const requestData = {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        'name': newName,
        'color': newColor,
        'type': newType,
        'style.placement': newPlacement
      })
    };

    fetch(url, requestData).then(response => {
      props.features[id]['name'] = newName;
      props.features[id]['color'] = newColor;
      props.features[id]['type'] = newType;
      props.features[id]['placement'] = newPlacement;
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

    await Object.entries(checkedItems).map(async ([id, checked]) => {
      if (checked) {
        const url = `http://${host}:${port}/locations/${props.locationId}/features/${id}`;
        const requestData = {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json'
          }
        };

        await fetch(url, requestData).then(response => {
          props.features.pop(id);
        });
      }
    })

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
            <th colSpan='4'>Style</th>
            <th colSpan='2' rowSpan='2'></th>
          </tr>
          <tr>
            <th>X</th>
            <th>Y</th>
            <th>Z</th>
            <th>Placement</th>
            <th>Radius</th>
            <th>Left Offset</th>
            <th>Top Offset</th>
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
                      editMode.status && editMode.featureId === id ? (
                        <input
                          defaultValue={feature.name}
                          placeholder="Edit Feature Name"
                          name={"feature-name-input" + id}
                          type="text"
                          ref={formReferences.name}
                          id={'feature-name-input' + id}/>
                      ) : (
                        feature.name
                      )
                    }
                  </td>
                  <td>
                    {
                      editMode.status && editMode.featureId === id ? (
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
                      editMode.status && editMode.featureId === id ? (
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
                  <td>{feature.position.x.toFixed(3)}</td>
                  <td>{feature.position.y.toFixed(3)}</td>
                  <td>{feature.position.z.toFixed(3)}</td>
                  <td>
                    {
                      editMode.status && editMode.featureId === id ? (
                        <select
                          id="feature-placement-dropdown"
                          title="Change Placement"
                          defaultValue={feature.style?.placement || "point"}
                          ref={formReferences.placement}>
                          {
                            placementTypes.map((name, index) => {
                              return <option style={{textTransform: 'capitalize'}} value={name}>{name}</option>
                            })
                          }
                          </select>
                      ) : (
                        /* If style.placement is undefined, show a bug icon. */
                        feature.style?.placement ?
                          feature.style.placement : <FontAwesomeIcon icon="bug" size="lg" />
                      )
                    }
                  </td>
                  <td>{feature.style?.radius}</td>
                  <td>{feature.style?.leftOffset}</td>
                  <td>{feature.style?.topOffset}</td>
                  <td>
                    {
                      (editMode.status && editMode.featureId === id) ? (
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
                        <Button
                          className={"btn-primary table-btns"}
                          onClick={(e) => enableEditMode(e, id)}
                          title='Edit'>
                          Edit
                        </Button>
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

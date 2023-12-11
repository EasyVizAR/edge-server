import './Tables.css';
import {Table, Button} from 'react-bootstrap';
import React, {useState} from 'react';
import moment from 'moment';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid} from '@fortawesome/fontawesome-svg-core/import.macro';

function LayerTable(props) {
  const host = process.env.PUBLIC_URL;

  // Only one row can be open for editing at a time. A reference is used to
  // query the value of the input field when the user clicks Save. The
  // performance is much better than using an onChange handler for every
  // key press.
  const formReferences = {
    name: React.createRef(),
    cutting_height: React.createRef()
  };

  const [editMode, setEditMode] = useState({
    enabled: false,
    layerId: null
  });

  const enableEditMode = (e, id) => {
    if (editMode.status) {
      alert("Only one row can be open for editing at a time. Please save or cancel the currently open row.");
      return;
    }

    setEditMode({
      status: true,
      layerId: id
    });
  }

  const cancelEditMode = (e, id) => {
    setEditMode({
      status: false,
      layerId: null
    });
  }

  const saveLayer = (index, id) => {
    const url = `${host}/locations/${props.locationId}/layers/${id}`;

    const newName = formReferences.name.current.value;
    const newCuttingHeight = formReferences.cutting_height.current.value;

    const requestData = {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        'name': newName,
        'cutting_height': newCuttingHeight
      })
    };

    fetch(url, requestData).then(response => {
      props.layers[index]['name'] = newName;
      props.layers[index]['cutting_height'] = newCuttingHeight;
      cancelEditMode(null, id);
    });
  }

  // deletes item with the id and name
  function deleteLayer(index, id, name) {
    const del = window.confirm("Are you sure you want to delete '" + name + "'?");
    if (!del) {
      return;
    }

    const url = `${host}/locations/${props.locationId}/layers/${id}`;
    const requestData = {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    fetch(url, requestData).then(response => {
      if (props.setLayers) {
        props.setLayers(prevLayers => {
          let newLayers = [];
          for (var layer of prevLayers) {
            if (layer.id !== id) {
              newLayers.push(layer);
            }
          }
          return newLayers;
        });
      }
    });
  }

  // code that creates the trash icons
  function TrashIcon(props) {
    const itemIndex = props.index;
    const itemId = props.id;
    const itemName = props.name;

    return (
      <Button style={{width: "30px", height: "30px"}} className='btn-danger table-btns'
        onClick={(e) => deleteLayer(itemIndex, itemId, itemName)} title="Delete Layer">

        <FontAwesomeIcon icon={solid('trash-can')} size="lg" style={{position: 'relative', right: '0px', top: '-1px'}}/>
      </Button>
    );
  }

  return(
    <div style={{marginTop: "20px"}}>
      <div>
        <h3 style={{textAlign: "left"}}>Map Layers</h3>
      </div>
      <Table striped bordered hover>
        <thead>
          <tr>
            <th>Layer ID</th>
            <th>Name</th>
            <th>Type</th>
            <th>Cutting Height</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {
            props.layers.length > 0 ? (
              props.layers.map((layer, index) => {
                return <tr>
                  <td>{layer.id}</td>
                  <td id={"layerName" + layer.id}>
                    {
                      editMode.status && editMode.layerId === layer.id ? (
                        <input
                          defaultValue={layer.name}
                          placeholder="Edit Layer Name"
                          name={"layer-name-input" + layer.id}
                          type="text"
                          ref={formReferences.name}
                          id={'layer-name-input' + layer.id}/>
                      ) : (
                        layer.name
                      )
                    }
                  </td>
                  <td>{layer.type}</td>
                  <td class="limit-width">
                    {
                      editMode.status && editMode.layerId === layer.id ? (
                        <div>
                          <input
                            defaultValue={layer.cutting_height}
                            placeholder="Edit Layer Cutting Height"
                            name={"layer-color-" + layer.id}
                            type="number"
                            ref={formReferences.cutting_height}
                            id="edit-layer-cutting-height" />
                          <label for="edit-layer-cutting-height">
                            Cutting plane height offset in meters relative to the reference height (e.g. QR code) used for floor plan construction.
                            Changing this value will cause the map to be regenerated, which may take some time to complete.
                          </label>
                        </div>
                      ) : (
                        layer.cutting_height
                      )
                    }
                  </td>
                  <td>
                    {
                      (editMode.status && editMode.layerId === layer.id) ? (
                        <React.Fragment>
                          <Button
                            className={"btn-success table-btns"}
                            id={'savebtn' + layer.id}
                            onClick={(e) => saveLayer(index, layer.id)}
                            title='Save'>
                            Save
                          </Button>
                          <Button
                            className={"btn-secondary table-btns"}
                            style={{marginLeft: 8}}
                            onClick={(event) => cancelEditMode(event, layer.id)}
                            title='Cancel'>
                            Cancel
                          </Button>
                        </React.Fragment>
                      ) : (
                        <React.Fragment>
                          <Button
                            className={"btn-primary table-btns"}
                            onClick={(e) => enableEditMode(e, layer.id)}
                            title='Edit'>
                            Edit
                          </Button>
                          <a class="btn btn-secondary table-btns" href={`/locations/${props.locationId}/layers/${layer.id}/image`}>SVG</a>
                          <a class="btn btn-secondary table-btns" href={`/locations/${props.locationId}/layers/${layer.id}/image.png`}>PNG</a>
                        </React.Fragment>
                      )
                    }
                  </td>
                  <td>
                    <div>
                      <TrashIcon index={index} id={layer.id} name={layer.name}/>
                    </div>
                  </td>
                </tr>
              })
            ) : (
              <tr><td colspan="100%">No Layers</td></tr>
            )
          }
        </tbody>
      </Table>
    </div>
  );
}

export default LayerTable;

import './Tables.css';
import {Table, Button} from 'react-bootstrap';
import React, {useEffect, useState} from 'react';
import moment from 'moment';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid} from '@fortawesome/fontawesome-svg-core/import.macro';

function MapPathTable(props) {
  const host = process.env.PUBLIC_URL;
  const icons = props.icons;
  const resourceName = "map-paths";

  // Only one row can be open for editing at a time. A reference is used to
  // query the value of the input field when the user clicks Save. The
  // performance is much better than using an onChange handler for every
  // key press.
  const formReferences = {
    target_marker_id: React.createRef(),
    type: React.createRef(),
    color: React.createRef(),
    label: React.createRef(),
  };

  const [checkedItems, setCheckedItems] = useState({});
  const [editRow, setEditRow] = useState({
    enabled: false,
    id: null,
  });

  const cancelEdit = () => {
    setEditRow({
      enabled: false,
      id: null,
    });
  }

  const saveItem = (e, id) => {
    const url = `${host}/locations/${props.locationId}/${resourceName}/${id}`;

    const requestData = {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        'target_marker_id': formReferences.target_marker_id.current.value,
        'type': formReferences.type.current.value,
        'color': formReferences.color.current.value,
        'label': formReferences.label.current.value,
      })
    };

    fetch(url, requestData)
      .then(response => response.json())
      .then(data => {
        props.setPaths(current => {
          const copy = {...current};
          copy[id] = data;
          return copy;
        });

        setEditRow({
          enabled: false,
          id: null,
        });
      });
  }

  // deletes item with the id and name
  function deleteItem(id, name) {
    const del = window.confirm("Are you sure you want to delete '" + name + "'?");
    if (!del) {
      return;
    }

    const url = `${host}/locations/${props.locationId}/${resourceName}/${id}`;
    const requestData = {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    fetch(url, requestData)
      .then(response => {
        props.setPaths(current => {
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
      for (const [id, item] of Object.entries(props.paths)) {
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
      .reduceRight((chain, [id]) => {
        const url = `${host}/locations/${props.locationId}/${resourceName}/${id}`;
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
                props.setPaths(current => {
                  const copy = {...current};
                  delete copy[id];
                  return copy;
                });
                resolve();
              })
              .catch(error => {
                console.error(`Error deleting item ${id}: ${error.message}`);
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
        onClick={(e) => deleteItem(itemId, itemName)} title="Delete Item">

        <FontAwesomeIcon icon={solid('trash-can')} size="lg" style={{position: 'relative', right: '0px', top: '-1px'}}/>
      </Button>
    );
  }

  return(
    <div style={{marginTop: "20px"}}>
      <div>
        <h3 style={{textAlign: "left"}}>Map Paths</h3>
      </div>
      <Table striped bordered hover>
        <thead>
          <tr>
            <th><input type="checkbox" checked={Object.keys(checkedItems).length > 0} onChange={toggleCheckAll} /></th>
            <th>ID</th>
            <th>Device</th>
            <th>Target</th>
            <th>Type</th>
            <th>Color</th>
            <th>Label</th>
            <th>Length</th>
            <th colSpan='2'></th>
          </tr>
        </thead>
        <tbody>
          {
            Object.keys(props.paths).length > 0 ? (
              Object.entries(props.paths).map(([id, path]) => {
                return <tr>
                  <td><input type="checkbox" checked={checkedItems[id]} onChange={() => toggleCheck(id)} /></td>
                  <td>{path.id}</td>
                  <td>{path.mobile_device_id || "any"}</td>
                  <td>
                    {
                      editRow.id === id ? (
                        <select
                          title="Change Target"
                          defaultValue={path.target_marker_id}
                          ref={formReferences.target_marker_id} >
                          <option value={null}>none</option>
                          {
                            Object.entries(props.features).map(([id, feature]) => {
                              return <option value={id}>{`${id}: ${feature.name}`}</option>
                            })
                          }
                        </select>
                      ) : (
                        <td>
                          {
                            path.target_marker_id ? (
                              `${path.target_marker_id}: ${props.features[path.target_marker_id]?.name}`
                            ) : (
                              "none"
                            )
                          }
                        </td>
                      )
                    }
                  </td>
                  <td>
                    {
                      editRow.id === id ? (
                        <select
                          title="Change Type"
                          defaultValue={path.type || "navigation"}
                          ref={formReferences.type}>
                            <option value="drawing">Drawing</option>
                            <option value="navigation">Navigation</option>
                            <option value="object">Object</option>
                        </select>
                      ) : (
                        path.type
                      )
                    }
                  </td>
                  <td>
                    {
                      editRow.id === id ? (
                        <input
                          defaultValue={path.color}
                          placeholder="Edit Color"
                          type="color"
                          ref={formReferences.color} />
                      ) : (
                        <FontAwesomeIcon icon="pen" size="lg" color={path.color}/>
                      )
                    }
                  </td>
                  <td>
                    {
                      editRow.id === id ? (
                        <input
                          defaultValue={path.label}
                          placeholder="Edit Label"
                          type="text"
                          ref={formReferences.label} />
                      ) : (
                        path.label
                      )
                    }
                  </td>
                  <td>{path.points.length || 0}</td>
                  <td>
                    {
                      (editRow.id === id) ? (
                        <React.Fragment>
                          <Button
                            className={"btn-success table-btns"}
                            onClick={(e) => saveItem(e, path.id)}
                            title='Save'>
                            Save
                          </Button>
                          <Button
                            className={"btn-secondary table-btns"}
                            style={{marginLeft: 8}}
                            onClick={cancelEdit}
                            title='Cancel'>
                            Cancel
                          </Button>
                        </React.Fragment>
                      ) : (
                        <Button
                          className={"btn-primary table-btns"}
                          onClick={() => setEditRow({
                            enabled: true,
                            id: id,
                          })}
                          title='Edit'>
                          Edit
                        </Button>
                      )
                    }
                  </td>
                  <td>
                    <div>
                      <TrashIcon id={path.id} name={path.label}/>
                    </div>
                  </td>
                </tr>
              })
            ) : (
              <tr><td colspan="100%">No Map Paths</td></tr>
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

export default MapPathTable;

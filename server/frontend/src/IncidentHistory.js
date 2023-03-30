import { Form, Button, FloatingLabel, Table } from 'react-bootstrap';
import React from "react";
import { useContext, useState, useEffect } from 'react';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid, regular, brands} from '@fortawesome/fontawesome-svg-core/import.macro';
import './IncidentHistory.css';
import useStateSynchronous from './useStateSynchronous.js';
import moment from 'moment';
import { ActiveIncidentContext } from './Contexts.js';
import NewIncidentModal from './NewIncidentModal.js';


function IncidentHistory(props) {
  const host = process.env.PUBLIC_URL;

  const { activeIncident, setActiveIncident } = useContext(ActiveIncidentContext);

  const [incidents, setIncidents] = useState([]);
  const [inEditMode, setInEditMode] = useState({
    status: false,
    rowKey: null
  });

  // Only one row can be open for editing at a time. A reference is used to
  // query the value of the input field when the user clicks Save. The
  // performance is much better than using an onChange handler for every
  // key press.
  const formReferences = {
    name: React.createRef()
  }

  useEffect(() => {
    getIncidentHistory();
  }, []);

  function sort_list(arr) {
    for (let i = 0; i < arr.length; i++) {
      for (let j = 0; j < arr.length - i - 1; j++) {
        if (parseInt(arr[j + 1]['created']) < parseInt(arr[j]['created'])) {
          [arr[j + 1], arr[j]] = [arr[j], arr[j + 1]]
        }
      }
    };
    return arr;
  }

  function getIncidentHistory() {
    const requestData = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    fetch(`${host}/incidents`, requestData).then(response => {
      if (response.ok) {
        return response.json();
      }
    }).then(data => {
      var temp = sort_list(data);
      setIncidents(temp);
    });
  }

  const onSave = (index, id) => {
    // save changes to incidents
    const newName = formReferences.name.current.value;

    const requestData = {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({name: newName})
    };

    fetch(`${host}/incidents/${id}`, requestData).then(response => {
      if (response.ok) {
        onCancel(id);
        return response.json();
      }
    }).then(data => {
      setIncidents(prevIncidents => {
        let newIncidents = [];
        for (var incident of prevIncidents) {
          if (incident.id === id) {
            newIncidents.push(data);
          } else {
            newIncidents.push(incident);
          }
        }
        return newIncidents;
      });

      if (id === activeIncident?.id) {
        setActiveIncident(data);
      }
    });
  }

  // cancels incident editing
  const onCancel = (index, id) => {
    // reset the inEditMode state value
    setInEditMode({
      status: false,
      rowKey: null
    });
  }

  const onEdit = (index, id) => {
    if (inEditMode.status == true && inEditMode.rowKey != null) {
      alert("Please save or cancel edit on other incident before editing another incident");
      return;
    }

    setInEditMode({
      status: true,
      rowKey: index
    });
  }

  function deleteIncident(index, id, name) {
      const del = window.confirm("Are you sure you want to delete incident '" + name + "'?");
      if (!del) {
          return;
      }

      const url = `${host}/incidents/${id}`;
      const requestData = {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
      };

      fetch(url, requestData)
        .then(response => {
          setIncidents(prevIncidents => {
            const newIncidents = [...prevIncidents];
            delete newIncidents[index];
            return newIncidents;
          });

          // If we just deleted the active incident, we need to refresh that.
          if (id === activeIncident?.id) {
            fetch(`${process.env.PUBLIC_URL}/incidents/active`)
              .then(response => response.json())
              .then(data => setActiveIncident(data));
          }
        });
  }

  function restoreIncident(index, id) {
    const requestData = {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(incidents[index])
    };

    fetch(`${host}/incidents/active`, requestData).then(response => {
      if (response.ok) {
        return response.json();
      }
    }).then(data => {
      setActiveIncident(data);
    });
  }

  // code that creates the trash icons
  function TrashIcon(props) {
    return (
      <Button style={{width: "30px", height: "30px"}} className='btn-danger table-btns'
              onClick={(e) => deleteIncident(props.index, props.id, props.name)} title="Delete Incident">
          <FontAwesomeIcon icon={solid('trash-can')} size="lg"
                           style={{position: 'relative', right: '0px', top: '-1px'}}/>
      </Button>
    );
  }

  return (
    <div className="incident-history">
      <h3 style={{textAlign: 'center', marginBottom: '15px'}}>Incidents</h3>

      <Table striped bordered hover>
        <thead>
          <tr>
              <th>Incident ID</th>
              <th>Incident Name</th>
              <th>Date Created</th>
              <th></th>
              <th></th>
          </tr>
        </thead>
        <tbody>
          {
            incidents.map((incident, index) => {
              return <tr>
                <td>
                  <p style={{ fontWeight: (incident.id === activeIncident?.id) ? "bold" : "normal" }}>
                    {incident.id}
                  </p>
                </td>
                <td>{
                  inEditMode.status && inEditMode.rowKey === index ? (
                    <input
                      defaultValue={incident.name}
                      placeholder="Edit Incident Name"
                      name={"incidentName" + incident.id}
                      type="text"
                      ref={formReferences.name}
                      id={'incidentName' + incident.id}/>
                  ) : (
                    incident.name
                  )
                }</td>
                <td>{moment.unix(incident.created).format("MM-DD-YYYY")}</td>
                <td>
                {
                  (inEditMode.status && inEditMode.rowKey === index) ? (
                    <React.Fragment>
                      <Button
                        className={"btn-success table-btns"}
                        id={'savebtn' + incident.id}
                        onClick={(e) => onSave(index, incident.id)}
                        title='Save'>
                        Save
                      </Button>

                      <Button
                        className={"btn-secondary table-btns"}
                        style={{marginLeft: 8}}
                        onClick={(event) => onCancel(index, incident.id)}
                        title='Cancel'>
                        Cancel
                      </Button>
                    </React.Fragment>
                  ) : (
                    <Button
                      className={"btn-primary table-btns"}
                      onClick={(e) => onEdit(index, incident.id)}
                      title='Edit'>
                      Edit
                    </Button>
                  )
                }
                </td>
                <td>
                  <div>
                    <TrashIcon item='incident' index={index} id={incident.id} name={incident.name}/>
                  </div>
                </td>
                <td>
                  <div>
                    {
                      incident.id !== activeIncident?.id ? (
                        <Button className={"btn-primary table-btns"} onClick={(event) => restoreIncident(index, incident.id)}>Restore</Button>
                      ) : ('')
                    }
                  </div>
                </td>
              </tr>
            })
          }
        </tbody>
      </Table>

      <NewIncidentModal setIncidents={setIncidents} />
    </div>
  );
}

export default IncidentHistory;

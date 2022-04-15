import { Form, Button, FloatingLabel, Table } from 'react-bootstrap';
import React from "react";
import { useState, useEffect } from 'react';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid, regular, brands} from '@fortawesome/fontawesome-svg-core/import.macro';
import './IncidentHistory.css';
import useStateSynchronous from './useStateSynchronous.js';

function IncidentHistory(props){
  const host = window.location.hostname;
  const port = props.port;
  var historyData = props.historyData;

  const [inEditMode, setInEditMode] = useState({
    status: false,
    rowKey: null,
    originalValue: null,
  });

  useEffect(() => {
    props.getIncidentHistory();
  }, []);

  const onSave = (e, id) => {
    // save changes to incidents

    inEditMode.originalValue = historyData[id]['name'];

    if (id == historyData.length - 1){
      props.currentIncident.set(inEditMode.originalValue);
      props.updateIncidentInfo();
    }

    const requestData = {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({'name': inEditMode.originalValue})
    };

    fetch(`http://${host}:${port}/incidents/${historyData[id]['id']}`, requestData).then(response => {
      if (response.ok) {
        onCancel(e, id);
        return response.json();
      }
    }).then(data => {});
  }

  // cancels incident editing
  const onCancel = (e, index) => {
    historyData[index]['name'] = inEditMode.originalValue;

    // reset the inEditMode state value
    setInEditMode({
      status: false,
      rowKey: null,
      originalValue: null,
    });
  }

  const onEdit = (e, id) => {
    if (inEditMode.status == true && inEditMode.rowKey != null) {
      alert("Please save or cancel edit on other incident before editing another incident");
      return;
    }

    setInEditMode({
      status: true,
      rowKey: id,
      originalValue: historyData[id]['name']
    });
  }

  function updateIncidentName(e){
    var newHistory = [];
    var prefix = "incidentName";
    var incidentId = e.target.id.substring(prefix.length, e.target.id.length);

    for (var x in historyData) {
      if (historyData[x]['number'] == incidentId) {
        historyData[x]['name'] = e.target.value;
      }
      newHistory.push(historyData[x]);
    }
    props.setHistoryData(newHistory);
  }

  function deleteIncident(incidentNumber, incidentName) {
      const del = window.confirm("Are you sure you want to delete incident '" + incidentName + "'?");
      if (!del) {
          return;
      }

      const url = `http://${host}:${port}/incidents/${incidentNumber}`;
      const requestData = {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
      };

      fetch(url, requestData)
      .then(response => {
        props.getIncidentHistory();
        props.getMaps();
        props.getHeadsets();
        props.getCurrentIncident();
      });
  }

  function restoreIncident(incidentNumber, incidentName){
    const requestData = {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({"id": incidentNumber})
    };

    fetch(`http://${host}:${port}/incidents/active`, requestData).then(response => {
      if (response.ok) {
        props.currentIncident.set(incidentNumber);
        props.incidentName.set(incidentName);
        props.getMaps();
        props.getHeadsets();
        props.getCurrentIncident();
        props.updateIncidentInfo();
        return response.json();
      }
    }).then(data => {
    });
  }

  // code that creates the trash icons
  function TrashIcon(props) {
    const incidentNumber = props.incidentNumber;
    const incidentName = props.incidentName;

    return (
      <Button style={{width: "30px", height: "30px"}} className='btn-danger table-btns'
              onClick={(e) => deleteIncident(incidentNumber, incidentName)} title="Delete Incident">
          <FontAwesomeIcon icon={solid('trash-can')} size="lg"
                           style={{position: 'relative', right: '0px', top: '-1px'}}/>
      </Button>
    );
  }

  return (
    <div className="incident-history">
      <h3 style={{textAlign: 'center', marginBottom: '15px'}}>All Incidents</h3>
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
            historyData.map((e, index) => {
              return <tr>
                <td>{(e.id == props.currentIncident.get()) ? (e.id + ' (Current)') : (e.id)}</td>
                <td>{
                  inEditMode.status && inEditMode.rowKey === index ? (
                    <input
                      value={historyData[index]['name']}
                      placeholder="Edit Incident Name"
                      onChange={updateIncidentName}
                      name={"incidentName" + e.id}
                      type="text"
                      id={'incidentName' + e.id}/>
                  ) : (
                    e.name
                  )
                }</td>
                <td>{e.created}</td>
                <td>
                {
                  (inEditMode.status && inEditMode.rowKey === index) ? (
                    <React.Fragment>
                      <Button
                        className={"btn-success table-btns"}
                        id={'savebtn' + e.id}
                        onClick={(e) => onSave(e, index)}
                        title='Save'>
                        Save
                      </Button>

                      <Button
                        className={"btn-secondary table-btns"}
                        style={{marginLeft: 8}}
                        onClick={(event) => onCancel(event, index)}
                        title='Cancel'>
                        Cancel
                      </Button>
                    </React.Fragment>
                  ) : (
                    <Button
                      className={"btn-primary table-btns"}
                      onClick={(e) => onEdit(e, index)}
                      title='Edit'>
                      Edit
                    </Button>
                  )
                }
                </td>
                <td>
                  <div>
                    <TrashIcon item='incident' incidentNumber={e.id} incidentName={e.name}/>
                  </div>
                </td>
                <td>
                  <div>
                    {e.number != props.currentIncident.get() ? (
                      <Button className={"btn-primary table-btns"} onClick={(event) => restoreIncident(e.id, e.name)}>Restore</Button>
                    ) : ('')
                    }
                  </div>
                </td>
              </tr>
            })
          }
        </tbody>
      </Table>
    </div>
  );
}

export default IncidentHistory;

import { Form, Button, FloatingLabel, Table } from 'react-bootstrap';
import React from "react";
import { useState, useEffect } from 'react';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid, regular, brands} from '@fortawesome/fontawesome-svg-core/import.macro';

function IncidentHistory(props){
  const host = window.location.hostname;
  const port = '5000';

  const [historyData, setHistoryData] = useState([]);
  const [inEditMode, setInEditMode] = useState({
    status: false,
    rowKey: null,
    originalValue: null,
  });

  useEffect(() => {
    getIncidentHistory();
  }, []);

  if(!props.show){
    return null;
  }

  function sort_list(arr){
     for(let i = 0; i < arr.length; i++){
        for(let j = 0; j < arr.length - i - 1; j++){
            if(parseInt(arr[j + 1]['number']) < parseInt(arr[j]['number'])){
                [arr[j + 1],arr[j]] = [arr[j],arr[j + 1]]
            }
        }
    };
    console.log(arr);
    return arr;
  }

  const onSave = (e, id) => {
    // save changes to incidents

    inEditMode.originalValue = historyData[id]['name'];

    if (id == historyData.length - 1){
      props.updateCurrentIncident(inEditMode.originalValue);
    }

    const requestData = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({'name': inEditMode.originalValue})
    };

    fetch(`http://${host}:${port}/incidents/${historyData[id]['number']}`, requestData).then(response => {
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
    setHistoryData(newHistory);
  }

  function getIncidentHistory(){
    const requestData = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    };

    fetch(`http://${host}:${port}/incidents/history`, requestData).then(response => {
      if (response.ok) {
        return response.json();
      }
    }).then(data => {
      var temp_data = [];
      for (var x in data){
        temp_data.push({
          'number': data[x]['incident_number'],
          'name': data[x]['name'],
          'date_created': data[x]['created']
        });
      }
      temp_data = sort_list(temp_data);
      setHistoryData(temp_data);
    });
  }

  function hideModal(){
    props.setShow(false);
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
        getIncidentHistory();
        props.getMaps();
        props.getHeadsets();
      });
  }

  // code that creates the trash icons
  function TrashIcon(props) {
    const incidentNumber = props.incidentNumber;
    const incidentName = props.incidentName;

    return (
      <button style={{width: "30px", height: "30px"}} className='btn-danger'
              onClick={(e) => deleteIncident(incidentNumber, incidentName)} title="Delete Incident">
          <FontAwesomeIcon icon={solid('trash-can')} size="lg"
                           style={{position: 'relative', right: '1.5px', top: '-1px'}}/>
      </button>
    );
  }

  return (
    <div className="incident-history">
      <h3 style={{textAlign: 'center', marginBottom: '15px'}}>Past Incidents</h3>
      <Button variant="danger" onClick={hideModal} style={{float: 'right', position: 'relative', top: '-45px', right: '30px'}}>X</Button>
      <Table striped bordered hover>
        <thead>
          <tr>
              <th>Incident Number</th>
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
                <td>{(index == historyData.length - 1) ? (e.number + ' (Current)') : (e.number)}</td>
                <td>{
                  inEditMode.status && inEditMode.rowKey === index ? (
                    <input
                      value={historyData[index]['name']}
                      placeholder="Edit Incident Name"
                      onChange={updateIncidentName}
                      name={"incidentName" + e.number}
                      type="text"
                      id={'incidentName' + e.number}/>
                  ) : (
                    e.name
                  )
                }</td>
                <td>{e.date_created}</td>
                <td>
                {
                  (inEditMode.status && inEditMode.rowKey === index) ? (
                    <React.Fragment>
                      <button
                        className={"btn-success"}
                        id={'savebtn' + e.id}
                        onClick={(e) => onSave(e, index)}
                        title='Save'>
                        Save
                      </button>

                      <button
                        className={"btn-secondary"}
                        style={{marginLeft: 8}}
                        onClick={(event) => onCancel(event, index)}
                        title='Cancel'>
                        Cancel
                      </button>
                    </React.Fragment>
                  ) : (
                    <button
                      className={"btn-primary"}
                      onClick={(e) => onEdit(e, index)}
                      title='Edit'>
                      Edit
                    </button>
                  )
                }
                </td>
                <td>
                  <div>
                    <TrashIcon item='incident' incidentNumber={e.number} incidentName={e.name}/>
                  </div>
                </td>
              </tr>
            })
          }
        </tbody>
      </Table>
      <hr/>
    </div>
  );
}

export default IncidentHistory;

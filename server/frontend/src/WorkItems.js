import React, { useState, useEffect } from 'react';
import { Table } from 'react-bootstrap';
import './WorkItems.css';

function WorkItems(props){
  const host = window.location.hostname;
  const port = '5000';
  const[workItems, setWorkItems] = useState([]);

  useEffect(() => {
    getWorkItems();
  }, []);

  function getWorkItems(){
    const requestData = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    };

    fetch(`http://${host}:${port}/work-items`, requestData).then(response => {
      if (response.ok) {
        return response.json();
      }
    }).then(data => {
      var temp_data = [];
      for (var x in data){
        temp_data.push({
          'num': x + 1,
          'contentType': data[x]['content-type'],
          'sourceType': data[x]['source-type'],
          'status': data[x]['status'],
          'wait': data[x]['wait']
        });
      }
      setWorkItems(temp_data);
    });
  }

  return (
    <div className="WorkItems">
      <h1 className="main-header">Work Items</h1>
      <Table className="work-items-table" striped bordered hover>
        <thead>
            <tr>
              <th></th>
              <th>Content</th>
              <th>Source</th>
              <th>Status</th>
              <th>Date Created</th>
              <th>Image URL</th>
            </tr>
          </thead>
          <tbody>
            {
              (workItems.length > 0) ? (
                workItems.map((e, index) => {
                  return <tr>
                    <td>{e.num}</td>
                    <td>{e.contentType}</td>
                    <td>{e.sourceType}</td>
                    <td>{e.status}</td>
                    <td>{e.date_created}</td>
                    <td>{e.url}</td>
                  </tr>
                })
              ) : (
                <tr>
                  <td colspan="100%">No Work Items</td>
                </tr>
              )
            }
          </tbody>
      </Table>
    </div>
  );
}

export default WorkItems;
import React, { useState, useEffect } from 'react';
import { Table } from 'react-bootstrap';
import './WorkItems.css';

function WorkItems(props){

  function getWorkItems(){
    return null;
  }

  return (
    <div className="WorkItems">
      <h1 className="main-header">Work Items</h1>

      <Table className="work-items-table" striped bordered hover>
        <thead>
            <tr>
              <th>Incident Number</th>
              <th>Incident Name</th>
              <th>Date Created</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>hi</td>
              <td>hi</td>
              <td>hi</td>
            </tr>
          </tbody>
      </Table>
    </div>
  );
}

export default WorkItems;
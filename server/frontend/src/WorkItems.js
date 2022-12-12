import React, { useState, useEffect } from 'react';
import { Button, Table } from 'react-bootstrap';
import './WorkItems.css';
import {Helmet} from 'react-helmet';
import {Link} from "react-router-dom";
import moment from 'moment';

function WorkItems(props){
  const host = window.location.hostname;
  const port = props.port;
  const[workItems, setWorkItems] = useState([]);

  useEffect(() => {
    getWorkItems();
  }, []);

  const handleDeleteClicked = (id) => {
    const url = `http://${host}:${port}/photos/${id}`;
    const requestData = {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    fetch(url, requestData).then(response => {
      setWorkItems(workItems.filter(item => item.id !== id));
    });
  }

  function getWorkItems(){
    const requestData = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    };

    fetch(`http://${host}:${port}/photos`, requestData).then(response => {
      if (response.ok) {
        return response.json();
      }
    }).then(data => {
      var temp_data = [];
      for (var x in data){

        var boundaryIndex = -1;
        var maxConfidence = 0;

        if (data[x]['annotations'].length > 0) {
          for(var y in data[x]['annotations']) {
            if (data[x]['annotations'][y]?.confidence > maxConfidence) {
              boundaryIndex = y;
              maxConfidence = data[x]['annotations'][y].confidence;
            }
          }
        }

        if (boundaryIndex >= 0){
          temp_data.push({
            'id': data[x]['id'],
            'created': data[x]['created'],
            'ready': Boolean(data[x]['ready']),
            'status': data[x]['status'],
            'imageUrl': data[x]['imageUrl'],
            'contentType': data[x]['contentType'],
            'hasBoundary': true,
            'topOffset': data[x]['annotations'][boundaryIndex]['boundary']['top'],
            'leftOffset': data[x]['annotations'][boundaryIndex]['boundary']['left'],
            'divWidth': data[x]['annotations'][boundaryIndex]['boundary']['width'],
            'divHeight': data[x]['annotations'][boundaryIndex]['boundary']['height']
          });
        }else{
          temp_data.push({
            'id': data[x]['id'],
            'created': data[x]['created'],
            'ready': Boolean(data[x]['ready']),
            'status': data[x]['status'],
            'imageUrl': data[x]['imageUrl'],
            'contentType': data[x]['contentType'],
            'hasBoundary': false
          });
        }
      }

      temp_data.sort((photo1, photo2) => (photo1.created < photo2.created) ? 1 : -1);

      setWorkItems(temp_data);
    });
  }

  function Photos(props){
    var url = '';
    var full_url = props.e.imageUrl;
    if (props.e.imageUrl != null){
      if (props.e.imageUrl.includes('http')){
        url = props.e.imageUrl;
      }else{
        url = `http://${host}:${port}/photos/${props.e.id}/thumbnail`;
        full_url = `http://${host}:${port}${props.e.imageUrl}`;
      }
    }else{
      return(<p style={{color: 'black'}}>No Image Yet</p>);
    }

    if (props.e.hasBoundary == false){
      return(
        <div>
          <a target="_blank" href={full_url}>
            <img className="work-items-images" src={url} alt="Photo" />
          </a>
        </div>
      );
    }else{
      var topOffset = props.e.topOffset * 100;
      var leftOffset = props.e.leftOffset * 100;
      var divWidth = props.e.divWidth * 100;
      var divHeight = props.e.divHeight * 100;

      return(
        <div className="image-parent">
          <Link to={"/photos/" + props.e.id}>
            <img className="work-items-images" src={url} alt="Photo" />
          </Link>
          <div className='imageBorderDiv' style={{top: topOffset + "%", left: leftOffset + "%", width: divWidth + "%", height: divHeight + "%"}}></div>
        </div>
      );
    }
  }

  return (
    <div className="WorkItems">
      <Helmet>
        <title>EasyVizAR Edge - Image Processing</title>
      </Helmet>
      <h1 className="main-header">Image Processing - Work Items</h1>
      <Table className="work-items-table" striped bordered hover>
        <thead>
            <tr>
              <th>ID</th>
              <th>Date Created</th>
              <th>Content Type</th>
              <th>Status</th>
              <th>Image URL</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {
              (workItems.length > 0) ? (
                workItems.map((e, index) => {
                  return <tr>
                    <td>
                      <Link to={"/photos/" + e.id}>
                        {e.id}
                      </Link>
                    </td>
                    <td>{moment.unix(e.created).fromNow()}</td>
                    <td>{e.contentType}</td>
                    <td>{e.status}</td>
                    <td>
                      <div>
                        <Photos e={e}/>
                      </div>
                    </td>
                    <td>
                      <Button
                        variant="danger" size="sm"
                        onClick={() => handleDeleteClicked(e.id)}
                        title="Delete photo">
                        Delete
                      </Button>
                    </td>
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

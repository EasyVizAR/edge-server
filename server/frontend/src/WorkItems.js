import React, { useState, useEffect } from 'react';
import { Table } from 'react-bootstrap';
import './WorkItems.css';
import {Helmet} from 'react-helmet';
import moment from 'moment';

function WorkItems(props){
  const host = window.location.hostname;
  const port = props.port;
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

    fetch(`http://${host}:${port}/photos`, requestData).then(response => {
      if (response.ok) {
        return response.json();
      }
    }).then(data => {
      var temp_data = [];
      for (var x in data){

        var hasBoundary = -1;

        if(data[x]['annotations'].length != 0){
          for(var y in data[x]['annotations']){
            if (data[x]['annotations'][y]['boundary'] != null){
              hasBoundary = y;
            }
          }
        }

        if (hasBoundary >= 0){
          temp_data.push({
            'id': data[x]['id'],
            'created': data[x]['created'],
            'ready': Boolean(data[x]['ready']),
            'imageUrl': data[x]['imageUrl'],
            'contentType': data[x]['contentType'],
            'hasBoundary': true,
            'topOffset': data[x]['annotations'][hasBoundary]['boundary']['top'],
            'leftOffset': data[x]['annotations'][hasBoundary]['boundary']['left'],
            'divWidth': data[x]['annotations'][hasBoundary]['boundary']['width'],
            'divHeight': data[x]['annotations'][hasBoundary]['boundary']['height']
          });
        }else{
          temp_data.push({
            'id': data[x]['id'],
            'created': data[x]['created'],
            'ready': Boolean(data[x]['ready']),
            'imageUrl': data[x]['imageUrl'],
            'contentType': data[x]['contentType'],
            'hasBoundary': false
          });
        }
      }
      //temp_data.push({"annotations":[],"cameraOrientation":null,"cameraPosition":null,"contentType":"image/jpeg","created":1651072243.0537646,"createdBy":null,"height":428,"id":"0cf47f4e-62a9-4e08-8a51-7674eb566cb7","imagePath":"data/incidents/1c6a7b24-659a-4217-bef5-cc93a1d75db6/photos/0cf47f4e-62a9-4e08-8a51-7674eb566cb7/image.jpeg","imageUrl":"/photos/0cf47f4e-62a9-4e08-8a51-7674eb566cb7/image","ready":true,"retention":"auto","updated":1651072243.1504846,"width":760});
      //temp_data.push({"annotations":[],"cameraOrientation":null,"cameraPosition":null,"contentType":"image/jpeg","created":1650907000.634958,"createdBy":null,"height":null,"id":"20eea52f-c2e2-486c-a129-370421c8f615","imagePath":null,"imageUrl":"https://farm4.staticflickr.com/3458/3179638162_476fa0b548_z.jpg","ready":true,"retention":"auto","updated":1650907000.636283,"width":null});
      setWorkItems(temp_data);
      console.log(temp_data);
    });
  }

  function Photos(props){
    var url = '';
    if (props.e.imageUrl != null){
      if (props.e.imageUrl.includes('http')){
        url = props.e.imageUrl;
      }else{
        url = `http://${host}:${port}` + `${props.e.imageUrl}`;
      }
    }else{
      return(<p style={{color: 'black'}}>No Image Yet</p>);
    }

    if (props.e.hasBoundary == false){
      return(
        <div>
          <a target="_blank" href={url}>
            <img className="work-items-images" src={url} alt="Work Items Image" />
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
          <a target="_blank" href={url}>
            <img className="work-items-images" src={url} alt="Work Items Image" />
          </a>
          <div className='imageBorderDiv' style={{top: topOffset + "%", left: leftOffset + "%", width: divWidth + "%", height: divHeight + "%"}}></div>
        </div>
      );
    }
  }

  return (
    <div className="WorkItems">
      <Helmet>
        <title>Work Items</title>
      </Helmet>
      <h1 className="main-header">Work Items</h1>
      <Table className="work-items-table" striped bordered hover>
        <thead>
            <tr>
              <th>ID</th>
              <th>Date Created</th>
              <th>Content Type</th>
              <th>Ready</th>
              <th>Image URL</th>
            </tr>
          </thead>
          <tbody>
            {
              (workItems.length > 0) ? (
                workItems.map((e, index) => {
                  return <tr>
                    <td>{e.id}</td>
                    <td>{moment.unix(e.created).fromNow()}</td>
                    <td>{e.contentType}</td>
                    <td>{(e.ready) ? ('Yes') : ('No')}</td>
                    <td>
                      <div>
                        <Photos e={e}/>
                      </div>
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
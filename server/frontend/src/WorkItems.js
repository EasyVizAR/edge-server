import React, { useContext, useState, useEffect } from 'react';
import { Button, Table, Pagination } from 'react-bootstrap';
import './WorkItems.css';
import {Helmet} from 'react-helmet';
import {Link} from "react-router-dom";
import moment from 'moment';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid, regular, brands} from '@fortawesome/fontawesome-svg-core/import.macro';

import { LocationsContext } from './Contexts.js';


function WorkItems(props){
  const host = process.env.PUBLIC_URL;
  const itemsPerPage = 10;

  const { locations, setLocations } = useContext(LocationsContext);

  const [currentPage, setCurrentPage] = useState(1);
  const[workItems, setWorkItems] = useState([]);
  const [sortBy, setSortBy] = useState({
    attr: "created",
    direction: -1,
  });

  useEffect(() => {
    getWorkItems();
  }, []);

  const handleDeleteClicked = (id) => {
    const url = `${host}/photos/${id}`;
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

    fetch(`${host}/photos`, requestData).then(response => {
      if (response.ok) {
        return response.json();
      }
    }).then(data => {
      var temp_data = [];
      for (var photo of data) {
        if (photo.retention === "temporary") {
          continue;
        }

        var boundaryIndex = -1;
        var maxConfidence = 0;

        if (photo['annotations'].length > 0) {
          for(var y in photo['annotations']) {
            if (photo['annotations'][y]?.confidence > maxConfidence) {
              boundaryIndex = y;
              maxConfidence = photo['annotations'][y].confidence;
            }
          }
        }

        if (boundaryIndex >= 0) {
          photo.hasBoundary = true;
          photo.topOffset = photo['annotations'][boundaryIndex]['boundary']['top'];
          photo.leftOffset = photo['annotations'][boundaryIndex]['boundary']['left'];
          photo.divWidth = photo['annotations'][boundaryIndex]['boundary']['width'];
          photo.divHeight = photo['annotations'][boundaryIndex]['boundary']['height'];
        } else {
          photo.hasBoundary = false;
        }

        temp_data.push(photo);
      }

      temp_data.sort((photo1, photo2) => (photo1.created < photo2.created) ? 1 : -1);

      setWorkItems(temp_data);
    });
  }

  function SortByLink(props) {
    if (sortBy.attr === props.attr) {
      return (
        <Button className="column-sort" variant="link" onClick={() => setSortBy({attr: props.attr, direction: -sortBy.direction})}>
          {props.text} <FontAwesomeIcon icon={sortBy.direction > 0 ? solid('sort-up') : solid('sort-down')} />
        </Button>
      )
    } else {
      return <Button className="column-sort" variant="link" onClick={() => setSortBy({attr: props.attr, direction: 1})}>{props.text}</Button>
    }
  }

  function Photos(props){
    var url = '';
    var full_url = props.e.imageUrl;
    if (props.e.imageUrl != null){
      if (props.e.imageUrl.includes('http')){
        url = props.e.imageUrl;
      }else{
        url = `${host}/photos/${props.e.id}/thumbnail`;
        full_url = `${host}${props.e.imageUrl}`;
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

  function handlePageChange(page){
    setCurrentPage(page)
  }

  function handleSort(){
    workItems.sort((a, b) => a[sortBy.attr] > b[sortBy.attr] ? sortBy.direction : -sortBy.direction)
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return workItems.slice(startIndex, endIndex);
  }

  return (
    <div>
      <Table striped bordered hover>
        <thead>
            <tr>
              <th><SortByLink attr="id" text="Photo ID" /></th>
              <th><SortByLink attr="created" text="Created" /></th>
              <th><SortByLink attr="camera_location_id" text="Location" /></th>
              <th><SortByLink attr="status" text="Status" /></th>
              <th>Image</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {
            (handleSort().length > 0) ? (
              handleSort().map((e, index) => {
                  return <tr>
                    <td>
                      <Link to={"/photos/" + e.id}>
                        {e.id}
                      </Link>
                    </td>
                    <td>{moment.unix(e.created).fromNow()}</td>
                    <td>
                      {
                        e.camera_location_id ? (
                          <Link to={`/locations/${e.camera_location_id}`}>
                            {locations[e.camera_location_id]?.name || e.camera_location_id}
                          </Link>
                        ) : (
                          "N/A"
                        )
                      }
                    </td>
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
      <Pagination>
        {Array.from({ length: Math.ceil(workItems.length / itemsPerPage) }).map((_, index) => (
          <Pagination.Item
            key={index}
            active={index + 1 === currentPage}
            onClick={() => handlePageChange(index + 1)}
            style={{ display: "inline-block", margin: "5px" }}
          >{index + 1}

          </Pagination.Item>
        ))}
      </Pagination>
    </div>
  );
}

export default WorkItems;

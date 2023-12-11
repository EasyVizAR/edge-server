import React, { useState, useEffect } from 'react';
import { Button, Table, Pagination, Dropdown } from 'react-bootstrap';
import './WorkItems.css';
import {Helmet} from 'react-helmet';
import {Link} from "react-router-dom";
import moment from 'moment';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid, regular, brands} from '@fortawesome/fontawesome-svg-core/import.macro';

function WorkItems(props){
  const host = process.env.PUBLIC_URL;
  const itemsPerPage = 10;
  const [currentPage, setCurrentPage] = useState(1);
  const[workItems, setWorkItems] = useState([]);
  let filterWorkItems = [];
  const [sortBy, setSortBy] = useState({
    attr: "created",
    direction: -1,
  });
  const [annotations, setAnnotations] = useState([]); 
  const [finalAnnotation, setFinalAnnotation] = useState("All");

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

        if (boundaryIndex >= 0){
          temp_data.push({
            'id': photo['id'],
            'created': photo['created'],
            'ready': Boolean(photo['ready']),
            'status': photo['status'],
            'imageUrl': photo['imageUrl'],
            'contentType': photo['contentType'],
            'hasBoundary': true,
            'topOffset': photo['annotations'][boundaryIndex]['boundary']['top'],
            'leftOffset': photo['annotations'][boundaryIndex]['boundary']['left'],
            'divWidth': photo['annotations'][boundaryIndex]['boundary']['width'],
            'divHeight': photo['annotations'][boundaryIndex]['boundary']['height'],
            'annotations': photo['annotations']
          });
        }else{
          temp_data.push({
            'id': photo['id'],
            'created': photo['created'],
            'ready': Boolean(photo['ready']),
            'status': photo['status'],
            'imageUrl': photo['imageUrl'],
            'contentType': photo['contentType'],
            'hasBoundary': false
          });
        }
      }

      temp_data.sort((photo1, photo2) => (photo1.created < photo2.created) ? 1 : -1);

      setWorkItems(temp_data);
      setAnnotations(findUniqueAnnotations(temp_data));
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

  function findUniqueAnnotations(workItems) {
    const uniqueAnnotations = new Set();

    workItems.forEach((item) => {
      if (item.annotations && item.annotations.length > 0) {
        item.annotations.forEach((annotation) => {
          const annotationKey = annotation.label;
          uniqueAnnotations.add(annotationKey);
        });
      }
    });

    const uniqueAnnotationsArray = Array.from(uniqueAnnotations);
    uniqueAnnotationsArray.push('All');
    return uniqueAnnotationsArray;
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
    var filteredWorkItems;
    if(finalAnnotation == "All")
      filteredWorkItems = workItems 
    else
      filteredWorkItems = workItems.filter((element) => element.annotations.some((subElement) => subElement.label == finalAnnotation ))
    filteredWorkItems.sort((a, b) => a[sortBy.attr] > b[sortBy.attr] ? sortBy.direction : -sortBy.direction)
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    filterWorkItems = filteredWorkItems;
    return filteredWorkItems.slice(startIndex, endIndex);
  }

  const onChangeAnnotation = (annotation) => {
    setFinalAnnotation(annotation);
    handleSort();
  };

  return (
    <div className="WorkItems">
      <Helmet>
        <title>EasyVizAR Edge - Image Processing</title>
      </Helmet>
      <h1 className="main-header">Image Processing - Work Items</h1>
      <Dropdown>
      <Dropdown.Toggle variant="success" id="dropdown-basic">
        Filter
      </Dropdown.Toggle>

      <Dropdown.Menu>
      {annotations.map((annotation, index) => (
          <Dropdown.Item key={index} onClick={(event) => onChangeAnnotation(event.target.innerText)}>
            {annotation}
          </Dropdown.Item>
        ))}
      </Dropdown.Menu>
    </Dropdown>
      <Table className="work-items-table" striped bordered hover>
        <thead>
            <tr>
              <th><SortByLink attr="id" text="Photo ID" /></th>
              <th><SortByLink attr="created" text="Created" /></th>
              <th><SortByLink attr="contentType" text="Content Type" /></th>
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
      <Pagination>
        {Array.from({ length: Math.ceil(filterWorkItems.length / itemsPerPage) }).map((_, index) => (
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

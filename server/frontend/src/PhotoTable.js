import './Tables.css';
import {Badge, Container, Table, Button, Pagination, Dropdown} from 'react-bootstrap';
import React, {useContext, useState, useEffect} from 'react';
import {Link} from "react-router-dom";
import moment from 'moment';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid, regular, brands} from '@fortawesome/fontawesome-svg-core/import.macro';
import ClickToEdit from './ClickToEdit.js';
import { UsersContext } from './Contexts.js';
import './PhotoWrapper.css';

const queueOptions = {
  "detection": "Object detection",
  "identification": "Person identification",
  "done": "Done",
};


function PhotoTable(props) {
  const host = process.env.PUBLIC_URL;
  const itemsPerPage = 10;
  const [currentPage, setCurrentPage] = useState(1);
  let annotations = findUniqueAnnotations(props.photos);
  const [finalAnnotation, setFinalAnnotation] = useState("All");
  var finalFilter = [];

  const [sortBy, setSortBy] = useState({
    attr: "created",
    direction: -1,
  });

  const { users, setUsers } = useContext(UsersContext);

  function handleDeleteClicked(id) {
    const del = window.confirm(`Delete photo ${id}?`);
    if (!del) {
      return;
    }

    const url = `${host}/photos/${id}`;
    const requestData = {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    fetch(url, requestData).then(response => {
      props.setPhotos(current => {
        const copy = {...current};
        delete copy[id];
        return copy;
      });
    });
  }

  function patchPhoto(id, patch) {
    const url = `${host}/photos/${id}`;
    const requestData = {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(patch)
    };

    fetch(url, requestData)
      .then(response => response.json())
      .then(data => {
        props.setPhotos(current => {
          const copy = {...current};
          copy[id] = data;
          return copy;
        });
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

  function chooseFile(photo) {
    var alternative = null;
    for (var file of photo.files) {
      if (file.purpose === "thumbnail") {
        // First choice is thumbnail for its small size.
        return file.name;
      } else if (file.purpose === "photo") {
        // Use the full size image as an alternative.
        alternative = file.name;
      } else if (alternative == null) {
        // Otherwise, use whatever we have.
        alternative = file.name;
      }
    }

    return alternative;
  }

  function Photo(props){
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

    return(
      <div className="photo-wrapper">
        <a target="_blank" href={full_url}>
          <Link to={"/photos/" + props.e.id}>
            <img className="work-items-images" src={url} alt="Photo" />
          </Link>
          {
            props.e.annotations && props.e.annotations.length > 0 &&
              props.e.annotations.map((annotation, index) => {
                if (finalAnnotation === "All" || finalAnnotation === annotation.label) {
                  const style = {
                    left: 100 * annotation.boundary.left + "%",
                    top: 100 * annotation.boundary.top + "%",
                    width: 100 * annotation.boundary.width + "%",
                    height: 100 * annotation.boundary.height + "%",
                  };
                  return <div className="object-bounding-box" style={style}></div>
                } else {
                  return null;
                }
              })
          }
        </a>
      </div>
    );
  }

  function Detections(props) {
    const annotations = props.photo.annotations || [];
    return (
      <div class="detections">
        {
          annotations.map((item) => {
            if (item.label === "face") {
              const label = users[item.identified_user_id]?.display_name || item.sublabel || "Unknown Person";
              return <Badge className="detection" bg="primary">{label}</Badge>
            } else {
              return <Badge className="detection" bg="secondary">{item.label}</Badge>
            }
          })
        }
      </div>
    );
  }

  const onChangeAnnotation = (annotation) => {
    setFinalAnnotation(annotation);
    handleSort(props);
  };

  function handlePageChange(page){
    setCurrentPage(page)
  }

  function findUniqueAnnotations(workItems) {
    const uniqueAnnotations = new Set();

    for(const key in workItems){
      var item = workItems[key];
      if(item['annotations']){
        item['annotations'].forEach((annotation) => {uniqueAnnotations.add(annotation['label'])})
      }
    }

    const uniqueAnnotationsArray = Array.from(uniqueAnnotations);
    uniqueAnnotationsArray.push('All');
    return uniqueAnnotationsArray;
  }

  function handleSort(props){
    if(finalAnnotation == 'All'){
      var filteredWorkItems = Object.values(props.photos);
      filteredWorkItems.sort((a, b) => a[sortBy.attr] > b[sortBy.attr] ? sortBy.direction : -sortBy.direction)
      const startIndex = (currentPage - 1) * itemsPerPage;
      const endIndex = startIndex + itemsPerPage;
      finalFilter = filteredWorkItems;
      return filteredWorkItems.slice(startIndex, endIndex);
    }
    else{
      var filteredWorkItems = Object.values(props.photos).filter((item) => {
        const annotations = item.annotations || [];
        return annotations.some((annotation) => annotation.label === finalAnnotation);
      });

      filteredWorkItems.sort((a, b) => a[sortBy.attr] > b[sortBy.attr] ? sortBy.direction : -sortBy.direction)
      const startIndex = (currentPage - 1) * itemsPerPage;
      const endIndex = startIndex + itemsPerPage;
      finalFilter = filteredWorkItems;
      return filteredWorkItems.slice(startIndex, endIndex);
    }
  }

  // setAnnotations(findUniqueAnnotations(props.photos));

  return (
    <div style={{marginTop: "20px"}}>
      <div>
        <h3 style={{textAlign: "left"}}>Photos</h3>
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
      </div>
      <Table striped bordered hover>
        <thead>
          <tr>
            <th><SortByLink attr="id" text="ID" /></th>
            <th><SortByLink attr="created" text="Date Created" /></th>
            <th><SortByLink attr="queue_name" text="Queue" /></th>
            <th>Detections</th>
            <th>Image</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {
            handleSort(props).length > 0 ? (
              handleSort(props).map((e, index)  => {
                return <tr>
                    <td>
                      <Link to={"/photos/" + e.id}>
                        {e.id}
                      </Link>
                    </td>
                    <td>{moment.unix(e.created).fromNow()}</td>
                    <td>
                      <ClickToEdit tag='span' initialValue={e.queue_name}
                        placeholder='Queue Name' select={queueOptions}
                        onSave={(newValue) => patchPhoto(e.id, {queue_name: newValue})} />
                    </td>
                    <td>
                      <Detections photo={e} />
                    </td>
                    <td>
                      <div>
                        <Photo e={e}/>
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
              <tr><td colspan="100%">No photos to display.</td></tr>
            )
          }
        </tbody>
      </Table>
      <Pagination>
        {Array.from({ length: Math.ceil(finalFilter.length / itemsPerPage) }).map((_, index) => (
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

export default PhotoTable;

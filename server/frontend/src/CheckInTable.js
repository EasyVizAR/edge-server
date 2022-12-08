import './Tables.css';
import {Container, Table, Button} from 'react-bootstrap';
import React, {useState, useEffect} from 'react';
import moment from 'moment';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid, regular, brands} from '@fortawesome/fontawesome-svg-core/import.macro';

function CheckInTable(props){
  const host = window.location.hostname;
  const port = props.port;

  const [checkIns, setCheckIns] = useState([]);

  useEffect(() => {
    const url = `http://${host}:${port}/headsets/${props.headsetId}/check-ins`;
    fetch(url)
      .then(response => response.json())
      .then(data => {
        setCheckIns(data);
      })
  }, []);

  // deletes headset with the id and name
  function deleteCheckIn(index, id) {
    const del = window.confirm("This will delete all position history related to the check-in. Do you want to continue?");
    if (!del) {
      return;
    }

    const url = `http://${host}:${port}/headsets/${props.headsetId}/check-ins/${id}`;
    const requestData = {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    fetch(url, requestData)
      .then(response => response.json())
      .then(data => {
        setCheckIns(checkIns.filter(item => item.id !== id));
      })
  }

  // code that creates the trash icons
  function TrashIcon(props) {
    const itemIndex = props.index;
    const itemId = props.id;

    return (
      <Button style={{width: "30px", height: "30px"}} className='btn-danger table-btns'
        onClick={(e) => deleteCheckIn(itemIndex, itemId)} title="Delete">
        <FontAwesomeIcon icon={solid('trash-can')} size="lg" style={{position: 'relative', right: '0px', top: '-1px'}}/>
      </Button>
    );
  }

  return(
    <div style={{marginTop: "20px"}}>
      <div>
        <h3 style={{textAlign: "left"}}>Check-ins</h3>
      </div>
      <Table striped bordered hover>
        <thead>
          <tr>
            <th>ID</th>
            <th>Location</th>
            <th>Time</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {
            checkIns.map((item, index) =>
              <tr>
                <td>{item.id}</td>
                <td>{props.locations[item.location_id] ? props.locations[item.location_id]['name'] : 'Unknown'}</td>
                <td>{moment.unix(item.start_time).fromNow()}</td>
                <td>
                  <div>
                    <TrashIcon index={index} id={item.id}/>
                  </div>
                </td>
              </tr>
            )
          }
        </tbody>
      </Table>
    </div>
  );
}

export default CheckInTable;

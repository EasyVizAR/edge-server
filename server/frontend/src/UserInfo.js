import React, {useState, useEffect} from 'react';
import './UserInfo.css';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid, regular, brands} from '@fortawesome/fontawesome-svg-core/import.macro';
import {Dropdown, DropdownButton} from 'react-bootstrap';

function UserInfo(props){
  const host = window.location.hostname;
  const port = props.port;
  const [show, setShow] = useState(false);

  const showDropdown = (e)=>{
      setShow(true);
  }

  const hideDropdown = e => {
      setShow(false);
  }

  function GetUserIcon(){
    return (<FontAwesomeIcon icon={'user'} size="lg" className="iconUser" id="accountIcon"/>);
  }

  function gotoDoc(){
    window.location = `http://${host}:${port}/openapi.html`;
  }

  return (
    <div className="user-content">
      <div className="userDropDown">
        <DropdownButton align="end" onMouseEnter={showDropdown} onMouseLeave={hideDropdown}id="account-dropdown"
                        title={<GetUserIcon />} defaultValue="0" show={show}>
          <Dropdown.Item className="dropdown-item" eventKey="0">Account</Dropdown.Item>
          <Dropdown.Item className="dropdown-item" eventKey="1">Login</Dropdown.Item>
          <Dropdown.Item className="dropdown-item" eventKey="2">Logout</Dropdown.Item>
          <Dropdown.Divider />
          <Dropdown.Item as="a" target="_blank" href={`http://${host}:${port}/openapi.html`} className="dropdown-item"
                         eventKey="3">API Documentation</Dropdown.Item>
        </DropdownButton>
      </div>
    </div>
  );
}

export default UserInfo;
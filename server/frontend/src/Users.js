import { Button, Table } from 'react-bootstrap';
import React, { useContext, useState, useEffect } from 'react';
import { Link } from "react-router-dom";
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid} from '@fortawesome/fontawesome-svg-core/import.macro';
import moment from 'moment';
import { LocationsContext } from './Contexts.js';
import NewUser from './NewUser.js';


function Users(props) {
  const host = process.env.PUBLIC_URL;

  // Only one row can be open for editing at a time. A reference is used to
  // query the value of the input field when the user clicks Save. The
  // performance is much better than using an onChange handler for every
  // key press.
  const formReferences = {
    display_name: React.createRef(),
    type: React.createRef(),
    password: React.createRef(),
  }

  const [editMode, setEditMode] = useState({
    enabled: false,
    user: null,
  });
  const [users, setUsers] = useState({});

  const [sortBy, setSortBy] = useState({
    attr: "name",
    direction: -1,
  });

  useEffect(() => {
      getUsers();
  }, []);

  function getUsers() {
    fetch(`${host}/users`)
      .then(response => response.json())
      .then(data => {
        var users = {};
        for (var w of data) {
          users[w.id] = w;
        }
        setUsers(users);
      })
  }

  function saveUser(id) {
    const url = `${host}/users/${id}`;

    const requestData = {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        'display_name': formReferences.display_name.current.value,
        'type': formReferences.type.current.value,
      })
    };

    fetch(url, requestData)
      .then(response => response.json())
      .then(data => {
        setUsers(current => {
          const copy = {...current};
          copy[id] = data;
          return copy;
        });

        setEditMode({enabled: false, user: null});
      });
  }

  function savePassword(id) {
    const url = `${host}/users/${id}`;

    const requestData = {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        'password': formReferences.password.current.value,
      })
    };

    fetch(url, requestData)
      .then(response => response.json())
      .then(data => {
        setUsers(current => {
          const copy = {...current};
          copy[id] = data;
          return copy;
        });
      });
  }

  function deleteUser(id, name) {
      const del = window.confirm("Are you sure you want to delete user '" + name + "'?");
      if (!del) {
          return;
      }

      const url = `${host}/users/${id}`;
      const requestData = {
          method: 'DELETE',
          headers: {
              'Content-Type': 'application/json'
          }
      };

      fetch(url, requestData)
        .then(response => response.json())
        .then(data => {
          setUsers(current => {
            const copy = {...current};
            delete copy[id];
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

  // code that creates the trash icons
  function TrashIcon(props) {
      const itemId = props.id;
      const itemName = props.name;

      return (
          <Button style={{width: "30px", height: "30px"}} className='btn-danger table-btns'
                  onClick={(e) => deleteUser(itemId, itemName)} title="Delete User">
              <FontAwesomeIcon icon={solid('trash-can')} size="lg"
                               style={{position: 'relative', right: '0px', top: '-1px'}}/>
          </Button>
      );
  }

  return (
    <div>
      <Table striped bordered hover>
        <thead>
          <tr>
            <th><SortByLink attr="id" text="ID" /></th>
            <th><SortByLink attr="name" text="Name" /></th>
            <th><SortByLink attr="display_name" text="Display Name" /></th>
            <th><SortByLink attr="type" text="Type" /></th>
            <th><SortByLink attr="updated_time" text="Updated Time" /></th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {
            Object.keys(users).length > 0 ? (
              Object.entries(users).sort((a, b) => a[1][sortBy.attr] > b[1][sortBy.attr] ? sortBy.direction : -sortBy.direction).map(([id, user]) => {
                return <tr>
                  <td>{id}</td>
                  <td>{user.name}</td>
                  <td>                                      {
                      (editMode.user === user) ? (
                        <input
                          placeholder="Edit user display name"
                          name="input"
                          type="text"
                          defaultValue={user.display_name}
                          ref={formReferences.display_name}/>
                      ) : (
                        user.display_name
                      )
                    }
                  </td>
                  <td>
                    {
                      (editMode.user === user) ? (
                        <select
                          id="device-type-dropdown"
                          title="Change user type"
                          defaultValue={user.type}
                          ref={formReferences.type}>
                          <option value="admin">admin</option>
                          <option value="user">user</option>
                        </select>
                      ) : (
                        user.type
                      )
                    }
                  </td>
                  <td>
                    {
                      (editMode.user === user) ? (
                        <React.Fragment>
                          <input
                            placeholder="New password"
                            name="input"
                            type="password"
                            defaultValue=""
                            ref={formReferences.password} />
                          <Button
                            className={"btn-success table-btns"}
                            id={'locationsbtn' + id}
                            onClick={() => savePassword(id)}
                            title='Change password'>
                            Change
                          </Button>
                        </React.Fragment>
                      ) : (
                        moment(user.updated_time).fromNow()
                      )
                    }
                  </td>
                  <td>
                    {
                      (editMode.user === user) ? (
                        <React.Fragment>
                          <Button
                            className={"btn-success table-btns"}
                            id={'locationsbtn' + id}
                            onClick={() => saveUser(id)}
                            title='Save'>
                            Save
                          </Button>
                          <Button
                            className={"btn-secondary table-btns"}
                            style={{marginLeft: 8}}
                            onClick={() => setEditMode({enabled: false, user: null})}
                            title='Cancel'>
                            Cancel
                          </Button>
                        </React.Fragment>
                      ) : (
                        <Button
                          className={"btn-primary table-btns"}
                          onClick={() => setEditMode({enabled: true, user: user})}
                          title='Edit'>
                          Edit
                        </Button>
                      )
                    }
                  </td>
                  <td>
                    <TrashIcon item='user' id={id} name={user.name}/>
                  </td>
                </tr>
              })
            ) : (
              <tr><td colspan="100%">No users</td></tr>
            )
          }
        </tbody>
      </Table>
      <NewUser setUsers={setUsers} />
    </div>
  );
}

export default Users;

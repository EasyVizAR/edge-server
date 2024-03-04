import React, {useState, useEffect} from 'react';
import {Button} from 'react-bootstrap';
import Form from 'react-bootstrap/Form';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid, regular, brands} from '@fortawesome/fontawesome-svg-core/import.macro';

import './ClickToEdit.css';


function ClickToEdit(props) {
  const [editMode, setEditMode] = useState(false);

  const inputRef = React.createRef();

  // props
  const initialValue = props.initialValue;
  const placeholder = props.placeholder;
  const onSave = props.onSave;
  const select = props.select || false;
  const textarea = props.textarea || false;
  const Tag = props.tag || 'span'; // dynamic tag names must be capitalized

  const handleSaveClicked = () => {
    if (onSave) {
      onSave(inputRef.current.value);
    }
    setEditMode(false);
  }

  function Input(props) {
    if (textarea) {
      return (
        <Form.Control
          as="textarea"
          defaultValue={initialValue}
          placeholder={placeholder}
          ref={inputRef} />
      );
    } else if (select) {
      return (
        <select
          title={placeholder}
          defaultValue={initialValue}
          ref={inputRef}>
          {
            Object.entries(select).map(([value, name]) => {
              return <option value={value}>{name}</option>
            })
          }
        </select>
      )
    } else {
      return (
        <Form.Control
          type="text"
          defaultValue={initialValue}
          placeholder={placeholder}
          ref={inputRef} />
      );
    }
  }

  return (
    editMode ? (
      <Form>
        <Input />
        <Button
          variant="primary"
          size="sm"
          onClick={handleSaveClicked}
          title="Save">
          Save
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setEditMode(false)}
          title="Cancel">
          Cancel
        </Button>
      </Form>
    ) : (
      <Tag class="click-to-edit" onClick={() => setEditMode(true)}>
        {props.initialValue}
        <FontAwesomeIcon icon={solid('edit')} size="sm" />
      </Tag>
    )
  );
}

export default ClickToEdit;

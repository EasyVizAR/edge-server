/*
import React from "react";

function Save_Delete_Buttons(props){
  const index = props.index;
  const inEditMode = props.inEditMode;

  return(
    {
      (inEditMode.status && inEditMode.rowKey === index) ? (
        <React.Fragment>
          <button
            className={"btn-success"}
            onClick={() => onSave({id: index})}>
            Save
          </button>

          <button
            className={"btn-secondary"}
            style={{marginLeft: 8}}
            onClick={() => onCancel()}>
            Cancel
          </button>
        </React.Fragment>
      ) : (
        <button
          className={"btn-primary"}
          onClick={(e) => onEdit(e, index)}>
            Edit
        </button>
      )
    }
  );
}

export default Save_Delete_Buttons;*/

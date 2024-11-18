import {Button} from 'react-bootstrap';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {solid} from '@fortawesome/fontawesome-svg-core/import.macro';

function TrashIcon(props) {
  const host = process.env.PUBLIC_URL;

  function buttonClicked() {
    var msg = props.name ? `Delete ${props.name}?` : "Delete this item?";
    const confirmed = window.confirm(msg);
    if (!confirmed) {
      return;
    }

    const url = host + props.uri;
    const requestData = {
      method: 'DELETE'
    };

    fetch(url, requestData);
  }

  return (
    <Button style={{width: "30px", height: "30px"}} className='btn-danger table-btns'
      onClick={buttonClicked} title="Delete">
      <FontAwesomeIcon icon={solid('trash-can')} size="lg" style={{position: 'relative', right: '0px', top: '-1px'}}/>
    </Button>
  );
}

export default TrashIcon;

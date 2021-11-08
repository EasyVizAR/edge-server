import { Button, Modal } from 'react-bootstrap';
import './Popup.css';

function Popup(){

    const state = {
        show: false
    };

    return (
        <div className="Popup">
            <Modal.Dialog>
                <Modal.Header closeButton>
                    <Modal.Title>Add Feature</Modal.Title>
                </Modal.Header>

                <Modal.Body>
                    <p>Modal body text goes here.</p>
                </Modal.Body>

                <Modal.Footer>
                    <Button variant="secondary">Close</Button>
                    <Button variant="primary">Save changes</Button>
                </Modal.Footer>
            </Modal.Dialog>
        </div>
    );
}

export default Popup;
import './NewLayer.css';
import {Form, Button, FloatingLabel} from 'react-bootstrap';
import React from "react";
import {useState} from 'react';

function NewLayer(props) {
    const host = window.location.hostname;
    const port = props.port;
    const [layerName, setLayerName] = useState(null);
    const [initDummy, setInitDummy] = useState(false);

    function handleSubmit(e) {

        const new_layer = {
            name: layerName,
            dummyData: initDummy
        }

        const requestData = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(new_layer)
        };

        let url = `http://${host}:${port}/layer`;
        fetch(url, requestData)
            .then(response => response.json())
            .then(data => {
                // props.getLayers();
                props.getHeadsets();
                e.target.form.elements.formLayerName.value = ""
                props.setTab('layer-view');
            });
    }

    function updateState(e, type) {
        let val = e.target.value;
        switch (type) {
            case "layer-name":
                setLayerName(val);
                break;
            default:
                console.log('bad type');
                break;
        }
    }

    return (
        <div className="new-layer">
            <div className='new-layer-content'>
                <h2>Create Layer</h2>
                <Form onSubmit={handleSubmit} className='new-layer-form'>
                    <Form.Group style={{width: '50%', margin: 'auto', display: 'flex', flexFlow: 'column'}}
                                className="mb-3" controlId="layer-name">
                        <FloatingLabel controlId="floating-name" label="Layer Name">
                            <Form.Control type="text" placeholder="Layer Name" name="formLayerName"
                                          onChange={(e) => updateState(e, "layer-name")}/>
                        </FloatingLabel>
                        <div className='option-container'>
                            <label style={{display: 'flex', marginRight: '1%'}}>Initialize with dummy data</label>
                            <input type='checkbox' id='dummy-layer-data-checkbox' value={initDummy}
                                   onChange={(e) => setInitDummy(e.target.checked)}/>
                        </div>
                        <div className='option-container'>
                            <input type="file" name="file"/>
                        </div>
                    </Form.Group>
                    <Button variant="primary" onClick={handleSubmit}>
                        Create
                    </Button>
                </Form>
            </div>
        </div>
    );
}

export default NewLayer;
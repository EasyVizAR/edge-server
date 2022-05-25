import './NewLayer.css';
import App from './App.js';
import {Form, Button, FloatingLabel, FormText, FormControl, Dropdown, DropdownButton} from 'react-bootstrap';
import React from "react";
import {useState} from 'react';

function NewLayer(props) {
    const host = window.location.hostname;
    const port = props.port;
    const [layerName, setLayerName] = useState(null);
    const [imageMode, setImageMode] = useState('uploaded');
    const [dropdownValue, setDropdownValue] = useState('');
    const [selectedLocation, setSelectedLocation] = useState('');
    const [file, setFile] = useState('');

    const handleSubmit = (e) => {

        if ((dropdownValue === '' || file === '' || file == null)  && imageMode === 'uploaded') {
            alert("Please select in content type and file");
            return;
        } else if (layerName === '' || layerName == null) {
            alert("Please fill in layer name");
            return;
        } else if (selectedLocation === '') {
            alert("Please select location");
            return;
        }

        const new_layer = {
            name: layerName,
            contentType: dropdownValue,
            type: imageMode
        }

        const requestData = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(new_layer)
        };

        let url = `http://${host}:${port}/locations/${selectedLocation}/layers`;
        fetch(url, requestData)
            .then(response => response.json())
            .then(data => {
                const url =  `http://${host}:${port}/locations/${selectedLocation}/layers/${data.id}/image`;
                const formData = new FormData();
                formData.append('image', file);
                const config = {
                    method: 'PUT',
                    body: formData
                };
                fetch(url, config)
                    .then(response => response.json())
                    .then(data => {
                        console.log("done");
                        props.getLayers();
                        e.target.form.elements.formLayerName.value = ""
                        props.setTab('layer-view');
                    });
            });
    }

    const updateState = (e, type) => {
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

    const onFileSelect = (e) => {
        setFile(e.target.files[0])
    }

    const changeImageMode = (e) => {
        setImageMode(e.target.value);
    };

    const handleLocationSelection = (e) => {
        setSelectedLocation(e);
    }

    const onImageTypeSelection = (e) => {
        if (e === 'jpeg')
            setDropdownValue('image/jpeg');
        else if (e === 'png')
            setDropdownValue('image/png');
        else if (e === 'svg')
            setDropdownValue('image/svg+xml');
    }

    return (
        <div className="new-layer">
            <div className='new-layer-content'>
                <h2>Create Layer</h2>
                <Form onSubmit={handleSubmit} className='new-layer-form'>
                    <Form.Group style={{width: '70%', margin: 'auto', display: 'flex', flexFlow: 'column'}}
                                className="mb-3" controlId="layer-name">
                        <DropdownButton id="location-dropdown" title="Select Location" onSelect={handleLocationSelection}>
                            {
                                Object.entries(props.locations).map(([id, loc]) => {
                                    return <Dropdown.Item eventKey={id}>{loc.name}</Dropdown.Item>
                                })
                            }
                        </DropdownButton>
                        <FloatingLabel controlId="floating-name" label="Layer Name">
                            <Form.Control type="text" placeholder="Layer Name" name="formLayerName"
                                          onChange={(e) => updateState(e, "layer-name")}/>
                        </FloatingLabel>
                        <div className='radio-container'>
                            <input type='radio' value='uploaded' checked={imageMode === 'uploaded'} name='image-mode-radio' onClick={changeImageMode}/>
                            <label htmlFor="onmap" style={{paddingLeft: '1%'}}>Upload Image: </label>
                            <input type="file" name="file" disabled={!(imageMode === 'uploaded')} onChange={onFileSelect}/>
                            <DropdownButton title='Select Image Type' onSelect={onImageTypeSelection} disabled={!(imageMode === 'uploaded')}>
                                <Dropdown.Item eventKey='jpeg'>JPEG</Dropdown.Item>
                                <Dropdown.Item eventKey='svg'>SVG</Dropdown.Item>
                                <Dropdown.Item eventKey='png'>PNG</Dropdown.Item>
                            </DropdownButton>
                        </div>
                        <div className='radio-container'>
                            <input type='radio' value='external' name='image-mode-radio' onClick={changeImageMode}/>
                            <label htmlFor="onmap" style={{paddingLeft: '1%'}}>Input Image Url: </label>
                            <FormControl type="text" placeholder="Image Url"  style={{width: '50%'}} disabled={!(imageMode === 'external')}/>
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

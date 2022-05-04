import {FontAwesomeIcon} from "@fortawesome/react-fontawesome";
import React, {useEffect, useState} from "react";
import {solid} from '@fortawesome/fontawesome-svg-core/import.macro';
import "./MapContainer.css"
import {Form, FormCheck} from "react-bootstrap";

function LayerContainer(props) {
    const host = window.location.hostname;
    const port = props.port;
    const mapIconSize = 7;
    const circleSvgIconSize = 11;

    const [selectedImage, setSelectedImage] = useState('');

    const icons = {
        fire: solid('fire'),
        warning: solid('triangle-exclamation'),
        injury: solid('bandage'),
        door: solid('door-closed'),
        elevator: solid('elevator'),
        stairs: solid('stairs'),
        user: solid('user'),
        object: solid('square'),
        extinguisher: solid('fire-extinguisher'),
        message: solid('message'),
        headset: solid('headset'),
    }

    useEffect(() => {
        const imgUrl = selectedImage.split("?")[0] + "?" + Math.floor(Math.random() * 100);
        const timer = setTimeout(() => {
            if (props.cursor != 'crosshair') // trigger only if not in on Location edit mode
                setSelectedImage(imgUrl)
        }, 6e4) // 60 secs
        return () => clearTimeout(timer)
    });

    useEffect(() => {
        setSelectedImage(getMapImage());
    }, [props.selectedLayerId]);

    useEffect(() => {
        if (props.selectedLayerId == undefined || props.selectedLayerId == -1) {
            if (props.layers.length > 0)
                props.setSelectedLayerId(getDefaultLayerId());
        } else {
            props.setSelectedLayerId(-1);
        }
    }, [props.layers, props.setLayers]);

    useEffect(() => {
        const imgUrl = selectedImage.split("?")[0] + "?" + Math.floor(Math.random() * 100);
        const timer = setTimeout(() => {
            if (props.cursor != 'crosshair') // trigger only if not in on Location edit mode
                setSelectedImage(imgUrl)
        }, 6e3) // 60 secs
        return () => clearTimeout(timer)
    });

    const getMapImage = () => {
        if (props.selectedLayerId == undefined || props.selectedLayerId == -1)
            return '';
        var map = null;
        for (var i = 0; i < props.layers.length; i++) {
            if (props.layers[i].id == props.selectedLayerId) {
                map = props.layers[i];
                break;
            }
        }
        if (map == null)
            return '';

        return `http://${host}:${port}/locations/${props.selectedLocation}/layers/${props.selectedLayerId}/image`;
    }

    const getDefaultLayerId = () => {
        if (props.layers.length == 0)
            return -1;
        return props.layers[0]['id'];
    }

    const convert2Pixel = (r) => {
        var map = {};
        for (var i = 0; i < props.layers.length; i++) {
            if (props.layers[i]['id'] == props.selectedLayerId)
                map = props.layers[i];
        }
        if (Object.keys(map).length === 0 || !props.layerLoaded)
            return 0;
        const width = map['viewBox']['width'];
        return document.getElementById('map-image').offsetWidth / width * r;
    }

    const convertScaled2Vector = (px, py) => {
        var list = [];
        var map = {};
        for (var i = 0; i < props.layers.length; i++) {
            if (props.layers[i]['id'] == props.selectedLayerId)
                map = props.layers[i];
        }
        if (Object.keys(map).length === 0 || !props.layerLoaded)
            return [0, 0];

        const xmin = map['viewBox']['left'];
        const ymin = map['viewBox']['top'];
        const width = map['viewBox']['width'];
        const height = map['viewBox']['height'];
        list.push((px * width / document.getElementById('map-image').offsetWidth + xmin));
        list.push((py * height / document.getElementById('map-image').offsetHeight + ymin));

        return list;
    }

    const onMouseClick = (e) => {
        if (props.cursor != 'crosshair')
            return;

        let f = []
        for (let i in props.features) {
            f.push(props.features[i]);
        }
        if (props.clickCount > 0)
            f.pop();
        f.push({
            id: 'fire-1',
            mapId: props.selectedLayerId,
            name: 'Fire',
            positionX: convertScaled2Vector(e.clientX - e.target.getBoundingClientRect().left, e.clientY - e.target.getBoundingClientRect().top)[0],
            positionY: 0,
            positionZ: convertScaled2Vector(e.clientX - e.target.getBoundingClientRect().left, e.clientY - e.target.getBoundingClientRect().top)[1],
            scaledX: e.clientX - e.target.getBoundingClientRect().left,
            scaledY: e.clientY - e.target.getBoundingClientRect().top,
            icon: props.crossHairIcon,
            iconValue: icons[props.iconIndex].iconName,
            editing: 'true',
            placement: props.placementType
        });

        props.setFeatures(f);
        props.setPointCoordinates([convertScaled2Vector(e.clientX - e.target.getBoundingClientRect().left,
            e.clientY - e.target.getBoundingClientRect().top)[0],
            0,
            convertScaled2Vector(e.clientX - e.target.getBoundingClientRect().left,
                e.clientY - e.target.getBoundingClientRect().top)[1]]);

        props.setClickCount(props.clickCount + 1);
    }

    const onMapLoad = () => {
        if (props.selectedLayerId == -1)
            return;

        props.setLayerLoaded(true);

        fetch(`http://${host}:${port}/locations/${props.selectedLocation}/features`)
            .then(response => {
                if (response.ok) {
                    return response.json();
                }
            }).then(data => {

            let fetchedFeatures = []
            if (data == undefined || data == null || data[0] === undefined) {
                console.log(`No features data for locationId ${props.selectedLocation}`);
            } else {
                for (let i in data) {
                    let v = data[i];
                    fetchedFeatures.push({
                        'id': v.id,
                        'locationId': props.selectedLocation,
                        'name': v.name,
                        'positionX': v.position.x,
                        'positionY': v.position.y,
                        'positionZ': v.position.z,
                        'iconValue': v.type,
                        'radius': v.style.radius,
                        'placement': v.style.placement
                    });
                }
            }
            props.setFeatures(fetchedFeatures);

            fetch(`http://${host}:${port}/headsets?location_id=${props.selectedLocation}`)
                .then(response => {
                    return response.json()
                }).then(data => {
                let fetchedHeadsets = []
                for (let k in data) {
                    let v = data[k];
                      fetchedHeadsets.push({
                          'id': v.id,
                          'updated': v.updated,
                          'locationId': v.location_id,
                          'name': v.name,
                          'orientationX': v.orientation.x,
                          'orientationY': v.orientation.y,
                          'orientationZ': v.orientation.z,
                          'positionX': v.position.x,
                          'positionY': v.position.y,
                          'positionZ': v.position.z,
                          'iconValue': 'user'
                      });
                }
                props.setHeadsets(fetchedHeadsets);
            });

        });

    }

    const getCircleSvgSize = (r) => {
        return Math.max(convert2Pixel(r) * 2, document.getElementById('map-image').offsetHeight / 100.0 * circleSvgIconSize);
    }

    const getCircleSvgShift = (r) => {
        return (Math.max(convert2Pixel(r) * 2, document.getElementById('map-image').offsetHeight / 100.0 * circleSvgIconSize)
            - document.getElementById('map-image').offsetHeight / 100.0 * mapIconSize) / 2.0;
    }

    const onLayerRadioChange = (e) => {
        for (const i in props.layers) {
            if (props.layers[i].id == e.target.id) {
                props.setSelectedLayerId(props.layers[i].id);
            }
        }
    }

    return (
        <div className="map-layer-container">
            <div className="map-image-container">
                <img id="map-image" src={selectedImage} alt="Map of the environment" onLoad={onMapLoad}
                     onClick={onMouseClick} style={{cursor: props.cursor}}/>
                {props.combinedMapObjects.map((f, index) => {
                    return f.placement == 'floating' && f.editing == 'true' ?
                        <div>
                            <FontAwesomeIcon icon={icons[f.iconValue]['iconName']} className="features" id={f.id}
                                             alt={f.name} style={{
                                left: props.combinedMapObjects[index].scaledX,
                                top: props.combinedMapObjects[index].scaledY,
                                height: mapIconSize + "%",
                                pointerEvents: "none"
                            }}/>
                            <svg className="features"
                                 width={getCircleSvgSize(props.sliderValue)}
                                 height={getCircleSvgSize(props.sliderValue)}
                                 style={{
                                     left: props.combinedMapObjects[index].scaledX - getCircleSvgShift(props.sliderValue),
                                     top: props.combinedMapObjects[index].scaledY - getCircleSvgShift(props.sliderValue),
                                     pointerEvents: "none"
                                 }}>
                                <circle style={{pointerEvents: "none"}} cx={getCircleSvgSize(props.sliderValue) / 2}
                                        cy={getCircleSvgSize(props.sliderValue) / 2}
                                        r={convert2Pixel(props.sliderValue)} fill-opacity="0.3" fill="#0000FF"/>
                            </svg>
                        </div>
                        : f.placement == 'floating' ?
                            <div>
                                <FontAwesomeIcon icon={icons[f.iconValue]['iconName']} className="features" id={f.id}
                                                 alt={f.name} style={{
                                    left: props.combinedMapObjects[index].scaledX,
                                    top: props.combinedMapObjects[index].scaledY,
                                    height: mapIconSize + "%",
                                    pointerEvents: "none"
                                }}/>
                                <svg className="features"
                                     width={getCircleSvgSize(f.radius)}
                                     height={getCircleSvgSize(f.radius)}
                                     style={{
                                         left: props.combinedMapObjects[index].scaledX - getCircleSvgShift(f.radius),
                                         top: props.combinedMapObjects[index].scaledY - getCircleSvgShift(f.radius),
                                         pointerEvents: "none"
                                     }}>
                                    <circle style={{pointerEvents: "none"}} cx={getCircleSvgSize(f.radius) / 2}
                                            cy={getCircleSvgSize(f.radius) / 2}
                                            r={convert2Pixel(f.radius)} fill-opacity="0.3" fill="#0000FF"/>
                                </svg>
                            </div>
                            : <FontAwesomeIcon icon={icons[f.iconValue]['iconName']} className="features" id={f.id}
                                               alt={f.name}
                                               style={{
                                                   left: props.combinedMapObjects[index].scaledX,
                                                   top: props.combinedMapObjects[index].scaledY,
                                                   height: mapIconSize + "%",
                                                   pointerEvents: "none"
                                               }}/>
                })}
            </div>
            <Form className='layer-radio-form'>
                {props.layers.map((layer, idx) => {
                    return <FormCheck
                        name="layer-radios"
                        id={layer.id}
                        label={layer.name}
                        type="radio"
                        value={layer.name}
                        onChange={onLayerRadioChange}
                        checked={layer.id == props.selectedLayerId}
                    />
                })}
            </Form>
        </div>
    );
}


export default LayerContainer;


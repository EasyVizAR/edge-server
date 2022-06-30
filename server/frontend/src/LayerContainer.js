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
        ambulance: solid('truck-medical'),
        door: solid('door-closed'),
        elevator: solid('elevator'),
        extinguisher: solid('fire-extinguisher'),
        fire: solid('fire'),
        headset: solid('headset'),
        injury: solid('bandage'),
        message: solid('message'),
        object: solid('square'),
        stairs: solid('stairs'),
        user: solid('user'),
        warning: solid('triangle-exclamation'),
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
        if (map.viewBox == null || map.viewBox.height == 0 || map.viewBox.width == 0)
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
            id: 'undefined',
            mapId: props.selectedLayerId,
            name: '(editing in map)',
            position: {
              x: convertScaled2Vector(e.clientX - e.target.getBoundingClientRect().left, e.clientY - e.target.getBoundingClientRect().top)[0],
              y: 0,
              z: convertScaled2Vector(e.clientX - e.target.getBoundingClientRect().left, e.clientY - e.target.getBoundingClientRect().top)[1]
            },
            scaledX: e.clientX - e.target.getBoundingClientRect().left,
            scaledY: e.clientY - e.target.getBoundingClientRect().top,
            icon: props.crossHairIcon,
            type: props.iconIndex,
            editing: 'true',
            style: {
              placement: props.placementType
            }
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
                for (var f of data) {
                    fetchedFeatures.push(f);
                }
            }
            props.setFeatures(fetchedFeatures);

            fetch(`http://${host}:${port}/headsets?location_id=${props.selectedLocation}`)
                .then(response => {
                    return response.json()
                }).then(data => {
                    var headsets = {};
                    for (var h of data) {
                      headsets[h.id] = h;
                    }
                    props.setHeadsets(headsets);
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
                    return f.style?.placement == 'floating' && f.editing == 'true' ?
                        <div>
                            <FontAwesomeIcon icon={icons?.[f.type]?.['iconName'] || "bug"}
                                             className="features" id={f.id}
                                             alt={f.name} color={f.color} style={{
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
                                <FontAwesomeIcon icon={icons?.[f.type]?.['iconName'] || "bug"}
                                                 className="features" id={f.id}
                                                 alt={f.name} color={f.color} style={{
                                    left: props.combinedMapObjects[index].scaledX,
                                    top: props.combinedMapObjects[index].scaledY,
                                    height: mapIconSize + "%",
                                    pointerEvents: "none"
                                }}/>
                                <svg className="features"
                                     width={getCircleSvgSize(f.style?.radius || 1.0)}
                                     height={getCircleSvgSize(f.style?.radius || 1.0)}
                                     style={{
                                         left: props.combinedMapObjects[index].scaledX - getCircleSvgShift(f.style?.radius || 1.0),
                                         top: props.combinedMapObjects[index].scaledY - getCircleSvgShift(f.style?.radius || 1.0),
                                         pointerEvents: "none"
                                     }}>
                                    <circle style={{pointerEvents: "none"}} cx={getCircleSvgSize(f.style?.radius || 1.0) / 2}
                                            cy={getCircleSvgSize(f.style?.radius || 1.0) / 2}
                                            r={convert2Pixel(f.style.radius)} fill-opacity="0.3" fill="#0000FF"/>
                                </svg>
                            </div>
                            : <FontAwesomeIcon icon={icons?.[f.type]?.['iconName'] || "bug"}
                                               className="features" id={f.id}
                                               alt={f.name} color={f.color}
                                               style={{
                                                   left: props.combinedMapObjects[index].scaledX,
                                                   top: props.combinedMapObjects[index].scaledY,
                                                   height: mapIconSize + "%",
                                                   pointerEvents: "none"
                                               }}/>
                })}
            </div>
            <Form className='layer-radio-form'>
                <h5>Layers</h5>
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


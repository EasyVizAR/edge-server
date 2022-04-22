import {FontAwesomeIcon} from "@fortawesome/react-fontawesome";
import React from "react";
import {solid} from '@fortawesome/fontawesome-svg-core/import.macro';

function MapContainer(props) {
    const host = window.location.hostname;
    const port = props.port;
    const mapIconSize = 7;
    const circleSvgIconSize = 11;


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

    const convert2Pixel = (r) => {
        var map = {};
        for (var i = 0; i < props.maps.length; i++) {
            if (props.maps[i]['id'] == props.selectedMap)
                map = props.maps[i];
        }
        if (Object.keys(map).length === 0 || !props.mapLoaded)
            return 0;
        const width = map['viewBox'][2];
        return document.getElementById('map-image').offsetWidth / width * r;
    }

    const convertScaled2Vector = (px, py) => {
        var list = [];
        var map = {};
        for (var i = 0; i < props.maps.length; i++) {
            if (props.maps[i]['id'] == props.selectedMap)
                map = props.maps[i];
        }
        if (Object.keys(map).length === 0 || !props.mapLoaded)
            return [0, 0];

        const xmin = map['viewBox'][0];
        const ymin = map['viewBox'][1];
        const width = map['viewBox'][2];
        const height = map['viewBox'][3];
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
            mapId: props.selectedMap,
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
        if (props.selectedMap == 'NULL')
            return;

        props.setMapLoaded(true);

        fetch(`http://${host}:${port}/maps/${props.selectedMap}/features`)
            .then(response => {
                if (response.ok) {
                    return response.json();
                }
            }).then(data => {

            let fetchedFeatures = []
            if (data == undefined || data == null || data[0] === undefined) {
                console.log("NO DATA FOR MAP")
            } else {
                for (let i in data) {
                    let v = data[i];

                    fetchedFeatures.push({
                        'id': v.id,
                        'mapId': v.mapId,
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

            fetch(`http://${host}:${port}/headsets`)
                .then(response => {
                    return response.json()
                }).then(data => {
                let fetchedHeadsets = []
                for (let k in data) {
                    let v = data[k];
                    if (props.selectedMap === v.mapId) {
                        fetchedHeadsets.push({
                            'id': v.id,
                            'lastUpdate': v.lastUpdate,
                            'mapId': v.mapId,
                            'name': v.name,
                            'orientationX': v.orientation.x,
                            'orientationY': v.orientation.y,
                            'orientationZ': v.orientation.z,
                            'positionX': v.position.x,
                            'positionY': v.position.y,
                            'positionZ': v.position.z,
                            'scaledX': props.convertVector2Scaled(v.position.x, v.position.z)[0],
                            'scaledY': props.convertVector2Scaled(v.position.x, v.position.z)[1],
                            'iconValue': 'user'
                        });
                    }
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

    return (<div>
        <div className="map-image-container">
            <img id="map-image" src={props.selectedImage} alt="Map of the environment" onLoad={onMapLoad}
                 onClick={onMouseClick} style={{cursor: props.cursor}}/>
            {props.combinedMapObjects.map((f, index) => {
                return f.placement == 'floating' && f.editing == 'true'?
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
    </div>);
}


export default MapContainer;


import {FontAwesomeIcon} from "@fortawesome/react-fontawesome";
import React from "react";
import {port} from "./App";

function MapView(props) {

    const host = 'localhost';

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
            iconValue: props.iconIndex
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
        console.log(`http://${host}:${port}/maps/${props.selectedMap}/features`);
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
                        'iconValue': v.type
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

    return (
        <div className="map-image-container" style={{cursor: props.cursor}}>
            <img id="map-image" src={props.selectedImage} alt="Map of the environment" onLoad={onMapLoad}
                 onClick={onMouseClick} style={{cursor: props.cursor}}/>
            {props.combinedMapObjects.map((f, index) => {
                return f.iconValue == '' ?
                    <FontAwesomeIcon icon={props.icons[f.iconValue]['iconName']} className="features" id={f.id}
                                     alt={f.name}
                                     style={{
                                         left: props.combinedMapObjects[index].scaledX,
                                         top: props.combinedMapObjects[index].scaledY
                                     }}/>
                    : <div>
                        <FontAwesomeIcon icon={props.icons[f.iconValue]['iconName']} className="features" id={f.id}
                                         alt={f.name} style={{
                            left: props.combinedMapObjects[index].scaledX,
                            top: props.combinedMapObjects[index].scaledY
                        }}/>
                        <svg className="features" style={{
                            left: props.combinedMapObjects[index].scaledX - 20,
                            top: props.combinedMapObjects[index].scaledY - 20
                        }}>
                            <circle cx="27.5" cy="27.5" r={props.sliderValue} fill-opacity="0.3" fill="#0000FF"/>
                        </svg>
                    </div>
            })}
        </div>
    );
}

export default MapView;
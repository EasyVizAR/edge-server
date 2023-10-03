import {FontAwesomeIcon} from "@fortawesome/react-fontawesome";
import React, {useEffect, useState} from "react";
import {solid} from '@fortawesome/fontawesome-svg-core/import.macro';
import IconMap from "./Icons";
import "./LayerContainer.css"
import {Form, FormCheck} from "react-bootstrap";

function MapContainer(props) {
    const host = process.env.PUBLIC_URL;

    const mapIconSize = 7;
    const circleSvgIconSize = 11;

    const [mapShape, setMapShape] = useState({
      xmin: 0,
      ymin: 0,
      width: 0,
      height: 0,
    });
    const [thumbnailImage, setThumbnailImage] = useState(null);

    const [layers, setLayers] = useState([]);
    const [selectedLayer, setSelectedLayer] = useState(null);
    const [layerImage, setLayerImage] = useState(null);
    const [layerLoaded, setLayerLoaded] = useState(false);

    const [mapScale, setMapScale] = useState({
      x: 1,
      y: 1,
    });

    useEffect(() => {
      getLayers();
    }, []);

    useEffect(() => {
      if (selectedLayer) {
        if (selectedLayer.ready && selectedLayer.imageUrl) {
          setLayerImage(selectedLayer.imageUrl);
        } else {
          setLayerImage(`${host}${selectedLayer.imageUrl}?v=${selectedLayer.version}`);
        }
      }

      setLayerLoaded(false);

      window.addEventListener('resize', changeMapScale);

      // Clean up event handler
      return _ => {
        window.removeEventListener('resize', changeMapScale)
      }
    }, [selectedLayer]);


    const getLayers = () => {
      fetch(`${host}/locations/${props.locationId}/layers`)
        .then(response => response.json())
        .then(data => {
          var layerList = [];
          for (const key in data) {
            if (data[key].ready)
              layerList.push(data[key]);
          }
          setLayers(layerList);
          if (layerList.length > 0) {
            setSelectedLayer(layerList[0]);
          }
        });
    }


    const convert2Pixel = (r) => {
        return mapScale.x * r;
    }

    const convertScaled2Vector = (px, py) => {
        var list = [];

        const xmin = selectedLayer['viewBox']['left'];
        const ymin = selectedLayer['viewBox']['top'];
        const width = selectedLayer['viewBox']['width'];
        const height = selectedLayer['viewBox']['height'];

        list.push((px * mapScale.x + xmin));
        list.push((height - (py / mapScale.y) + ymin));

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

        const scaled = convertScaled2Vector(
          e.clientX - e.target.getBoundingClientRect().left,
          e.clientY - e.target.getBoundingClientRect().top
        );

        f.push({
            id: 'undefined',
            mapId: selectedLayer.id,
            name: '(editing in map)',
            position: {
              x: scaled[0],
              y: 0,
              z: scaled[1],
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

        props.setPointCoordinates([scaled[0], 0, scaled[1]]);
        props.setClickCount(props.clickCount + 1);
    }

    const changeMapScale = () => {
      if (layerLoaded) {
        var map_image = document.getElementById('map-image');

        setMapScale({
          x: map_image.offsetWidth / selectedLayer['viewBox']['width'],
          y: map_image.offsetHeight / selectedLayer['viewBox']['height'],
        });
      }
    }

    const onMapLoad = () => {
        setLayerLoaded(true);

        setMapShape({
          xmin: selectedLayer['viewBox']['left'],
          ymin: selectedLayer['viewBox']['top'],
          width: selectedLayer['viewBox']['width'],
          height: selectedLayer['viewBox']['height'],
        });

        changeMapScale();
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
                props.setSelectedLayer(props.layers[i].id);
                break;
            }
        }
    }

    const handleMouseOverPhoto = (ev, photo) => {
      const x = mapScale.x * (photo.camera_position.x - mapShape.xmin);
      const y = mapScale.y * (mapShape.height - (photo.camera_position.z - mapShape.ymin));

      // Bounding rect for the icon.
      // Use this to center the corner of the photo within the icon.
      const rect = ev.target.getBoundingClientRect();

      var url = photo.imageUrl;
      if (!url.startsWith('http')) {
        url = `${host}/photos/${photo.id}/thumbnail`;
      }

      setThumbnailImage({
        url: url,
        left: x + 0.5*rect.width,
        top: y + 0.5*rect.height
      })
    }

    function NavigationTarget(props) {
      const target = props.target;

      if (layerLoaded && target && props.enabled) {
        const x = mapScale.x * (target.position.x - mapShape.xmin);
        const y = mapScale.y * (mapShape.height - (target.position.z - mapShape.ymin));
        return (
            <FontAwesomeIcon icon={solid('sun')}
              className="features"
              color="#FFD700"
              style={{
                left: x,
                  top: y,
                  height: mapIconSize + "%",
                  pointerEvents: "none"
              }} />
        );
      } else {
        return null;
      }
    }

    function NavigationRoute(props) {
      const route = props.route;

      if (route && route.length >= 2 && props.enabled) {
        const points = [];
        for (var p of route) {
          const x = mapScale.x * (p.x - mapShape.xmin);
          const y = mapScale.y * (mapShape.height - (p.z - mapShape.ymin));
          points.push(`${x},${y}`);
        }

        const polyline = points.join(" ");

        return (
          <svg width={mapShape.width * mapScale.x}
               height={mapShape.height * mapScale.y}
               style={{
                 top: 0,
                 left: 0,
                 "z-index": 1,
                 position: "absolute"
               }} >
            <polyline points={polyline} style={{ fill:"none", stroke:"gray", "stroke-width":3, "stroke-dasharray":"10,10" }} />
          </svg>
        );
      } else {
        return null;
      }
    }

    return (
        <div className="container-lg map-layer-container">
          <div className="row">
            <div className="col-lg-9 map-image-container">
                <img id="map-image" src={layerImage} alt="Map of the environment" onLoad={onMapLoad}
                     onClick={onMouseClick} style={{cursor: props.cursor}}/>
                <NavigationTarget enabled={props.navigationChecked} target={props.navigationTarget} />
                <NavigationRoute enabled={props.navigationChecked} route={props.navigationRoute} />
                {
                  layerLoaded && props.showHistory && Object.keys(props.history).length > 0 &&
                    Object.entries(props.history).map(([id, item]) => {
                      const x = mapScale.x * (item.position.x - mapShape.xmin);
                      const y = mapScale.y * (mapShape.height - (item.position.z - mapShape.ymin));

                      // Get the point age in seconds, constrained to between 0 and 255-16.
                      // Then set the opacity such that older points are more transparent.
                      // Note: The -16 means the minimum opacity will be 0x10 (two digits).
                      const age = Math.max(0, Math.min(255-16, Date.now()/1000.0 - item.time));
                      const color = item.color + Math.round(255-age).toString(16);

                      return <FontAwesomeIcon icon={IconMap?.[item.type]?.['iconName'] || "bug"}
                                              className="features" id={item.id}
                                              alt={item.name}
                                              color={color}
                                              style={{
                                                  left: x,
                                                  top: y,
                                                  "z-index": 1,
                                                  height: mapIconSize + "%",
                                                  pointerEvents: "none"
                                              }}/>
                    })
                }
                {
                  layerLoaded && props.showPhotos && Object.keys(props.photos).length > 0 &&
                    Object.entries(props.photos).map(([id, item]) => {
                      if (!item.camera_position || !item.ready) {
                        return null;
                      }

                      /*
                       * 2*atan2(y, w) gives us the angle of rotation around
                       * the vertical Y axis, ie. the heading direction.  We
                       * subtract PI/2 because the arrow icon starts pointing
                       * in the positive X direction, but from the headset
                       * perspective, zero rotation points in the positive Z
                       * direction.
                       */
                      const rotation = (2 * Math.atan2(item.camera_orientation.y, item.camera_orientation.w)) - (0.5 * Math.PI);

                      const x = mapScale.x * (item.camera_position.x - mapShape.xmin);
                      const y = mapScale.y * (mapShape.height - (item.camera_position.z - mapShape.ymin));
                      const color = (item.created_by && props.headsets && props.headsets[item.created_by]) ? props.headsets[item.created_by].color : props.defaultIconColor;

                      return <div>
                        <FontAwesomeIcon icon={solid('caret-right')}
                                        className="heading"
                                        color={color}
                                        style={{
                                            left: x,
                                            top: y,
                                            height: mapIconSize + "%",
                                            pointerEvents: "none",
                                            opacity: 0.75,
                                            transform: "translate(-50%, -50%) rotate(" + rotation + "rad) translateX(100%)"
                                        }} />
                          <FontAwesomeIcon icon={IconMap['photo']['iconName']}
                                            className="features" id={"photo-" + item.id}
                                            alt="Photo taken by a headset"
                                            color={color}
                                            onMouseEnter={(e) => handleMouseOverPhoto(e, item)}
                                            onMouseLeave={() => setThumbnailImage(null)}
                                            style={{
                                                left: x,
                                                top: y,
                                                "z-index": 2,
                                                height: mapIconSize + "%"
                                            }}/>
                        </div>
                    })
                }
                {
                  layerLoaded && props.showFeatures && Object.keys(props.features).length > 0 &&
                    Object.entries(props.features).map(([id, item]) => {
                      const x = mapScale.x * (item.position.x - mapShape.xmin);
                      const y = mapScale.y * (mapShape.height - (item.position.z - mapShape.ymin));
                      if (item.style?.placement == "floating") {
                        return <div>
                                <FontAwesomeIcon icon={IconMap?.[item.type]?.['iconName'] || "bug"}
                                                 className="features" id={item.id}
                                                 alt={item.name} color={item.color} style={{
                                    left: x,
                                    top: y,
                                    "z-index": 3,
                                    height: mapIconSize + "%",
                                    pointerEvents: "none"
                                }}/>
                                <svg className="features"
                                     width={getCircleSvgSize(item.style?.radius || 1.0)}
                                     height={getCircleSvgSize(item.style?.radius || 1.0)}
                                     style={{
                                         left: x - getCircleSvgShift(item.style?.radius || 1.0),
                                         top: y - getCircleSvgShift(item.style?.radius || 1.0),
                                         "z-index": 3,
                                         pointerEvents: "none"
                                     }}>
                                    <circle style={{pointerEvents: "none"}} cx={getCircleSvgSize(item.style?.radius || 1.0) / 2}
                                            cy={getCircleSvgSize(item.style?.radius || 1.0) / 2}
                                            r={convert2Pixel(item.style.radius)} fill-opacity="0.3" fill="#0000FF"/>
                                </svg>
                            </div>
                      } else {
                        return <FontAwesomeIcon icon={IconMap?.[item.type]?.['iconName'] || "bug"}
                                                className="features" id={item.id}
                                                alt={item.name} color={item.color}
                                                style={{
                                                    left: x,
                                                    top: y,
                                                    "z-index": 4,
                                                    height: mapIconSize + "%",
                                                    pointerEvents: "none"
                                                }}/>
                      }
                    })
                }
                {
                  layerLoaded && props.showHeadsets && Object.keys(props.headsets).length > 0 &&
                    Object.entries(props.headsets).map(([id, item]) => {
                      const x = mapScale.x * (item.position.x - mapShape.xmin);
                      const y = mapScale.y * (mapShape.height - (item.position.z - mapShape.ymin));

                      /*
                       * 2*atan2(y, w) gives us the angle of rotation around
                       * the vertical Y axis, ie. the heading direction.  We
                       * subtract PI/2 because the arrow icon starts pointing
                       * in the positive X direction, but from the headset
                       * perspective, zero rotation points in the positive Z
                       * direction.
                       */
                      const rotation = (2 * Math.atan2(item.orientation.y, item.orientation.w)) - (0.5 * Math.PI);

                      return <div>
                              <FontAwesomeIcon icon={solid('caret-right')}
                                              className="heading"
                                              color={item.color}
                                              style={{
                                                  left: x,
                                                  top: y,
                                                  height: mapIconSize + "%",
                                                  pointerEvents: "none",
                                                  opacity: 0.75,
                                                  transform: "translate(-50%, -50%) rotate(" + rotation + "rad) translateX(100%)"
                                              }} />
                              <FontAwesomeIcon icon={IconMap['headset']['iconName']}
                                              className="features" id={item.id}
                                              alt={item.name} color={item.color}
                                              style={{
                                                  left: x,
                                                  top: y,
                                                  height: mapIconSize + "%",
                                                  pointerEvents: "none"
                                              }}/>
                        </div>
                    })
                }
                {
                  thumbnailImage && <img class="thumbnail-image" src={thumbnailImage.url} style={{
                    width: "33%",
                    left: thumbnailImage.left,
                    top: thumbnailImage.top,
                    pointerEvents: "none"
                  }}/>
                }
            </div>
            <div className='col-lg-3'>
              <Form className='layer-radio-form'>
                  <h5>Layers</h5>
                  {
                    layers.map((layer, idx) => {
                      return <FormCheck
                          name="layer-radios"
                          id={layer.id}
                          label={layer.name}
                          type="radio"
                          value={layer.name}
                          onChange={() => setSelectedLayer(layer)}
                          checked={layer.id === selectedLayer?.id}
                      />
                    })
                  }
              </Form>
            </div>
          </div>
        </div>
    );
}

MapContainer.defaultProps = {
  headsets: {},
  features: {},
  photos: {},
  showHeadsets: false,
  showFeatures: false,
  showPhotos: false,
  defaultIconColor: "#808080",
};

export default MapContainer;

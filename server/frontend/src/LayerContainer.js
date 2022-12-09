import {FontAwesomeIcon} from "@fortawesome/react-fontawesome";
import React, {useEffect, useState} from "react";
import {solid} from '@fortawesome/fontawesome-svg-core/import.macro';
import "./LayerContainer.css"
import {Form, FormCheck} from "react-bootstrap";

function LayerContainer(props) {
    const host = window.location.hostname;
    const port = props.port;
    const icons = props.icons;
    const mapIconSize = 7;
    const circleSvgIconSize = 11;

    const [mapShape, setMapShape] = useState({
      xmin: 0,
      ymin: 0,
      xscale: 1,
      yscale: 1
    });
    const [layerImage, setLayerImage] = useState(null);
    const [layerLoaded, setLayerLoaded] = useState(false);
    const [thumbnailImage, setThumbnailImage] = useState(null);

//    useEffect(() => {
//        const imgUrl = selectedImage.split("?")[0] + "?" + Math.floor(Math.random() * 100);
//        const timer = setTimeout(() => {
//            if (props.cursor != 'crosshair') // trigger only if not in on Location edit mode
//                setSelectedImage(imgUrl)
//        }, 6e4) // 60 secs
//        return () => clearTimeout(timer)
//    });

    useEffect(() => {
        var selectedLayerIsValid = false;
        var url = "";
        for (var layer of props.layers) {
            if (layer.id === props.selectedLayer && layer.ready) {
              if (layer.ready && layer.imageUrl) {
                if (layer.imageUrl.startsWith("http")) {
                  url = layer.imageUrl;
                } else {
                  url = `http://${host}:${port}${layer.imageUrl}?v=${layer.version}`;
                }
              }
              selectedLayerIsValid = true;
              break;
            }
        }

        if (!selectedLayerIsValid) {
            props.setSelectedLayer(getDefaultLayerId());
        }

        setLayerLoaded(false);
        setLayerImage(url);
    }, [props.layers, props.selectedLayer]);

//    useEffect(() => {
//        const imgUrl = selectedImage.split("?")[0] + "?" + Math.floor(Math.random() * 100);
//        const timer = setTimeout(() => {
//            if (props.cursor != 'crosshair') // trigger only if not in on Location edit mode
//                setSelectedImage(imgUrl)
//        }, 6e3) // 60 secs
//        return () => clearTimeout(timer)
//    });

    const getDefaultLayerId = () => {
        if (props.layers.length == 0)
            return null;
        return props.layers[0]['id'];
    }

    const convert2Pixel = (r) => {
        var map = {};
        for (var i = 0; i < props.layers.length; i++) {
            if (props.layers[i]['id'] == props.selectedLayer)
                map = props.layers[i];
        }
        if (Object.keys(map).length === 0 || !layerLoaded)
            return 0;
        const width = map['viewBox']['width'];
        return document.getElementById('map-image').offsetWidth / width * r;
    }

    const convertScaled2Vector = (px, py) => {
        var list = [];
        var map = {};
        for (var i = 0; i < props.layers.length; i++) {
            if (props.layers[i]['id'] == props.selectedLayer)
                map = props.layers[i];
        }
        if (Object.keys(map).length === 0 || !layerLoaded)
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
            mapId: props.selectedLayer,
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

        props.setPointCoordinates([convertScaled2Vector(e.clientX - e.target.getBoundingClientRect().left,
            e.clientY - e.target.getBoundingClientRect().top)[0],
            0,
            convertScaled2Vector(e.clientX - e.target.getBoundingClientRect().left,
                e.clientY - e.target.getBoundingClientRect().top)[1]]);

        props.setClickCount(props.clickCount + 1);
    }

    const onMapLoad = () => {
        var layer = null;
        for (var v of props.layers) {
          if (v.id === props.selectedLayer) {
            layer = v;
            break;
          }
        }
        if (!layer)
          return

        setLayerLoaded(true);

        setMapShape({
          xmin: layer['viewBox']['left'],
          ymin: layer['viewBox']['top'],
          xscale: document.getElementById('map-image').offsetWidth / layer['viewBox']['width'],
          yscale: document.getElementById('map-image').offsetHeight / layer['viewBox']['height']
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
                props.setSelectedLayer(props.layers[i].id);
                break;
            }
        }
    }

    const convertVector2Scaled = (x, yy) => {
      var list = [];
      var map = {};
      for (var i = 0; i < props.layers.length; i++) {
        if (props.layers[i]['id'] === props.selectedLayer)
          map = props.layers[i];
      }
      if (Object.keys(map).length === 0 || !layerLoaded)
        return [0, 0];
      const xmin = map['viewBox']['left'];
      const ymin = map['viewBox']['top'];
      const width = map['viewBox']['width'];
      const height = map['viewBox']['height'];
      list.push(document.getElementById('map-image').offsetWidth / width * (x - xmin));
      list.push(document.getElementById('map-image').offsetHeight / height * (yy - ymin));
      return list;
    }

    const handleMouseOverPhoto = (ev, photo) => {
      const x = mapShape.xscale * (photo.camera_position.x - mapShape.xmin);
      const y = mapShape.yscale * (photo.camera_position.z - mapShape.ymin);

      // Bounding rect for the icon.
      // Use this to center the corner of the photo within the icon.
      const rect = ev.target.getBoundingClientRect();

      setThumbnailImage({
        url: photo.imageUrl,
        left: x + 0.5*rect.width,
        top: y + 0.5*rect.height
      })
    }

    return (
        <div className="map-layer-container">
            <div className="map-image-container">
                <img id="map-image" src={layerImage} alt="Map of the environment" onLoad={onMapLoad}
                     onClick={onMouseClick} style={{cursor: props.cursor}}/>
                {
                  layerLoaded && props.photosChecked && Object.keys(props.photos).length > 0 &&
                    Object.entries(props.photos).map(([id, item]) => {
                      const x = mapShape.xscale * (item.camera_position.x - mapShape.xmin);
                      const y = mapShape.yscale * (item.camera_position.z - mapShape.ymin);
                      return <FontAwesomeIcon icon={icons['photo']['iconName']}
                                              className="features" id={"photo-" + item.id}
                                              alt={item.imageUrl} color="#808080"
                                              onMouseEnter={(e) => handleMouseOverPhoto(e, item)}
                                              onMouseLeave={() => setThumbnailImage(null)}
                                              style={{
                                                  left: x,
                                                  top: y,
                                                  height: mapIconSize + "%"
                                              }}/>
                    })
                }
                {
                  layerLoaded && props.featuresChecked && Object.keys(props.features).length > 0 &&
                    Object.entries(props.features).map(([id, item]) => {
                      const x = mapShape.xscale * (item.position.x - mapShape.xmin);
                      const y = mapShape.yscale * (item.position.z - mapShape.ymin);
                      if (item.style?.placement == "floating") {
                        return <div>
                                <FontAwesomeIcon icon={icons?.[item.type]?.['iconName'] || "bug"}
                                                 className="features" id={item.id}
                                                 alt={item.name} color={item.color} style={{
                                    left: x,
                                    top: y,
                                    height: mapIconSize + "%",
                                    pointerEvents: "none"
                                }}/>
                                <svg className="features"
                                     width={getCircleSvgSize(item.style?.radius || 1.0)}
                                     height={getCircleSvgSize(item.style?.radius || 1.0)}
                                     style={{
                                         left: x - getCircleSvgShift(item.style?.radius || 1.0),
                                         top: y - getCircleSvgShift(item.style?.radius || 1.0),
                                         pointerEvents: "none"
                                     }}>
                                    <circle style={{pointerEvents: "none"}} cx={getCircleSvgSize(item.style?.radius || 1.0) / 2}
                                            cy={getCircleSvgSize(item.style?.radius || 1.0) / 2}
                                            r={convert2Pixel(item.style.radius)} fill-opacity="0.3" fill="#0000FF"/>
                                </svg>
                            </div>
                      } else {
                        return <FontAwesomeIcon icon={icons?.[item.type]?.['iconName'] || "bug"}
                                                className="features" id={item.id}
                                                alt={item.name} color={item.color}
                                                style={{
                                                    left: x,
                                                    top: y,
                                                    height: mapIconSize + "%",
                                                    pointerEvents: "none"
                                                }}/>
                      }
                    })
                }
                {
                  layerLoaded && props.headsetsChecked && Object.keys(props.headsets).length > 0 &&
                    Object.entries(props.headsets).map(([id, item]) => {
                      const x = mapShape.xscale * (item.position.x - mapShape.xmin);
                      const y = mapShape.yscale * (item.position.z - mapShape.ymin);
                      return <FontAwesomeIcon icon={icons['headset']['iconName']}
                                              className="features" id={item.id}
                                              alt={item.name} color={item.color}
                                              style={{
                                                  left: x,
                                                  top: y,
                                                  height: mapIconSize + "%",
                                                  pointerEvents: "none"
                                              }}/>
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
                        checked={layer.id === props.selectedLayer}
                    />
                })}
            </Form>
        </div>
    );
}


export default LayerContainer;


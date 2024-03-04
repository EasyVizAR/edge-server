import {FontAwesomeIcon} from "@fortawesome/react-fontawesome";
import React, {useEffect, useState} from "react";
import {solid} from '@fortawesome/fontawesome-svg-core/import.macro';
import IconMap from "./Icons";
import "./MapContainer.css"
import {Form, FormCheck} from "react-bootstrap";
import {useNavigate} from 'react-router-dom';


function MapContainer(props) {
    const host = process.env.PUBLIC_URL;

    const navigate = useNavigate();

    const mapIconSize = 7;
    const circleSvgIconSize = 11;

    const [imgShape, setImgShape] = useState({
      width: 0,
      height: 0,
    });

    const [mapShape, setMapShape] = useState({
      xmin: 0,
      ymin: 0,
      width: 0,
      height: 0,
      xscale: 1,
      yscale: 1,
    });
    const [thumbnailImage, setThumbnailImage] = useState(null);

    const [layers, setLayers] = useState([]);
    const [selectedLayer, setSelectedLayer] = useState(null);
    const [layerImage, setLayerImage] = useState(null);
    const [layerLoaded, setLayerLoaded] = useState(false);

    useEffect(() => {
      window.addEventListener('resize', handleWindowResize);

      // Clean up event handler
      return _ => {
        window.removeEventListener('resize', handleWindowResize);
      }
    }, []);

    useEffect(() => {
      // The parent component can set layers as a prop and update them.
      // This will lead to the map refreshing as the layers change.
      // On the other hand, if the parent did not pass the layers, we
      // will just load the map image once.
      if (props.layers === null) {
        getLayers();
      } else {
        setLayers(props.layers);
      }
    }, [props.layers, props.locationId]);

    useEffect(() => {
      var found = false;
      if (selectedLayer) {
        for (var layer of layers) {
          if (selectedLayer.id === layer.id) {
            setSelectedLayer(layer);
            found = true;
            break;
          }
        }
      }

      if (!found && layers.length > 0) {
        setSelectedLayer(layers[0]);
      }
    }, [layers]);

    useEffect(() => {
      if (selectedLayer && selectedLayer.ready) {
        setLayerImage(`${host}${selectedLayer.imageUrl}?v=${selectedLayer.version}`);
      }
    }, [selectedLayer]);

    useEffect(() => {
      if (selectedLayer) {
        setMapShape({
          xmin: selectedLayer['viewBox']['left'],
          ymin: selectedLayer['viewBox']['top'],
          width: selectedLayer['viewBox']['width'],
          height: selectedLayer['viewBox']['height'],
          xscale: imgShape.width / selectedLayer['viewBox']['width'],
          yscale: imgShape.height / selectedLayer['viewBox']['height'],
        });
      }
    }, [selectedLayer, imgShape]);

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
        });
    }

    const handleWindowResize = () => {
      const map_image = document.getElementById('map-image');

      if (map_image) {
        setImgShape({
          width: map_image.offsetWidth,
          height: map_image.offsetHeight,
        });
      }
    }

    const onMapLoad = () => {
        setLayerLoaded(true);

        var map_image = document.getElementById('map-image');

        if (map_image) {
          setImgShape({
            width: map_image.offsetWidth,
            height: map_image.offsetHeight,
          });
        }
    }

    const convert2Pixel = (r) => {
        return mapShape.xscale * r;
    }

    const convertScaled2Vector = (px, py) => {
        var list = [];

        const xmin = selectedLayer['viewBox']['left'];
        const ymin = selectedLayer['viewBox']['top'];
        const width = selectedLayer['viewBox']['width'];
        const height = selectedLayer['viewBox']['height'];

        list.push((px / mapShape.xscale + xmin));
        list.push((height - (py / mapShape.yscale) + ymin));

        return list;
    }

    const onMouseClick = (e) => {
        if (props.cursor != 'crosshair')
            return;

        // Get a valid y-value based on the selected map layer.
        // This allows us to place features roughly on different floors of a building.
        const y = selectedLayer.reference_height || selectedLayer.cutting_height || 0;

        const scaled = convertScaled2Vector(
          e.clientX - e.target.getBoundingClientRect().left,
          e.clientY - e.target.getBoundingClientRect().top
        );

//        f.push({
//            id: 'undefined',
//            mapId: selectedLayer.id,
//            name: '(editing in map)',
//            position: {
//              x: scaled[0],
//              y: y,
//              z: scaled[1],
//            },
//            scaledX: e.clientX - e.target.getBoundingClientRect().left,
//            scaledY: e.clientY - e.target.getBoundingClientRect().top,
//            icon: props.crossHairIcon,
//            type: props.iconIndex,
//            editing: 'true',
//            style: {
//              placement: props.placementType
//            }
//        });

        props.setPointCoordinates([scaled[0], y, scaled[1]]);
    }

    const getCircleSvgSize = (r) => {
        return Math.max(convert2Pixel(r) * 2, document.getElementById('map-image').offsetHeight / 100.0 * circleSvgIconSize);
    }

    const getCircleSvgShift = (r) => {
        return (Math.max(convert2Pixel(r) * 2, document.getElementById('map-image').offsetHeight / 100.0 * circleSvgIconSize)
            - document.getElementById('map-image').offsetHeight / 100.0 * mapIconSize) / 2.0;
    }

    const handleMouseOverPhoto = (ev, photo) => {
      const x = mapShape.xscale * (photo.camera_position.x - mapShape.xmin);
      const y = mapShape.yscale * (mapShape.height - (photo.camera_position.z - mapShape.ymin));

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

      if (layerLoaded && target && target.position && props.enabled) {
        const x = mapShape.xscale * (target.position.x - mapShape.xmin);
        const y = mapShape.yscale * (mapShape.height - (target.position.z - mapShape.ymin));
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
          const x = mapShape.xscale * (p.x - mapShape.xmin);
          const y = mapShape.yscale * (mapShape.height - (p.z - mapShape.ymin));
          points.push(`${x},${y}`);
        }

        const polyline = points.join(" ");

        return (
          <svg width={mapShape.width * mapShape.xscale}
               height={mapShape.height * mapShape.yscale}
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

    function MapMarker(props) {
      const icon = IconMap?.[props.type]?.['iconName'] || "bug"
      
      const x = props.mapShape.xscale * (props.position.x - props.mapShape.xmin);
      const y = props.mapShape.yscale * (props.mapShape.height - (props.position.z - props.mapShape.ymin));

      const rotation = () => {
        return (2 * Math.atan2(props.orientation.y, props.orientation.w)) - (0.5 * Math.PI);
      }

      const pointerEvents = (props.onClick || props.onMouseEnter || props.onMouseLeave) ? "auto" : "none";

      return (
        <React.Fragment>
        {
          props.orientation ? (
            /*
             * 2*atan2(y, w) gives us the angle of rotation around
             * the vertical Y axis, ie. the heading direction.  We
             * subtract PI/2 because the arrow icon starts pointing
             * in the positive X direction, but from the headset
             * perspective, zero rotation points in the positive Z
             * direction.
             */
            <FontAwesomeIcon
              icon={solid('caret-right')}
              className="heading"
              color={props.color}
              style={{
                left: x,
                top: y,
                height: mapIconSize + "%",
                pointerEvents: "none",
                opacity: 0.75,
                transform: "translate(-50%, -50%) rotate(" + rotation() + "rad) translateX(100%)"
              }} />
          ) : (
            null
          )
        }
        <FontAwesomeIcon
          icon={icon}
          className="features"
          alt={props.name}
          color={props.color}
          onClick={props.onClick}
          onMouseEnter={props.onMouseEnter}
          onMouseLeave={props.onMouseLeave}
          style={{
            left: x,
            top: y,
            height: mapIconSize + "%",
            "z-index": props.priority || 1,
            pointerEvents: pointerEvents,
          }} />
        </React.Fragment>
      )
    }

    return (
        <div className="map-layer-container">
          <div className="row">
            <div className="col-lg-8 map-image-container">
                <img id="map-image" src={layerImage} alt="Map of the environment" onLoad={onMapLoad}
                     onClick={onMouseClick} style={{cursor: props.cursor}}/>
                <NavigationTarget enabled={props.showNavigation} target={props.navigationTarget} />
                <NavigationRoute enabled={props.showNavigation} route={props.navigationRoute} />
                {
                  layerLoaded && props.showHistory && Object.keys(props.history).length > 0 &&
                    Object.entries(props.history).map(([id, item]) => {
                      // Get the point age in seconds, constrained to between 0 and 255-16.
                      // Then set the opacity such that older points are more transparent.
                      // Note: The -16 means the minimum opacity will be 0x10 (two digits).
                      const age = Math.max(0, Math.min(255-16, Date.now()/1000.0 - item.time));
                      const color = item.color + Math.round(255-age).toString(16);

                      return <MapMarker
                              type={item.type}
                              name={item.name}
                              color={color}
                              position={item.position}
                              priority={1}
                              mapShape={mapShape} />
                    })
                }
                {
                  layerLoaded && props.showPhotos && Object.keys(props.photos).length > 0 &&
                    Object.entries(props.photos).map(([id, item]) => {
                      if (!item.camera_position || !item.ready) {
                        return null;
                      }

                      const color = (item.created_by && props.headsets && props.headsets[item.created_by]) ? props.headsets[item.created_by].color : props.defaultIconColor;

                      return <MapMarker
                              type="photo"
                              name="photo"
                              color={color}
                              position={item.camera_position}
                              orientation={item.camera_orientation}
                              priority={2}
                              onClick={() => navigate(`/photos/${item.id}`)}
                              onMouseEnter={(e) => handleMouseOverPhoto(e, item)}
                              onMouseLeave={() => setThumbnailImage(null)}
                              mapShape={mapShape} />
                    })
                }
                {
                  layerLoaded && props.showFeatures && Object.keys(props.features).length > 0 &&
                    Object.entries(props.features).map(([id, item]) => {
                      const x = mapShape.xscale * (item.position.x - mapShape.xmin);
                      const y = mapShape.yscale * (mapShape.height - (item.position.z - mapShape.ymin));
                      if (item.style?.placement == "floating") {
                        return <div>
                          <MapMarker
                            type={item.type}
                            name={item.name}
                            color={item.color}
                            position={item.position}
                            priority={3}
                            mapShape={mapShape} />
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
                      return <MapMarker
                              type={item.type}
                              name={item.name}
                              color={item.color}
                              position={item.position}
                              orientation={item.orientation}
                              priority={4}
                              mapShape={mapShape} />
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
            <div className='col-lg-4'>
              <h5>Map Layers</h5>
              <div class="list-group" id="list-layers">
                {
                  layers.map((layer, idx) => {
                    return <a
                      className={
                        layer.id === selectedLayer?.id ? (
                          "list-group-item list-group-item-action active"
                        ) : (
                          "list-group-item list-group-item-action"
                        )}
                      onClick={() => setSelectedLayer(layer)}
                      aria-controls={layer.name}>
                        {layer.name}
                    </a>
                  })
                }
              </div>
            </div>
          </div>
        </div>
    );
}

MapContainer.defaultProps = {
  layers: null,
  headsets: {},
  features: {},
  photos: {},
  navigationTarget: {},
  navigationRoute: [],
  showHeadsets: false,
  showFeatures: false,
  showPhotos: false,
  showNavigation: false,
  defaultIconColor: "#808080",
};

export default MapContainer;

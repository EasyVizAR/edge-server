import { useEffect, createContext, useRef } from "react";

import moment from 'moment';
import mqtt from "mqtt";
import { load } from "protobufjs";


const MQTTContext = createContext()


// Convert long form UUI to short form for MQTT topics.
function uuid_long_to_short(s) {
  return s.replaceAll('-', '');
}

// Convert short form UUID to long form for presentation.
function uuid_short_to_long(s) {
  const parts = [s.slice(0, 8), s.slice(8, 12), s.slice(12, 16), s.slice(16, 20), s.slice(20)];
  return parts.join("-");
}

// Convert an enum string value to a locally-used string, e.g. (DEVICE_HEADSET -> headset).
function enum_to_string(s, prefix) {
  return s.slice(prefix.length + 1).replaceAll("_", "-").toLowerCase();
}


function MQTTProvider({ children }) {
  const client = useRef(null)
  const channels = useRef({}) // map each channel to the callback
  const messages = useRef({})


  /* called from a component that registers a callback for a channel */
  // channels:
  // - devices
  // - layers
  // - markers
  // - paths
  // - photos
  // - pose
  const subscribe = (channel, location_id, callback) => {
    var topic;
    if (channel === "pose") {
      topic = `locations/${uuid_long_to_short(location_id)}/devices/+/pose`;
    } else {
      topic = `locations/${uuid_long_to_short(location_id)}/${channel}/+`;
    }
    channels.current[channel] = callback;
    if (client.current) {
      client.current.subscribe(topic);
    }
  }

  /* remove callback  */
  const unsubscribe = (channel, location_id) => {
    var topic;
    if (channel === "pose") {
      topic = `locations/${uuid_long_to_short(location_id)}/devices/+/pose`;
    } else {
      topic = `locations/${uuid_long_to_short(location_id)}/${channel}/+`;
    }
    if (client.current) {
      client.current.unsubscribe(topic);
    }
    delete channels.current[channel];
  }

  useEffect(() => {
    load("messages.proto", function(err, root) {
      messages.current.DevicePose = root.lookupType("EasyVizAR.DevicePose");
      messages.current.DeviceType = root.lookupEnum("EasyVizAR.DeviceType");
      messages.current.Layer = root.lookupType("EasyVizAR.Layer");
      messages.current.LayerType = root.lookupEnum("EasyVizAR.LayerType");
      messages.current.MapMarker = root.lookupType("EasyVizAR.MapMarker");
      messages.current.MapPath = root.lookupType("EasyVizAR.MapPath");
      messages.current.MarkerType = root.lookupEnum("EasyVizAR.MarkerType");
      messages.current.MobileDevice = root.lookupType("EasyVizAR.MobileDevice");
      messages.current.PathType = root.lookupEnum("EasyVizAR.PathType");
    });

    client.current = mqtt.connect({
      host: window.location.hostname,
      port: (window.location.protocol === "https:") ? 8883 : 8083,
      protocol: (window.location.protocol === "https:") ? 'wss' : 'ws',
      path:  '/mqtt',
      username: 'frontend',
      password: 'vaoLahJush2eezii',
    });

    client.current.on("connect", () => {

    });

    client.current.on("message", (topic, message) => {
      const topic_parts = topic.split("/");
      const meta = {};

      if (topic_parts.length == 5 && topic_parts[4] == "pose") {
        meta.channel = "pose";
        meta.location_id = uuid_short_to_long(topic_parts[1]);
      } else if (topic_parts.length == 4 && topic_parts[0] == "locations") {
        meta.channel = topic_parts[2];
        meta.location_id = uuid_short_to_long(topic_parts[1]);
      } else {
        console.log(`Warning: message received on unrecognized topic ${topic}`);
        return;
      }

      var updated_object;
      switch (meta.channel) {
        case "devices":
          updated_object = messages.current.MobileDevice.decode(message);
          meta.deleted = updated_object.type === 0;
          updated_object.id = uuid_short_to_long(topic_parts[3]);
          updated_object.type = enum_to_string(messages.current.DeviceType.valuesById[updated_object.type], "DEVICE");
          break;

        case "layers":
          updated_object = messages.current.Layer.decode(message);
          meta.deleted = updated_object.type === 0;
          updated_object.id = topic_parts[3];
          updated_object.type = enum_to_string(messages.current.LayerType.valuesById[updated_object.type], "LAYER");
          break;

        case "markers":
          updated_object = messages.current.MapMarker.decode(message);
          meta.deleted = updated_object.type === 0;
          updated_object.id = topic_parts[3];
          updated_object.type = enum_to_string(messages.current.MarkerType.valuesById[updated_object.type], "MARKER");
          updated_object.enabled = updated_object.enabled || false; // explicitly set because protobuf omits false booleans
          break;

        case "paths":
          updated_object = messages.current.MapPath.decode(message);
          meta.deleted = updated_object.type === 0;
          updated_object.id = topic_parts[3];
          updated_object.type = enum_to_string(messages.current.PathType.valuesById[updated_object.type], "PATH");
          break;

        case "pose":
          updated_object = messages.current.DevicePose.decode(message);
          meta.deleted = false;
          updated_object.device_id = uuid_short_to_long(topic_parts[3]);
          break;
      }
      updated_object.updated = moment().unix();

      if (channels.current[meta.channel]) {
        channels.current[meta.channel](updated_object, meta)
      }
    });

    return () => { client.current.end() }
  }, [])

  /* subscribe and unsubscribe are the only required prop for the context */
  return (
    <MQTTContext.Provider value={[subscribe, unsubscribe]}>
      {children}
    </MQTTContext.Provider>
  )
}

export { MQTTContext, MQTTProvider }

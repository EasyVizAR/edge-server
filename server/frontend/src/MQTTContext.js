import { useEffect, createContext, useRef } from "react";

import mqtt from "mqtt";
import { load } from "protobufjs";


const MQTTContext = createContext()


function MQTTProvider({ children }) {
  const client = useRef(null)
  const channels = useRef({}) // map each channel to the callback
  const messages = useRef({})


  /* called from a component that registers a callback for a channel */
  const subscribe = (channel, topic, callback) => {
    channels.current[channel] = callback;
    if (client.current) {
      client.current.subscribe(topic);
    }
  }

  /* remove callback  */
  const unsubscribe = (channel, topic) => {
    if (client.current) {
      client.current.unsubscribe(topic);
    }
    delete channels.current[channel];
  }

  useEffect(() => {
    load("messages.proto", function(err, root) {
      messages.current.Pose = root.lookupType("EasyVizAR.Pose");
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
      console.log(topic);

      const topic_parts = topic.split("/");

      if (topic_parts[0] == "locations" && topic_parts[2] == "devices" && topic_parts[4] == "pose") {
        const meta = {
          location_id: topic_parts[1],
          device_id: topic_parts[3],
        };
        const pose = messages.current.Pose.decode(message);
        if (channels.current.pose) {
          channels.current.pose(pose, meta);
        }
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

/*
 * Source: https://blog.stackademic.com/websockets-and-react-wscontext-and-components-subscription-pattern-4e580fc67bb5
 */

import { useEffect, createContext, useRef } from "react";

import ReconnectingWebSocket from './ReconnectingWebSocket.js';


const WebSocketContext = createContext()

function WebSocketProvider({ children }) {
  const ws = useRef(null)
  const channels = useRef({}) // maps each channel to the callback

  /* called from a component that registers a callback for a channel */
  const subscribe = (event, uri, callback) => {
    channels.current[event] = callback;
    if (ws.current) {
      ws.current.send(`subscribe ${event} ${uri}`);
    }
  }
  /* remove callback  */
  const unsubscribe = (event, uri) => {
    if (ws.current) {
      ws.current.send(`unsubscribe ${event} ${uri}`);
    }
    delete channels.current[event];
  }

  useEffect(() => {
    if (window.location.protocol === "https:") {
      ws.current = new ReconnectingWebSocket(`wss://${window.location.host}/ws`, "json-v2");
    } else {
      ws.current = new ReconnectingWebSocket(`ws://${window.location.host}/ws`, "json-v2");
    }

    ws.current.connect();

    /* WS initialization and cleanup */
    ws.current.onopen = () => {
      for (const [event, callback] of Object.entries(channels.current)) {
        ws.current.send(`subscribe ${event} *`);
      }
    }
    ws.current.onclose = () => { console.log('WS close') }

    ws.current.onmessage = (message) => {
      const { _meta, ...data } = JSON.parse(message.data);
      const { event, uri } = _meta;

      if (channels.current[event]) {
        channels.current[event](event, uri, data);
      }
    }

    return () => { ws.current.close() }
  }, [])

  /* WS provider dom */
  /* subscribe and unsubscribe are the only required prop for the context */
  return (
    <WebSocketContext.Provider value={[subscribe, unsubscribe]}>
      {children}
    </WebSocketContext.Provider>
  )
}

export { WebSocketContext, WebSocketProvider }

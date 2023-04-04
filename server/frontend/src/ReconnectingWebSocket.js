export default class ReconnectingWebSocket {
  constructor(url) {
    this.url = url;

    this.onopen = null;
    this.onmessage = null;

    this.ws = null;
  }

  connect() {
    this.ping_interval = null;
    this.ping_timeout = null;

    this.ws = new WebSocket(this.url);

    const that = this;

    this.ws.onclose = (event) => {
      that.ws = null;
      clearInterval(that.ping_interval);
      setTimeout(that.connect.bind(that), 1000);
    };

    this.ws.onerror = (event) => {
      that.ws.close();
    };

    this.ws.onopen = (event) => {
      that.ping_interval = setInterval(() => {
        if (!that.ping_timeout) {
          that.ws.send("ping");
          that.ping_timeout = setTimeout(() => {
            that.ws.close();
          }, 5000);
        }
      }, 15000);

      if (that.onopen) {
        that.onopen(event);
      }
    };

    this.ws.onmessage = (event) => {
      if (event.data === "pong") {
        if (that.ping_timeout) {
          clearTimeout(that.ping_timeout);
          that.ping_timeout = null;
        }
        return;
      }

      if (that.onmessage) {
        that.onmessage(event);
      }
    };
  }

  send(data) {
    if (this.ws && this.ws.readyState === 1) {
      return this.ws.send(data);
    }
  }
}

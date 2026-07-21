/**
 * Reconnecting WebSocket client for the /ws/telemetry stream.
 *
 * Usage:
 *   const client = new TelemetryClient({ onSample: (s) => ... });
 *   client.connect();
 *   ...
 *   client.disconnect();
 */

export const WS_URL = (typeof window !== 'undefined' && window.electronAPI?.getWsUrl)
  ? window.electronAPI.getWsUrl()
  : 'ws://127.0.0.1:8472/ws/telemetry';

const INITIAL_BACKOFF_MS = 1000;
const MAX_BACKOFF_MS = 15000;

export class TelemetryClient {
  constructor({ onSample, onStatus, onOpen, onClose, url = WS_URL } = {}) {
    this.url = url;
    this.onSample = onSample;
    this.onStatus = onStatus;
    this.onOpen = onOpen;
    this.onClose = onClose;
    this.ws = null;
    this.backoff = INITIAL_BACKOFF_MS;
    this.closedByUser = false;
    this.reconnectTimer = null;
  }

  connect() {
    this.closedByUser = false;
    this.open();
  }

  open() {
    try {
      this.ws = new WebSocket(this.url);
    } catch (e) {
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this.backoff = INITIAL_BACKOFF_MS;
      this.onOpen?.();
    };

    this.ws.onmessage = (event) => {
      let msg;
      try {
        msg = JSON.parse(event.data);
      } catch {
        return;
      }
      if (msg.type === 'telemetry') this.onSample?.(msg);
      else if (msg.type === 'status') this.onStatus?.(msg.data);
    };

    this.ws.onclose = () => {
      this.onClose?.();
      if (!this.closedByUser) this.scheduleReconnect();
    };

    this.ws.onerror = () => {
      // onclose fires afterwards and drives the reconnect
    };
  }

  scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (!this.closedByUser) this.open();
    }, this.backoff);
    this.backoff = Math.min(this.backoff * 2, MAX_BACKOFF_MS);
  }

  send(payload) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload));
    }
  }

  ping() {
    this.send({ action: 'ping' });
  }

  requestStatus() {
    this.send({ action: 'get_status' });
  }

  disconnect() {
    this.closedByUser = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close();
    this.ws = null;
  }
}

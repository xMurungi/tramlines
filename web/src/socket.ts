// The live wire from the server (ADR-0005): one WebSocket, JSON messages, reconnect on loss.
// The viewer sends two kinds of message back: which knowledge setting it wants (ADR-0042),
// and a request for the free-will fan at a moment (ADR-XXXX).

import type { Choose, FreeWill, Message } from "./model";

export interface Wire {
  send(message: Choose | FreeWill): void;
}

export function connect(onMessage: (message: Message) => void, onState: (open: boolean) => void): Wire {
  let ws: WebSocket;
  const open = () => {
    const url = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/stream`;
    ws = new WebSocket(url);
    ws.onopen = () => onState(true);
    ws.onmessage = (event) => onMessage(JSON.parse(String(event.data)) as Message);
    ws.onclose = () => {
      onState(false);
      setTimeout(open, 2000);
    };
  };
  open();
  return {
    send(message) {
      if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(message));
    },
  };
}

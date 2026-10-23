// The live wire from the server (ADR-0005): one WebSocket, JSON messages, reconnect on loss.

import type { Message } from "./model";

export function connect(onMessage: (message: Message) => void, onState: (open: boolean) => void): void {
  const url = `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/stream`;
  const ws = new WebSocket(url);
  ws.onopen = () => onState(true);
  ws.onmessage = (event) => onMessage(JSON.parse(String(event.data)) as Message);
  ws.onclose = () => {
    onState(false);
    setTimeout(() => connect(onMessage, onState), 2000);
  };
}

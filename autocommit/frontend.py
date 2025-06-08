import http.server
import socketserver
import threading
import asyncio
import websockets

from pydantic import BaseModel

class FrontendData(BaseModel):
    path: str
    log: str

class FrontendServer:
    def __init__(self, host='localhost', port=8000, ws_port=8765):
        self.host = host
        self.port = port
        self.ws_port = ws_port
        self.clients = set()
        self.loop = asyncio.new_event_loop()
        self.onconnect = None

    def start(self):
        # Start HTTP and WebSocket servers in background threads
        threading.Thread(target=self._start_http, daemon=True).start()
        threading.Thread(target=self._start_ws, daemon=True).start()

    def _start_http(self):
        handler = http.server.SimpleHTTPRequestHandler
        socketserver.TCPServer.allow_reuse_address = True
        httpd = socketserver.TCPServer((self.host, self.port), handler)
        print(f"Serving HTTP on http://{self.host}:{self.port}")
        httpd.serve_forever()

    async def _ws_handler(self, websocket):
        if self.onconnect:
            try:
                self.onconnect(websocket)
            except Exception as e:
                print(f"[FrontendServer] onconnect callback error: {e}")
        self.clients.add(websocket)
        try:
            async for _ in websocket:
                pass  # We don't expect messages from client
        finally:
            self.clients.remove(websocket)

    def _start_ws(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._run_ws_server())

    async def _run_ws_server(self):
        async with websockets.serve(self._ws_handler, self.host, self.ws_port):
            print(f"Serving WebSocket on ws://{self.host}:{self.ws_port}")
            await asyncio.Future()  # run forever

    def send_data(self, data: FrontendData):
        # Broadcast data to all connected websocket clients
        json = data.model_dump_json()
        async def _broadcast():
            if self.clients:
                await asyncio.gather(*(client.send(json) for client in self.clients), return_exceptions=True)
        if self.loop.is_running():
            asyncio.run_coroutine_threadsafe(_broadcast(), self.loop)
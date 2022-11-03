"""
This file is used to connect to disord gateway in order to receive messages sent to our bot
"""

import asyncio
import websockets
import json
import logging
import requests
_LOGGER = logging.getLogger(__name__)
GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"

class GatewayConnection(object):
    def __init__(self, token, handling_func):
        _LOGGER.info("init Gateway Connection")
        self._token = token
        self._q = asyncio.Queue()
        self._pulse = 1
        self.handling_function = handling_func
        self.send_task = None
        self.ping_task = None
        self.recv_task = None

    async def _run_connection(self):
        _LOGGER.info("running Gateway")
        async with websockets.connect(GATEWAY_URL) as ws:
            self.send_task = asyncio.create_task(self._send_loop(ws))
            self.recv_task = asyncio.create_task(self._recv_loop(ws))
            self.ping_task = asyncio.create_task(self._ping_loop(ws))
            try :
                await self.ping_task
                await self.send_task
                await self.recv_task
            except :
                pass

    async def decode_msg(self, msg):
        obj = json.loads(msg) 
        return {"op": obj.get("op"),
                "data": obj.get("d"),
                "seq": obj.get('s'), 
                "name": obj.get('t')}

    async def _recv_loop(self, ws):
        async for msg in ws:
            try :
                decoded = await self.decode_msg(msg)
                try:
                    await self.handle_message(decoded)
                except Exception as e:
                    _LOGGER.info(f"exception in handler: {e}")
            except asyncio.CancelledError :
                break

    async def _send_loop(self, ws):
        while True:
            try:
                msg = await self._q.get()
                strmsg = json.dumps(msg)
                _LOGGER.info(f"gateway send: {msg}")
                if msg == {"close"} :
                    await ws.close()
                else :
                    await ws.send(strmsg)
            except Exception as e:
                _LOGGER.info(f"exception in send: {e}")
                break

    async def _ping_loop(self, ws):
        while True:
            try :
                await asyncio.sleep(self._pulse)
                ping = {"op": 1, "d": None}
                await self.send(ping)
            except asyncio.CancelledError:
                break


    async def handle_message(self, msg):
        if msg['op'] == 10:
            _LOGGER.info("recieve HELLO, sending identify")
            self._pulse = msg['data']['heartbeat_interval'] / 1000
            await self.identify()
            _LOGGER.info("done identify")
        #treat other codes
        else :
            await self.handling_function(msg)

    async def send(self, msg):
        _LOGGER.info("pushing msg to send")
        await self._q.put(msg)
    
    async def identify(self):
        _LOGGER.info("sending identify")
        identity = {
            "op": 2,
            "d": {
                "token": self._token,
                "intents": 1 << 12,
                "properties": {
                    "$os": "linux",
                    "$browser": "test_opsdroid",
                    "$device": "test_opsdroid",
                },
            }
        }
        await self.send(identity)
    
    async def closeWebsocket(self):
        await self.send({"close"})
        self.ping_task.cancel()
        self.send_task.cancel()
        self.recv_task.cancel()
        await self.ping_task
        await self.send_task
        await self.recv_task
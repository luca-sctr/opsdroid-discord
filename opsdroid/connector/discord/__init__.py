"""A connector for Discord."""
import json
import logging
import asyncio
import websockets
import aiohttp

from voluptuous import Required

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message
from.gateway import GatewayConnection

_LOGGER = logging.getLogger(__name__)
_DISCORD_SEND_URL = "https://discord.com/api"
CONFIG_SCHEMA = {
    Required("token"): str,
    "bot-name": str,
}

class ConnectorDiscord(Connector):

    def __init__(self, config, opsdroid=None):
        """Connector Setup."""
        super().__init__(config, opsdroid=opsdroid)
        _LOGGER.debug("Starting Discord Connector.")
        self.name = config.get("name", "discord")
        self.bot_name = config.get("bot-name", "opsdroid")
        self.token = config["token"]
        self.gateway = GatewayConnection(self.token, self.handling_message)
        self.bot_id = None
    
    async def request_oauth_token(self):
        """Call discord api and request a new oauth token."""
        async with aiohttp.clientSession() as session: 
            params = {
                "client_id": self.client_id, 
                "client_secret": self.client_secret, 
                "code": self.config, 
                "redirect_uri": self.redirect_uri, 
                "scope": "identify connections",
                'grant_type': 'client_credentials',
            }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        request = await session.post("{DISCORD API ENDPOINT}/oauth2/token", data=params, headers=headers) 
        data = await request.json()
        _LOGGER.info(data)

        try:
            self.token = data["access_token"]
            self.save_authentication_data(data) 
        except KeyError:
            _LOGGER.warning(_("Unable to request oauth token - %s"), data)

    async def handling_message(self, msg):
        if msg['name'] == "READY":
            self.bot_id = msg['data']['user']['id']
        if msg['name'] == "MESSAGE_CREATE" :
            id = msg['data']['author']['id']
            if id != self.bot_id : # don't respond to our message
                event = Message(text=msg['data']['content'],user=msg['data']['author']['username'], user_id=msg['data']['author']['id'], target=msg['data']['channel_id'], connector=self,raw_event=msg)
                _LOGGER.info(msg['data']['author']['username']+" said "+msg['data']['content'])
                await self.opsdroid.parse(event)
    
    async def connect(self):
        """Used to discuss with the gateway of discord"""
        
        #await self.request_oauth_token()
        try :
            await self.gateway._run_connection()
        except :
            pass

        """ async with aiohttp.ClientSession() as session:
            channel_request = await session.post(_DISCORD_SEND_URL+"/oauth2/applications/@me", headers={"Authorization": f"Bot {self.token}"})
            data = await channel_request.json()
            _LOGGER.info(data)"""

    async def listen(self):
        """Listen handled by webhooks."""
        pass

    @register_event(Message)
    async def send_message(self, message):
        """Respond with a message."""
        _LOGGER.debug(_("Responding to Discord."))
        url = _DISCORD_SEND_URL+"/channels/"+message.target+"/messages"
        headers = {
                "Authorization": "Bot "+self.token,
                "Content-Type" : "application/json"
            }
        payload = {
            "content": message.text,
        }
        async with aiohttp.ClientSession() as session:
            resp = await session.post(url, data=json.dumps(payload), headers=headers)
            if resp.status < 300:
                _LOGGER.info(_("Responded with: %s."), message.text)
            else:
                _LOGGER.debug(resp.status)
                _LOGGER.debug(await resp.text())
                _LOGGER.error(_("Unable to respond to Discord."))
    
    async def disconnect(self):
        self.gateway.closeWebsocket()
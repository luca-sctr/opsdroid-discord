"""A connector for Discord."""
import logging
from .client import DiscordNoThread
import discord as discord
import io
import aiohttp

from voluptuous import Required

from opsdroid.connector import Connector, register_event
from opsdroid.events import Message,File,Image

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
        self.client = DiscordNoThread(self.token, self.handle_message, self.handle_image, self.handle_file)
        self.bot_id = None
    
    async def handle_message(self, text,user,user_id,target,msg):
        event = Message(text=text,user=user, user_id=user_id, target=target, connector=self,raw_event=msg)
        _LOGGER.info(user+" said "+text)
        await self.opsdroid.parse(event)
    
    async def connect(self):
        await self.client.start()

    async def listen(self):
        """Listen handled by webhooks."""
        pass

    @register_event(Message)
    async def send_message(self, message):
        """Respond with a message."""
        _LOGGER.debug(_("Responding to Discord."))
        await message.target.send(message.text)
    
    async def disconnect(self):
        _LOGGER.debug(_("disconnecting"))
        pr("disconnecting")
        #_LOGGER.debug(_("disconnecting"))
        self.client.close()
        pr("disconnecting done")
        self.client.join()
        # for now, the thread is terminated

    async def handle_image(self, url,user,user_id,target,img):
        event = Image(url=url,user=user, user_id=user_id, target=target, connector=self,raw_event=img)
        _LOGGER.info(user+" sent the image "+url)
        await self.opsdroid.parse(event)

    async def handle_file(self, url,user,user_id,target,file):
        event = File(url=url,user=user, user_id=user_id, target=target, connector=self,raw_event=file)
        _LOGGER.info(user+" sent the file "+url)
        await self.opsdroid.parse(event)

    @register_event(Image)
    async def send_image(self, image_event):
        """Send image to Discord."""
        _LOGGER.debug(_("Sending image to Discord."))
        await image_event.target.send(image_event.url)

    @register_event(File)
    async def send_file(self, file_event):
        """Send file to Discord."""
        _LOGGER.debug(_("Sending file to Discord."))
        async with aiohttp.ClientSession() as session:
            async with session.get(file_event.url) as resp:
                if resp.status != 200:
                    return await file_event.target.send('Could not download file...')
                data = io.BytesIO(await resp.read())
                await file_event.target.send(file=discord.File(data, file_event.raw_event.filename))


def pr(mes):
    with open("D:\Documents\Ecole\\02IMTAtlantique\IDL\debug.txt", "a") as f:
        f.write(mes + "\n")


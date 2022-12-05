import logging
_LOGGER = logging.getLogger(__name__)
import discord

def pr(mes):
    with open("D:\Documents\Ecole\\02IMTAtlantique\IDL\debug.txt", "a") as f:
        f.write(mes + "\n")


class DiscordNoThread():
    def __init__(self, token, handle_message_func, handle_image_func,handle_file_func):
        self.handle_message_func = handle_message_func
        self.handle_image_func = handle_image_func
        self.handle_file_func = handle_file_func
        self.client = DiscordClient(self.handle_message_func, handle_image_func, handle_file_func)
        self.token = token
    
    async def start(self):
        await self.client.start(self.token)

    async def close(self):
        pr("closing")
        self.client.close()


class DiscordClient(discord.Client):

    def __init__(self, handle_message_func, handle_image_func, handle_file_func):
        super().__init__(intents=discord.Intents.default())
        self.handle_message_func = handle_message_func
        self.handle_image_func = handle_image_func
        self.handle_file_func = handle_file_func
        discord.utils.setup_logging(
                level=_LOGGER.level,
                root=False,
            )
    
    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return
        else :
            await self.handle_message_func(message.content, message.author.name, message.author.id, message.channel, message)
            # we test if a file is attached
            if (len(message.attachments) > 0):
                for file in message.attachments:
                    # then we test if one of the attached files is an image
                    if file.filename.endswith(('.jpg','.jpeg','.png')):
                        await self.handle_image_func(str(file), message.author.name, message.author.id, message.channel, file)
                    else :
                        await self.handle_file_func(str(file), message.author.name, message.author.id, message.channel, file)
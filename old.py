import discord
import asyncio

#client = discord.Client()

from discord.ext import commands
import asyncio

""" @client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!') """

class Instance:
    def __init__(self, context):
        self.id = context.guild.id
        user = context.message.author
        self.voice_channel = user.voice.channel
        self.voice_channel_name = self.voice_channel.name
        #self.queue = [] # list of all queued music

everything = {}

bot = commands.Bot(command_prefix = "Q, ")

@bot.command(
    name='leave',
    description="Leaves",
    pass_context=True,
)
async def leave(context):
    guild = context.guild.id
    if guild in everything.keys():
        await context.message.channel.send("Byyye!")
        myinstance = everything[guild]
        await myinstance.voice_client.disconnect()

@bot.command(
    name='join',
    description='Joins',
    pass_context=True,
)
async def join(context):
    # grab the user who sent the command
    guild = context.guild.id
    if guild in everything.keys():
        await context.message.channel.send("Oi, I've already joined! >:(")
        return

    user = context.message.author
    voice_channel = user.voice.channel
    channel = None

    # only play music if user is in a voice channel
    if voice_channel != None:
        # grab user's voice channel
        channel = voice_channel.name
        #await bot.say('User is in channel: ' + channel)

        # create StreamPlayer
        voice_client = await discord.VoiceChannel.connect(voice_channel)
        #vc = await bot.join_voice_channel(voice_channel)
        #player = voice_client.create_ffmpeg_player('PATH', after=lambda: print('done'))

        source = discord.FFmpegPCMAudio('PATH')
        player = voice_client.play(source)

        #player.resume()
        while not player.is_done():
            await asyncio.sleep(1)

        # disconnect after the player has finished
        player.stop()
        await voice_client.disconnect()
    else:
        #await bot.say('User is not in a channel.')
        #print("user not in channel")
        await context.message.channel.send("Oi, you're not in a voice channel! >:(")

with open('../qdata/qtoken.txt', 'r') as fd:
    token = fd.read()
bot.run(token)

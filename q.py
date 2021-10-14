from typing import List
from discord.ext import commands
import asyncio
import discord
import os
import json
#import signal

everything = {}

try:
    with open("../qdata/qpath.json", "r") as fp:
        qpath = json.load(fp)
except:
    qpath = {"shortcuts":{}}

def get_songs(path) -> List[str]:
    target = qpath['shortcuts'].get(path)
    if target is None:
        target = path

    if not os.path.exists(target):
        return []

    if os.path.isdir(target):
        songs = os.listdir(target)
        songs = map(lambda song: f"{target}/{song}", songs)
    else:
        songs = [target]

    songs = [mp3 for mp3 in songs if mp3.endswith('.mp3')]
    return songs

class Instance:
    def __init__(self, context):
        self.id = context.guild.id
        user = context.message.author
        self.voice_channel = user.voice.channel
        self.voice_channel_name = self.voice_channel.name
        self.voice_client = None

        self._queue = [] # list of all queued music
        self.source = None
        self.do_skip = False

        if self.id in everything.keys():
            self._has_joined = False
        else:
            self._has_joined = True
            everything[self.id] = self

    def has_joined(self):
        return self._has_joined

    def save_voice_client(self, voice_client):
        self.voice_client = voice_client

    def queue(self, path: List[str]):
        if isinstance(path, str):
            self._queue.append(path)
        elif isinstance(path, list):
            self._queue.extend(path)

def fetch_instance(context):
    myid = context.guild.id
    if myid in everything.keys():
        return everything[myid]
    return None

bot = commands.Bot(command_prefix = "Q, ")

@bot.command(
    name='q',
    description="Queues",
    pass_context=True,
)
async def qq(context):
    if (myinstance := fetch_instance(context)) is None:
        return

    # message 'Q, q WHAT I'M INTERESTED IN', get the interested part
    text = context.message.content
    split = text.split()
    path = split[2:]
    joined = ' '.join(path)
    songs = get_songs(joined)
    myinstance.queue(songs)

@bot.command(
    name='list',
    description="Lists",
    pass_context=True,
)
async def qlist(context):
    if (myinstance := fetch_instance(context)) is None:
        return
    builder = ['List:']
    for i, path in enumerate(myinstance._queue):
        builder.append(f"{i+1}. {path}")
    text = '\n'.join(builder)
    await context.message.channel.send(text)

@bot.command(
    name='leave',
    description="Leaves",
    pass_context=True,
)
async def qleave(context):
    if (myinstance := fetch_instance(context)) is None:
        return
    await context.message.channel.send("Cya")
    await myinstance.voice_client.disconnect()
    del everything[myinstance.id]

@bot.command(
    name='play',
    description='Plays',
    pass_context=True,
)
async def qplay(context):
    if (myinstance := fetch_instance(context)) is None:
        return
    if myinstance.voice_client and myinstance.voice_client.is_playing():
        return

    while True:
        myinstance.do_skip = False
        if len(myinstance._queue) == 0:
            return

        path = myinstance._queue.pop(0)
        try:
            myinstance.source = discord.FFmpegPCMAudio(path)
        except:
            await context.message.channel.send(f"Can't find {path}")
            return

        await context.message.channel.send(f"Hey, coming up next we got {path}")
        myinstance.voice_client.play(myinstance.source)
        while myinstance.voice_client.is_playing():
            await asyncio.sleep(0.25)
            if myinstance.do_skip:
                break
        myinstance.voice_client.stop()

@bot.command(
    name='stop',
    description='Stops',
    pass_context=True,
)
async def qstop(context):
    if (myinstance := fetch_instance(context)) is None:
        return
    if myinstance.voice_client and not myinstance.voice_client.is_playing():
        return
    myinstance.voice_client.stop()

@bot.command(
    name='skip',
    description='Skips',
    pass_context=True,
)
async def qskip(context):
    if (myinstance := fetch_instance(context)) is None:
        return
    myinstance.do_skip = True

@bot.command(
    name='clear',
    description='Clears',
    pass_context=True,
)
async def qclear(context):
    if (myinstance := fetch_instance(context)) is None:
        return
    await qstop(context)
    myinstance._queue = []

@bot.command(
    name='join',
    description='Joins',
    pass_context=True,
)
async def qjoin(context):
    # grab the user who sent the command
    myinstance = Instance(context)
    if not myinstance.has_joined():
        await context.message.channel.send("Oi, I've already joined! >:(")
        return

    # only play music if user is in a voice channel
    if myinstance.voice_channel != None:
        voice_client = await discord.VoiceChannel.connect(myinstance.voice_channel)
        myinstance.save_voice_client(voice_client)
    else:
        await context.message.channel.send("Oi, you're not in a voice channel! >:(")

# skip command
# pause, resume, stop, leave while playing, play <MUSIC>

#async def async_cleanup():
#    for myinstance in everything.values():
#        if myinstance.voice_client and myinstance.voice_client.is_connected:
#            await myinstance.voice_client.disconnect()
#
#def sig_cleanup(sig, frame):
#    asyncio.get_event_loop().run_until_complete(async_cleanup())
#signal.signal(signal.SIGINT, sig_cleanup)

with open('../qdata/qtoken.txt', 'r') as fd:
    token = fd.read()
bot.run(token)

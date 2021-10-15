from typing import List
from discord.ext import commands
import asyncio
import discord
import os
import sys
import json
#import signal

def arg_check(args: list, da, ddarg):
    return da in args or ddarg in args

def arg_get(args: list, da, ddarg):
    try:
        idx = args.index(da)
    except:
        try:
            idx = args.index(ddarg)
        except:
            return None
    if idx + 1 < len(args):
        return args[idx + 1]
    return None

# load data/private token info
pflag = arg_get(sys.argv, "-p", "--path")
if pflag is None:
    print('Error: Expected -p PATH to a qdata.json with "token": "XYZ"')
    exit(1)

data = {}
everything = {}

NO_SONG = "Nothing"
DATA_FILE = f"{pflag}/qdata.json"

try:
    with open(DATA_FILE, "r") as fp:
        qdata = json.load(fp)
except:
    qdata = {"token": '', "shortcuts": {}, "modules": []}

def get_songs(path) -> List[str]:
    target = qdata['shortcuts'].get(path)
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

        self.whats_playing = NO_SONG
        self._queue = [] # list of all queued music
        self.source = None
        self.do_skip = False
        self.do_loop = False
        self.do_front = False # queue in the front instead of back

        if self.id in everything.keys():
            self._has_joined = False
        else:
            self._has_joined = True
            everything[self.id] = self

    def reset(self):
        self.whats_playing = NO_SONG
        self._queue = []
        self.source = None
        self.do_skip = False
        self.do_loop = False
        self.do_front = False

    def has_joined(self):
        return self._has_joined

    def save_voice_client(self, voice_client):
        self.voice_client = voice_client

    def queue(self, path: List[str]):
        if isinstance(path, str):
            self._queue.append(path)
        elif isinstance(path, list):
            self._queue.extend(path)
        
    def queue_front(self, path: List[str]):
        self._queue = path + self._queue

def fetch_instance(context):
    # the instance or None
    return everything.get(context.guild.id)

def decorator(command):
    return {'name': command, 'description': COMMAND_LOOKUP[command], 'pass_context': True}

COMMAND_PREFIX = "Q, "
bot = commands.Bot(command_prefix=COMMAND_PREFIX)
COMMAND_LOOKUP = {
    "help": f"           View this help. Ex. '{COMMAND_PREFIX}help'",
    "q": f"              Queues a song. Ex. '{COMMAND_PREFIX}q SONG.mp3'",
    "list": f"           Lists all queued songs. Ex. '{COMMAND_PREFIX}list'",
    "leave": f"          Disconnects from the voice chat. Ex. '{COMMAND_PREFIX}leave'",
    "loop": f"           Loops the current song. See noloop to stop. Will loop next after a 'skip'. Ex. '{COMMAND_PREFIX}loop'",
    "noloop": f"         Stops looping the current song.. Ex. '{COMMAND_PREFIX}loop'",
    "play": f"           Starts to play the queue or a song (optional). Ex. '{COMMAND_PREFIX}play [SONG.mp3]'",
    "stop": f"           Stops playing the current song. Ex. '{COMMAND_PREFIX}stop'",
    "skip": f"           Skips the current song. Ex. '{COMMAND_PREFIX}skip'",
    "clear": f"          Clears the queue. Ex. '{COMMAND_PREFIX}clear'",
    "join": f"           Join the voice chat that you are in. Ex. '{COMMAND_PREFIX}join'",
    "songname": f"       Display the current song being played. Ex. '{COMMAND_PREFIX}songname'",
    "commands": f"       Like the help menu but better. Ex. '{COMMAND_PREFIX}commands'",
}

@bot.command(**decorator('commands'))
async def qhelp(context):
    builder = '```\nQ Bot\n==========================================================\n'
    for key, value in COMMAND_LOOKUP.items():
        builder += f"{key}\t{value}\n"
    builder += '```'
    await context.message.channel.send(builder)

@bot.command(**decorator('q'))
async def qq(context):
    if (myinstance := fetch_instance(context)) is None:
        return

    # message 'Q, q WHAT I'M INTERESTED IN', get the interested part
    text = context.message.content
    split = text.split()
    if len(split) < 3:
        return
    path = split[2:]
    joined = ' '.join(path)
    songs = get_songs(joined)

    if myinstance.do_front:
        myinstance.queue_front(songs)
        myinstance.do_front = False
    else:
        myinstance.queue(songs)

@bot.command(**decorator('songname'))
async def qwhatsplaying(context):
    if (myinstance := fetch_instance(context)) is None:
        return
    await context.message.channel.send(myinstance.whats_playing)

@bot.command(**decorator('list'))
async def qlist(context):
    if (myinstance := fetch_instance(context)) is None:
        return
    builder = ['List:']
    for i, path in enumerate(myinstance._queue):
        builder.append(f"{i+1}. {path}")
    text = '\n'.join(builder)
    await context.message.channel.send(text)

@bot.command(**decorator('leave'))
async def qleave(context):
    if (myinstance := fetch_instance(context)) is None:
        return
    await context.message.channel.send("Cya")
    await myinstance.voice_client.disconnect()
    del everything[myinstance.id]

@bot.command(**decorator('loop'))
async def qloop(context):
    if (myinstance := fetch_instance(context)) is None:
        return
    myinstance.do_loop = True

@bot.command(**decorator('noloop'))
async def qnoloop(context):
    if (myinstance := fetch_instance(context)) is None:
        return
    myinstance.do_loop = False

@bot.command(**decorator('play'))
async def qplay(context):
    if (myinstance := fetch_instance(context)) is None:
        return

    if myinstance.voice_client:
        if myinstance.voice_client.is_playing():
            myinstance.do_front = True
            await qq(context)
            await qskip(context)
            return
        else:
            await qq(context)
    else:
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

        while True:
            #await context.message.channel.send(f"Hey, coming up next we got {path}")
            myinstance.whats_playing = path
            myinstance.voice_client.play(myinstance.source)
            while myinstance.voice_client.is_playing():
                await asyncio.sleep(0.25)
                if myinstance.do_skip:
                    break

            myinstance.voice_client.stop()
            myinstance.whats_playing = ''
            if not myinstance.do_loop or myinstance.do_skip:
                break
        pass

@bot.command(**decorator('stop'))
async def qstop(context):
    if (myinstance := fetch_instance(context)) is None:
        return
    if myinstance.voice_client and not myinstance.voice_client.is_playing():
        return
    myinstance.voice_client.stop()
    myinstance.reset()

@bot.command(**decorator('skip'))
async def qskip(context):
    if (myinstance := fetch_instance(context)) is None:
        return
    myinstance.do_skip = True

@bot.command(**decorator('clear'))
async def qclear(context):
    if (myinstance := fetch_instance(context)) is None:
        return
    await qstop(context)
    myinstance._queue = []

@bot.command(**decorator('join'))
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

## TODO: Add loopall
## TODO: Add noloop (cancels loop and loopall)

bot.run(qdata["token"])

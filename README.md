# Q
```
Requirements:
python -m pip install discord.py[voice]
ffmpeg on your path
```
You need to have a file with a JSON configuration, e.g., `config.json`:
```json
{
    "token": "DISCORD_TOKEN",
    "shortcuts": {
        "a": "F:/some/path/to/a/folder/with/mp3s/or/a/file.mp3"
    },
    "modules": []
}
```

## Running
```bash
python q.py -p config.json
```

From Discord you can run `Qq a` to run the shortcut or `Qq F:/some/path/to/a/file.mp3`

Run `Qhelp` from Discord for more info.

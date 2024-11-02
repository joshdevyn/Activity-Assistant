import random
import os
from dotenv import load_dotenv
from pathlib import Path

"""Discord Variables"""
dotenv_path = Path('.env')
load_dotenv(dotenv_path=dotenv_path)
TOKEN = os.getenv('TOKEN')

"""Bot Variables"""
prefix = "!aa "
pre = prefix

"""String Variables"""
usage = "**Usage :** "
explain = "**Explanation :** "
perms = "**Permissions :** "
aliases = "**Aliases :** "
example = "**Example :** "
cool_down = "**Cool Down :** "
note = "**Note :** "
another = "**or**"
cancel = ["Cancel", "cancel"]
stop = ["Stop", "stop"]
forward = "▶"
backward = "◀"
cancel_emoji = "⏹"
approve = "✅"
retry = "🔄"
lock = "🔒"
deny = "❎"
one = "1️⃣"
two = "2️⃣"
pre = "!aa "
skip = ["Skip", "skip"]
remove = ["Remove", "remove"]

"""Integer Variables"""
random_color = random.randint(0, 0xffffff)

"""Helper Functions"""
def random_color():
  return random.randint(0, 0xffffff)
<div align="center">
<h3 align="center">
<img src="https://readme-typing-svg.herokuapp.com?color=00BFFF&center=true&vCenter=true&width=500&lines=+NOVUSMUSIC+BOT+;+FAST+•+SMOOTH+•+POWERFUL+;+TELEGRAM+VC+MUSIC+BOT+">
</h3>
<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">
  
<p align="center">
<a href="https://t.me/NovusSociety">
<img src="https://i.ibb.co/qYbmh3w1/x.jpg" width="600">
</a>
</p>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">

<img src="https://readme-typing-svg.herokuapp.com?font=Orbitron&weight=900&size=36&duration=3000&pause=1000&color=00BFFF&center=true&vCenter=true&width=700&lines=+NovusMusic+Bot;First+Open-Source+VC+Music+Bot;Fast+•+Smooth+•+Powerful" alt="NovusMusic" />

<br>

<p>
  <b>First Open-Source Telegram VC Music Bot </b><br>
  Works Fully Free on Render, Koyeb & More &nbsp;•&nbsp; Zero VPS Cost<br>
  Fast • Smooth • Powerful<br>
  Powered by <b>Pyrogram</b> & <b>Py-TgCalls</b><br>
  Developed by — <b>PBX</b>
</p>

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">

</div>

---

<div align="center">

##  Developer

<img src="https://avatars.githubusercontent.com/Badmunda05" width="110" style="border-radius:50%;" /><br>
**PBX** — Developer of NovusMusic<br>

[![Telegram](https://img.shields.io/badge/Telegram-PBX-%2326A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/PBX_BOT)
[![GitHub](https://img.shields.io/badge/GitHub-Badmunda05-%23181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Badmunda05)

</div>

---

<div align="center">

##  Visitors

<img src="https://profile-counter.glitch.me/Badmunda05/count.svg" />

</div>

---

##  Features

-  High Quality VC Music Streaming
-  Queue System with Auto-Play
- ⏸ Pause / Resume / Skip / Stop Controls
-  Live Progress Bar in Chat
-  Works on Render, Koyeb, Heroku & VPS — Free!
-  Fast & Lightweight — Pyrogram + Py-TgCalls
-  Audio Quality Control
-  Admin-Only Controls

---

##  Deploy Now

<div align="center">

###  Heroku

[![Deploy on Heroku](https://img.shields.io/badge/Deploy%20On%20Heroku-430098?style=for-the-badge&logo=heroku&logoColor=white)](https://dashboard.heroku.com/new?template=https://github.com/Badmunda05/NovusMusic)

---

###  Koyeb

[![Deploy on Koyeb](https://img.shields.io/badge/Deploy%20On%20Koyeb-121212?style=for-the-badge&logo=koyeb&logoColor=white)](https://app.koyeb.com/deploy?type=git&repository=github.com/Badmunda05/NovusMusic&branch=main&name=novusmusic)

---

###  Render

[![Deploy on Render](https://img.shields.io/badge/Deploy%20On%20Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://render.com/deploy?repo=https://github.com/Badmunda05/NovusMusic)

---

###  Railway

[![Deploy on Railway](https://img.shields.io/badge/Deploy%20On%20Railway-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)](https://railway.app/new/template?template=https://github.com/Badmunda05/NovusMusic)

</div>

---

##  VPS Deployment (Self-Host)

> Recommended: Ubuntu 20.04+ / Debian 11+

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install dependencies
sudo apt install -y python3 python3-pip git ffmpeg

# 3. Clone the repo
git clone https://github.com/Badmunda05/NovusMusic
cd NovusMusic

# 4. Install Python requirements
pip3 install -r requirements.txt

# 5. Copy and edit config
cp sample.env .env
nano .env

# 6. Run the bot
python3 -m NovusMusic
```

> To keep running after closing terminal:
```bash
# Install screen
sudo apt install screen -y

# Start a screen session
screen -S novus

# Run the bot
python3 -m NovusMusic

# Detach: Press Ctrl + A then D
# Reattach later:
screen -r novus
```

---

##  Config Variables

###  Required — Bot won't start without these

| Variable | Description |
|---|---|
| `API_ID` | Get from [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | Get from [my.telegram.org](https://my.telegram.org) |
| `BOT_TOKEN` | Get from [@BotFather](https://t.me/BotFather) |
| `STRING_SESSION` | Pyrogram assistant session — Generate at [telegram.tools](https://telegram.tools/session-string-generator#pyrogram) |
| `MONGO_DB_URL` | MongoDB URI — Get free cluster at [mongodb.com](https://www.mongodb.com/cloud/atlas/register) |
| `OWNER_ID` | Your Telegram user ID (integer) |

###  Optional — Default values set, can be changed

| Variable | Default | Description |
|---|---|---|
| `BOT_NAME` | `Novus Music` | Name shown in bot messages |
| `BOT_LINK` | `https://t.me/NovusMusicBot` | Bot's Telegram link |
| `UPDATES_CHANNEL` | `https://t.me/PBX_UPDATE` | Updates channel link |
| `SUPPORT_GROUP` | `https://t.me/NovusSociety` | Support group link |
| `LOGGER_ID` | `-1003544580602` | Log channel/group ID |
| `START_ANIMATION` | *(catbox video)* | Video/GIF for /start command |
| `PING_IMG_URL` | *(catbox image)* | Image shown in /ping response |
| `SESSION_NAME` | `NovusMusic` | Pyrogram session file name |
| `PORT` | `10000` | Web server port (for Render/Koyeb) |

###  Limits — Fine-tune performance

| Variable | Default | Description |
|---|---|---|
| `MAX_DURATION_SECONDS` | `1800` | Max song duration (30 minutes) |
| `QUEUE_LIMIT` | `20` | Max songs in queue per chat |
| `COOLDOWN` | `10` | Seconds between /play per chat |

---

##  Requirements

- Python 3.10+
- MongoDB — Free at [mongodb.com](https://www.mongodb.com/cloud/atlas/register)
- Telegram API credentials — [my.telegram.org](https://my.telegram.org)
- Pyrogram Session String — [telegram.tools](https://telegram.tools/session-string-generator#pyrogram)
- A userbot/assistant account (for VC streaming)

---
##  License

This project is licensed under the [MIT License](https://github.com/Badmunda05/NovusMusic/blob/main/LICENSE) © 2026 NovusMusic™

---
<div align="center">

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">

**Made with  by PBX — NovusMusic™**

[![Repo](https://img.shields.io/badge/GitHub-NovusMusic-181717?style=for-the-badge&logo=github)](https://github.com/Badmunda05/NovusMusic)
[![Stars](https://img.shields.io/github/stars/Badmunda05/NovusMusic?style=for-the-badge&color=yellow)](https://github.com/Badmunda05/NovusMusic/stargazers)
[![Forks](https://img.shields.io/github/forks/Badmunda05/NovusMusic?style=for-the-badge&color=blue)](https://github.com/Badmunda05/NovusMusic/network/members)

<img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-908a-139a6edaec5c.gif">

</div>

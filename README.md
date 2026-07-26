\# 🚀 FB Empire Auto-Bot V10.0 - Premium Edition



\*\*Complete Facebook Automation Tool with Anti-Detect Engine\*\*



Multi-workspace • Anti-Detect Video Processing • Auto Upload • Persona System • 33 Thumbnail Templates



\---



\## 📋 TABLE OF CONTENTS



1\. \[Features](#-features)

2\. \[System Requirements](#-system-requirements)

3\. \[Installation Guide](#-installation-guide)

4\. \[Setup Instructions](#-setup-instructions)

5\. \[How to Use](#-how-to-use)

6\. \[Cookies Setup (Important)](#-cookies-setup)

7\. \[Troubleshooting](#-troubleshooting)

8\. \[File Structure](#-file-structure)

9\. \[Updating](#-updating)



\---



\## ✨ FEATURES



\### 🎨 \*\*Premium UI\*\*

\- Modern sidebar navigation

\- Dashboard with real-time stats

\- Search, filter, and sort workspaces

\- Toast notifications

\- Dark theme optimized



\### 📁 \*\*Workspace Management\*\* 

\- Create/Rename/Delete workspaces

\- Pin favorites \& Archive old ones

\- Duplicate settings

\- Export/Import as JSON

\- Tags system

\- Bulk operations



\### 🎭 \*\*Persona System\*\*

\- Auto-generated identity per workspace

\- Real device specs (iPhone/Samsung/Pixel etc.)

\- USA cities database

\- Locked identity (never changes)

\- Editable in settings



\### 🎬 \*\*Video Processing\*\*

\- Multi-platform download (YouTube, TikTok, Instagram, FB, Twitter)

\- Reels/Shorts/Videos/Images support

\- 33 anti-detect techniques

\- 3 preset styles (StealthMax, Balanced, Visual)

\- Custom presets (save/load/export)

\- Human-like delays (bot prevention)



\### 🎨 \*\*Thumbnail Generator (V3.0)\*\*

\- 33 professional templates

\- Smart frame detection (AI scoring)

\- Face detection

\- 3 variations per video

\- Auto text placement (avoids faces)

\- Category-based emoji packs



\### 📤 \*\*Auto Upload\*\*

\- Facebook Business Suite integration

\- Warmup scrolling (human behavior)

\- Page switching support

\- Boost popup handler

\- Schedule posts (with random offset)

\- Multi-account support



\### 🛡️ \*\*Anti-Detection\*\*

\- Video hash breaker

\- Metadata spoofing (device/GPS/timestamps)

\- Audio fingerprint change

\- Random delays between actions

\- Cookie-based downloads

\- User-agent rotation



\---



\## 💻 SYSTEM REQUIREMENTS



\### \*\*Minimum:\*\*

\- \*\*OS:\*\* Windows 10/11 (64-bit)

\- \*\*RAM:\*\* 8 GB

\- \*\*Storage:\*\* 5 GB free space

\- \*\*CPU:\*\* Intel i5 / AMD Ryzen 5

\- \*\*Internet:\*\* Stable connection



\### \*\*Recommended:\*\*

\- \*\*RAM:\*\* 16 GB

\- \*\*Storage:\*\* 20 GB free (for videos)

\- \*\*CPU:\*\* Intel i7 / AMD Ryzen 7

\- \*\*GPU:\*\* Optional (for faster video editing)



\### \*\*Required Software:\*\*

\- Python 3.10 or 3.11

\- Google Chrome (latest)

\- FFmpeg (see installation)

\- ChromeDriver (matching Chrome version)



\---



\## 🔧 INSTALLATION GUIDE



\### \*\*Step 1: Install Python\*\*



Download Python 3.10 or 3.11 from:

```

https://www.python.org/downloads/

```



⚠️ \*\*IMPORTANT:\*\* During installation, check ✅ \*\*"Add Python to PATH"\*\*



Verify installation:

```bash

python --version

```

Should show: `Python 3.10.x` or `Python 3.11.x`



\---



\### \*\*Step 2: Install FFmpeg\*\*



FFmpeg is required for video processing.



\*\*Option A: Manual Download (Recommended)\*\*



1\. Go to: https://www.gyan.dev/ffmpeg/builds/

2\. Download: \*\*ffmpeg-git-full.7z\*\*

3\. Extract to: `C:\\ffmpeg`

4\. Add to PATH:

&#x20;  - Search "Environment Variables" in Windows

&#x20;  - Click "Environment Variables"

&#x20;  - Under "System Variables", find "Path"

&#x20;  - Click "Edit" → "New"

&#x20;  - Add: `C:\\ffmpeg\\bin`

&#x20;  - Click OK



Verify:

```bash

ffmpeg -version

```



\*\*Option B: Using Chocolatey\*\*

```bash

choco install ffmpeg

```



\---



\### \*\*Step 3: Install ChromeDriver\*\*



1\. Check your Chrome version:

&#x20;  - Open Chrome → `chrome://version`

&#x20;  - Note the version (e.g., 120.0.6099.129)



2\. Download matching ChromeDriver:

&#x20;  - Go to: https://googlechromelabs.github.io/chrome-for-testing/

&#x20;  - Download for your Chrome version

&#x20;  - Choose: \*\*chromedriver-win64.zip\*\*



3\. Extract `chromedriver.exe` to:

&#x20;  ```

&#x20;  C:\\Users\\YourName\\Downloads\\FB\_Empire\_AutoBot\\app\\chromedriver.exe

&#x20;  ```

&#x20;  (Same folder as `main.py`)



\---



\### \*\*Step 4: Install Python Packages\*\*



Open Command Prompt in the app folder:



```bash

cd "C:\\Users\\YourName\\Downloads\\FB\_Empire\_AutoBot\\app"

```



Install all required packages:



```bash

pip install -r requirements.txt

```



\*\*If you get numpy conflict error:\*\*

```bash

pip install numpy==1.26.4 --force-reinstall

```



\*\*Verify installation:\*\*

```bash

pip list

```



Should show all packages installed.



\---



\### \*\*Step 5: Install Chrome Extension (For Cookies)\*\*



For Instagram/Facebook downloads, you need cookies:



1\. Open Chrome

2\. Go to: https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc

3\. Click \*\*"Add to Chrome"\*\*

4\. Extension installed ✅



\---



\## ⚙️ SETUP INSTRUCTIONS



\### \*\*Step 1: First Launch\*\*



```bash

python main.py

```



If everything is installed correctly, the app will open with:

\- Sidebar on left (Dashboard/Workspaces)

\- Empty dashboard

\- "+ New Workspace" button



\---



\### \*\*Step 2: Create First Workspace\*\*



1\. Click \*\*"➕ Create New Workspace"\*\*

2\. Enter workspace name (e.g., "Funny Cats Hub")

3\. Enter FB page URL (optional)

4\. Chrome path auto-fills as: `C:\\ChromeBot\\Funny\_Cats\_Hub\\Default`

5\. Keep \*\*"Auto-create Chrome folder"\*\* ✅ checked

6\. Click \*\*"✨ Create Workspace"\*\*



\*\*What happens:\*\*

\- Chrome folder created automatically

\- Random persona generated (device + USA city)

\- Excel log initialized

\- Workspace ready to use



\---



\### \*\*Step 3: Setup Chrome for Facebook\*\*



1\. Go to your workspace \*\*Settings\*\* tab

2\. Click \*\*"🌐 Open Chrome (Login)"\*\*

3\. New Chrome window opens with your workspace profile

4\. \*\*Login to Facebook\*\* in this window

5\. Close Chrome

6\. Now bot can auto-upload from this account



\---



\### \*\*Step 4: Export Cookies (For Downloads)\*\*



For Instagram/FB downloads (login required):



1\. \*\*Chrome mein Instagram open karo\*\*

2\. Login karo (if not)

3\. Click extension icon (top right - puzzle icon)

4\. Click \*\*"Get cookies.txt LOCALLY"\*\*

5\. Click \*\*"Export"\*\*

6\. Save file as: `instagram\_cookies.txt`

7\. Move file to: `app/cookies/instagram\_cookies.txt`



\*\*Same for other platforms:\*\*

\- `facebook\_cookies.txt`

\- `tiktok\_cookies.txt`

\- `twitter\_cookies.txt`



\---



\## 📚 HOW TO USE



\### \*\*Basic Workflow:\*\*



```

1\. Create Workspace

&#x20;    ↓

2\. Setup Chrome (Login to FB)

&#x20;    ↓

3\. Add Videos (URL / PC files / CSV)

&#x20;    ↓

4\. Process \& Edit (Auto anti-detect)

&#x20;    ↓

5\. Post to Facebook (Auto upload)

```



\---



\### \*\*Adding Videos:\*\*



\*\*Method 1: Single URL\*\*

1\. Open workspace → "📥 Add Videos" tab

2\. Paste URL (YouTube/TikTok/Instagram/etc.)

3\. Click "➕ Add to Queue"



\*\*Method 2: Local Files\*\*

1\. Click "📁 Browse Files"

2\. Select multiple videos (Ctrl+Click)

3\. Auto-added to queue



\*\*Method 3: Bulk Import CSV\*\*

1\. Prepare CSV file with "URL" column:

&#x20;  ```csv

&#x20;  URL

&#x20;  https://youtube.com/watch?v=xxx

&#x20;  https://tiktok.com/@user/video/yyy

&#x20;  ```

2\. Click "📑 Import CSV/Excel"

3\. All URLs added at once



\---



\### \*\*Processing Videos:\*\*



1\. Go to "⚙️ Process \& Post" tab

2\. Click \*\*"📥 Download \& Process"\*\* on any video

3\. Options:

&#x20;  - \*\*Mirror Flip\*\* ✅

&#x20;  - \*\*Thumbnail\*\* ✅ (uses 33 templates)

&#x20;  - \*\*Blur Position\*\* (Top-Left/Right etc.)

4\. Bot will:

&#x20;  - Download video (with human delays)

&#x20;  - Apply anti-detect editing

&#x20;  - Generate thumbnail

&#x20;  - Create AI title

&#x20;  - Mark as "READY\_TO\_POST"



\*\*Stop/Pause:\*\*

\- Click \*\*⏹ Stop\*\* to cancel

\- Click \*\*⏸ Pause\*\* to resume later



\---



\### \*\*Uploading to Facebook:\*\*



1\. Video shows \*\*"🚀 Post to Facebook"\*\* button

2\. Edit caption, hashtags, time

3\. Click Post button

4\. Chrome opens automatically

5\. Bot:

&#x20;  - Does warmup scrolling

&#x20;  - Opens Business Suite

&#x20;  - Uploads video

&#x20;  - Fills caption

&#x20;  - Publishes

&#x20;  - Handles boost popup



\---



\### \*\*Editing Settings (Anti-Detect):\*\*



1\. Open workspace → "🎬 Editing" tab

2\. Choose preset:

&#x20;  - \*\*StealthMax v2.0\*\* (all anti-detect ON)

&#x20;  - \*\*Balanced\*\* (medium)

&#x20;  - \*\*Visual Quality\*\* (looks best)

3\. Or customize:

&#x20;  - 11 Anti-detect checkboxes

&#x20;  - Speed slider (0.94-1.10x)

&#x20;  - Crop position/percent

&#x20;  - Color grading

&#x20;  - Audio settings

4\. Save as custom preset



\---



\## 🍪 COOKIES SETUP (IMPORTANT!)



\### \*\*Why Needed:\*\*



Instagram/Facebook now require login for most content. Without cookies:

\- ❌ Can't download Instagram reels

\- ❌ Can't download Facebook videos

\- ❌ Get "login required" errors



\### \*\*How to Setup:\*\*



\*\*1. Install Chrome Extension:\*\*

```

Search: "Get cookies.txt LOCALLY"

Or direct link: https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc

```



\*\*2. For each platform:\*\*



\*\*Instagram:\*\*

1\. Chrome mein instagram.com open karo

2\. Login karo

3\. Extension icon → Export

4\. Save as: `app/cookies/instagram\_cookies.txt`



\*\*Facebook:\*\*

1\. Chrome mein facebook.com open karo

2\. Login karo

3\. Extension icon → Export

4\. Save as: `app/cookies/facebook\_cookies.txt`



\*\*TikTok:\*\*

1\. Same process

2\. Save as: `app/cookies/tiktok\_cookies.txt`



\*\*⚠️ IMPORTANT:\*\*

\- Cookies expire in 2-4 weeks

\- Refresh them when downloads fail

\- Never share cookie files (has your login)



\---



\## 🔧 TROUBLESHOOTING



\### \*\*Problem: "python is not recognized"\*\*



\*\*Solution:\*\*

\- Reinstall Python

\- Check "Add Python to PATH" during install

\- Restart Command Prompt



\---



\### \*\*Problem: "ffmpeg is not recognized"\*\*



\*\*Solution:\*\*

1\. Verify FFmpeg installation:

&#x20;  ```bash

&#x20;  ffmpeg -version

&#x20;  ```

2\. If not working:

&#x20;  - Re-add to PATH

&#x20;  - Restart Command Prompt

&#x20;  - Or restart PC



\---



\### \*\*Problem: "ChromeDriver version mismatch"\*\*



\*\*Solution:\*\*

1\. Check Chrome version: `chrome://version`

2\. Download matching ChromeDriver:

&#x20;  - https://googlechromelabs.github.io/chrome-for-testing/

3\. Replace old chromedriver.exe



\---



\### \*\*Problem: Numpy/Pandas conflict\*\*



\*\*Solution:\*\*

```bash

pip install numpy==1.26.4 --force-reinstall

```



\---



\### \*\*Problem: Instagram "empty media response"\*\*



\*\*Solution:\*\*

\- Cookies expired or missing

\- Follow "Cookies Setup" section above

\- Refresh cookies



\---



\### \*\*Problem: FFmpeg filter error\*\*



\*\*Solution:\*\*

\- Update yt-dlp:

&#x20; ```bash

&#x20; pip install -U yt-dlp

&#x20; ```

\- Update FFmpeg to latest version



\---



\### \*\*Problem: "cv2 not found"\*\*



\*\*Solution:\*\*

```bash

pip install opencv-python --force-reinstall

```



\---



\### \*\*Problem: Chrome doesn't open\*\*



\*\*Solution:\*\*

1\. Close ALL Chrome windows first

2\. Kill chrome.exe in Task Manager

3\. Try again



\---



\### \*\*Problem: Videos not editing properly\*\*



\*\*Solution:\*\*

1\. Check FFmpeg is working:

&#x20;  ```bash

&#x20;  ffmpeg -version

&#x20;  ```

2\. Try different preset (Balanced instead of StealthMax)

3\. Check disk space



\---



\### \*\*Problem: Rate limited / IP blocked\*\*



\*\*Solution:\*\*

\- Take a break (30-60 min)

\- Use VPN

\- Reduce download frequency

\- Bot has auto-human delays but bulk is risky



\---



\## 📁 FILE STRUCTURE



```

FB\_Empire\_AutoBot/

│

├── app/

│   ├── main.py                    ← Main application

│   ├── downloader.py              ← Video/image downloader

│   ├── video\_editor.py            ← Anti-detect editing

│   ├── uploader.py                ← Facebook uploader

│   ├── thumbnail\_gen.py           ← 33 template thumbnails

│   ├── db\_manager.py              ← Database (SQLite)

│   ├── ai\_writer.py               ← AI title generator

│   ├── preset\_manager.py          ← Preset management

│   ├── sheet\_manager.py           ← Excel exporter

│   ├── scheduler.py               ← Post scheduler

│   ├── chrome\_profile\_cloner.py   ← Chrome profile cloner

│   ├── chromedriver.exe           ← Download separately

│   │

│   ├── requirements.txt           ← Python packages

│   ├── README.md                  ← This file

│   ├── openai\_key.txt             ← Optional (for AI)

│   │

│   ├── cookies/                   ← Browser cookies

│   │   ├── instagram\_cookies.txt

│   │   ├── facebook\_cookies.txt

│   │   ├── tiktok\_cookies.txt

│   │   └── twitter\_cookies.txt

│   │

│   ├── downloads/                 ← Downloaded videos

│   │   └── {workspace}/

│   │       ├── raw\_videos/

│   │       ├── raw\_images/

│   │       └── edited\_videos/

│   │

│   ├── presets/                   ← Custom editing presets

│   │   └── user\_presets.json

│   │

│   └── fb\_automation\_v3.db        ← Database (auto-created)

│

└── C:\\ChromeBot/                  ← Chrome profiles (auto-created)

&#x20;   └── {workspace\_name}/

&#x20;       ├── Default/

&#x20;       └── {workspace\_name}\_log.xlsx

```



\---



\## 🔄 UPDATING



\### \*\*Update Python Packages:\*\*



```bash

pip install -r requirements.txt --upgrade

```



\### \*\*Update yt-dlp (Important for downloads):\*\*



```bash

pip install -U yt-dlp

```



\### \*\*Update Chrome + ChromeDriver:\*\*



1\. Update Chrome:

&#x20;  - Chrome menu → Help → About Google Chrome

&#x20;  - Auto-updates



2\. Update ChromeDriver:

&#x20;  - Check new Chrome version

&#x20;  - Download matching driver

&#x20;  - Replace old `chromedriver.exe`



\### \*\*Update FFmpeg:\*\*



1\. Download latest from:

&#x20;  - https://www.gyan.dev/ffmpeg/builds/

2\. Replace old files in `C:\\ffmpeg\\`



\---



\## 📞 QUICK COMMAND REFERENCE



\### \*\*Setup Commands:\*\*

```bash

\# Install everything

pip install -r requirements.txt



\# Fix numpy conflict

pip install numpy==1.26.4 --force-reinstall



\# Update yt-dlp

pip install -U yt-dlp



\# Update pip itself

python -m pip install --upgrade pip

```



\### \*\*Run Commands:\*\*

```bash

\# Run main app

python main.py



\# Test downloader alone

python downloader.py



\# Test thumbnail generator alone

python thumbnail\_gen.py



\# Test video editor alone

python video\_editor.py

```



\### \*\*Verification Commands:\*\*

```bash

\# Check Python

python --version



\# Check FFmpeg

ffmpeg -version



\# Check installed packages

pip list



\# Check specific package

pip show yt-dlp

```



\---



\## ⚠️ IMPORTANT NOTES



\### \*\*Security:\*\*

\- 🔒 Never share `cookies/` folder (contains login info)

\- 🔒 Never share `fb\_automation\_v3.db` (has all data)

\- 🔒 Add these to `.gitignore` if using Git



\### \*\*Bot Detection Prevention:\*\*

\- ✅ Bot has human-like delays built-in

\- ✅ Rotates user-agents

\- ✅ Uses your Chrome cookies

\- ⚠️ Don't upload 100+ videos per day

\- ⚠️ Use VPN if IP gets blocked

\- ⚠️ Refresh cookies every 2-4 weeks



\### \*\*Content Guidelines:\*\*

\- Only download PUBLIC content

\- Respect copyright

\- Follow platform ToS

\- Don't spam or abuse



\---



\## 🎯 QUICK START (TL;DR)



```bash

\# 1. Install Python 3.10 or 3.11



\# 2. Install FFmpeg (add to PATH)



\# 3. Install packages

pip install -r requirements.txt



\# 4. Fix numpy

pip install numpy==1.26.4 --force-reinstall



\# 5. Download ChromeDriver (matching Chrome version)

\# Place chromedriver.exe in app/ folder



\# 6. Install Chrome extension "Get cookies.txt LOCALLY"



\# 7. Export Instagram/FB cookies to app/cookies/



\# 8. Run the app

python main.py



\# 9. Create workspace

\# 10. Setup Chrome (login to FB)

\# 11. Start automating!

```



\---



\## 💡 TIPS \& TRICKS



\### \*\*For Best Results:\*\*

1\. \*\*One workspace = one identity\*\* (never mix)

2\. \*\*Refresh cookies weekly\*\*

3\. \*\*Use StealthMax preset for max stealth\*\*

4\. \*\*Don't bulk upload from same IP\*\*

5\. \*\*Take breaks between sessions\*\*

6\. \*\*Backup your database occasionally\*\*



\### \*\*Performance Tips:\*\*

1\. Close unnecessary programs while processing

2\. Use SSD for faster video editing

3\. 16GB RAM recommended for bulk processing

4\. Good internet speeds up downloads



\### \*\*Facebook Tips:\*\*

1\. Warmup scrolling improves account trust

2\. Random offset makes posts look natural

3\. Different times for different content types

4\. Engage with comments manually



\---



\## 📊 FEATURE COMPARISON



| Feature | Free Alternatives | FB Empire |

|---------|-------------------|-----------|

| Multi-workspace | ❌ | ✅ Unlimited |

| Anti-detect | Basic | 33 techniques |

| Persona system | ❌ | ✅ Real devices |

| Thumbnails | 1 style | 33 templates |

| Auto upload | Manual | ✅ Full auto |

| Scheduling | Basic | ✅ With offset |

| Cookies support | Manual | ✅ Integrated |

| Modern UI | Old | ✅ Premium |



\---



\## 🏆 CREDITS



\*\*Built with:\*\*

\- Python + CustomTkinter

\- yt-dlp (downloading)

\- FFmpeg (video processing)

\- Selenium (Facebook automation)

\- OpenAI (title generation)

\- OpenCV (frame detection)

\- Pillow (image editing)



\---



\## 📝 VERSION HISTORY



\*\*V10.0 - Premium Edition (Current)\*\*

\- Complete UI redesign

\- 33 thumbnail templates

\- Persona system

\- Advanced workspace management

\- Cookie file support

\- Bug fixes



\*\*V9.1 - Fixed Edition\*\*

\- Basic thumbnail generation

\- Multi-workspace support

\- Anti-detect V1



\*\*V9.0 - Initial Release\*\*

\- Core automation

\- Simple UI



\---



\## 📄 LICENSE



Private tool - Not for redistribution.



\---



\## ❓ NEED HELP?



Check troubleshooting section above, or:

1\. Check error message carefully

2\. Verify all installations

3\. Update packages

4\. Restart the app



\---



\*\*🚀 Happy Automating!\*\*


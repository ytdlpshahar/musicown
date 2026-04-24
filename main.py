from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
import yt_dlp
import os
import urllib.parse

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

download_folder = "downloads"
if not os.path.exists(download_folder):
    os.makedirs(download_folder)


@app.get("/")
async def index():
    return FileResponse("templates/index.html")


@app.post("/download")
async def dl(url: str = Form(...)):
    if not url:
        raise HTTPException(status_code=400, detail="נא להזין URL")

    # הגדרות הורדה
    song_settings = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
        'ffmpeg_location': r'C:\Users\User\Downloads\PyCharm\FastAPI_Web\ffmpeg-8.0.1-essentials_build\bin',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }],
        'quiet': True,
        'noplaylist': True
    }

    try:
        # הרצת yt-dlp ב-thread נפרד כדי לא לחסום את השרת האסינכרוני
        def download():
            with yt_dlp.YoutubeDL(song_settings) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info).replace(info['ext'], 'mp3')

        filename = await run_in_threadpool(download)

        # טיפול בשם הקובץ כך שדפדפנים יבינו עברית (Encoded)
        encoded_filename = urllib.parse.quote(os.path.basename(filename))

        return FileResponse(
            path=filename,
            filename=os.path.basename(filename),
            headers={"Content-Disposition": f"attachment; filename=\"{encoded_filename}\""}
        )

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
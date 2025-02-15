from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List
from youtube_transcript_api import YouTubeTranscriptApi
from pytubefix import YouTube
from pytubefix.cli import on_progress
import tempfile
import cv2
import os
import uuid
from supabase import create_client
import uvicorn

# Initialize Supabase client
supabase_url = "YOUR_SUPABASE_URL"
supabase_key = "YOUR_SUPABASE_KEY"
supabase = create_client(supabase_url, supabase_key)

class TranscriptSegment(BaseModel):
    text: str
    start: float
    duration: float

class Transcript(BaseModel):
    segments: List[TranscriptSegment]
    full_text: str

    @classmethod
    def from_youtube_transcript(cls, transcript_data):
        segments = [TranscriptSegment(**segment) for segment in transcript_data]
        full_text = ' '.join(segment.text for segment in segments)
        return cls(segments=segments, full_text=full_text)

class VideoRequest(BaseModel):
    video: str

    @property
    def video_id(self) -> str:
        import re
        patterns = [
            r'(?:v=|/)([0-9A-Za-z_-]{11})(?:[&?/]|$)',
            r'^([0-9A-Za-z_-]{11})$'
        ]
        for pattern in patterns:
            if match := re.search(pattern, self.video):
                return match.group(1)
        raise ValueError("Invalid YouTube video ID or URL format")

async def process_video(video_url: str, video_id: str):
    """Process video and store data in Supabase"""
    # Get transcript
    transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
    transcript = Transcript.from_youtube_transcript(transcript_data)
    
    # Extract frames at transcript segment starts
    timestamps = [segment.start for segment in transcript.segments]
    
    # Download video and process frames
    yt = YouTube(video_url, on_progress_callback=on_progress)
    ys = yt.streams.get_by_resolution("360p")
    
    segments_data = []
    
    with tempfile.NamedTemporaryFile(suffix=".mp4") as video_file:
        temp_dir = tempfile.gettempdir()
        ys.download(output_path=temp_dir, filename=video_file.name.split('/')[-1])
        
        capture = cv2.VideoCapture(video_file.name)
        
        for i, (timestamp, segment) in enumerate(zip(timestamps, transcript.segments)):
            capture.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ret, frame = capture.read()
            
            if ret:
                # Save frame to temporary file
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as frame_file:
                    cv2.imwrite(frame_file.name, frame)
                    
                    # Upload to Supabase storage
                    storage_path = f"frames/{video_id}/{i}.jpg"
                    with open(frame_file.name, 'rb') as f:
                        supabase.storage.from_("youtube_frames").upload(
                            file=f,
                            path=storage_path,
                            file_options={"cache-control": "3600", "upsert": "true"},
                        )
                    
                    # Get public URL
                    storage_url = supabase.storage.from_("youtube_frames").get_public_url(storage_path)
                    
                    segments_data.append({
                        "item": i,
                        "start": int(timestamp * 1000),
                        "storage_url": storage_url
                    })
                    
                    os.unlink(frame_file.name)
        
        capture.release()

    # Create database entries
    youtube_entry = {
        "youtube_link": video_url,
        "id": str(uuid.uuid4())
    }
    
    # Insert YouTube entry
    youtube_response = supabase.table("youtube_table").upsert(youtube_entry).execute()
    youtube_id = youtube_response.data[0]['id']
    
    # Insert transcript
    transcript_entry = {
        "id": str(uuid.uuid4()),
        "youtube_id": youtube_id,
        "full_text": transcript.full_text
    }
    transcript_response = supabase.table("transcripts").upsert(transcript_entry).execute()
    
    # Insert segments
    for segment in segments_data:
        segment["id"] = str(uuid.uuid4())
        segment["youtube_id"] = youtube_id
    
    segments_response = supabase.table("segments").upsert(segments_data).execute()
    
    # Clean up temporary video file
    if os.path.exists(video_file.name):
        os.unlink(video_file.name)
    
    return {
        "youtube": youtube_response.data[0],
        "transcript": transcript_response.data[0],
        "segments": segments_response.data
    }

app = FastAPI(title="YouTube Processor API")

@app.post("/process")
async def process_youtube_video(request: VideoRequest):
    try:
        video_id = request.video_id
        result = await process_video(request.video, video_id)
        return JSONResponse(content=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return HTMLResponse(
        """
        <h1>YouTube Processor API</h1>
        <p>Process YouTube videos for transcripts and frame captures.</p>
        <ul>
            <li><a href="/docs">API Documentation</a></li>
        </ul>
        """
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
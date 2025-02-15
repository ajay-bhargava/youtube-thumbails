from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List
from youtube_transcript_api import YouTubeTranscriptApi
import uvicorn

# Reuse the data models
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

class TranscriptRequest(BaseModel):
    video: str

    @property
    def video_id(self) -> str:
        """Extract video ID from various possible YouTube URL formats or return the ID directly."""
        import re
        patterns = [
            r'(?:v=|/)([0-9A-Za-z_-]{11})(?:[&?/]|$)',  # Regular URLs
            r'^([0-9A-Za-z_-]{11})$'  # Direct video ID
        ]
        
        for pattern in patterns:
            if match := re.search(pattern, self.video):
                return match.group(1)
        raise ValueError("Invalid YouTube video ID or URL format")

# Create FastAPI app
app = FastAPI(title="YouTube Transcript API")

@app.post("/transcript")
async def get_transcript(request: TranscriptRequest):
    try:
        video_id = request.video_id
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = Transcript.from_youtube_transcript(transcript_data)
        return JSONResponse(content=transcript.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return HTMLResponse(
        """
        <h1>YouTube Transcript API</h1>
        <p>Get transcripts from YouTube videos.</p>
        <ul>
            <li><a href="/docs">API Documentation</a></li>
        </ul>
        """
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 
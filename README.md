# YouTube Frame Extractor & Transcript API 🎥

This service processes YouTube videos by extracting frames at specific timestamps and matching them with transcript segments. Perfect for creating video summaries or analyzing video content!

## How it Works 🛠️

1. The service accepts a YouTube video URL/ID via a FastAPI endpoint
2. It extracts the video transcript and downloads the video
3. For each transcript segment, it captures a frame at the corresponding timestamp
4. Frames are stored in Supabase storage, and metadata is saved in Supabase database
5. Returns a structured response with all video, transcript, and segment data

## Key Libraries 📚

### YouTube Processing
- **pytubefix**: Enhanced fork of pytube for reliable YouTube video downloads
  - Handles video stream selection
  - Provides download progress callbacks
  - Supports various video quality options

- **youtube_transcript_api**: Powerful transcript extraction
  - Fetches closed captions/subtitles
  - Supports multiple languages
  - Provides timestamp-accurate text segments

## Supabase Integration 🗄️

The service uses Supabase for both storage and database operations. Here's where data gets stored:

1. **Storage**: Frames are stored in the `youtube_frames` bucket with path structure:
   ```
   frames/{video_id}/{segment_number}.jpg
   ```

2. **Database Tables**:
   - `youtube_table`: Stores video metadata
   - `transcripts`: Stores full video transcripts
   - `segments`: Stores individual segments with frame URLs

### Data Structure

```typescript
youtube_table {
    id: uuid
    youtube_link: string
}

transcripts {
    id: uuid
    youtube_id: uuid (foreign key)
    full_text: text
}
segments {
    id: uuid
    youtube_id: uuid (foreign key)
    item: integer
    start: integer (milliseconds)
    storage_url: string
    text: string
}
```

## Installation 📦

1. Clone the repository
2. Install dependencies

## Production Deployment with Modal Proxy ⚡️

Youtube disallows the use of Lambda API's for their API endpoints. The proper work around is to standup a server that uses 

## Environment Setup 🔧

1. Create a `.env` file with:

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## Running the Service 🚀

1. Start the FastAPI server:

```
python3 src/youtube_processor.py
```
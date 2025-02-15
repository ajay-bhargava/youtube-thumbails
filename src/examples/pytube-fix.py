from pytubefix import YouTube
from pytubefix.cli import on_progress
import tempfile
import cv2
import os
import json
from typing import List

def extract_frames(youtube_url: str, timestamps: List[float]) -> List[dict]:
    """
    Extract frames from YouTube video at given timestamps and save frame info to JSON
    
    Args:
        youtube_url: YouTube video URL
        timestamps: List of timestamps in seconds
    
    Returns:
        List of segment records with local file paths
    """
    # Download video
    yt = YouTube(youtube_url, on_progress_callback=on_progress)
    ys = yt.streams.get_by_resolution("360p")
    
    segments = []
    
    with tempfile.NamedTemporaryFile(suffix=".mp4") as file_dir:
        # Get the directory path of the temporary file
        temp_dir = tempfile.gettempdir()
        ys.download(output_path=temp_dir, filename=file_dir.name.split('/')[-1])
        
        # Process each timestamp
        for i, timestamp in enumerate(timestamps):
            # Use the full path of the temporary file for VideoCapture
            capture = cv2.VideoCapture(file_dir.name)
            capture.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            
            ret, frame = capture.read()
            if ret:
                # Create temporary file for frame
                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as frame_file:
                    frame_path = frame_file.name
                    cv2.imwrite(frame_path, frame)
                    
                    # Create segment record
                    segment = {
                        "item": i,
                        "start": int(timestamp * 1000),  # Convert to milliseconds
                        "frame_path": frame_path,
                        "timestamp": timestamp
                    }
                    
                    segments.append(segment)
            
            capture.release()
    
    # Save segments info to JSON
    output_json = {
        "youtube_url": youtube_url,
        "segments": segments
    }
    
    with open("frames_info.json", "w") as f:
        json.dump(output_json, f, indent=2)
    
    return segments

if __name__ == "__main__":
    timestamps = [0, 30, 60, 90]  # timestamps in seconds
    segments = extract_frames("https://www.youtube.com/watch?v=GAuCQe2qqro", timestamps)

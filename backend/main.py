from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import shutil
import uuid
from typing import List, Optional
from moviepy.editor import VideoFileClip, concatenate_videoclips
from klingai_client import KlingAIClient
from minimax_client import MinimaxClient

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Initialize API clients
klingai_client = None
minimax_client = None

try:
    print("Attempting to initialize KlingAI client...")
    klingai_client = KlingAIClient()
    print("KlingAI client initialized successfully")
except ValueError as e:
    print(f"Warning: KlingAI client initialization failed - {str(e)}")
except Exception as e:
    print(f"Error initializing KlingAI client: {str(e)}")

try:
    print("Attempting to initialize Minimax client...")
    minimax_client = MinimaxClient()
    print("Minimax client initialized successfully")
except ValueError as e:
    print(f"Warning: Minimax client not available - {str(e)}")
except Exception as e:
    print(f"Error initializing Minimax client: {str(e)}")

# Define API providers and check which ones are available
api_providers = []
if klingai_client:
    print("Adding KlingAI to available providers")
    api_providers.append({"id": "kling", "name": "Kling"})
if minimax_client:
    print("Adding Minimax to available providers")
    api_providers.append({"id": "minmax", "name": "Minimax"})

print(f"Available providers: {api_providers}")

class VideoGenerationRequest(BaseModel):
    prompts: List[str]
    provider: str = "kling"  # Default to Kling if not specified
    apiKey: str
    accessKeySecret: Optional[str] = None
    groupId: Optional[str] = None

@app.post("/upload-images")
async def upload_images(files: List[UploadFile] = File(...)):
    if len(files) < 1 or len(files) > 6:
        raise HTTPException(status_code=400, detail="Number of images must be between 1 and 6")
    
    saved_files = []
    for file in files:
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file_path)
    
    return {"message": "Images uploaded successfully", "files": saved_files}

@app.get("/api-providers")
async def get_api_providers():
    return {"providers": api_providers}

async def merge_videos(video_paths: List[str], output_path: str):
    """Merge multiple videos into one"""
    clips = [VideoFileClip(path) for path in video_paths]
    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile(output_path)
    
    # Clean up
    for clip in clips:
        clip.close()
    final_clip.close()
    
    # Remove temporary video files
    for path in video_paths:
        try:
            os.remove(path)
        except:
            pass

@app.post("/generate-video")
async def generate_video(request: VideoGenerationRequest, background_tasks: BackgroundTasks):
    try:
        prompts = request.prompts
        provider = request.provider
        
        print(f"Received video generation request - Provider: {provider}, Prompts: {prompts}")
        
        # Validate provider
        if provider == "kling" and not klingai_client:
            print("Error: KlingAI client not initialized")
            raise HTTPException(status_code=500, detail="Kling API not configured")
        elif provider == "minmax" and not minimax_client:
            print("Error: Minimax client not initialized")
            raise HTTPException(status_code=500, detail="Minimax API not configured")
        elif provider not in ["kling", "minmax"]:
            print(f"Error: Invalid provider {provider}")
            raise HTTPException(status_code=400, detail="Invalid API provider")
        
        if len(prompts) < 1 or len(prompts) > 6:
            print(f"Error: Invalid number of prompts {len(prompts)}")
            raise HTTPException(status_code=400, detail="Number of prompts must be between 1 and 6")
        
        # Get the latest uploaded images
        image_files = sorted([f for f in os.listdir(UPLOAD_DIR) if not f.startswith("temp_")], 
                           key=lambda x: os.path.getctime(os.path.join(UPLOAD_DIR, x)))
        image_paths = [os.path.join(UPLOAD_DIR, f) for f in image_files[-len(prompts):]]
        
        print(f"Found image paths: {image_paths}")
        
        if len(image_paths) != len(prompts):
            print(f"Error: Number of images ({len(image_paths)}) does not match number of prompts ({len(prompts)})")
            raise HTTPException(status_code=400, detail="Number of images does not match number of prompts")
        
        try:
            # Generate individual videos based on selected provider
            if provider == "kling":
                print("Generating videos with KlingAI")
                if not request.accessKeySecret:
                    raise HTTPException(status_code=400, detail="Access Key Secret is required for Kling API")
                video_paths = klingai_client.generate_videos(
                    image_paths, 
                    prompts, 
                    access_key_id=request.apiKey,
                    access_key_secret=request.accessKeySecret
                )
            else:  # minmax
                if not request.groupId:
                    print("Error: Missing Group ID for Minimax")
                    raise HTTPException(status_code=400, detail="Group ID is required for Minimax API")
                print("Generating videos with Minimax")
                video_paths = minimax_client.generate_videos(image_paths, prompts)
            
            print(f"Generated video paths: {video_paths}")
            
            # Generate a unique ID for the final video
            video_id = str(uuid.uuid4())
            final_video_path = os.path.join(UPLOAD_DIR, f"{video_id}.mp4")
            
            print(f"Final video path: {final_video_path}")
            
            # Merge videos in the background
            background_tasks.add_task(merge_videos, video_paths, final_video_path)
            
            return {
                "message": "Video generation started",
                "status": "processing",
                "video_id": video_id,
                "provider": provider
            }
        except Exception as e:
            print(f"Error during video generation: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        print(f"Unexpected error in generate_video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.api_route("/video/{video_id}", methods=["GET", "HEAD"])
async def get_video(video_id: str):
    video_path = os.path.join(UPLOAD_DIR, f"{video_id}.mp4")
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(video_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
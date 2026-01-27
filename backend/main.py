from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import os
import uuid
import re
from typing import List, Optional
from moviepy.editor import VideoFileClip, concatenate_videoclips
from klingai_client import KlingAIClient
from minimax_client import MinimaxClient
from dotenv import load_dotenv

load_dotenv()

# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Configure CORS with environment variable for allowed origins
# Default to localhost for development
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3001,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "HEAD"],  # Restrict to only needed methods
    allow_headers=["Content-Type", "Authorization"],  # Restrict headers
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

# Configuration for file uploads
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/gif"}
MAX_PROMPT_LENGTH = 1000  # Maximum characters per prompt

class VideoGenerationRequest(BaseModel):
    prompts: List[str]
    provider: str = "kling"  # Default to Kling if not specified
    apiKey: str
    accessKeySecret: Optional[str] = None
    groupId: Optional[str] = None

@app.post("/upload-images")
@limiter.limit("10/minute")
async def upload_images(request: Request, files: List[UploadFile] = File(...)):
    if len(files) < 1 or len(files) > 6:
        raise HTTPException(status_code=400, detail="Number of images must be between 1 and 6")

    saved_files = []
    for file in files:
        # Validate file type
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Only JPEG, PNG, and GIF images are allowed."
            )

        # Validate filename - only allow safe characters
        safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', file.filename)

        # Read file content to check size
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} exceeds maximum size of {MAX_FILE_SIZE / (1024*1024)}MB"
            )

        # Save file with sanitized name
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{safe_filename}")
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
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
@limiter.limit("5/minute")
async def generate_video(request_obj: Request, request: VideoGenerationRequest, background_tasks: BackgroundTasks):
    try:
        prompts = request.prompts
        provider = request.provider

        print(f"Received video generation request - Provider: {provider}")

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

        # Validate and sanitize prompts
        sanitized_prompts = []
        for i, prompt in enumerate(prompts):
            if not prompt or not prompt.strip():
                raise HTTPException(status_code=400, detail=f"Prompt {i+1} is empty")

            # Check prompt length
            if len(prompt) > MAX_PROMPT_LENGTH:
                raise HTTPException(
                    status_code=400,
                    detail=f"Prompt {i+1} exceeds maximum length of {MAX_PROMPT_LENGTH} characters"
                )

            # Sanitize prompt - remove any potentially dangerous characters
            sanitized_prompt = prompt.strip()
            sanitized_prompts.append(sanitized_prompt)

        prompts = sanitized_prompts
        
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
@limiter.limit("30/minute")
async def get_video(request: Request, video_id: str):
    # Validate video_id to prevent path traversal attacks
    # Only allow alphanumeric characters and hyphens (UUID format)
    if not re.match(r'^[a-zA-Z0-9\-]+$', video_id):
        raise HTTPException(status_code=400, detail="Invalid video ID format")

    # Construct the full path
    video_path = os.path.join(UPLOAD_DIR, f"{video_id}.mp4")

    # Verify the resolved path is within UPLOAD_DIR to prevent path traversal
    upload_dir_abs = os.path.abspath(UPLOAD_DIR)
    video_path_abs = os.path.abspath(video_path)

    if not video_path_abs.startswith(upload_dir_abs):
        raise HTTPException(status_code=400, detail="Invalid video path")

    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")

    return FileResponse(video_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
import os
import requests
import time
import jwt
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class KlingAIClient:
    def __init__(self):
        self.base_url = "https://api.klingai.com/v1"
        self.headers = {
            "Content-Type": "application/json"
        }

    def _get_auth_headers(self, access_key_id, content_type="application/json"):
        """Get headers with API key"""
        return {
            "Content-Type": content_type,
            "Authorization": f"Bearer {access_key_id}"  # Using access_key_id directly as Bearer token
        }

    def generate_video(self, image_path: str, prompt: str, access_key_id: str, access_key_secret: str) -> str:
        """
        Generate a 10-second video from an image and prompt using KlingAI API.
        Returns the path to the generated video.
        """
        try:
            print(f"Generating video for image: {image_path} with prompt: {prompt}")
            
            # Step 1: Upload the image to get URL
            print("Step 1: Uploading image")
            with open(image_path, "rb") as image_file:
                files = {"file": image_file}
                # Don't set Content-Type for multipart form upload
                upload_headers = {
                    "Authorization": f"Bearer {access_key_id}"
                }
                upload_response = requests.post(
                    f"{self.base_url}/upload",  # Using upload endpoint to get image URL
                    headers=upload_headers,
                    files=files
                )
                print(f"Upload response status: {upload_response.status_code}")
                upload_response.raise_for_status()
                image_url = upload_response.json()["data"]["url"]  # Get the uploaded image URL
                print(f"Image uploaded successfully with URL: {image_url}")

            # Step 2: Start video generation
            print("Step 2: Starting video generation")
            generation_response = requests.post(
                f"{self.base_url}/videos/image2video",  # Updated endpoint
                headers=self._get_auth_headers(access_key_id),
                json={
                    "model_name": "kling-v1",
                    "mode": "pro",
                    "duration": "10",
                    "image": image_url,
                    "prompt": prompt,
                    "cfg_scale": 0.5
                }
            )
            print(f"Generation response status: {generation_response.status_code}")
            generation_response.raise_for_status()
            task_id = generation_response.json()["data"]["taskId"]
            print(f"Video generation started with task ID: {task_id}")

            # Step 3: Poll for completion
            print("Step 3: Polling for completion")
            max_retries = 60  # 5 minutes maximum wait time (60 * 5 seconds)
            retry_count = 0
            
            while retry_count < max_retries:
                status_response = requests.get(
                    f"{self.base_url}/videos/tasks/{task_id}",  # Updated status endpoint
                    headers=self._get_auth_headers(access_key_id)
                )
                print(f"Status check response: {status_response.status_code}")
                status_response.raise_for_status()
                status_data = status_response.json()["data"]
                status = status_data["status"]
                progress = status_data.get("progress", 0)
                print(f"Current status: {status} - Progress: {progress}%")

                if status == "completed":
                    video_url = status_data["videoUrl"]
                    print(f"Video generation completed. URL: {video_url}")
                    break
                elif status == "failed":
                    error_msg = status_data.get("error", "Unknown error")
                    print(f"Video generation failed: {error_msg}")
                    raise Exception(f"Video generation failed: {error_msg}")
                elif status == "processing":
                    print(f"Video still processing... ({retry_count + 1}/{max_retries} checks)")
                else:
                    print(f"Unknown status: {status}")
                
                retry_count += 1
                if retry_count >= max_retries:
                    raise Exception("Video generation timed out after 5 minutes")
                
                time.sleep(5)  # Poll every 5 seconds

            # Step 4: Download the video
            print("Step 4: Downloading video")
            video_response = requests.get(video_url)
            print(f"Video download response status: {video_response.status_code}")
            video_response.raise_for_status()
            
            # Save the video to a temporary file
            output_path = f"uploads/temp_{task_id}.mp4"
            with open(output_path, "wb") as f:
                f.write(video_response.content)
            print(f"Video saved to: {output_path}")
            
            return output_path
        except Exception as e:
            print(f"Error in generate_video: {str(e)}")
            raise

    def generate_videos(self, image_paths: List[str], prompts: List[str], access_key_id: str, access_key_secret: str) -> List[str]:
        """
        Generate multiple videos from images and prompts.
        Returns a list of paths to the generated videos.
        """
        try:
            print(f"Generating videos for {len(image_paths)} images")
            if len(image_paths) != len(prompts):
                raise ValueError("Number of images must match number of prompts")
            
            generated_videos = []
            for i, (image_path, prompt) in enumerate(zip(image_paths, prompts)):
                print(f"Processing video {i+1}/{len(image_paths)}")
                video_path = self.generate_video(image_path, prompt, access_key_id, access_key_secret)
                generated_videos.append(video_path)
                print(f"Video {i+1} generated successfully")
            
            print(f"All videos generated successfully: {generated_videos}")
            return generated_videos
        except Exception as e:
            print(f"Error in generate_videos: {str(e)}")
            raise 
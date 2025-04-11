import os
import requests
import time
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class MinimaxClient:
    def __init__(self):
        self.api_key = os.getenv("MINIMAX_API_KEY")
        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY not found in environment variables")
        
        self.group_id = os.getenv("MINIMAX_GROUP_ID", "")
        if not self.group_id:
            raise ValueError("MINIMAX_GROUP_ID not found in environment variables")
        
        self.base_url = "https://api.minimax.chat/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generate_video(self, image_path: str, prompt: str) -> str:
        """
        Generate a 10-second video from an image and prompt using Minimax API.
        Returns the path to the generated video.
        """
        # Step 1: Upload the image to get a URL
        with open(image_path, "rb") as image_file:
            files = {"file": image_file}
            upload_response = requests.post(
                f"{self.base_url}/media/upload",
                headers={"Authorization": f"Bearer {self.api_key}"},
                files=files
            )
            upload_response.raise_for_status()
            image_url = upload_response.json().get("url")

        # Step 2: Request video generation
        generation_response = requests.post(
            f"{self.base_url}/text_to_video",
            headers=self.headers,
            json={
                "model": "video-gen",
                "image_url": image_url,
                "prompt": prompt,
                "duration": 10,
                "group_id": self.group_id,
                "quality": "high"
            }
        )
        generation_response.raise_for_status()
        task_id = generation_response.json().get("task_id")

        # Step 3: Poll for completion
        max_retries = 60  # 5 minutes with 5 second intervals
        retry_count = 0
        
        while retry_count < max_retries:
            status_response = requests.get(
                f"{self.base_url}/text_to_video/status/{task_id}",
                headers=self.headers
            )
            status_response.raise_for_status()
            status_data = status_response.json()
            
            if status_data.get("status") == "completed":
                video_url = status_data.get("result", {}).get("video_url")
                if video_url:
                    break
            elif status_data.get("status") == "failed":
                raise Exception(f"Video generation failed: {status_data.get('error', 'Unknown error')}")
            
            time.sleep(5)
            retry_count += 1
            
        if retry_count >= max_retries:
            raise Exception("Video generation timed out")

        # Step 4: Download the video
        video_response = requests.get(video_url)
        video_response.raise_for_status()
        
        # Save the video to a temporary file
        output_path = f"uploads/temp_minimax_{task_id}.mp4"
        with open(output_path, "wb") as f:
            f.write(video_response.content)
        
        return output_path

    def generate_videos(self, image_paths: List[str], prompts: List[str]) -> List[str]:
        """
        Generate multiple videos from images and prompts.
        Returns a list of paths to the generated videos.
        """
        if len(image_paths) != len(prompts):
            raise ValueError("Number of images must match number of prompts")
        
        generated_videos = []
        for image_path, prompt in zip(image_paths, prompts):
            video_path = self.generate_video(image_path, prompt)
            generated_videos.append(video_path)
        
        return generated_videos 
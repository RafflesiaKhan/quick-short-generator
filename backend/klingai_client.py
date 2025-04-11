import os
import requests
import time
import jwt
import base64 # Import base64
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class KlingAIClient:
    def __init__(self):
        self.base_url = "https://api.klingai.com/v1"

    def _encode_jwt_token(self, access_key_id: str, access_key_secret: str) -> str:
        """Generates a JWT token for Kling AI API authentication."""
        headers = {
            "alg": "HS256",
            "typ": "JWT"
        }
        payload = {
            "iss": access_key_id,
            "exp": int(time.time()) + 1800, # Token valid for 30 minutes
            "nbf": int(time.time()) - 5    # Token effective 5 seconds ago
        }
        token = jwt.encode(payload, access_key_secret, headers=headers)
        return token

    def _get_auth_headers(self, access_key_id: str, access_key_secret: str, content_type="application/json") -> Dict[str, str]:
        """Get headers with JWT authorization token."""
        token = self._encode_jwt_token(access_key_id, access_key_secret)
        return {
            "Content-Type": content_type,
            "Authorization": f"Bearer {token}"
        }

    def generate_video(self, image_path: str, prompt: str, access_key_id: str, access_key_secret: str) -> str:
        """
        Generate a 10-second video from an image and prompt using KlingAI API.
        Sends the image as Base64 directly to the image2video endpoint.
        Returns the path to the generated video.
        """
        try:
            print(f"Generating video for image: {image_path} with prompt: {prompt}")

            # Step 1: Read image and encode as Base64
            print("Step 1: Reading and encoding image as Base64")
            try:
                with open(image_path, "rb") as image_file:
                    image_bytes = image_file.read()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                print(f"Image encoded successfully (first 30 chars): {image_base64[:30]}...")
            except FileNotFoundError:
                print(f"Error: Image file not found at {image_path}")
                raise
            except Exception as e:
                print(f"Error reading or encoding image file: {str(e)}")
                raise

            # Step 2: Start video generation using Base64 image
            print("Step 2: Starting video generation using Base64 image")
            generation_headers = self._get_auth_headers(access_key_id, access_key_secret) # Default content-type is json
            generation_payload = {
                "model_name": "kling-v1",
                "mode": "pro",
                "duration": "10", # Consider making this dynamic or configurable
                "image": image_base64, # Pass Base64 string here
                "prompt": prompt,
                "cfg_scale": 0.5
            }
            
            # Log payload size for debugging (optional, Base64 can be long)
            # print(f"Generation payload size: {len(str(generation_payload))} bytes")
            
            generation_response = requests.post(
                f"{self.base_url}/videos/image2video",
                headers=generation_headers,
                json=generation_payload
            )
            print(f"Generation response status: {generation_response.status_code}")
            generation_response.raise_for_status()
            # Ensure the response is parsed correctly
            gen_response_json = generation_response.json()
            if "data" in gen_response_json and "task_id" in gen_response_json["data"]:
                task_id = gen_response_json["data"]["task_id"]
            else:
                print("Error: 'data' or 'task_id' key not found in generation response JSON")
                print(f"Generation Response JSON: {gen_response_json}")
                raise KeyError("Could not extract task ID from generation response.")
            print(f"Video generation started with task ID: {task_id}")

            # Step 3: Poll for completion
            print("Step 3: Polling for completion")
            max_retries = 180  # Increased to 15 minutes (180 * 5 seconds)
            retry_count = 0

            while retry_count < max_retries:
                # Generate a fresh token for each poll request, as the old one might expire
                polling_headers = self._get_auth_headers(access_key_id, access_key_secret, content_type=None) # No Content-Type for GET

                status_response = requests.get(
                    f"{self.base_url}/videos/image2video/{task_id}", # Corrected polling endpoint
                    headers=polling_headers
                )
                print(f"Status check response: {status_response.status_code} for task {task_id}")
                status_response.raise_for_status()
                # Ensure the response is parsed correctly
                status_response_json = status_response.json()
                if "data" in status_response_json:
                    status_data = status_response_json["data"]
                else:
                    print("Error: 'data' key not found in status response JSON")
                    print(f"Status Response JSON: {status_response_json}")
                    raise KeyError("Could not extract status data from polling response.")

                # Adjusted parsing based on Query Task documentation
                status = status_data.get("task_status")
                status_msg = status_data.get("task_status_msg", "") # Get status message if available
                # Progress might not be available in this response structure, remove if causing errors
                # progress = status_data.get("progress", 0) 
                print(f"Current task status: {status} {status_msg}")

                if status == "succeed": # Changed from "completed" based on doc
                     # Parse task_result structure based on doc
                    task_result = status_data.get("task_result", {})
                    videos = task_result.get("videos", [])
                    if videos and videos[0].get("url"):
                        video_url = videos[0]["url"]
                    else:
                        print("Error: 'task_result.videos[0].url' not found in successful task data")
                        print(f"Status Data: {status_data}")
                        raise KeyError("'videoUrl' missing from successful task.")
                    print(f"Video generation succeeded. URL: {video_url}")
                    break
                elif status == "failed":
                    error_msg = status_data.get("task_status_msg", "Unknown error")
                    print(f"Video generation task failed: {error_msg}")
                    raise Exception(f"Video generation task failed: {error_msg}")
                elif status == "processing" or status == "submitted": # Handle both processing states
                    print(f"Video task still processing... ({retry_count + 1}/{max_retries} checks)")
                else:
                    # Handle potential unknown statuses if the API defines others
                    print(f"Warning: Unknown task status encountered: {status}")

                retry_count += 1
                if retry_count >= max_retries:
                    print("Error: Video generation timed out.")
                    raise Exception("Video generation timed out after 15 minutes")

                time.sleep(5)  # Poll every 5 seconds

            # Step 4: Download the video
            print("Step 4: Downloading video")
            # No specific headers usually needed for direct download links
            video_response = requests.get(video_url)
            print(f"Video download response status: {video_response.status_code}")
            video_response.raise_for_status()

            # Save the video to a temporary file
            UPLOAD_DIR = "uploads"
            if not os.path.exists(UPLOAD_DIR):
                 os.makedirs(UPLOAD_DIR)
            # Use a consistent naming convention, maybe based on task ID
            output_path = os.path.join(UPLOAD_DIR, f"temp_{task_id}.mp4")

            with open(output_path, "wb") as f:
                f.write(video_response.content)
            print(f"Video saved to: {output_path}")

            return output_path
        except requests.exceptions.RequestException as e:
            # Handle specific request errors (like connection errors, timeouts)
            print(f"Network or API Request Error: {str(e)}")
            if e.response is not None:
                print(f"Response Status Code: {e.response.status_code}")
                try:
                    print(f"Response Body: {e.response.text}")
                except Exception:
                    print("Could not read response body.")
            raise # Re-raise after logging
        except KeyError as e:
            # Handle errors from missing keys in API responses
             print(f"API Response Format Error: Missing expected key - {str(e)}")
             raise # Re-raise after logging
        except Exception as e:
            # Catch other potential errors during the process
            print(f"An unexpected error occurred in generate_video: {str(e)}")
            # Consider logging the full traceback here for debugging
            # import traceback
            # print(traceback.format_exc())
            raise # Re-raise the original exception

    def generate_videos(self, image_paths: List[str], prompts: List[str], access_key_id: str, access_key_secret: str) -> List[str]:
        """
        Generate multiple videos from images and prompts.
        Returns a list of paths to the generated videos.
        """
        try:
            print(f"Generating videos for {len(image_paths)} images using KlingAI.")
            if len(image_paths) != len(prompts):
                raise ValueError("Number of images must match number of prompts")
            
            generated_videos = []
            for i, (image_path, prompt) in enumerate(zip(image_paths, prompts)):
                print(f"--- Processing video {i+1}/{len(image_paths)} ---")
                try:
                    video_path = self.generate_video(image_path, prompt, access_key_id, access_key_secret)
                    generated_videos.append(video_path)
                    print(f"--- Video {i+1} generated successfully: {video_path} ---")
                except Exception as e:
                    # Catch errors during single video generation but continue if possible
                    print(f"!!! Failed to generate video {i+1} for image {image_path}. Error: {str(e)} !!!")
                    # Decide if you want to stop all generation on first error or continue
                    # Option 1: Stop all generation
                    # raise Exception(f"Failed on video {i+1}. Stopping generation.") from e
                    # Option 2: Continue with next video (current behavior implicitly)
                    print("--- Continuing with next video generation ---")
                    # Optionally, add a placeholder or skip this video in the results
                    # generated_videos.append(None) # Or handle differently

            # Check if any videos were successfully generated
            successful_videos = [v for v in generated_videos if v is not None]
            if not successful_videos:
                 raise Exception("All video generations failed.")

            print(f"Finished generating videos. Successful count: {len(successful_videos)}/{len(image_paths)}")
            print(f"Generated video paths: {successful_videos}")
            return successful_videos # Return only successfully generated paths
        except ValueError as e: # Catch specific validation error
             print(f"Input Error in generate_videos: {str(e)}")
             raise
        except Exception as e:
            # Catch broader errors during the loop or final processing
            print(f"Error during bulk video generation (generate_videos): {str(e)}")
            raise 
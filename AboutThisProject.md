**Project Title:** AI Video Generator (Kling & Minimax Integration)

**1. Introduction:**

This project is a web application that allows users to generate short videos automatically using Artificial Intelligence. It takes multiple images and corresponding text prompts as input and leverages external AI video generation APIs (currently supporting Kling AI and Minimax) to animate each image according to its prompt. The resulting video segments are then seamlessly merged into a single final video.

**2. Core Features:**

*   **Multi-Image Upload:** Supports uploading 1 to 6 images via a user-friendly drag-and-drop interface or file selection.
*   **Per-Image Prompts:** Users provide individual text prompts for each uploaded image, describing the desired animation or content.
*   **Selectable AI Providers:** Offers a choice between different AI video generation services (Kling AI and Minimax).
*   **API Credential Management:** Allows users to input their specific API credentials (Access Key ID/Secret for Kling, API Key/Group ID for Minimax) for the chosen provider.
*   **Developer Mode:** Includes a "Dev Mode" toggle to use API credentials securely stored in environment variables, bypassing manual input during development.
*   **Segmented Generation:** Each image-prompt pair is processed independently by the selected AI service to generate an individual video segment.
*   **Background Video Merging:** Generated video segments are automatically merged into a single cohesive video file using background processing on the server.
*   **Real-time Status Updates:** The frontend polls the backend to provide status updates during the generation and merging process.
*   **Video Playback & Download:** Once completed, the final merged video is displayed in a player, and users can download the MP4 file.
*   **Error Handling:** Implements checks for invalid inputs (e.g., missing prompts, incorrect image count) and handles potential API errors during generation.

**3. Workflow:**

1.  **Launch:** The user accesses the React-based web interface.
2.  **Upload:** The user uploads 1-6 images. Image previews are displayed.
3.  **Prompt:** The user enters a text prompt for each uploaded image.
4.  **Select Provider:** The user chooses either Kling AI or Minimax from the available options.
5.  **Authenticate:**
    *   If Dev Mode is OFF: The user enters the required API credentials for the selected provider.
    *   If Dev Mode is ON: Credentials are automatically sourced from backend environment variables.
6.  **Initiate Generation:** The user clicks the "Generate Video" button.
7.  **Backend Processing:**
    *   The FastAPI backend receives the images, prompts, provider choice, and credentials.
    *   Images are temporarily stored on the server.
    *   The backend selects the appropriate API client (`KlingAIClient` or `MinimaxClient`).
    *   For each image/prompt:
        *   Authentication (JWT for Kling) is handled.
        *   Image data (Base64 for Kling) and prompt are sent to the AI API.
        *   The API is polled until the video segment is generated.
        *   The segment is downloaded to the server.
    *   Once all segments are ready, a background task (`Moviepy`) merges them into a final video file (`{video_id}.mp4`).
    *   The backend initially responds to the frontend with a `video_id`.
8.  **Frontend Polling:** The React frontend polls the `/video/{video_id}` endpoint using `HEAD` requests.
9.  **Completion:** Once the merged video file exists on the server, the backend responds with `200 OK` to the frontend's poll.
10. **Display & Download:** The frontend displays the video player with the final generated video and enables the download button.

**4. Technology Stack:**

*   **Frontend:** React, Axios, react-dropzone, Bootstrap CSS
*   **Backend:** Python, FastAPI, Moviepy, Requests, PyJWT

**5. Key Technical Aspects:**

*   **API Abstraction:** Separate client classes (`klingai_client.py`, `minimax_client.py`) encapsulate the logic for interacting with each specific external AI service.
*   **JWT Authentication:** Implemented for Kling AI API calls.
*   **Base64 Image Encoding:** Used for sending image data directly to the Kling AI generation endpoint.
*   **Asynchronous Processing:** Utilizes FastAPI's `BackgroundTasks` and `Moviepy` to perform time-consuming video merging without blocking the API response.
*   **Client-Side Polling:** The frontend uses polling with `HEAD` requests to efficiently check for the availability of the final video.

**6. Why You Need This Project:**

In the rapidly evolving landscape of AI video generation, Kling AI and Minimax stand out as leading models for creating compelling short-form content. However, using their services often means juggling separate interfaces, managing different workflows, and potentially incurring higher costs through web UIs compared to direct API access. This project consolidates access to these powerful tools into a single, streamlined application. It eliminates the hassle of navigating multiple platforms, offering a unified and potentially more cost-effective way to leverage the best AI video models through their APIs. By providing a superior user experience focused specifically on multi-image short video creation, this tool becomes your one-stop storybook for quickly turning image sequences and ideas into engaging animated narratives.

**7. Future Improvements:**

*   **Additional AI Providers:** Integrate other popular video generation APIs (e.g., RunwayML, Pika Labs) to offer users more creative options.
*   **Advanced Prompting:** Introduce features like negative prompts or style references for more fine-grained control over the output.
*   **Video Editing Features:** Add basic post-generation editing capabilities within the app (e.g., trimming, reordering segments, adding text overlays or background music).
*   **Template System:** Allow users to save and reuse prompt/image combinations or stylistic settings.
*   **Improved Status Tracking:** Provide more granular progress updates during the AI generation phase (if the APIs support it).
*   **User Accounts & History:** Implement user accounts to save generated videos and track usage history.
*   **Cost Estimation:** Integrate API cost estimation based on provider pricing and video length/mode.
*   **Configurable Parameters:** Expose more API parameters (like `cfg_scale`, specific model versions, etc.) to the user interface for advanced control.



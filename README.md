# Video Generator with KlingAI and Minimax API

This project allows users to upload 1-6 images, provide prompts for each image, and generate a video using either KlingAI's or Minimax's API. The generated videos are merged into a single video file.

## Features

- Upload 1-6 images
- Add prompts for each image
- Choose between KlingAI and Minimax APIs for video generation
- Generate 10-second videos for each image
- Merge all videos into a single output
- Modern and user-friendly interface

## Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn

## Setup

### Backend Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r backend/requirements.txt
```

3. Create a `.env` file in the backend directory with your API keys:
```
# KlingAI Credentials
KLINGAI_ACCESS_KEY_ID=your_klingai_access_key_id_here
KLINGAI_ACCESS_KEY_SECRET=your_klingai_access_key_secret_here

# Minimax Credentials (optional)
MINIMAX_API_KEY=your_minimax_api_key_here
MINIMAX_GROUP_ID=your_minimax_group_id_here
```

Note: You only need to provide the API keys for the services you plan to use. The application will automatically detect available APIs.

4. Run the backend server:
```bash
cd backend
uvicorn main:app --reload
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm start
```

## Usage

1. Open your browser and navigate to `http://localhost:3001`
2. Upload 1-6 images by dragging and dropping or clicking to select
3. Add prompts for each image
4. Select your preferred API provider (KlingAI or Minimax)
5. Click "Generate Video" when ready
6. Wait for the video generation to complete
7. The merged video will be displayed and can be downloaded

## Project Structure

```
project/
├── frontend/           # React frontend
├── backend/           # FastAPI backend
│   ├── klingai_client.py  # KlingAI API client
│   ├── minimax_client.py  # Minimax API client
│   └── main.py        # FastAPI application
├── uploads/          # Temporary storage for uploaded files
└── README.md
```

## API Endpoints

- `POST /upload-images`: Upload images
- `GET /api-providers`: Get available API providers
- `POST /generate-video`: Generate video from images and prompts
- `GET /video/{video_id}`: Get the generated video

## Getting API Keys

### KlingAI API
To get KlingAI credentials:
1. Visit [KlingAI's website](https://klingai.com)
2. Sign up for an account
3. Navigate to the API section in your dashboard
4. You will receive:
   - Access Key ID: Used to identify your account
   - Access Key Secret: Used to verify your identity (keep this secure)

### Minimax API
To get a Minimax API key:
1. Visit [Minimax's website](https://minimax.chat)
2. Create an account
3. Navigate to the developer section
4. Create a project to get your API key and Group ID

## Demo

Watch a demo video of the application in action: [Video Generator Demo](https://youtu.be/o2ag4GX7GZE)

## Try It Out & Future Ideas

We encourage you to clone this repository, set it up using the instructions above, and generate your own videos!

If you're interested in expanding the project, consider tackling some of the potential improvements mentioned in the `AboutThisProject.md` file, such as:

*   Integrating other AI video providers (RunwayML, Pika Labs, etc.)
*   Adding advanced prompting options (negative prompts, style references)
*   Implementing basic video editing features (trimming, music)
*   Building a template system

Feel free to fork the repository, experiment, and share your enhancements! If you encounter issues or have suggestions, please open an issue on the GitHub repository. 
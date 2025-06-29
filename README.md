# youtube_transcriber_tool
Tired of scrubbing through long videos to find the information you need? This tool leverages the power of Large Language Models to instantly transcribe, summarize, and even chat with the content of any YouTube video.

✨ Features
Instant Transcription: Get the full text transcript of a video in seconds.
Interactive Player: The video is embedded on the page, and you can click on any timestamp in the transcript to jump directly to that moment in the video.
AI-Powered Summaries: Generate a quick, one-paragraph summary or a more comprehensive, detailed summary for long videos.
Key Point Extraction: Automatically pull out the main ideas as a clean list of bullet points.
Chat with the Video: Ask specific questions about the video's content and get contextual answers directly from an AI that has "watched" the video for you.

🛠️ Technology Stack
Backend: Python
Web UI Framework: Gradio - A fast and simple way to build interactive UIs for machine learning applications.
YouTube Interaction:
youtube-transcript-api: For instantly fetching pre-existing text transcripts.
yt-dlp: A robust library used to fetch video metadata like the title.
AI & Language Model: Google Gemini API (specifically, the gemini-1.5-flash-latest model) for all natural language processing tasks, including summaries, bullet points, and chat.

⚙️ Setup and Local Installation
To run this project on your own machine, follow these steps:
Clone the repository:
Bash
git clone https://github.com/YOUR_USERNAME/youtube-transcriber-app.git
cd youtube-transcriber-app

Create and activate a Python virtual environment:

Bash
# Create the environment
python -m venv venv
# Activate on Windows
.\venv\Scripts\activate

Install the required dependencies:
Bash
pip install -r requirements.txt

Create a .env file for your API key. In the main project folder, create a file named .env and add your Google Gemini API key to it like this:
GOOGLE_API_KEY="PASTE_YOUR_API_KEY_HERE"

Run the application:
Bash
python app.py

🚀 Future Improvements
Mind Map Generation: An AI feature to visually map out the core concepts of the video.
Export Options: Add buttons to download the transcript or summaries as .txt or .pdf files.

Important Security Update for Your app.py
Never put secret API keys directly in your code when you upload it to a public place like GitHub. The best practice is to load them from a local .env file that you do not upload.

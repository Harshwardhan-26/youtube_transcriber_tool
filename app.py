import gradio as gr
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import google.generativeai as genai

# --- CONFIGURE THE GEMINI AI ---
# IMPORTANT: Paste your API Key here.
GOOGLE_API_KEY = "AIzaSyC_RsVg-6WDL7pNC1bfLpNTLZOefPghhns"
genai.configure(api_key=GOOGLE_API_KEY)
# -----------------------------


# --- ALL BACKEND FUNCTIONS ARE DEFINED FIRST ---

def get_video_info_and_transcript(url):
    """Gets title and transcript using reliable libraries."""
    try:
        video_id = url.split("v=")[1].split("&")[0]
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video_title = info_dict.get('title', 'Unknown Title')
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return video_id, video_title, transcript_list
    except Exception as e:
        raise gr.Error(f"Failed to get transcript. Is it a valid YouTube URL with transcripts enabled? Error: {e}")

def rebatch_transcript(transcript_list, min_gap_seconds=80):
    """Groups transcript segments into larger paragraphs."""
    if not transcript_list: return []
    batched_transcript = []
    current_batch_text = transcript_list[0].get('text', '')
    current_batch_start_time = transcript_list[0]['start']
    for i in range(1, len(transcript_list)):
        segment = transcript_list[i]
        time_since_batch_start = segment['start'] - current_batch_start_time
        if time_since_batch_start >= min_gap_seconds and current_batch_text:
            batched_transcript.append({'text': current_batch_text.strip(), 'start': current_batch_start_time})
            current_batch_text = segment['text']
            current_batch_start_time = segment['start']
        else:
            current_batch_text += " " + segment['text']
    batched_transcript.append({'text': current_batch_text.strip(), 'start': current_batch_start_time})
    return batched_transcript

def get_short_summary(transcript):
    if not transcript: return "Please generate a transcript first."
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest') 
        prompt = f"Generate a short, one-paragraph summary of the following video transcript:\n\n{transcript[:20000]}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e: return f"An error occurred during summary generation: {e}"

def generate_detailed_summary(transcript):
    if not transcript: return "Please generate a transcript first."
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        chunk_size = 12000; overlap = 1000
        chunks = [transcript[i:i + chunk_size] for i in range(0, len(transcript), chunk_size - overlap)]
        
        print(f"Transcript divided into {len(chunks)} chunks for detailed summary.")
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            print(f"Summarizing chunk {i+1} of {len(chunks)}...")
            prompt = f"This is one part of a larger video transcript. Please provide a concise summary of just this section:\n\n{chunk}"
            response = model.generate_content(prompt)
            chunk_summaries.append(response.text)

        print("All chunks summarized. Creating final summary...")
        combined_summary_text = "\n".join(chunk_summaries)
        final_prompt = f"The following are summaries of sequential parts of a video. Please combine them into a single, detailed, and coherent summary of the entire video:\n\n{combined_summary_text}"
        final_response = model.generate_content(final_prompt)
        print("Final summary generated!")
        return final_response.text
    except Exception as e: return f"An error occurred during detailed summary generation: {e}"

def get_bullet_points(transcript):
    if not transcript: return "Please generate a transcript first."
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest') 
        prompt = f"Based on the following video transcript, extract the main ideas and present them as a concise list of bullet points. Each bullet point should be on a new line and start with a '*' character:\n\n{transcript}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e: return f"An error occurred during bullet point generation: {e}"

def chat_with_video(chat_message, chat_history, current_transcript):
    if not current_transcript: return "Please generate a transcript first before chatting."
    try:
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
        prompt = f"You are a helpful assistant. Your task is to answer a user's question based *only* on the provided video transcript.\nIf the answer is not in the transcript, say \"I could not find an answer to that in the video.\"\n\nHere is the full video transcript for context:\n---\n{current_transcript}\n---\n\nHere is the conversation history so far:\n{chat_history}\n\nNew Question: {chat_message}\n\nYour Answer:"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e: return f"Sorry, an error occurred: {e}"


# --- MAIN UI CODE ---
with gr.Blocks(title="YouTube Transcriber", theme=gr.themes.Soft()) as app:
    transcript_state = gr.State(value="") 

    gr.Markdown("# 🗣️ YouTube Video Transcriber & Analyzer")
    with gr.Row():
        youtube_url = gr.Textbox(label="YouTube URL", placeholder="https://www.youtube.com/watch?v=...", scale=3)
        generate_btn = gr.Button("Generate", variant="primary", scale=1)
    
    error_output = gr.Textbox(label="Status", visible=True, interactive=False)
    video_title_md = gr.Markdown(visible=False)
    video_player = gr.HTML(visible=False)      
    interactive_transcript_display = gr.HTML(visible=False)

    with gr.Tabs():
        with gr.TabItem("AI Features & Chat"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### AI Summaries & Points")
                    short_summary_output = gr.Textbox(label="Short Summary", lines=6, interactive=False)
                    short_summary_btn = gr.Button("Generate Short Summary")
                    detailed_summary_output = gr.Textbox(label="Detailed Summary", lines=12, interactive=False)
                    detailed_summary_btn = gr.Button("Generate Detailed Summary")
                    bullet_points_output = gr.Textbox(label="Key Bullet Points", lines=10, interactive=False)
                    bullet_points_btn = gr.Button("Generate Bullet Points")
                with gr.Column(scale=2):
                    gr.ChatInterface(fn=chat_with_video, additional_inputs=[transcript_state], additional_inputs_accordion="Video Transcript Context")
        
        with gr.TabItem("Full Transcript"):
             gr.Markdown("The interactive transcript will appear above after you click 'Generate'.")

    def format_timestamp(seconds):
        minutes = int(seconds // 60); seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def on_generate_click(url):
        try:
            yield {error_output: gr.update(value="Starting generation...", visible=True), video_title_md: gr.update(visible=False), video_player: gr.update(visible=False), interactive_transcript_display: gr.update(visible=False)}
            video_id, video_title, raw_transcript_list = get_video_info_and_transcript(url)
            
            yield {error_output: gr.update(value="Processing data...")}
            paragraph_transcript = rebatch_transcript(raw_transcript_list)
            full_transcript_text = " ".join([d['text'] for d in raw_transcript_list])
            
            transcript_html = "<style> .transcript-p { margin-bottom: 20px; line-height: 1.6; font-family: sans-serif; padding-left: 10px; } .timestamp-link { color: #007bff; text-decoration: none; font-weight: bold; cursor: pointer; } </style>"
            transcript_html += """<script>
                var player;
                function onYouTubeIframeAPIReady() { player = new YT.Player('youtube-player-iframe'); }
                function seekTo(seconds) { if (player) { player.seekTo(seconds, true); } }
            </script>"""
            for segment in paragraph_transcript:
                start_time = segment['start']
                formatted_time = format_timestamp(start_time)
                text = segment['text'].strip()
                transcript_html += f'<p class="transcript-p"><a href="#" onclick="seekTo({start_time}); return false;" class="timestamp-link">{formatted_time}</a>{text}</p>'
            
            video_embed_html = f'<iframe id="youtube-player-iframe" width="100%" height="400" src="https://www.youtube.com/embed/{video_id}?enablejsapi=1" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe><script src="https://www.youtube.com/iframe_api"></script>'
            title_md_output = f"### {video_title}\n[Visit on YouTube]({url})"
            
            yield {
                transcript_state: full_transcript_text,
                error_output: gr.update(value="Done!", visible=True),
                video_title_md: gr.update(value=title_md_output, visible=True),
                video_player: gr.update(value=video_embed_html, visible=True),
                interactive_transcript_display: gr.update(value=transcript_html, visible=True)
            }
        except Exception as e:
            yield {error_output: gr.update(value=f"An error occurred: {e}", visible=True)}

    generate_btn.click(fn=on_generate_click, inputs=youtube_url, outputs=[transcript_state, video_title_md, video_player, interactive_transcript_display, error_output])
    short_summary_btn.click(fn=get_short_summary, inputs=transcript_state, outputs=short_summary_output)
    detailed_summary_btn.click(fn=generate_detailed_summary, inputs=transcript_state, outputs=detailed_summary_output)
    bullet_points_btn.click(fn=get_bullet_points, inputs=transcript_state, outputs=bullet_points_output)

app.launch(debug=True,share=True)
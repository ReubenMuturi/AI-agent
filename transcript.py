# example inputs
# 1 - https://www.youtube.com/watch?v=rCPXBkeBWCQ
# 2 - https://en.wikipedia.org/wiki/Artificial_intelligence


import os
import openai
import tiktoken  # For accurate token counting
import logging
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from googleapiclient.discovery import build
from google.oauth2 import service_account
import requests
from bs4 import BeautifulSoup

# Load API keys securely
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")
SCOPES = ["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive"]
TOKEN_LIMIT = 2048

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_google_credentials():
    """Load Google API credentials."""
    try:
        credentials = service_account.Credentials.from_service_account_file(GOOGLE_CREDENTIALS_PATH, scopes=SCOPES)
        return credentials
    except Exception as e:
        logging.error(f"Failed to load Google credentials: {e}")
        return None

def create_google_doc(title, content):
    """Create a Google Docs file, insert content, and set permissions."""
    credentials = get_google_credentials()
    if not credentials:
        return None

    try:
        service = build("docs", "v1", credentials=credentials)
        drive_service = build("drive", "v3", credentials=credentials)
        
        # Create document
        doc = service.documents().create(body={"title": title}).execute()
        doc_id = doc.get("documentId")
        
        # Insert content
        requests = [{"insertText": {"location": {"index": 1}, "text": content}}]
        service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
        
        # Set document permissions (make public)
        permission = {
            "type": "anyone",
            "role": "reader"
        }
        drive_service.permissions().create(
            fileId=doc_id,
            body=permission,
            fields="id"
        ).execute()

        return f"https://docs.google.com/document/d/{doc_id}"
    except Exception as e:
        logging.error(f"Failed to create Google Doc: {e}")
        return None

def summarize_content(content):
    """Summarize text content using OpenAI."""
    if not content.strip():
        return "No content provided."
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "Summarize the following content:"},
                      {"role": "user", "content": content}],
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

def scrape_website(url):
    """Extract text content from a webpage."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        return "\n".join(p.get_text() for p in paragraphs if p.get_text()) or "No content found."
    except requests.exceptions.RequestException as e:
        return f"Error scraping website: {e}"

def extract_video_id(video_url):
    """Extract YouTube video ID from URL."""
    parsed_url = urlparse(video_url)
    video_id = parse_qs(parsed_url.query).get("v")
    return video_id[0] if video_id else parsed_url.path.split("/")[-1] if "/shorts/" in parsed_url.path else None

def get_youtube_transcript(video_url):
    """Fetch and truncate YouTube transcript if needed."""
    video_id = extract_video_id(video_url)
    if not video_id:
        return None
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = "\n".join(entry['text'] for entry in transcript)
        return transcript_text[:TOKEN_LIMIT]  # Truncate if needed
    except Exception as e:
        logging.error(f"Failed to fetch transcript: {e}")
        return None

def generate_text(prompt, model="gpt-3.5-turbo", max_tokens=1000):
    """Generate AI text from a given prompt."""
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"AI Text Generation Failed: {e}")
        return None

def main():
    """Main function to process user choice."""
    print("Choose an option:")
    print("Process a YouTube transcript")
    print("Scrape a website and summarize")
    choice = input("Enter 1 or 2: ").strip()
    if choice == "1":
        video_url = input("Enter YouTube video URL: ").strip()
        transcript = get_youtube_transcript(video_url)
        if transcript:
            summary = summarize_content(transcript)
            doc_link = create_google_doc("YouTube Transcript Summary", summary)
            print(f"Summary saved: {doc_link}")
    elif choice == "2":
        url = input("Enter website URL: ").strip()
        content = scrape_website(url)
        summary = summarize_content(content)
        doc_link = create_google_doc("Website Summary", summary)
        print(f"Summary saved: {doc_link}")
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()

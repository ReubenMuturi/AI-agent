import os
import openai
import tiktoken  # For accurate token counting
import logging
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from googleapiclient.discovery import build
from google.oauth2 import service_account
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import openai
import datetime


# Load API key from environment variables or a secure file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Corrected

def summarize_content(content):
    """
    Summarizes the given text content using OpenAI's GPT-4.
    
    :param content: The text content to summarize.
    :return: A summarized version of the text.
    """
    if not content or content.strip() == "":
        return "No content provided for summarization."

    try:
        openai.api_key = OPENAI_API_KEY
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "Summarize the following content:"},
                      {"role": "user", "content": content}],
            max_tokens=300
        )

        return response["choices"][0]["message"]["content"].strip()
    
    except Exception as e:
        return f"Error generating summary: {e}"


def scrape_website(url):
    """
    Fetches and extracts text content from the given website URL.
    
    :param url: The URL of the webpage to scrape.
    :return: Extracted text content as a string.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0"}  # Helps prevent blocking
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (e.g., 404, 500)
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract text from paragraphs
        paragraphs = soup.find_all("p")
        content = "\n".join(p.get_text() for p in paragraphs if p.get_text())

        return content if content else "No content found on the page."
    
    except requests.exceptions.RequestException as e:
        return f"Error scraping website: {e}"


client = openai.OpenAI()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load Google API credentials securely
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")

if not GOOGLE_CREDENTIALS_PATH:
    import logging
    logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.error("Missing Google API credentials. Set GOOGLE_CREDENTIALS_PATH as an environment variable.")
    raise ValueError("Missing Google API credentials.")

print(f"Google credentials found: {GOOGLE_CREDENTIALS_PATH}")


SCOPES = ["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive"]

# Load credentials from the service account file
def get_google_credentials():
    try:
        credentials = service_account.Credentials.from_service_account_file(
            "central-web-451617-v6-f1ac1704fe2a.json", scopes=SCOPES
        )
        return credentials
    except Exception as e:
        logging.error(f"Failed to load Google credentials: {e}")
        return None

def create_google_doc(title, content):
    """Create a Google Docs file and insert AI-generated content."""
    credentials = get_google_credentials()
    if not credentials:
        logging.error("Google API authentication failed.")
        return None

    try:
        service = build("docs", "v1", credentials=credentials)
        doc = service.documents().create(body={"title": title}).execute()
        doc_id = doc.get("documentId")

        # Insert content into the document
        requests = [{"insertText": {"location": {"index": 1}, "text": content}}]
        service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

        doc_url = f"https://docs.google.com/document/d/{doc_id}"
        logging.info(f"✅ Google Doc created successfully: {doc_url}")
        return doc_id
    except Exception as e:
        logging.error(f"❌ Failed to create Google Doc: {e}")
        return None

# Load API Key securely

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Corrected

if not OPENAI_API_KEY:
    logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.error("Missing OpenAI API Key. Set it as an environment variable.")
    raise ValueError("Missing OpenAI API Key.")

openai.api_key = OPENAI_API_KEY
print("OpenAI API Key loaded successfully.")

# Define token limit
TOKEN_LIMIT = 2048  # Maximum tokens OpenAI models can process in a single request

def extract_video_id(video_url):
    """Extract the video ID from a YouTube URL."""
    parsed_url = urlparse(video_url)
    video_id = parse_qs(parsed_url.query).get("v")
    if video_id:
        return video_id[0]
    elif parsed_url.path.startswith("/shorts/"):
        return parsed_url.path.split("/")[-1]
    return None

def count_tokens(text):
    """Count tokens in the given text using OpenAI's tokenizer."""
    encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
    return len(encoder.encode(text))

def truncate_text(text, max_tokens=TOKEN_LIMIT):
    """Truncate text to fit within a token limit."""
    encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
    tokens = encoder.encode(text)
    truncated_tokens = tokens[:max_tokens]  
    return encoder.decode(truncated_tokens)

def get_youtube_transcript(video_url):
    """Fetch transcript of a YouTube video and truncate if needed."""
    video_id = extract_video_id(video_url)
    if not video_id:
        logging.error("Invalid YouTube URL")
        return None

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = "\n".join([entry['text'] for entry in transcript])

        if count_tokens(transcript_text) > TOKEN_LIMIT:
            transcript_text = truncate_text(transcript_text, TOKEN_LIMIT)

        return transcript_text
    except Exception as e:
        logging.error(f"Failed to fetch transcript: {e}")
        return None

def generate_outline(transcript_text):
    """Generate a structured outline using OpenAI."""
    prompt = f"Summarize the following transcript into a structured outline:\n\n{transcript_text}\n\nOutline:"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000  
        )
        return response.choices[0].message.content.strip()  # Use dot notation
    except Exception as e:
        logging.error(f"OpenAI Outline Generation Failed: {e}")
        return None


def generate_blog_post(outline_text):
    """Generate a full blog post from the structured outline."""
    prompt = f"Write a detailed and engaging blog post based on the following outline:\n\n{outline_text}\n\nBlog Post:"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000  
        )
        return response.choices[0].message.content.strip()  # Use dot notation
    except Exception as e:
        logging.error(f"OpenAI Blog Post Generation Failed: {e}")
        return None

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Store your API key in an environment variable

def generate_text(prompt):
    """Generates AI-generated text using GPT-3."""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Use GPT-3.5 for efficiency
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Example Usage
print(generate_text("Write a blog introduction on AI automation."))

def main():
    print("Choose an option:")
    print("1️⃣ Process a YouTube transcript")
    print("2️⃣ Scrape a website and summarize")
    
    choice = input("Enter 1 or 2: ").strip().lower()

    if choice == "1":
        video_url = input("Enter the YouTube video URL: ").strip()
        transcript = get_youtube_transcript(video_url)

        if transcript:
            outline = generate_outline(transcript)
            if outline:
                logging.info("\nGenerated Outline:\n" + outline)

                blog_post = generate_blog_post(outline)
                if blog_post:
                    logging.info("\nGenerated Blog Post:\n" + blog_post)

                    # Save to a file with timestamp
                    filename = f"blog_post_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    with open(filename, "w", encoding="utf-8") as file:
                        file.write(blog_post)

                    # Upload to Google Docs
                    doc_id = create_google_doc("AI-Generated Blog Post", blog_post)
                    if doc_id:
                        logging.info(f"Document uploaded successfully: {doc_id}")
                else:
                    logging.error("Failed to generate blog post.")
            else:
                logging.error("Failed to generate outline.")
        else:
            logging.error("Failed to fetch YouTube transcript.")

    elif choice == "2":
        url = input("Enter the URL to scrape: ").strip()
        
        print("\n🔄 Scraping website...")
        scraped_content = scrape_website(url)
        
        if "Error" in scraped_content:
            print(scraped_content)
            return

        print("\n📝 Generating summary...")
        summary = summarize_content(scraped_content)

        print("\n✅ Summary:\n")
        print(summary)

    else:
        print("❌ Invalid choice. Please enter 1 or 2.")

if __name__ == "__main__":
    main()



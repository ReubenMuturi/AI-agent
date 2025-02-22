<!-- # YouTube Transcript & Web Scraper

This script extracts transcripts from YouTube videos or scrapes text content from a website, summarizes the extracted content using OpenAI's API, and saves it to a Google Docs file with public read access.

## Requirements

### API Keys and Credentials
- OpenAI API Key
- Google Cloud Service Account JSON file (for Google Docs and Drive access)

### Python Libraries
Make sure you have the following Python libraries installed:
```sh
pip install openai google-auth google-auth-oauthlib google-auth-httplib2 google-auth googleapiclient requests beautifulsoup4 youtube-transcript-api
```

## Setup

1. **Set Up API Keys and Credentials**
   - Store your OpenAI API Key in an environment variable:
     ```sh
     export OPENAI_API_KEY="your_openai_api_key"
     ```
   - Set the path to your Google Cloud Service Account credentials:
     ```sh
     export GOOGLE_CREDENTIALS_PATH="path/to/your/service_account.json"
     ```

2. **Run the Script**
   Execute the script using:
   ```sh
   python script.py
   ```

3. **Choose an Option**
   - Enter `1` to process a YouTube transcript.
   - Enter `2` to scrape and summarize a website.

4. **Provide Input**
   - For YouTube: Enter the YouTube video URL.
   - For Website: Enter the webpage URL.

5. **View Summary**
   - The script will generate a summary and create a Google Docs file.
   - A link to the Google Docs file will be displayed in the terminal.

## Features
- Extracts YouTube video transcripts automatically.
- Scrapes webpage text content.
- Uses OpenAI to summarize extracted text.
- Saves the summary to Google Docs.
- Sets public read permissions for easy access.

## Notes
- Ensure your Google Cloud Service Account has permissions to create and edit Google Docs.
- The script automatically grants public read access to the generated Google Docs file.

 -->

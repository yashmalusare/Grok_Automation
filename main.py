from dotenv import load_dotenv
import requests
import os
load_dotenv(override=True)



import requests
import os
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import streamlit as st
import json
import re

load_dotenv(override=True)
# Setup for Google Sheets and environment variables
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
CREDENTIALS_FILE = 'startup-441418-b11058491d88.json'  # Path to credentials file
API_KEY = "xai-Age3ZQ1iREPjsun617Q4dfYD7rrssFYJilahzawzyA1U7Z3Cuxr22EMvW40AneyD6KeXKdYNxWYrpSiw"  # Replace with actual API key
SENDER_EMAIL = "20210802074@dypiu.ac.in"  # Replace with sender email
SENDER_PASSWORD = "pvud cnvc xwto bdnv"  # Replace with sender email password

# Helper function to get Google Sheets service
def get_gsheet_service():
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPE)
    client = gspread.authorize(creds)
    return client

# Function to scrape and retrieve content from LinkedIn using Jina API
def get_content(linkedin_url: str) -> str:
    """Scrape LinkedIn profile content using Jina API."""
    jina_url = f'https://r.jina.ai/{linkedin_url}'
    headers = {
        "X-Return-Format": "markdown",
        "Authorization": f"Bearer {os.getenv('READER_API_KEY')}"
    }
    try:
        response = requests.get(jina_url, headers=headers, timeout=10)
        if response.status_code == 200:
            content = response.text[:1800]
            if content:
                st.write(f"LinkedIn content retrieved for URL: {linkedin_url}")
                return content
            else:
                st.write(f"No content retrieved for URL: {linkedin_url}")
        else:
            st.write(f"Failed to retrieve content for {linkedin_url} - Status Code: {response.status_code}")
    except Exception as e:
        st.write(f"Error fetching LinkedIn content for {linkedin_url}: {e}")
    return ""

# Function to evaluate a candidate's suitability with Grok based on LinkedIn content
def evaluate_candidate_with_grok(content: str, name: str) -> dict:
    """Get rating and evaluation using Grok API."""
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are Grok, an AI designed to evaluate candidate suitability."
            },
            {
                "role": "user",
                "content": f"Evaluate the following LinkedIn content for candidate '{name}' on a scale of 1-10 for suitability. Provide the rating and reasoning.\n\n{content}"
            }
        ],
        "model": "grok-beta",
        "temperature": 0.7
    }
    response = requests.post("https://api.x.ai/v1/chat/completions", headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }, data=json.dumps(payload))
    
    if response.status_code == 200:
        result = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        evaluation = parse_grok_response(result)
        st.write(f"Grok evaluation for {name}: {evaluation}")
        return evaluation
    st.write(f"Failed to evaluate candidate {name} - Status Code: {response.status_code}")
    return {"rating": 0, "reason": "Error in retrieving data"}

# Helper function to parse Grok's response
def parse_grok_response(response_text: str) -> dict:
    """Extract rating and reason from Grok's response."""
    rating_match = re.search(r'(\d{1,2})/10', response_text)
    rating = int(rating_match.group(1)) if rating_match else 0
    reason = response_text.split("Reason:", 1)[1].strip() if "Reason:" in response_text else response_text
    return {"rating": rating, "reason": reason}

# Function to send emails to candidates meeting the threshold rating
# Function to send emails to candidates meeting the threshold rating
def send_email(candidate, email_content):
    email = candidate.get('Emails', '').strip()  # Get and trim the email address
    
    # Check if email is valid (not empty and basic email format check)
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        st.write(f"Invalid or missing email for {candidate['Applicant Name']}. Skipping email.")
        return  # Skip sending email if the email is invalid
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = email
    msg['Subject'] = "Wassup Flea Event Invitation"
    msg.attach(MIMEText(email_content, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, email, msg.as_string())
        st.write(f"Email sent to {email}")
    except smtplib.SMTPRecipientsRefused:
        st.write(f"Email not sent to {email} due to invalid recipient address.")
    except Exception as e:
        st.write(f"Failed to send email to {email}: {e}")


# Main function for Streamlit app
def main():
    st.title("Event Invitation Email Automation with Candidate Screening")
    
    google_sheet_id = st.text_input("Enter Google Sheet ID:")
    
    if google_sheet_id:
        client = get_gsheet_service()
        sheet = client.open_by_key(google_sheet_id).sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        date = st.text_input("Enter Event Date:")
        time = st.text_input("Enter Event Time:")
        location = st.text_input("Enter Event Location:")
        event_description = st.text_area("Enter Event Description:")
        threshold_rating = st.slider("Select Minimum Rating for Invitation", 1, 10, 7)

        if date and time and location and event_description:
            if st.button("Evaluate and Send Invitations"):
                df['Rating'] = 0
                df['Evaluation Reason'] = ""
                df['Status'] = "Not Selected"
                
                for idx, row in df.iterrows():
                    linkedin_url = row['Linked In']
                    content = get_content(linkedin_url)
                    if content:
                        evaluation = evaluate_candidate_with_grok(content, row['Applicant Name'])
                        df.at[idx, 'Rating'] = evaluation['rating']
                        df.at[idx, 'Evaluation Reason'] = evaluation['reason']
                        
                        if evaluation['rating'] >= threshold_rating:
                            email_content = f"""Hello {row['Applicant Name']},\n
                            You're invited to our exciting event happening on {date} at {location} from {time}.\n\n{event_description}
                            \n\nThanks & Regards,\nWassup Flea"""
                            send_email(row, email_content)
                            df.at[idx, 'Status'] = "Selected and Email Sent"
                        else:
                            df.at[idx, 'Status'] = "Not Selected"
                
                # Update Google Sheet with the ratings, evaluation reasons, and statuses
                sheet.update([df.columns.values.tolist()] + df.values.tolist())
                st.success("Evaluation and Email Sending Complete")

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import requests
import json
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
import re

# Google Sheets API setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

# Path to your Google Sheets API credentials JSON file
CREDENTIALS_FILE = 'startup-441418-b11058491d88.json'  # Replace with your actual credentials file path

# Google Sheets setup function
def get_gsheet_service():
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPE)
    client = gspread.authorize(creds)
    return client

# Hard-coded credentials and API key
API_KEY = "xai-Age3ZQ1iREPjsun617Q4dfYD7rrssFYJilahzawzyA1U7Z3Cuxr22EMvW40AneyD6KeXKdYNxWYrpSiw"  # Replace with actual Grok API key
SENDER_EMAIL = "20210802074@dypiu.ac.in"  # Replace with actual sender email
SENDER_PASSWORD = "pvud cnvc xwto bdnv"  # Replace with actual sender email password

# Function to get content from Grok AI API using a chat completion endpoint
def get_grok_chat_completion(api_key, payload, model="grok-beta"):
    api_url = "https://api.x.ai/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [])[0].get("message", {}).get("content", "").strip()
            return content
        else:
            return f"Error: Received status code {response.status_code} with message {response.text}"
    except Exception as e:
        return f"An error occurred: {e}"

def clean_email_content(content):
    return content.replace("**", "")  # Remove all instances of ** (used in markdown for bold)

def send_email(row, email_content):
    email = row['emails']
    name = row['Name']

    # Create the MIME structure for the email
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = email
    msg['Subject'] = "Wassup Flea Event"
    msg.attach(MIMEText(email_content, 'plain'))

    # Send email
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())
    return "completed"

def typing_effect(text):
    """Displays text with a typing animation."""
    placeholder = st.empty()
    displayed_text = ""
    for char in text:
        displayed_text += char
        placeholder.write(displayed_text)
        time.sleep(0.005)

def animated_input(prompt):
    typing_effect(prompt)
    return st.text_input("", key=prompt)

def animated_text_area(prompt):
    typing_effect(prompt)
    return st.text_area("", key=prompt)

def extract_sheet_id(sheet_url):
    """Extracts the Google Sheet ID from a given URL."""
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', sheet_url)
    if match:
        return match.group(1)
    else:
        return None

def main():
    st.title("Event Invitation Email Automation Chatbot")

    conversation = []  # To store the chat history

    def add_to_conversation(role, content):
        conversation.append({"role": role, "content": content})
        st.session_state.conversation = conversation

    if "conversation" not in st.session_state:
        st.session_state.conversation = []

    typing_effect("🤖 Welcome! I'm here to help you send event invitations. Let's get started.")

    # Step 1: Google Sheet URL
    sheet_url = animated_input("💡 First, enter your Google Sheet link:")
    if sheet_url:
        sheet_id = extract_sheet_id(sheet_url)
        if sheet_id:
            add_to_conversation("user", f"Google Sheet Link: {sheet_url}")
            client = get_gsheet_service()

            try:
                sheet = client.open_by_key(sheet_id).sheet1  # Access the first sheet
                data = sheet.get_all_records()  # Fetch all records
                df = pd.DataFrame(data)

                add_to_conversation("system", "Great! I've connected to your Google Sheet. Now, let's set up your event.")

                # Step 2: Event Details
                date = animated_input("📅 What's the date of the event? (e.g., 25th Dec 2024):")
                if date:
                    add_to_conversation("user", f"Event Date: {date}")

                    time = animated_input("⏰ What time is the event? (e.g., 6 PM):")
                    if time:
                        add_to_conversation("user", f"Event Time: {time}")

                        location = animated_input("📍 Where's the event happening? (e.g., Central Park):")
                        if location:
                            add_to_conversation("user", f"Event Location: {location}")

                            event_description = animated_text_area("📝 Describe the event:")
                            if event_description:
                                add_to_conversation("user", f"Event Description: {event_description}")

                                if st.button("🚀 Send Invitations"):
                                    add_to_conversation("user", "Send Invitations")

                                    if 'status' not in df.columns:
                                        df['status'] = 'not_fetched'

                                    for index, row in df.iterrows():
                                        if row['status'] == 'not_fetched':
                                            name = row['Name']
                                            payload = {
                                                "messages": [
                                                    {
                                                        "role": "system",
                                                        "content": "You are Grok, an AI designed to craft interactive and engaging email invitations for events."
                                                    },
                                                    {
                                                        "role": "user",
                                                        "content": f"Create an email invitation for {name} for the event on {date} at {time}, held at {location}. Event details: {event_description}"
                                                    }
                                                ],
                                                "model": "grok-beta",
                                                "stream": False,
                                                "temperature": 0.7
                                            }

                                            email_content = get_grok_chat_completion(API_KEY, payload)
                                            email_content = clean_email_content(email_content)

                                            try:
                                                result_status = send_email(row, email_content)
                                                df.at[index, 'status'] = result_status
                                                st.write(f"✅ Email sent to {row['emails']}")
                                            except Exception as e:
                                                st.error(f"❌ Error sending email to {row['emails']}: {e}")

                                    sheet.update([df.columns.values.tolist()] + df.values.tolist())
                                    st.success("🎉 All invitations sent successfully!")

            except Exception as e:
                st.error(f"⚠️ Error accessing Google Sheet: {e}")
        else:
            st.error("⚠️ Invalid Google Sheet URL. Please provide a valid link.")

    # Display the conversation history
    for message in st.session_state.conversation:
        if message['role'] == 'user':
            st.write(f"👤 **You:** {message['content']}")
        else:
            st.write(f"🤖 **Bot:** {message['content']}")

if __name__ == "__main__":
    main()

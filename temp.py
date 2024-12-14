import streamlit as st
import pandas as pd
import requests
import json
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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

def main():
    st.title("Event Invitation Email Automation")

    # Google Sheets file ID (you can find this in the URL of your Google Sheet)
    google_sheet_id = st.text_input("Enter Google Sheet ID:")

    # If Google Sheet ID is provided
    if google_sheet_id:
        client = get_gsheet_service()
        sheet = client.open_by_key(google_sheet_id).sheet1  # Access the first sheet
        data = sheet.get_all_records()  # Fetch all records

        # Convert the fetched data into a pandas DataFrame
        df = pd.DataFrame(data)

        # Get Event Details from the User
        date = st.text_input("Enter Event Date:")
        time = st.text_input("Enter Event Time:")
        location = st.text_input("Enter Event Location:")
        event_description = st.text_area("Enter Event Description:")

        # Check if all inputs are provided
        if date and time and location and event_description:
            if st.button("Send Invitations"):
                # Make sure 'status' column exists, otherwise add it
                if 'status' not in df.columns:
                    df['status'] = 'not_fetched'

                # Loop through each row in the dataframe
                for index, row in df.iterrows():
                    if row['status'] == 'not_fetched':
                        # Prepare payload for API
                        name = row['Name']
                        payload = {
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You are Grok, an AI designed to craft interactive and engaging email invitations for events. Your job is to create diverse, catchy, and elegant emails that feel personal, fun, and exciting."
                                },
                                {
                                    "role": "user",
                                    "content": f"""Create a dynamic, friendly, and highly engaging email invitation for {name}. Make it feel like a close friend inviting them to an exciting event. The email should have a warm, inviting, and personal tone. Use emojis to make it lively and visually appealing.

                                    Event Details:
                                    - Date: {date}
                                    - Time: {time}
                                    - Location: {location}
                                    - Event Description: {event_description}

                                    The email should:
                                    - Be engaging, with a sense of fun and excitement 💃🎉
                                    - Encourage the recipient to bring friends 👫💃
                                    - Sound spontaneous, like a personal invitation you would send to a close friend
                                    - Use playful, friendly language and a few emojis to enhance the vibe 🌟
                                    - Be elegant and classy, while keeping it informal and fun 🎶
                                    - Avoid *, # 
                                    - Do not include a subject line
                                    - Write Thanks & Regards, Instead of any other thing
                                    - Below Thanks & Regards, write Wassup Flea
                                    - Do not write [Your Name]after Thanks & Regards


                                    The tone should be upbeat, friendly, and inviting, but also fresh and unique each time to ensure that it doesn’t feel robotic. Feel free to experiment with different expressions, word choices, and emoji combinations to keep it interesting and engaging! 🚀
                                    """
                                }
                            ],
                            "model": "grok-beta",
                            "stream": False,
                            "temperature": 0.7
                        }

                        email_content = get_grok_chat_completion(API_KEY, payload)
                        email_content = clean_email_content(email_content)

                        # Send the email and update status
                        try:
                            result_status = send_email(row, email_content)
                            df.at[index, 'status'] = result_status
                            st.write(f"Email sent to {row['emails']}")
                        except Exception as e:
                            st.error(f"Error sending email to {row['emails']}: {e}")

                # Update the Google Sheet with the new statuses
                sheet.update([df.columns.values.tolist()] + df.values.tolist())
                st.write("Processing Complete!")

    else:
        st.warning("Please enter the Google Sheet ID to proceed.")

# Run the app
if __name__ == "__main__":
    main()

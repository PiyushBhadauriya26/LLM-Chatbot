from sendgrid.helpers.mail import *
import sendgrid
from dotenv import load_dotenv
import os
import os.path
import json
import datetime

load_dotenv()
from vectordb import Pinecode_DB

vector_db = Pinecode_DB()
sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))


def send_email(to_email, msg):
    try:
        from_email = Email("coolpiyushsingh@gmail.com")
        to_email = To(to_email)
        subject = "Diagnosis Result"
        content = Content("text/plain", msg)
        mail = Mail(from_email, to_email, subject, content)
        response = sg.client.mail.send.post(request_body=mail.get())
    except Exception as e:
        print(e)
        return "Error! Failed to send email."
    else:
        return "Success! sent email to {}".format(to_email.email)


def retrieve_knowledge(symptoms):
    query = f"User Input: I have {symptoms}."
    # print(query)
    kb = vector_db.retrieve(query)
    print(kb)
    return kb


def search_chat_history(user_email):
    file = user_email + ".json"

    if os.path.isfile(file):
        with open(file, 'r+') as file:
            # First we load existing data into a dict.
            file_data = json.load(file)

            if len(file_data["chat"]) > 0:
                return ' Here is user chat history: ' + str(file_data["chat"])

            return 'No Chat history found'

    else:
        a_dict = {
            'chat': []
        }

        with open(file, 'w') as outfile:
            json.dump(a_dict, outfile)

        return 'No Chat history found'


def save_chat_history(file_name_to_save, chat_summary):
    dt = datetime.datetime.now()

    with open(file_name_to_save, 'r+') as file:
        file_data = json.load(file)
        # Join new_data with file_data inside emp_details
        file_data["chat"].append({'date-time': str(dt), 'chat summary': chat_summary})
        # Sets file's current position at offset.
        file.seek(0)
        # convert back to json.
        json.dump(file_data, file, indent=4)

        return "Summary Saved"


available_functions = {
    "send_email": send_email,
    "retrieve_knowledge": retrieve_knowledge,
    "search_chat_history": search_chat_history,
    "save_chat_history": save_chat_history
}
tools = [
    {
        "type": "function",
        "function": {
            "name": "save_chat_history",
            "description": "chat summary for future",
            "parameters": {
                "type": "object",
                "properties": {
                    "chat_summary": {
                        "type": "string",
                        "description": "recent diagnosis summary ",
                    },
                },
                "required": ["chat_summary"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_chat_history",
            "description": "search chat history",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "the recipient email address",
                    },
                },
                "required": ["email"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email to patient with Diagnosis Result",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_email": {
                        "type": "string",
                        "description": "the recipient email address",
                    },
                    "msg": {
                        "type": "string",
                        "description": "Body of the email with Diagnosis Result",
                    },
                },
                "required": ["to_email", "msg"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_knowledge",
            "description": "retrive knowledge from the knowledge base",
            "parameters": {
                "type": "object",
                "properties": {
                    "symptoms": {
                        "type": "array",
                        "description": "List of patients symptoms",
                        "items": {
                            "type": "string",
                        },
                    },
                },
                "required": ["symptoms"],
            },
        },
    }
]

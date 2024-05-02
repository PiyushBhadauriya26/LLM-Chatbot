from sendgrid.helpers.mail import *
import sendgrid
from dotenv import load_dotenv
import os
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

available_functions = {
    "send_email": send_email,
    "retrieve_knowledge": retrieve_knowledge
}
tools = [
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

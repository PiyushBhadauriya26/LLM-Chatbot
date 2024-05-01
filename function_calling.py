from sendgrid.helpers.mail import *
import sendgrid
from dotenv import load_dotenv
load_dotenv()
def send_email(to_email, msg):
    try:
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
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

available_functions = {
    "send_email": send_email,
}
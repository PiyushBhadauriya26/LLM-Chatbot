
from flask import Flask, render_template, request
from diagnostic_bot import Diagnostic_bot

app = Flask(__name__)
d_bot = None

def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = {"role": "user", "content": prompt}
    response = d_bot.chat_completion_request(messages, model=model)
    d_bot.log_chat_interaction(prompt, response) 
    return response

@app.route("/")
def home():
    global d_bot 
    d_bot =  Diagnostic_bot()
    return render_template("index.html")

@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    if userText:
        response = get_completion(userText)
        return response
    else:
        return "No message received", 400  


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=False)

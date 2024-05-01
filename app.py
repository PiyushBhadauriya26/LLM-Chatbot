from flask import Flask, render_template, request
from diagnostic_bot import Diagnostic_bot

app = Flask(__name__)
def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    response = chat_completion_request(messages, model=model)
    print(response)
    return response.choices[0].message.content
@app.route("/")
def home():
    return render_template("index.html")
@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    d_bot = Diagnostic_bot()
    response = d_bot.chat_completion_request(userText)
    return response
if __name__ == "__main__":
    app.run()
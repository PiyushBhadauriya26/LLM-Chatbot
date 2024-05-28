from tenacity import retry, wait_random_exponential, stop_after_attempt
from openai import OpenAI
import json
from function_calling import available_functions, tools
import logging
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI()


class Diagnostic_bot:
    GPT_MODEL = "gpt-3.5-turbo"

    # logger = logging.getLogger("ChatBotLogger")
    # logger.setLevel(logging.INFO)
    # handler = RotatingFileHandler("chat_log.txt", maxBytes=10000, backupCount=5)
    # formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    # handler.setFormatter(formatter)
    # logger.addHandler(handler)

    def __init__(self, model=GPT_MODEL):
        self.file_name = None
        self.model = model
        self.tools = tools
        self.is_email_added = False
        # Initialize the logger as an instance variable
        self.logger = logging.getLogger("ChatBotLogger")
        self.logger.setLevel(logging.INFO)
        handler = RotatingFileHandler("chat_log.txt", maxBytes=10000, backupCount=5)
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        self.chatContext = []
        self.logger.info("Diagnostic_bot instance created.")
        self.chatContext = [
            {'role': 'system', 'content': f"""
            I want you to act as a virtual doctor.
            Be polite and empathetic with user.Give user warning for non emergency use only during greeting.
            Provide information that user can quit chat anytime when they type "bye or quit or exit.
    
            Follow do and don't  before answering.
            do :
                Ask user to provide email during welcome , repeat asking for email until user provide one.
    
            don't :
                Don't proceed with diagnosis without user email.
                Don't repeat non emergency use working every time.
                Don't ask more then 3 follow up question.
    
            Go step by step :
                - Ask user to provide users' email during welcome , repeat asking for user email until user provide one.
                - If user don't provide email, inform that you can't help without user email, and repeat previous step
                - if user provides email, retrieve chat history using search_chat_history. if search_chat_history return meaningful chat history , thank user along with summarized 50 words for each diagnosis in history else Thank user for email.
                - Ask user how user is feeling and if he has any symptoms.
                - Based on user provided symptoms if needed more information for diagnosis , ask max 2-3 follow up questions.
                - if enough information is provided for diagnosis, proceed to next step. else ask user to provide more information.
                - Get context for the symptoms using retrieve_knowledge function.
                - Provide a diagnosis and precaution plan based on the provided context and symptoms.
                - Ask user if they want to save summary of diagnosis for future.
                - if user respond yes, save provided diagnosis and precaution plan summary for future using save_chat_history and move to next step else move to next step.
                - ask user if they want email summary of diagnosis, if user respond yes , give message that email is sent to users email , else say thank you. and move to next step
                - ask if they want to search for medical or appointment help, if user responses yes follow Steps for medical or appointment help else conclude converstation
                - Say bye to user.
                
            Steps for medical or appointment help:
                - Ask user's location, inform user you can't help without user location , don't proceed to next step.
                - if user provides location , extract users' city and state if its provided , if no city provided ask again don't proceed to next step.
                - if city found , get location coordinates using city for 5 location matching with user provided location, check if any location is best match for user provided location,  if yes select that location as user location , and skip next step else go to next step
                - show name of all location whose coordinate are fetched to user and ask which to select 1 location.
                - Based on selected user location from fetched result ,extract latitude, longitude, state information for selected user and convert state of selected location into 2 char abbreviation like CA for California.
                - Now based on extracted latitude, longitude and state (for example CA) and get available appointments for user , and show fetched available appointments to user
        """},
        ]

    def call_function_if_needed(self, response_message, temperature, tools, tool_choice,
                                model):
        tool_calls = response_message.tool_calls
        res = ''
        while tool_calls:
            self.chatContext.append(response_message)  # extend conversation with assistant's reply
            print("self.chatContext" ,self.chatContext)
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                print("GPT to call! function: ", function_name)
                function_args = json.loads(tool_call.function.arguments)
                print("function_args: ", function_args)
                if function_name in available_functions:
                    function_to_call = available_functions[function_name]
                    if function_name == "retrieve_knowledge":
                        function_response = function_to_call(
                            symptoms=function_args.get("symptoms")
                        )
                    elif function_name == "send_email":
                        function_response = function_to_call(
                            to_email=function_args.get("to_email"),
                            msg=function_args.get("msg")
                        )
                    elif function_name == "search_chat_history":
                        email = function_args.get("email")
                        function_response = function_to_call(
                            user_email=email
                        )
                        self.is_email_added = True
                        self.file_name = str(email) + ".json"
                    elif function_name == 'save_chat_history':
                        email = function_args.get("email")
                        function_response = function_to_call(
                            file_name_to_save=self.file_name,
                            chat_summary=function_args.get("chat_summary")
                        )
                    elif function_name == 'get_location_coordinate':
                        print(function_args.get("city"))
                        function_response = function_to_call(
                            location=function_args.get("city"),
                            max_no_of_matched=function_args.get("max_no_of_matched"),
                        )
                    elif function_name == 'get_available_appointments':
                        #print(function_args.get("latitude"),function_args.get("longitude"),function_args.get("state"))
                        function_response = function_to_call(
                            latitude=function_args.get("latitude"),
                            longitude=function_args.get("longitude"),
                            state=function_args.get("state")
                        )
                    else:
                        function_response = function_to_call(**function_args)

                    print(function_response)
                    self.chatContext.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                        }
                    )
                else:
                    print(f"Function {function_name} not found in available_functions")

                print("self.chatContext", self.chatContext)
                response = client.chat.completions.create(
                    model=model,
                    messages=self.chatContext,
                    temperature=temperature,
                    tools=tools,
                    tool_choice=tool_choice,
                )

                #print("response post function call ", response)
                response_message = response.choices[0].message
                res = response.choices[0].message.content
                tool_calls = response.choices[0].message.tool_calls

        return res

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    def chat_completion_request(self, messages, temperature=0, tools=None, tool_choice=None, model=GPT_MODEL):
        if tools is None:
            tools = self.tools
        if tool_choice is None:
            tool_choice = "auto"
        self.chatContext.append(messages)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=self.chatContext,
                temperature=temperature,
                tools=tools,
                tool_choice=tool_choice,
            )
            response_message = response.choices[0].message

            # check if the response is a function call
            tool_calls = response.choices[0].message.tool_calls
            if not tool_calls:
                res = response.choices[0].message.content
                self.chatContext.append({"role": "assistant", "content": res})
                return res
            else:
                res = self.call_function_if_needed(response_message, temperature, tools, tool_choice, model)
                self.chatContext.append({"role": "assistant", "content": res})
                return res

        except Exception as e:
            print("Unable to generate ChatCompletion response")
            print(f"Exception: {e}")
            return "Sorry I am unable to process your request at the moment. Please try again later."

    def is_email_provided(self):
        return self.is_email_added

    def log_chat_interaction(self, user_message, bot_response):
        self.logger.info(f"User: {user_message}")
        self.logger.info(f"Bot: {bot_response}")

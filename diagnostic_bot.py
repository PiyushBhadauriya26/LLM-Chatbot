import os
from tenacity import retry, wait_random_exponential, stop_after_attempt
from dotenv import load_dotenv
from openai import OpenAI
import json
from function_calling import available_functions

load_dotenv()
client = OpenAI()


class Diagnostic_bot:
    GPT_MODEL = "gpt-3.5-turbo"

    def __init__(self, model=GPT_MODEL):
        self.model = model
        self.tools = [
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
        ]
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
                - If user don't provide email, inform that you can't help without user email, and repeat previous step, else Thank user for providing email and move to next step
                - Ask user how user is feeling.
                - Based on user provided symptoms if needed more information for diagnosis , ask max 2-3 follow up questions.
                - Provide a diagnosis and precaution plan based on the provided context and symptoms.
                - ask user if they want email summary of diagnosis.
                - if user respond yes , give message that email is sent to users email , else say thank you.
                - Say bye to user.
        """},
        ]

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
    def chat_completion_request(self, messages, temperature=0, tools=None, tool_choice=None, model=GPT_MODEL):
        if tools is None:
            tools = self.tools
        if tool_choice is None:
            tool_choice = "auto"
        self.chatContext.append(messages)
        #print("Chat Context: ", self.chatContext)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=self.chatContext,
                temperature=temperature,
                tools=tools,
                tool_choice=tool_choice,
            )
            # check if the response is a function call
            tool_calls = response.choices[0].message.tool_calls
            if not tool_calls:
                res = response.choices[0].message.content
                self.chatContext.append({"role": "assistant", "content": res})
                return res
            else:
                self.chatContext.append(response.choices[0].message)
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    print("GPT to call! function: ", function_name)
                    function_args = json.loads(tool_call.function.arguments)
                    if function_name in available_functions:
                        function_to_call = available_functions[function_name]
                        function_response = function_to_call(
                            to_email=function_args.get("to_email"),
                            msg=function_args.get("msg")
                        )
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
                response = client.chat.completions.create(
                    model=model,
                    messages=self.chatContext,
                    temperature=temperature,
                    tools=tools,
                    tool_choice=tool_choice,
                )
                res = response.choices[0].message.content
                self.chatContext.append({"role": "assistant", "content": res})
                return res

        except Exception as e:
            print("Unable to generate ChatCompletion response")
            print(f"Exception: {e}")
            return "Sorry I am unable to process your request at the moment. Please try again later."


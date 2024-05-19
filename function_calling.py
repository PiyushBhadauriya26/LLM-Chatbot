from sendgrid.helpers.mail import *
import sendgrid
from dotenv import load_dotenv
import os
import os.path
import json
import datetime
import requests

load_dotenv()
from vectordb import Pinecode_DB

vector_db = Pinecode_DB()
sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))


def send_email(to_email, msg):
    try:
        # ADD EMAIL before running
        from_email = Email("")
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


# To get latitude ,longitude and location details for matching name of a location
def get_location_coordinate(location, max_no_of_matched=1):
    # print(location,max_no_of_matched)
    try:
        count = int(max_no_of_matched)
    except:
        count = 1
    urlCoordinates = "https://geocoding-api.open-meteo.com/v1/search?name=" + location + "&count=" + str(
        count) + "&language=en&format=json"
    payload = {}
    headers = {}

    response = requests.request("GET", urlCoordinates, headers=headers, data=payload)
    data = response.json()
    selectedLocations = ''
    #print(data)
    if (len(data['results'])):
        for city in data['results']:
            try:
                if city['country_code'] == 'US':
                        obj = {'name': city['name'] + ', ' + city['admin1'] + ', ' + city['country_code'],
                               'state': city['admin1'],
                               'latitude': city['latitude'],
                               'longitude': city['longitude'],
                               'postcodes': city['postcodes']}
                        selectedLocations += str(obj) + '\n'
            except:
                continue
    #print(selectedLocations)
    return selectedLocations


def get_available_appointments(latitude, longitude, state):
    print(state)
    state_code = 'US-' + str(state)
    url = "https://api.sesamecare.com/graphql"
    today = datetime.datetime.today().strftime('%Y-%m-%d')

    query = '''
        query searchV2(
          $resultsFilters: Consumer_ServiceDefintionInventoryMappingFiltersInputV2!
          $offset: Int
          $limit: Int
          $sort: [Sort]
        ) {
          results: consumer_serviceDefinitionInventoryMatchesV2(
            filters: $resultsFilters
            limit: $limit
            offset: $offset
            sort: $sort
          ) {
            items {
              ...UseSearchQueryV2__Consumer_ServiceDefinitionInventoryMatch
              __typename
            }
            totalItems
            __typename
          }
        }
        fragment UseSearchQueryV2__Consumer_ServiceDefinitionInventoryMatch on Consumer_ServiceDefinitionInventoryMatch {
          ...InventoryCardV2__Consumer_ServiceDefinitionInventoryMatch
          __typename
        }
        fragment InventoryCardV2__Consumer_ServiceDefinitionInventoryMatch on Consumer_ServiceDefinitionInventoryMatch {
          availabilitySummaryV2 {
            nextAvailableAt
            __typename
          }
          inventoryMapping {
            ...InventoryCardV2__Consumer_ServiceDefinitionInventoryMapping
            __typename
          }
          __typename
        }
        fragment InventoryCardV2__Consumer_ServiceDefinitionInventoryMapping on Consumer_ServiceDefinitionInventoryMapping {
          location {
            address {
              addressOne
              addressTwo
              city
              locality
              neighbourhood
              route
              state
              zipCode
              __typename
            }
            timeZoneId
            phoneNumberPatients
            telemedicine
            __typename
          }
          provider {
            ...InventoryCardV2__Consumer_Provider
            __typename
          }
          __typename
        }
        fragment InventoryCardV2__Consumer_Provider on Consumer_Provider {
          credentials
          firstName
          casualName
          gender
          id
          lastName
          photoUrl
          title
          shortId
          specialties {
            name
            __typename
          }
          gender
          languagesSpoken
          __typename
        }
    '''

    variables = {
        "limit": 10,
        "offset": 0,
        "resultsFilters": {
            "availability": {
                "appointmentStartsWithinMinutes": 7200,
                "daysCount": 30,
                "startDate": today
            },
            "location": {
                "origin": {
                    "lat": float(latitude),
                    "lon": float(longitude)
                },
                "radius": 50
            },
            "provider": {
                "accountConfirmationStatus": "CONFIRMED",
                "practiceStates": [
                    state_code
                ]
            },
            "service": {
                "patientType": "ANY",
                "template": []
            },
            "serviceTemplateGroup": {
                "slug": "primary-care",
                "type": "SPECIALTY"
            }
        },
        "sort": [
            {
                "direction": "ASC",
                "field": "next"
            }
        ]
    }

    payload = {
        'query': query,
        'variables': variables
    }

    headers = {
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://sesamecare.com',
        'priority': 'u=1, i'
    }

    payload = json.dumps(payload)
    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code != 200:
        return 'Error'

    appointment_availability_list = []
    resp = response.json()

    for item in resp['data']['results']['items']:
        data = {}

        title = ''
        if item['inventoryMapping']['provider']['title']:
            title = item['inventoryMapping']['provider']['title']

        date_obj = datetime.datetime.strptime(item['availabilitySummaryV2']['nextAvailableAt'], "%Y-%m-%dT%H:%M:%S.%fZ")

        formatted_date = date_obj.strftime("%B %dth %Y %I:%M %p")

        data['title_name'] = title + ' ' + item['inventoryMapping']['provider']['casualName']
        specialties = ''
        for spec in item['inventoryMapping']['provider']['specialties']:
            specialties = specialties + ' ' + spec['name']

        languages = ''
        for language in item['inventoryMapping']['provider']['languagesSpoken']:
            languages = languages + ',' + language

        data['specialties'] = specialties
        data['languages'] = languages
        if item['inventoryMapping']['location']['telemedicine']:
            data['address'] = 'Virtual'
        else:
            data['address'] = item['inventoryMapping']['location']['address']['city'] + '' + \
                              item['inventoryMapping']['location']['address']['state'] + '' + \
                              item['inventoryMapping']['location']['address']['zipCode']

        data['contact_no'] = item['inventoryMapping']['location']['phoneNumberPatients']
        data['timeZoneId'] = item['inventoryMapping']['location']['timeZoneId']
        data['availability'] = formatted_date

        appointment_availability_list.append(data)

    return str(list(appointment_availability_list))


available_functions = {
    "send_email": send_email,
    "retrieve_knowledge": retrieve_knowledge,
    "search_chat_history": search_chat_history,
    "save_chat_history": save_chat_history,
    "get_location_coordinate": get_location_coordinate,
    "get_available_appointments": get_available_appointments
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_available_appointments",
            "description": "Get available appointment slot ",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "string",
                        "description": "latitude value for example  37.54827 ",
                    },
                    "longitude": {
                        "type": "string",
                        "description": "longitude value for example -121.98857",
                    },
                    "state": {"type": "string", "description": "state abbreviation for example CA "},
                },
                "required": ["latitude", "longitude", "state"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_location_coordinate",
            "description": "Get the coordinates of possible matching locations",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city, e.g. San Francisco",
                    },
                    "max_no_of_matched": {"type": "number", "description": "default is 1"},

                },
                "required": ["location"],
            },
        }
    },
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
            "description": "retrieve knowledge from the knowledge base",
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

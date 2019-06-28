from controllers import search,learn
from config import config
from config.skeleton import CurrentConversation
import os
import json
import jsonpickle
from pymongo import MongoClient


# MongoDB is not fork() safe, thus need to create a new instance for every child process in order to stop deadlock.
# see MongoDB FAQ for more information
# Connecting to MondoDB
client = MongoClient(config.db_config["DB_HOST"], config.db_config["DB_PORT"], username=config.db_config["DB_USER"],
                    password=config.db_config["DB_PASSWORD"], connect=False)  # Connection to MongoDB
database = config.db_config["DB_NAME"]
currentConversation = config.db_config["CURRENT"]
db = client[database][currentConversation]


def identify_actions(response: json, message: str) -> str:
    try:
        if 'actions' in response['output'] and response['output']['actions'][0]['type'] == 'client':
            if 'search' == response['output']['actions'][0]['name']:
                return search.search_apps(message)
            if 'learn' == response['output']['actions'][0]['name']:
                return learn.answer_query(message)
    except Exception as e:
        status = dict()
        status["Exception in identifying actions"] = str(e)
        raise Exception(status)


def identify_generic_output(response: json) -> str:
    try:
        if response['output']['generic']:
            if response['output']['generic'][0]['response_type'] == 'text':
                return json.dumps(response['output']['generic'][0])
            if response['output']['generic'][0]['options']:
                return json.dumps(response['output']['generic'][0])
    except Exception as e:
        status = dict()
        status["Exception in identifying Generic Output"] = str(e)
        raise Exception(status)


def process_message(message: str, user):
    # User input
    message_input = {
        'message_type:': 'text',
        'text': message
    }

    try:
        entry = db.find_one({'user_id': user})
    except Exception as e:
        status = dict()
        status["error in querying database"] = str(e)
        raise Exception(status)

    try:
        if not entry:
            response = config.service.message(
                workspace_id=os.environ['WORKSPACE_ID'],
                input=message_input).get_result()

        else:
            context = entry["context"]
            response = config.service.message(
                workspace_id=os.environ['WORKSPACE_ID'],
                input=message_input, context=context).get_result()
    except Exception as e:
        status = dict()
        status["error in watson"] = str(e)
        raise Exception(status)

    try:
        # creating class for json file here
        convo = CurrentConversation(user)
        convo.context = response['context']

        # inserting json into database
        convojson = jsonpickle.encode(convo)

    except Exception as e:
        status = dict()
        status["error in creating json for database"] = str(e)
        raise Exception(status)


    try:
        db.replace_one({'user_id': user}, json.loads(convojson), upsert=True)
    except Exception as e:
        status = dict()
        status["error while inserting/updating database"] = str(e)
        raise Exception(status)

    try:
        actions = identify_actions(response, message)
        text = identify_generic_output(response)
        if actions and text:
            merged_response = {**json.loads(actions), **json.loads(text)}
            return merged_response
        return actions or text
    except Exception as e:
        status = dict()
        status["error in creating response"] = str(e)
        raise Exception(status)

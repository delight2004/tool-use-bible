# tool.py

import json
from typing import Callable
import requests

# take a standard Python function and turn it into a structured dictionary that the LLM can read 
def get_fn_signature(fn: Callable)->dict:
    """
    Generates the signature for a given function.

    This signature is a structured dictionary that an LLM can parse to understand the function's purpose and its required parameters.

    Args:
        fn(Callable): The function whose signature needs to be extracted.

    Returns:
        dict: A dictionary containing the function's name, description and parameter types.
    """

    fn_signature: dict = {
        "name": fn.__name__,
        "description": fn.__doc__,
        "parameters": {"properties": {}}
    }
    
    # schema dictionary
    schema = {
        k: {"type": v.__name__} for k, v in fn.__annotations__.items() if k!="return"
    }
    # the schema dictionary is assigned to the nested key
    fn_signature["parameters"]["properties"] = schema
    return fn_signature

# ensures the LLM-generated arguments match what the tool function expects
def validate_argument(tool_call: dict, tool_signature: dict)->dict:
    """
    Validates and converts arguments in the input dictionary to match the expected types.

    Args:
        tool_call (dict): A dictionary containing the arguments passed to the tool.
        tool_signature (dict): The expected function signature and parameter types.

    Returns:
        dict: The tool call dictionary with the arguments converted to the correct types if necessary.
    """
    properties = tool_signature["parameters"]["properties"]

    # simple mapping from the type names ("int", "str") to the actual Python classes (int, str)
    type_mapping = {
        "int": int,
        "str": str,
        "bool": bool,
        "float": float,
    }

    for arg_name, arg_value in tool_call["arguments"].items():
        expected_type = properties[arg_name].get("type")

        if not isinstance(arg_value, type_mapping[expected_type]):
            try:
                # attempt to convert the argument to the expected type
                tool_call["arguments"][arg_name] = type_mapping[expected_type](arg_value)
            except (ValueError, TypeError) as e:
                raise TypeError(f"Could not convert argument '{arg_name}' with value '{arg_value}'")
    return tool_call

# wrapper for our functions
class Tool:
    """
    A class representing a tool that wraps a callable and its signature
    """

    def __init__(self, name:str, fn: Callable, fn_signature: dict):
        # code to initialize the object
        self.name = name
        self.fn = fn
        self.fn_signature = fn_signature

    def run(self, **kwargs):
        """
        Executes the tool(function) with provided arguments
        """
        # code to run the function
        return self.fn(**kwargs)

COMMON_TOPICS = {
    "love": "john 3:16",
    "patience": "romans 5:3-4",
    "strength": "isaiah 40:31",
    "faith": "hebrews 11:1"
}

def fetch_daily_verse():
    """Fetches a random verse for the day"""
    # placeholder for API call later
    print("ACTION: Fetching daily verse from API...")

    try:
        response = requests.get("https://bible-api.com/?random=verse")
        status_code = response.status_code

        if status_code == 404:
            return "Error: Page not found (404)"
        elif status_code == 500:
            return "Error: Internal server error (500)"
        else:        
            data = response.json()
            verse_text = data.get("text", "No text found.")
            verse_ref = data.get("reference", "No reference found.")
            return f"{verse_ref} - {verse_text}"        
    except requests.exceptions.RequestException as e:
        return f"Error: failed to retrieve a daily verse. {e}"
    
    

def search_topic(topic: str):
    """Searches for a verse about a specific topic using a mock-like API call"""
    print(f"ACTION: Searching for verses about '{topic}'...")
    # this API doesn't support topic search directly, so we'll fall back to our mock logic
    reference = COMMON_TOPICS.get(topic.lower())
    if reference:
        try:
            response = requests.get(f"https://bible-api.com/{reference}")
            response.raise_for_status()
            data = response.json()
            verse_text = data.get("text", "No text found.")
            return f"{data.get('reference')} - {verse_text}"
        except requests.exceptions.RequestException as e:
            return f"Error: Failed to retrieve verse for topic. {e}"
    else:
        return f"Sorry, I couldn't find the verse for the topic: '{topic}'"
    
    
def get_book_list()->list[str]:
    """Returns a list of all books in the bible"""
    print("ACTION: Listing all the books...")
    return ["Matthew", "Mark", "Luke", "John"]

def get_verse_by_chapter(book:str, chapter:int):
    """Returns required book and its chapter"""
    print("ACTION: Getting required book and chapter....")
    
    if book.lower()=="john" and chapter==3:
        return "John 3:16 - For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life."
    else:
        return f"Sorry I couldn't find the verse from '{book}' chapter {chapter}"
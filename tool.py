# tool.py

import json
from typing import Callable

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
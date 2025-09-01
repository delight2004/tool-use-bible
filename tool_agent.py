from groq import Groq
import json
import os
from dotenv import load_dotenv
import re # provides support for regular expressions in python -> used for pattern matching in strings
from tool import (
    validate_argument,
    get_fn_signature,
    Tool,
    fetch_daily_verse,
    search_topic,
    get_book_list,
    get_verse_by_chapter,
)

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY environment variable not set. Please check your .env file")

client = Groq(api_key=api_key)

def extract_tag_content(text: str, tag: str) -> str | None:
        """
        Extracts the content from a specified tag.
        Returns the content if the tag is found, otherwise None.
        """
        match = re.search(f"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
        # The parentheses () define a capture group, meaning the matched content inside them can be accessed later (via match.group(1)).
        # . matches any character (letters, numbers, spaces, etc.).
        # * means “zero or more” of those characters.
        # ? makes it non-greedy, which is crucial when there might be multiple tags in the text.
        if match:
            return match.group(1).strip()
        return None


TOOL_SYSTEM_PROMPT = """You are a helpful assistant with access to the following tools:

<tools>
{tools}
</tools>

In order to use a tool, you must use <tool_code> tags. The JSON object must contain 'name' and 'arguments'.

<tool_code>
{{"name": "tool_name", "arguments": {{"arg1": "value1"}}}}
</tool_code>
"""


class ToolAgent: # communicates with an LLM and manages a collection of tools/ bridge an LLM with a set of executable tools
    """
    A class that orchestrates tool use by interacting with an LLM.
    """

    def __init__(self, client, tools):
        # code to initialize the agent
        self.tools = tools # collection of Tool objects. Each Tool would wrap a cllable function and its signature
        self.client = client # object/interface for interacting with an LLM -> used to send queries to the LLM and receive responses
    
   

    def add_tool_signatures(self):
        """
        Formats all tool signatures into a single string for the LLM.
        """

        # creates a list of all tool signatures from tool objects
        signatures = [json.dumps(tool.fn_signature, indent=4) for tool in self.tools]

        # Join the signatures with a newline character and return them
        return f"<tools>\n{'\n'.join(signatures)}</tools>"
    
    def run(self, user_msg: str):
        # create the two chat histories

        # 1. Prepare the messages for the LLM

        # Get the formatted tool signatures
        formatted_tools = self.add_tool_signatures()

        # full system prompt that tells the LLM about its tools
        system_message_content = TOOL_SYSTEM_PROMPT.format(tools=formatted_tools)

        # we'll use this system message for our tool calling chat history
        system_message = {"role": "system", "content": system_message_content}

        # user's message formatted for the LLM
        user_message = {"role": "user", "content": user_msg}

        tool_chat_history = [system_message, user_message]
        agent_chat_history = [system_message, user_message]
        user_chat_history = [user_message]

        # the agent then takes its internal "thought" and passes it to the LLM to get a decision
        
        try:
            llm_response=self.client.chat.completions.create(
                messages=tool_chat_history,
                model="openai/gpt-oss-120b"
            )
        except Exception as e:
            # for now we'll just print the error
            raise RuntimeError(f"An error occurred during the LLM call: {e}")
        
        # The LLM's response is a bit like a wrapped present—you have to open it to get to the good stuff inside. You're not just getting a string back, but a structured object.

        # To get the actual text content from the LLM's response, you need to navigate through its nested structure.
        if llm_response.choices and llm_response.choices[0].message.content:
            llm_content = llm_response.choices[0].message.content
        else:
            return "Sorry, I couldn't get a response from the LLM."
        
        # check for tool calls and extract content
        tool_call_json = extract_tag_content(llm_content, "tool_code")

        # if a tool_call was found, tool_call_json will not be None
        if tool_call_json:
            try:
                tool_call_deserialized=json.loads(tool_call_json)
                name = tool_call_deserialized["name"]
                arguments = tool_call_deserialized["arguments"]

                # find the correct tool object based on its name
                # he next() function is a built-in Python function that retrieves the first item from an iterator. It takes two arguments:

                #The iterator to process (in this case, a generator expression).
                #A default value to return if the iterator is empty (in this case, None).
                tool_object = next(
                    (tool for tool in self.tools if tool.name == name),
                    None
                )

                if tool_object:
                    # 2. Validate the arguments using the tool's signature
                    validated_call = validate_argument(tool_call_deserialized, tool_object.fn_signature)

                    # 3. Run the tool and get the observation
                    # part of the logic that processes the LLM’s response after extracting a <tool_code> tag (using extract_tag_content) and finding the corresponding tool (using next(...)). It’s the step that turns the LLM’s decision (e.g., “use the get_weather tool with city=London”) into an actual action (e.g., fetching the weather).
                    observation = tool_object.run(**validated_call["arguments"])
                    # Add the observation to the agent's chat history
                    agent_chat_history.append({"role": "assistant", "content": str(observation)})
                    agent_chat_history.append({"role": "user", "content": str(observation)})

                    # 4. Final LLM call: generate the final response
                    # If you want the final response to be based only on the user's message and the observation, use user_chat_history + observation:
                    final_chat_history = [system_message, user_message, {"role": "user", "content": str(observation)}]

                    final_response = self.client.chat.completions.create(
                        messages=final_chat_history,
                        model="openai/gpt-oss-120b"
                    )

                    return final_response.choices[0].message.content

            except Exception as e:
                # handle cases where the JSON or tool call is invalid
                return f"Sorry, I had trouble processing the tool call. Error: {e}"
        else:
            # if no tool call was found, the LLM content is the final answer
            return llm_content

if __name__ == "__main__":
    # 1. Create the tools
    tools = [
        Tool(
            name="fetch_daily_verse",
            fn=fetch_daily_verse,
            fn_signature=get_fn_signature(fetch_daily_verse),
        ),
        Tool(
            name="search_topic",
            fn=search_topic,
            fn_signature=get_fn_signature(search_topic),
        ),
        Tool(
            name="get_book_list",
            fn=get_book_list,
            fn_signature=get_fn_signature(get_book_list),
        ),
        Tool(
            name="get_verse_by_chapter",
            fn=get_verse_by_chapter,
            fn_signature=get_fn_signature(get_verse_by_chapter),
        ),
    ]

    # 2. Initialize the agent
    agent = ToolAgent(client=client, tools=tools)

    # 3. Start the conversation loop
    print("Bible Tool Agent. Ask me for 'today's verse' or a 'verse about [topic]'. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break
        
        response = agent.run(user_input)
        print(f"Agent: {response}")
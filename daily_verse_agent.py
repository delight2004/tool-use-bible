# daliy_verse_agent.py

import requests
import json
import random

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
    
    if book.lower()=="John" and chapter=="3":
        return "John 3:16 - For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life."
    else:
        return f"Sorry I couldn't find the verse from '{book}' chapter {chapter}"

    
# a simple Tool Registry to map intents to functions
TOOL_REGISTRY = {
    "fetch_daily_verse": fetch_daily_verse,
    "search_topic": search_topic,
    "get_book_list": get_book_list,
    "get_verse_by_chapter": get_verse_by_chapter,
}
    

def parse_intent(user_input: str)->dict:
    """
    Parses user input to determine the intended action and its parameters.
    Returns a dictionary with 'action' and 'param' keys.
    """
    normalized_input = user_input.lower().strip()

    if "get_verse" in normalized_input or "from" in normalized_input:
        parts = normalized_input.split("from")
        # get verse from -->book<--
        book = parts[1].strip()

        # make parts before "from" a list of words ["get", "verse", "5"]
        verse_parts = parts[0].split()

        # find the verse number assuming it is an integer after "get_verse"
        chapter_str = [p for p in verse_parts if p.isdigit()]

        if chapter_str:
            chapter = int(chapter_str[0])
            return {"action": "get_verse_by_chapter", "param": {"book": book, "chapter": chapter}}
        else:
            return {"action": "no_intent", "param": None}

    elif "today" in normalized_input or "daily" in normalized_input:
        return {"action": "fetch_daily_verse", "param": None}
    elif "verse about" in normalized_input:
        #extract the topic by splitting the string
        try:
            topic = normalized_input.split("verse about")[1].strip()
            return {"action": "search_topic", "param": topic}
        except IndexError:
            return {"action": "no_intent", "param": None}
    elif "a verse about comfort" in normalized_input:
        return {"action": "search_topic", "param":"comfort"}
    elif "list" in normalized_input or "books" in normalized_input:
        return {"action": "get_book_list", "param": None}
    else:
        return {"action": "no_intent", "param": None}
    
def format_output(tool_output: str)->str:
    """
    Formats the raw tool output into  pleasant, journal-friendly response.
    """
    # this is our post-processing logic
    verse = tool_output
    if "Error:" in verse:
        return verse # pass through error messages directly
    
    formatted_verse = f"**Daily Verse**\n\n{verse}\n\n"
    random_commentary = ["This verse is a classic!", "This is sobering!", "This is so wholesome!", "This is very unsettling!", "This is so packed!"]
    random_choice = random.choice(random_commentary)
    reflection_prompt = "--- Reflection Prompt ---\nHow can you apply this verse to your life today?"

    return f"{formatted_verse}{random_choice}\n\n{reflection_prompt}"

def main():
    print("Daily Verse Agent. Ask me for 'today's verse' or a 'verse about [topic]' or even a list of books in the bible. Type'exit' to quit.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break

        #Phase 1: Intent Parsing
        intent = parse_intent(user_input)
        action = intent.get("action")
        param = intent.get("param")

        #Phase 2: Decision Policy & Exection
        if action and action != "no_intent":
            # --- Start Decision Trace ---
            print("\n--- Agent Trace ---")
            print(f"Plan: User wants to '{action}'")
            print(f"Tool chosen: '{action}'")
            print(f"Tool Inputs: {param if param else 'None'}")
            print("----------------------\n")

            tool_function = TOOL_REGISTRY.get(action)
            if tool_function:
                if param:
                    result = tool_function(param)
                else:
                    result = tool_function()
                
                # --- End Execution Trace ---
                print("\n---- Agent Result ----")
                print(f"Raw Tool Output: {result}")
                print("---------------------\n")

                # Phase 3: Post-processing and Formatting
                final_response = format_output(result)
                print(f"Agent: {final_response}")
            else:
                print("Agent: Sorry, I couldn't find a tool for that action.")
        else:
            print("\n--- Trial Failure Trace ---")
            print("Plan: There seems to be no clear intent. I will inform the user that I can't help with the current request and suggest they try again.")
            print("---------------------------\n")

            print("Agent: I'm not sure what you mean. Please try again.")

if __name__ == "__main__":
    main()
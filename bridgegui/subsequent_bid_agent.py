import os
from dotenv import load_dotenv
from langchain.agents import Tool, initialize_agent
from langchain.agents import AgentType
from langchain_community.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOpenAI
import json
import logging
from typing import Dict
from bridgegui.llm_tools import count_hcp_tool, get_suit_distribution_tool, analyze_partner_opening_bid_tool
from bridgegui.llm_tools import is_allowed_bid_tool
from bridgegui.bid_analisis import get_bid_analisis
from bridgegui.subsequent_bid_suggestion_llm import get_subsequent_bid_suggestion

########################################
# 1) DEFINE OUR CUSTOM BRIDGE TOOLS
########################################

def get_subsequent_bid_suggestion_wrapper(input_data: dict | str) -> str:
    """
    Wrapper for the get_subsequent_bid_suggestion function to handle input as a dictionary or JSON string.
    Arguments:
    - input_data: A dictionary or JSON string containing the bidding history
    Returns:
    - A string with the suggested subsequent bid.
    """

    # If input_data is a string, attempt to parse it as JSON
    if isinstance(input_data, str):
        try:
            input_data = json.loads(input_data)  # Parse the string into a dictionary
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON input: {input_data}") from e

    # Ensure input_data is a dictionary
    if not isinstance(input_data, dict):
        raise TypeError("Input data must be a dictionary or a JSON string.")

    # Extract relevant fields from the input data
    position = input_data.get("position")
    updated_your_team_analisis = input_data.get("updated_your_team_analisis")
    updated_opponents_bid_analisis = input_data.get("updated_opponents_bid_analisis")
    bidding_history = input_data.get("bidding_history", [])
    allowed_bids = input_data.get("allowed_bids", [])

    # Ensure bidding_history and allowed_bids are lists
    if not isinstance(bidding_history, list):
        raise ValueError("bidding_history must be a list of strings.")
    if not isinstance(allowed_bids, list):
        raise ValueError("allowed_bids must be a list of strings.")

    return get_subsequent_bid_suggestion(
        position,
        updated_your_team_analisis,
        updated_opponents_bid_analisis,
        bidding_history,
        allowed_bids
    )

def last_4_bids_tool_wrapper(input_data: dict | str) -> list[str]:
    """
    Wrapper for the last_n_bids_function to handle input as a dictionary or JSON string.
    Arguments:
    - input_data: A dictionary or JSON string containing the bidding history
    Returns:
    - A list of the last n bids from the bidding history.
    """
    # If input_data is a string, attempt to parse it as JSON
    if isinstance(input_data, str):
        try:
            input_data = json.loads(input_data)  # Parse the string into a dictionary
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON input: {input_data}") from e

    # Ensure input_data is a dictionary
    if not isinstance(input_data, dict):
        raise TypeError("Input data must be a dictionary or a JSON string.")

    # Extract bidding history and n
    bidding_history = input_data.get("bidding_history", [])
    n = 4

    # Ensure bidding_history is a list
    if not isinstance(bidding_history, list):
        raise ValueError("bidding_history must be a list of strings.")

    return last_n_bids_function(bidding_history, n)

def last_n_bids_function(bidding_history: list[str], n: int) -> list[str]:
    """
    Extract the last n bids from the bidding history.
    Arguments:
    - bidding_history: A list of strings representing the bidding history. Example: ["south: Pass", "west: Pass", "north 2S", "east: 2NT", "south: 3S", "west: Pass"]
    - n: The number of last bids to extract. Example: 4
    Returns:
    - A list of the last n bids from the bidding history.
    """
    return bidding_history[-n:] if len(bidding_history) >= n else bidding_history

def update_your_team_analisis_function(input_data: dict | str) -> str:
    """
    Update your team analysis based on the last n bids.
    Input should be a dictionary with keys: 'position', 'perspective', 'your_team_analisis', and 'last_4_bids'.
    """

    input_data = input_data.replace("'", '"')


    if isinstance(input_data, str):
        input_data = json.loads(input_data)  # Parse the string into a dictionary

    position = input_data["position"]
    perspective = input_data["perspective"]
    your_team_analisis = input_data["your_team_analisis"]
    last_4_bids = input_data["last_4_bids"]

    response = get_bid_analisis(
        position=position,
        perspective=perspective,
        previouse_analisis=your_team_analisis,
        last_n_bids=last_4_bids
    )
    logging.debug("DEBUG: response from get_bid_analisis: %s", response)
    updated_analisis = response
    return updated_analisis

def update_opponents_bid_analisis_function(input_data: dict | str) -> str:
    """
    Update your opponents' bid analysis based on the last n bids.
    Input should be a dictionary with keys: 'position', 'perspective', 'opponents_bid_analisis', and 'last_4_bids'.
    """

    input_data = input_data.replace("'", '"')

    if isinstance(input_data, str):
        input_data = json.loads(input_data)  # Parse the string into a dictionary

    position = input_data["position"]
    perspective = input_data["perspective"]
    opponents_bid_analisis = input_data["opponents_bid_analisis"]
    last_4_bids = input_data["last_4_bids"]

    response = get_bid_analisis(
        position=position,
        perspective=perspective,
        previouse_analisis=opponents_bid_analisis,
        last_n_bids=last_4_bids
    )
    logging.debug("DEBUG: response from get_bid_analisis: %s", response)
    return response

def subsequent_bid_function(input_data: dict | str) -> str:
    """
    Analyze the current bidding situation and suggest a subsequent bid.
    Input should be a dictionary with keys: 'updated_your_team_analisis', 'updated_opponents_bid_analisis', 'bidding_history', and 'allowed_bids'.
    """

    input_data = input_data.replace("'", '"')

    if isinstance(input_data, str):
        input_data = json.loads(input_data)
    # Extract the relevant data from the input
    updated_your_team_analisis = input_data["updated_your_team_analisis"]
    updated_opponents_bid_analisis = input_data["updated_opponents_bid_analisis"]
    bidding_history = input_data["bidding_history"]
    allowed_bids = input_data["allowed_bids"]


    analysis = (
        f"Your team analysis: {updated_your_team_analisis}\n"
        f"Opponent's analysis: {updated_opponents_bid_analisis}\n"
        f"Bidding history: {', '.join(bidding_history)}\n"
        f"Allowed bids: {', '.join(allowed_bids)}\n"
        "Based on this analysis, you should consider making a bid."
    )
    return analysis

    
########################################
# 2) WRAP THE TOOLS AS LANGCHAIN TOOLS
########################################



last_4_bids_tool = Tool(
    name="last_4_bids_tool",
    func=last_4_bids_tool_wrapper,
    description=(
        "Use this tool to extract the last 4 bids from the bidding history based on:"
        "bidding history"
        "Input should be a dictionary with keys: 'bidding_history'."
        "The function returns a list of the last 4 bids."

    )
)

update_your_team_analisis_tool = Tool(
    name="update_your_team_analisis_tool",
    func=update_your_team_analisis_function,
    description=(
        "Use this tool to update your team analysis based on:"
        "your position, perspective, your team analysis, and the last 4 bids. "
        "Input should be a dictionary with keys: 'position', 'perspective', 'your_team_analisis', and 'last_4_bids'."
        "perspective is:Your team"
        "The function returns the updated your team analysis."
    )
)

update_opponents_bid_analisis_tool = Tool(
    name="update_opponents_bid_analisis_tool",
    func=update_opponents_bid_analisis_function,
    description=(
        "Use this tool to update your opponents' bid analysis based on:"
        "Your position, previouse opponents analisis, last 4 bids"
        "Input should be a dictionary with keys: 'position', 'perspective', 'opponents_bid_analisis', and 'last_4_bids'."
        "perspective is:Your opponents"
        "The function returns the updated opponents' analysis."
    )
)

get_subsequent_bid_suggestion_tool = Tool(
    name="get_subsequent_bid_suggestion_tool",
    func=get_subsequent_bid_suggestion_wrapper,
    description=(
        "Use this tool to analyze the current bidding situation and suggest a subsequent bid based on:"
        "your position, your updated team analysis, updated opponents' analysis, "
        "bidding history, and allowed bids."
        "Input should be a dictionary with keys: 'position', 'updated_your_team_analisis', "
        "'updated_opponents_bid_analisis', 'bidding_history', and 'allowed_bids'."
        "The function returns a string with the suggested bid."
    )
)


########################################
# 3) SET UP THE PROMPT FOR THE AGENT
########################################

# The agent prompt is crucial. We feed it all relevant context about
# the current state of the game, plus instructions on how to proceed.

response_bidding_prompt = PromptTemplate(
    input_variables=["position", "hand", "your_team_analisis", "your_last_bid", "opponents_bid_analisis", "allowed_bids", "bidding_history"],
    template="""
You are a Bridge Advisor specialized in the subsequent phase of bidding (after opening and response to opening).

Your job is to:
1. Extract the last 4 bids using the `last_4_bids_tool`.
2. Update your team's bid analysis using the `update_your_team_analisis_tool`.
3. Update your opponents' bid analysis using the `update_opponents_bid_analisis_tool`.
4. Analyze the current bidding situation using the `analyze_current_bidding_situation_tool`.
5. Verify if the suggested response is allowed using the `is_allowed_bid_tool`.

**Important**: Do not provide a final answer until all tools have been executed successfully. Only provide the final answer after completing all steps.

Respond with the final answer in json format:
    "your_team_analisis": "<updated_your_team_analisis>",
    "opponents_bid_analisis": "<updated_opponents_bid_analisis>",
    "bid_suggestion": "<subsequent_bid_suggestion>"


Position: {position}
Hand: {hand}
Your team analysis: {your_team_analisis}
Your last bid: {your_last_bid}
Opponents' bid analysis: {opponents_bid_analisis}
Bidding history: {bidding_history}
Allowed bids: {allowed_bids}
""".strip()
)

########################################
# 4) INITIALIZE THE LLM + AGENT
########################################

load_dotenv()

# Initialize the LLM using the new ChatOpenAI interface
llm = ChatOpenAI(
    temperature=0.0,
    model="gpt-3.5-turbo",  # Use the correct model name
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    verbose=True
)

subsequent_bidding_agent_tools = [
    is_allowed_bid_tool,
    last_4_bids_tool,
    update_your_team_analisis_tool,
    update_opponents_bid_analisis_tool,
    get_subsequent_bid_suggestion_tool
]

subsequent_bidding_agent = initialize_agent(
    tools=subsequent_bidding_agent_tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, 
    verbose=True,
    input=response_bidding_prompt,
)


########################################
# 5) EXAMPLE USAGE
########################################

def get_subsequent_bid_advice(
    position: str,
    hand: list[Dict[str, str]],  # Ensure the type hint reflects the expected structure
    your_team_analisis: str,
    your_last_bid: str,
    opponents_bid_analisis: str,
    allowed_bids: list[str] = None,
    bidding_history: list[str] = None,
) -> str:
    """
    This function is the "broker" that orchestrates context gathering
    and calls the LLM agent for a recommendation of subsequent bid phase
    """
    if allowed_bids is None:
        allowed_bids = []
    if bidding_history is None:
        bidding_history = []

    # Prepare input data for the agent's prompt
    prompt_input = {
        "position": position,
        "hand": json.dumps(hand),  # Serialize the hand properly
        "your_team_analisis": your_team_analisis,
        "your_last_bid": your_last_bid,
        "opponents_bid_analisis": opponents_bid_analisis,
        "allowed_bids": allowed_bids,  # Pass as a list, not serialized
        "bidding_history": bidding_history,  # Pass as a list, not serialized
    }

    # Debug: Log the prompt input
    print("DEBUG: Prompt input:", prompt_input)

    # Format the input for the agent
    response = subsequent_bidding_agent.invoke(
        input=response_bidding_prompt.format(
            position=prompt_input["position"],
            hand=prompt_input["hand"],  # Serialized hand
            your_team_analisis=prompt_input["your_team_analisis"],
            your_last_bid=prompt_input["your_last_bid"],
            opponents_bid_analisis=prompt_input["opponents_bid_analisis"],
            allowed_bids=json.dumps(prompt_input["allowed_bids"]),  # Serialize here
            bidding_history=json.dumps(prompt_input["bidding_history"]),  # Serialize here
        )
    )

    return response

# Example: BIDDING PHASE
if __name__ == "__main__":
    

    logging.basicConfig(level=logging.DEBUG)
    recommendation = get_subsequent_bid_advice(
        position="north",
        hand=[{"rank":"ace", "suit": "spades"}, {"rank": "king", "suit": "spades"}, {"rank": "queen", "suit": "spades"}, {"rank": "jack", "suit": "spades"}, {"rank": "10", "suit": "spades"}, {"rank": "ace", "suit": "hearts"}, {"rank": "king", "suit": "hearts"}, {"rank": "queen", "suit": "hearts"}, {"rank": "jack", "suit": "hearts"}, {"rank": "10", "suit": "hearts"}, {"rank": "9", "suit": "clubs"},{"rank": "8", "suit": "clubs"},{"rank": "7", "suit": "clubs"}],
        your_team_analisis="Your partner opened with Pass. So it is likely that your partner has 0-12 HCP and no 5-card suit. You have 20 HCP. So in total you have between 20-32 HCP and at least 5 spades. In total you have at least 5 hearts. In total you have at least 3 diamonds. In total you have at least 3 clubs. Your last bid was 2S to indicate to your partner strong hand with 5 spades and 20 HCP.",
        your_last_bid="2S",
        opponents_bid_analisis="Your opponents are West and East. West has passed. So it is likely that West has 0-12 HCP and no 5-card suit.",
        allowed_bids=["Pass", "1S", "1NT", "2C", "2D", "2H", "2S", "2NT", "3C", "3D", "3H", "3S", "3NT", "4C", "4D", "4H", "4S", "4NT", "5C", "5D", "5H", "5S", "5NT", "6C", "6D", "6H", "6S","6NT", "7C", "7D", "7H", "7S", "7NT", "X", "XX"],
        bidding_history=["south: Pass","west: Pass", "north 2S", "east: 2NT", "south: 3S", "west: Pass"],  # The prior bids
    )
    print("Bidding opening advice:", recommendation)



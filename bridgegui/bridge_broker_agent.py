import os
from dotenv import load_dotenv
from langchain.agents import Tool, initialize_agent
from langchain.agents import AgentType
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOpenAI
import json
import logging
from typing import List
from bridgegui.utils2 import parse_input_data
from bridgegui.bid_opening_agent import get_opening_advice
from bridgegui.bid_response_agent import get_opening_response_advice
from bridgegui.subsequent_bid_agent import get_subsequent_bid_advice
from langchain.tools import StructuredTool
from bridgegui.schemas import (
    RecognizeBiddingStageInput,
    OpeningBiddingToolInput,
    OpeningBiddingToolReponse,
    PlayAnalysisToolInput,
    getBrdidgeAdviceResponse,
    Card)




########################################
# 1) DEFINE OUR CUSTOM BRIDGE TOOLS
########################################



def bidding_stage_tool(position: str, bidding_history: List[Card]) -> str:
    """
    This function determines the bidding stage based on the position and bidding history.
    Args:
        position (str): The position of the player (e.g., "north", "south", "east", "west").
        bidding_history (List[str]): The history of bids made in the game.
    Returns:
        str: The bidding stage, which can be "Opening", "Response", or "Subsequent".
    """
    
    
    # Determine partner's position
    if position.lower() == "north":
        partners_position = "south"
    elif position.lower() == "south":
        partners_position = "north"
    elif position.lower() == "east":
        partners_position = "west"
    elif position.lower() == "west":
        partners_position = "east"
    else:
        raise ValueError("Invalid position. Must be one of: north, south, east, west.")

    # Count occurrences of position in bidding history
    position_count = sum(1 for bid in bidding_history if bid.lower().startswith(position.lower()))
    partners_count = sum(1 for bid in bidding_history if bid.lower().startswith(partners_position.lower()))

    if position_count == 0 and partners_count == 0:
        return "Opening"
    elif position_count == 0 and partners_count == 1:
        return "Response"
    else:
        return "Subsequent"
    
def opening_bidding_stage_function(position: str, hand: List[Card], allowed_bids: List[str], bidding_history: List[str]) -> OpeningBiddingToolReponse:
    """
    This function analyzes the opening bid based on the position, hand, allowed bids, and bidding history.
    Args:
        position (str): The position of the player (e.g., "north", "south", "east", "west").
        hand (List[Card]): The player's hand represented as a list of Card objects.
        allowed_bids (List[str]): The list of allowed bids.
        bidding_history (List[str]): The history of bids made in the game.
    Returns:
        str: The recommended opening bid.
    """
    input_data = OpeningBiddingToolInput(
        position=position,
        hand=hand,
        allowed_bids=allowed_bids,
        bidding_history=bidding_history
    )

    # Adjust the arguments passed to get_opening_advice
    response = get_opening_advice(input_data)
    logging.debug("Opening bidding stage response: %s", response)

    return response.get("output", "pass")  # Adjust based on the expected response format


def analyze_bidding_function(position, hand, bidding_history, allowed_bids, bidding_stage) -> str:
    """
    Parses the input_data string to a dictionary and applies bidding heuristics.
    Args:
        position (str): The position of the player (e.g., "north", "south", "east", "west").
        hand (List[Card]): The player's hand represented as a list of Card objects.
        bidding_history (List[str]): The history of bids made in the game.
        allowed_bids (List[str]): The list of allowed bids.
        bidding_stage (str): The current stage of the bidding process.
    Returns:
        str: The recommended bid.
    """

    if bidding_stage == "Opening":
        # Call the opening bidding stage tool
        input_data = OpeningBiddingToolInput(
            position=position,
            hand=hand,
            allowed_bids=allowed_bids,
            bidding_history=bidding_history
        )
        response = get_opening_advice(input_data)
    elif bidding_stage == "Response":
        # Call the response bidding stage tool
        response = get_opening_response_advice(
            position=position,
            hand=hand,
            allowed_bids=allowed_bids,
            bidding_history=bidding_history
        )
    elif bidding_stage == "Subsequent": 
        # Call the subsequent bidding stage tool
        response = get_subsequent_bid_advice(
            position=position,
            hand=hand,
            allowed_bids=allowed_bids,
            bidding_history=bidding_history
        )
    else:
        raise ValueError("Invalid bidding stage. Must be one of: Opening, Response, Subsequent.")
    # Debug: Log the response from the bidding analysis
    logging.debug("Bidding analysis response: %s", response)
    # Return the response from the bidding analysis
    if response is None:
        return "pass"
    if isinstance(response, str):
        # If the response is a string, check if it's empty
        if response.strip() == "":
            return "pass"
    elif isinstance(response, list):
        # If the response is a list, check if it's empty
        if not response:
            return "pass"
    elif isinstance(response, dict):
        # If the response is a dictionary, check if it has any keys
        if not response.keys():
            return "pass"
    # If the response is not empty, return it
    if isinstance(response, str):
        return response.strip()
    elif isinstance(response, list):
        # If the response is a list, return the first element
        return response[0].strip()
    elif isinstance(response, dict):
        # If the response is a dictionary, return the first value
        return list(response.values())[0].strip()
    # If the response is not empty, return it
    if not response:
        return "pass"
    return response
    
        

def analyze_play_tool(input_data: str) -> str:
    """
    Parses the input_data string to a dictionary and applies play analysis heuristics.
    """
    try:
        # Try JSON parsing first in case it comes in as valid JSON
        input_dict = json.loads(input_data)
    except json.JSONDecodeError:
        # Fall back to custom parsing if JSON fails
        input_dict = parse_input_data(input_data)

    # Extract the required fields
    position = input_dict.get("position")
    hand = input_dict.get("hand")
    dummy_hand = input_dict.get("dummy_hand")
    current_trick = input_dict.get("current_trick")
    allowed_cards = input_dict.get("allowed_cards")
    contract = input_dict.get("contract")
    tricks_taken = input_dict.get("tricks_taken")

    # Placeholder logic: simply return the first allowed card if any
    if allowed_cards and isinstance(allowed_cards, list) and allowed_cards:
        return allowed_cards[0]
    else:
        return "No valid card"
    


########################################
# 2) WRAP THE TOOLS AS LANGCHAIN TOOLS
########################################


play_analysis_tool = StructuredTool.from_function(
    name="play_analysis",
    func=analyze_play_tool,
    description=(
        "Use this tool to analyze the best card to play, given the position, "
        "hand, dummy hand, current trick, allowed cards, the contract, "
        "and the number of tricks already taken."
    ),
    handle_validation_error = True,
    args_schema=PlayAnalysisToolInput
)



recognize_bidding_stage_tool = StructuredTool.from_function(
    name="recognize_bidding_stage",
    func=bidding_stage_tool,
    description=(
        "Use this tool to recognize the bidding stage, given the "
        "bidding history and the position. "
        "Input should be a dictionary with keys 'position' and 'bidding_history'. "
        "The position can be one of: north, south, east, west. "
        "The bidding history is a list of strings, each representing a bid. "
        "The possible stages are: Opening, Response, Subsequent."
    ),
    handle_validation_error=True,
    args_schema=RecognizeBiddingStageInput
)


opening_bidding_tool = StructuredTool.from_function(
    name="opening_bidding_tool",
    func=opening_bidding_stage_function,
    description=(
        "Use this tool to analyze the opening bid. "
    ),
    handle_validation_error=True,
    args_schema=OpeningBiddingToolInput,
    response_format="content"
)




########################################
# 3) SET UP THE PROMPT FOR THE AGENT
########################################

# The agent prompt is crucial. We feed it all relevant context about
# the current state of the game, plus instructions on how to proceed.

bridge_prompt = PromptTemplate(
    input_variables=[
        "position", "phase", "hand", "allowed_bids", "bidding_history",
        "dummy_hand", "current_trick", "allowed_cards", "contract",
        "tricks_taken", "tricks_history", "your_team_analysis",
        "opponent_analysis", "bid_suggestion", "play_suggestion"
    ],
    template="""
You are a Bridge Advisor. 

Your job:
1. Determine if you need specialized analysis from the bidding or play tool.
2. If in bidding phase, determine the bidding stage and then figure out the best possible bid. 
3. If in play phase, figure out the best possible card to play.


Remember to call the appropriate tool if needed. If you already have enough 
information, propose a final answer. 

Your response must be in JSON format with the following keys:
    "your_team_analysis": "<updated_your_team_analysis>",
    "opponent_analysis": "<updated_opponent_analysis>",
    "bid_suggestion": "<subsequent_bid_suggestion>",
    "play_suggestion": "<card_to_play>"


You receive the following game state:

Position: {position}
Phase of the game: {phase}
Hand: {hand}
Allowed Bids: {allowed_bids}
Bidding History: {bidding_history}
Dummy Hand (if any): {dummy_hand}
Current Trick: {current_trick}
Allowed Cards: {allowed_cards}
Contract: {contract}
Tricks Taken: {tricks_taken}
Tricks History: {tricks_history}
Your team analysis: {your_team_analysis}
Opponent analysis: {opponent_analysis}
Bid suggestion: {bid_suggestion}
Play suggestion: {play_suggestion}

Your recommendation:
"""
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

tools = [play_analysis_tool, recognize_bidding_stage_tool, opening_bidding_tool]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, 
    verbose=True
)

########################################
# 5) EXAMPLE USAGE
########################################

def get_bridge_advice(
    position: str,
    phase: str,
    hand: list[str],
    allowed_bids: list[str] = None,
    bidding_history: list[str] = None,
    dummy_hand: list[str] = None,
    current_trick: list[str] = None,
    allowed_cards: list[str] = None,
    contract: str = None,
    tricks_taken: dict[str, int] = None,
    tricks_history: list[str] = None

) -> getBrdidgeAdviceResponse:
    """
    This function is the "broker" that orchestrates context gathering
    and calls the LLM agent for a recommendation.
    It takes a dictionary or a JSON string as input and returns the
    recommendation as a dictionary.
    Args:
        position (str): The position of the player (e.g., "north", "south", "east", "west").
        phase (str): The phase of the game ("bidding" or "play").
        hand (list[str]): The player's hand, represented as a list of dictionaries with 'rank' and 'suit'.
        allowed_bids (list[str]): A list of allowed bids.
        bidding_history (list[str]): A list of strings representing the history of bids.
        dummy_hand (list[str]): The dummy hand, represented as a list of dictionaries with 'rank' and 'suit'.
        current_trick (list[str]): The current trick, represented as a list of strings.
        allowed_cards (list[str]): A list of allowed cards to play.
        contract (str): The contract for the game.
        tricks_taken (dict[str, int]): A dictionary representing the number of tricks taken by each team.
        tricks_history (list[str]): A list of strings representing the history of tricks taken.
    Returns:
        getBrdidgeAdviceResponse: The recommendation from the agent.
    """
    if allowed_bids is None:
        allowed_bids = []
    if bidding_history is None:
        bidding_history = []
    if dummy_hand is None:
        dummy_hand = []
    if current_trick is None:
        current_trick = []
    if allowed_cards is None:
        allowed_cards = []
    if tricks_taken is None:
        tricks_taken = {"NS": 0, "EW": 0}
    if tricks_history is None:
        tricks_history = []

    logging.debug("DEBUG: Prompt input: %s", {
        "position": position,
        "phase": phase,
        "hand": hand,
        "allowed_bids": allowed_bids,
        "bidding_history": bidding_history,
        "dummy_hand": dummy_hand,
        "current_trick": current_trick,
        "allowed_cards": allowed_cards,
        "contract": contract,
        "tricks_taken": tricks_taken,
        "tricks_history": tricks_history
    })
    # Call the agent with the formatted input

    agent_response = agent.invoke({
        "input": bridge_prompt.format(
            position=position,
            phase=phase,
            hand=hand,  # Pass as a dictionary
            allowed_bids=allowed_bids,  # Pass as a list
            bidding_history=bidding_history,  # Pass as a list
            dummy_hand=dummy_hand,
            current_trick=current_trick,
            allowed_cards=allowed_cards,
            contract=contract,
            tricks_taken=tricks_taken,
            tricks_history=tricks_history,
            your_team_analysis="",  # Add default value
            opponent_analysis="",  # Add default value
            bid_suggestion="",  # Add default value
            play_suggestion=""  # Add default value
        )
    })
    # get output from the response
    output_json = agent_response['output']
    logging.debug("DEBUG: Agent response: %s", output_json)

    return output_json

# Example: BIDDING PHASE
if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    recommendation = get_bridge_advice(
        position="north",
        phase="bidding",
        hand=[{"rank":"ace", "suit": "spades"}, {"rank": "king", "suit": "spades"}, {"rank": "queen", "suit": "spades"}, {"rank": "jack", "suit": "spades"}, {"rank": "10", "suit": "spades"}, {"rank": "ace", "suit": "hearts"}, {"rank": "king", "suit": "hearts"}, {"rank": "queen", "suit": "hearts"}, {"rank": "jack", "suit": "hearts"}, {"rank": "10", "suit": "hearts"}, {"rank": "9", "suit": "clubs"},{"rank": "8", "suit": "clubs"},{"rank": "7", "suit": "clubs"}],
        allowed_bids=["Pass", "1NT", "1H", "2H", "2S", "2C"],
        bidding_history=[],  # The prior bids
        contract="",  # Not established yet
        tricks_taken={"NS": 0, "EW": 0}
    )
    print("Bidding advice:", recommendation)

    # Example: PLAY PHASE
    '''
    recommendation = get_bridge_advice(
        position="south",
        phase="Play",
        hand=[{"rank":"5", "suit": "spades"},{"rank":"3", "suit": "spades"}, {"rank":"2", "suit": "hearts"}, {"rank":"4", "suit": "hearts"}, {"rank":"ace", "suit": "clubs"}, {"rank":"king", "suit": "clubs"}, {"rank":"queen", "suit": "clubs"}, {"rank":"jack", "suit": "clubs"}, {"rank":"10", "suit": "clubs"}, {"rank":"9", "suit": "clubs"}],
        dummy_hand=[{"rank":"7", "suit": "spades"},{"rank":"6", "suit": "spades"}, {"rank":"5", "suit": "hearts"}, {"rank":"4", "suit": "hearts"}, {"rank":"3", "suit": "hearts"}, {"rank":"2", "suit": "diamonds"}, {"rank":"ace", "suit": "diamonds"}, {"rank":"king", "suit": "diamonds"}, {"rank":"queen", "suit": "diamonds"}, {"rank":"jack", "suit": "diamonds"}],
        current_trick=["West: 10S", "North: ???"],  # so far in the trick
        allowed_cards=[{"rank":"5", "suit": "spades"},{"rank":"3", "suit": "spades"}],  # Must follow suit in real Bridge
        contract="4S by NS",
        tricks_taken={"NS": 4, "EW": 2}
    )
    print("Play advice:", recommendation)'
    '''

import os
from dotenv import load_dotenv
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOpenAI
import json
import logging
from typing import List
from bridgegui.schemas import Card
from bridgegui.schemas import OpeningBiddingToolInput, OpeningBidToolInput, OpeningBidToolOutput, BidOpeningAgentOutput
from bridgegui.utils2 import parse_input_data
from bridgegui.llm_tools import count_hcp_tool, is_balanced_hand_tool, dominant_suit_tool, get_suit_distribution_tool
from langchain.tools import StructuredTool  # Import StructuredTool
from bridgegui.opening_bid_llm import  get_opening_bid


########################################
# 1) DEFINE OUR CUSTOM BRIDGE TOOLS
########################################
    
def opening_bid_function(**kwargs) -> OpeningBidToolOutput:
    """
    This function responds to the opening bid analysis and bid suggestion based on the input data.
    Args:
        kwargs: The input data containing position, hand, allowed bids, and bidding history.
    Returns:
        OpeningBidToolOutput: The recommendation from the agent.
    """
    # Extract arguments from kwargs
    hcp = kwargs.get("hcp")
    distribution = kwargs.get("distribution")
    balanced_hand = kwargs.get("balanced_hand")
    dominant_suit = kwargs.get("dominant_suit")

    # Debug: Log the input data
    logging.debug("DEBUG: Input data for opening bid function: %s", kwargs)

    # Call the LLM to get the opening bid analysis
    input_data = OpeningBidToolInput(
        hcp=hcp,
        distribution=distribution,
        balanced_hand=balanced_hand,
        dominant_suit=dominant_suit
    )

    response = get_opening_bid(input_data)
    return response

########################################
# 2) WRAP THE TOOLS AS LANGCHAIN TOOLS
########################################

opening_bid_tool = StructuredTool.from_function(
    name="opening_bid_tool",
    func=opening_bid_function,
    description=(
        "Use this tool to analyze the opening bid. "
    ),
    handle_validation_error=True,
    args_schema=OpeningBidToolInput,  # Ensure this matches the expected input type
    response_format="content"
)

########################################
# 3) SET UP THE PROMPT FOR THE AGENT
########################################

# The agent prompt is crucial. We feed it all relevant context about
# the current state of the game, plus instructions on how to proceed.

opening_bidding_prompt = PromptTemplate(
    input_variables=["position", "hand", "allowed_bids", "bidding_history"],
    template="""
You are a Bridge Advisor specialized in opening bids. Follow the instructions carefully and respond explicitly using the provided tools.

Bridge Suit Ranking (highest to lowest):
1. Spades (♠)
2. Hearts (♥)
3. Diamonds (♦)
4. Clubs (♣)

Counting High Card Points (HCP):
- Ace: 4 points
- King: 3 points
- Queen: 2 points
- Jack: 1 point
- Others: 0 points


Steps to Follow (in exact order, do not skip any):
1. Count High Card Points (HCP). Use count_hcp.
2. Determine suit distribution. Use get_suit_distribution.
3. Check if hand is balanced (no 5-card suit). Use is_balanced_hand.
   - If not balanced, identify dominant suit(s) (5+ cards). Use dominant_suit_tool.
4. Analyze the optimum opening bid based on the HCP, suit distribution, and balanced hand. Use opening_bid_tool.

Final response must be in this JSON format:
    "position": "<position>",
    "hand": <hand_as_json>,
    "bidding_history": <bidding_history>,
    "allowed_bids": <allowed_bids>,
    "hcp": <hcp>,
    "suit_distribution": <suit_distribution>,
    "is_balanced_hand": <true_or_false>,
    "dominant_suit": "<dominant_suit_as_json_string>",
    "your_team_analysis": "<concise_observation_summary>",
    "bid_suggestion": "<valid_bid_from_allowed_list_or_pass>"

Constraints:
- Ensure the bid suggestion is within the Allowed Bids. If the optimal bid is not allowed, then pass.

Input Information:
- Position: {position}
- Hand: {hand}
- Allowed Bids: {allowed_bids}
- Bidding History: {bidding_history}

Execute now:
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

opening_bidding_agent_tools =  [count_hcp_tool, is_balanced_hand_tool, dominant_suit_tool, get_suit_distribution_tool, opening_bid_tool]


opening_bidding_agent = initialize_agent(
    tools=opening_bidding_agent_tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, 
    verbose=True,
    input=opening_bidding_prompt
)

########################################
# 5) EXAMPLE USAGE
########################################

def get_opening_advice(input_data: "OpeningBiddingToolInput") -> "BidOpeningAgentOutput":
    """
    This function is the "broker" that orchestrates context gathering
    and calls the LLM agent for a recommendation.
    It takes a dictionary or a JSON string as input and returns the
    recommendation as a dictionary.
    Args:
        input_data (OpeningBiddingToolInput): The input data containing position, hand, allowed bids, and bidding history.
    Returns:
        OpeningBiddingToolOutput: The recommendation from the agent.
    """

    if input_data.allowed_bids is None:
        input_data.allowed_bids = []
    if input_data.bidding_history is None:
        input_data.bidding_history = []

    # Prepare input data for the agent's prompt
    prompt_input = {
        "position": input_data.position,
        "hand": input_data.hand,  # Pass the hand as-is
        "allowed_bids": input_data.allowed_bids,
        "bidding_history": input_data.bidding_history,
    }

    # Debug: Log the prompt input
    logging.debug("DEBUG: Prompt input: %s", prompt_input)

    # Call the agent with the formatted input
    response = opening_bidding_agent.invoke({
        "input": opening_bidding_prompt.format(
            position=input_data.position,
            hand=json.dumps([card.model_dump() for card in input_data.hand]),  # Ensure the hand is passed as a JSON string
            allowed_bids=json.dumps(input_data.allowed_bids),
            bidding_history=json.dumps(input_data.bidding_history)
        )
    })

    # Debug: Log the response
    logging.debug("DEBUG: get_opening_advice - Response: %s", response)

    return response

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    # Example usage
    position = "north"
    hand = [
            {"rank": "5", "suit": "clubs"}, 
            {"rank": "queen", "suit": "spades"}, 
            {"rank": "jack", "suit": "clubs"}, 
            {"rank": "6", "suit": "diamonds"}, 
            {"rank": "ace", "suit": "hearts"}, 
            {"rank": "8", "suit": "clubs"}, 
            {"rank": "queen", "suit": "clubs"}, 
            {"rank": "5", "suit": "spades"}, 
            {"rank": "9", "suit": "hearts"}, 
            {"rank": "6", "suit": "spades"}, 
            {"rank": "4", "suit": "spades"}, 
            {"rank": "3", "suit": "spades"}, 
            {"rank": "3", "suit": "clubs"}]
    #convert the hand to a list of Card objects
    hand = [Card(rank=card["rank"], suit=card["suit"]) for card in hand]

    allowed_bids = ["pass", "1 clubs", "1 diamonds", "1 hearts", "1 spades", "1 notrump", "2 clubs", "2 diamonds", "2 hearts", "2 spades", "2 notrump", "3 clubs", "3 diamonds", "3 hearts", "3 spades", "3 notrump", "4 clubs", "4 diamonds", "4 hearts", "4 spades", "4 notrump", "5 clubs", "5 diamonds", "5 hearts", "5 spades", "5 notrump", "6 clubs", "6 diamonds", "6 hearts", "6 spades", "6 notrump", "7 clubs", "7 diamonds", "7 hearts", "7 spades", "7 notrump"]
    bidding_history = []
    # Call the function to get the opening advice
    input_data = OpeningBiddingToolInput(
        position=position,
        hand=hand,
        allowed_bids=allowed_bids,
        bidding_history=bidding_history
    )
    recommendation = get_opening_advice(input_data)
    # Print the recommendation
    print("Recommendation:", recommendation)
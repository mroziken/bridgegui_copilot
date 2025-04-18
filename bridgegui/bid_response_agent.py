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
from bridgegui.llm_tools import is_allowed_bid_tool, suggest_response_bid_tool

########################################
# 1) DEFINE OUR CUSTOM BRIDGE TOOLS
########################################


    
########################################
# 2) WRAP THE TOOLS AS LANGCHAIN TOOLS
########################################



########################################
# 3) SET UP THE PROMPT FOR THE AGENT
########################################

# The agent prompt is crucial. We feed it all relevant context about
# the current state of the game, plus instructions on how to proceed.

response_bidding_prompt = PromptTemplate(
    input_variables=["position", "hand", "allowed_bids", "bidding_history"],
    template="""
You are a Bridge Advisor specialised in responses to partner opening bid. 

Use available tools to count HCP, check for 5-card suits, and determine if the hand is balanced.

Your job is:
1. Count the number of high card points (HCP) in your hand.
2. Get the distribution of suits in your hand.
3. Analyze the opening bid of your partner. 
4. Suggest a response to your partner's opening bid based on analisis of partners opening bid and your hand analisis.
5. Verify if the suggested response is allowed and finalize the response.

Respond with the final answer in json format:
    "your_team_analisis": "<updated_your_team_analisis>",
    "bid_suggestion": "<subsequent_bid_suggestion>"


## Exampes

**Example 1:
    User input:
        Position: north
        Hand: [{{"rank":"ace", "suit": "spades"}}, {{"rank": "king", "suit": "spades"}}, {{"rank": "queen", "suit": "spades"}}, {{"rank": "jack", "suit": "spades"}}, {{"rank": "10", "suit": "spades"}}, {{"rank": "ace", "suit": "hearts"}}, {{"rank": "king", "suit": "hearts"}}, {{"rank": "queen", "suit": "hearts"}}, {{"rank": "jack", "suit": "hearts"}}, {{"rank": "10", "suit": "hearts"}}, {{"rank": "9", "suit": "clubs"}},{{"rank": "8", "suit": "clubs"}},{{"rank": "7", "suit": "clubs"}}]
        Allowed Bids: ["Pass", "1NT", "1H", "2H", "2S", "2C", "5H"]
        Bidding History: ["south: 1H","west: Pass"]
    Your answer:
    {{
        "your_team_analisis": "Your partner is South, who has bid 1H. Your partner has betwen 12-18 HCP. You have 20 HCP. So in total you have between 32-38 HCP. Your partner has at least 5 hearts. You have 5 hearts. So in total you have at least 10 hearts. Based on analisis of your partners opening and your hand analisis you should bid 5 Hearts."
        "bid_suggestion": "5 Hearts is allowed bid. 5 Hearts is the last bid of your opponent on your left hand side. You bid contra (X) to opponents last bid which is allowed bid. So your bid is: 5 Hearts."
    }}
**End of Example 1**

**Example 2:
    User input:
        Position: north
        Hand: [{{"rank":"ace", "suit": "spades"}}, {{"rank": "king", "suit": "spades"}}, {{"rank": "queen", "suit": "spades"}}, {{"rank": "jack", "suit": "spades"}}, {{"rank": "10", "suit": "spades"}}, {{"rank": "ace", "suit": "hearts"}}, {{"rank": "king", "suit": "hearts"}}, {{"rank": "queen", "suit": "hearts"}}, {{"rank": "jack", "suit": "hearts"}}, {{"rank": "10", "suit": "hearts"}}, {{"rank": "9", "suit": "clubs"}},{{"rank": "8", "suit": "clubs"}},{{"rank": "7", "suit": "clubs"}}]
        Allowed Bids: ["Pass", "1NT", "1H", "2H", "2S", "2C", "X"]
        Bidding History: ["south: 1H","west: 5H"]
    Your answer:
    {{
        "your_team_analisis": "Your partner is South, who has bid 1H. Your partner has betwen 12-18 HCP. You have 20 HCP. So in total you have between 32-38 HCP. Your partner has at least 5 hearts. You have 5 hearts. So in total you have at least 10 hearts. Based on analisis of your partners opening and your hand analisis you should bid 5 Hearts."
        "bid_suggestion:": "5 Hearts is allowed bid. 5 Hearts is the last bid of your opponent on your left hand side. You bid contra (X) to opponents last bid which is allowed bid. So your bid is: X."
    }}
**End of Example 2**
## End of Examples
        
Hand: {hand}
Allowed Bids: {allowed_bids}
Bidding History: {bidding_history}

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

response_bidding_agent_tools =  [count_hcp_tool, get_suit_distribution_tool, analyze_partner_opening_bid_tool, is_allowed_bid_tool, suggest_response_bid_tool]

response_bidding_agent = initialize_agent(
    tools=response_bidding_agent_tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, 
    verbose=True,
    input=response_bidding_prompt,
)

########################################
# 5) EXAMPLE USAGE
########################################

def get_opening_response_advice(
    position: str,
    hand: list[Dict[str, str]],  # Ensure the type hint reflects the expected structure
    allowed_bids: list[str] = None,
    bidding_history: list[str] = None,
) -> str:
    """
    This function is the "broker" that orchestrates context gathering
    and calls the LLM agent for a recommendation of response to opening
    bid of a partner.
    """
    if allowed_bids is None:
        allowed_bids = []
    if bidding_history is None:
        bidding_history = []

    # Prepare input data for the agent's prompt
    prompt_input = {
        "position": position,
        "hand": json.dumps(hand),  # Serialize the hand properly
        "allowed_bids": json.dumps(allowed_bids),
        "bidding_history": json.dumps(bidding_history),
    }

    # Debug: Log the prompt input
    print("DEBUG: Prompt input:", prompt_input)

    response = response_bidding_agent.run(
        input=response_bidding_prompt.format(
            position=prompt_input["position"],
            hand=prompt_input["hand"],  # Pass the serialized hand
            allowed_bids=prompt_input["allowed_bids"],
            bidding_history=prompt_input["bidding_history"]
        )
    )

    return response

# Example: BIDDING PHASE
if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    recommendation = get_opening_response_advice(
        position="north",
        hand=[{"rank":"ace", "suit": "spades"}, {"rank": "king", "suit": "spades"}, {"rank": "queen", "suit": "spades"}, {"rank": "jack", "suit": "spades"}, {"rank": "10", "suit": "spades"}, {"rank": "ace", "suit": "hearts"}, {"rank": "king", "suit": "hearts"}, {"rank": "queen", "suit": "hearts"}, {"rank": "jack", "suit": "hearts"}, {"rank": "10", "suit": "hearts"}, {"rank": "9", "suit": "clubs"},{"rank": "8", "suit": "clubs"},{"rank": "7", "suit": "clubs"}],
        allowed_bids=["Pass", "1S", "1NT", "2C", "2D", "2H", "2S", "2NT", "3C", "3D", "3H", "3S", "3NT", "4C", "4D", "4H", "4S", "4NT", "5C", "5D", "5H", "5S", "5NT", "6C", "6D", "6H", "6S","6NT", "7C", "7D", "7H", "7S", "7NT", "X", "XX"],
        bidding_history=["south: 1D","west: Pass"],  # The prior bids
    )
    print("Bidding opening advice:", recommendation)


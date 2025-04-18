import os
from dotenv import load_dotenv
from langchain_community.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOpenAI
import logging
from bridgegui.schemas import OpeningBidToolInput, OpeningBidToolOutput

########################################
# 1) DEFINE OUR CUSTOM BRIDGE TOOLS
########################################
    
########################################
# 2) WRAP THE TOOLS AS LANGCHAIN TOOLS
########################################

########################################
# 3) SET UP THE PROMPT FOR THE AGENT
########################################

opening_bidding_prompt = PromptTemplate(
    input_variables=["hcp", "distribution", "balanced_hand", "dominant_suit"],
    template="""
You are a Bridge Advisor specialised in opening bid. 

You assume the opening strategy is as described in bidding strategy below.

Bid Rules:
- **pass** if HCP < 12.
- **12–18 HCP**:
  - If you have a 5-card suit, open at the **1-level** in the dominant suit (use suit priority above).
  - **Balanced hand, 12–14 HCP**: Open **1 Clubs (♣)**.
  - **Balanced hand, 15–18 HCP**: Open **1 Notrump**.
- **19+ HCP and a 5-card suit**: Open at the **2-level** in the dominant suit.
- **19–23 HCP, no 5-card suit**: Open **2 Clubs (♣)**.
- **24+ HCP, no 5-card suit**: Open **3 Notrump**.

Respond with json format:
    "hcp": {hcp},
    "distribution": {distribution},
    "balanced_hand": {balanced_hand},
    "dominant_suit": {dominant_suit},
    "your_team_analysis": "Your team analysis here.",
    "bid_suggestion": "Your bid suggestion here."

bid_suggestion must be unambiguous and in the format "1H", "2S", "3NT", etc.
your_team_analysis must explain the reasoning behind the bid suggestion.

Input data:
- HCP: {hcp}
- Distribution: {distribution}
- Balanced hand: {balanced_hand}
- Dominant suit: {dominant_suit}

Execute now: 

""".strip()
)

########################################
# 4) INITIALIZE THE LLM 
########################################

load_dotenv()

# Initialize the LLM using the new ChatOpenAI interface
llm = ChatOpenAI(
    temperature=0.0,
    model="gpt-3.5-turbo",  # Use the correct model name
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    verbose=True
)

########################################
# 5) EXAMPLE USAGE
########################################

def get_opening_bid(
    input_data: OpeningBidToolInput
) -> OpeningBidToolOutput:
    """
    Returns the opening bid analysis for the given input data.
    Args:
        input_data (OpeningBidToolInput): The input data for the opening bid analysis.
    Returns:
        OpeningBidToolOutput: The output data for the opening bid analysis.
    """

    # Prepare input data for the agent's prompt
    prompt_input = {
        "hcp": input_data.hcp,
        "distribution": input_data.distribution,
        "balanced_hand": input_data.balanced_hand,
        "dominant_suit": input_data.dominant_suit,
    }

    # Debug: Log the prompt input
    print("DEBUG: Prompt input:", prompt_input)

    response = llm.invoke(
        opening_bidding_prompt.format(
            hcp=prompt_input["hcp"],
            distribution=prompt_input["distribution"],
            balanced_hand=prompt_input["balanced_hand"],
            dominant_suit=prompt_input["dominant_suit"]
            )
        )
    # Debug: Log the response
    print("DEBUG: Response:", response)

    return response.content

# Example: BIDDING PHASE
if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    # Example input data
    hcp = 15
    distribution = "5-3-3-2"
    balanced_hand = True
    dominant_suit = "Hearts"
    input_data = OpeningBidToolInput(
        hcp=hcp,
        distribution=distribution,
        balanced_hand=balanced_hand,
        dominant_suit=dominant_suit,
        allowed_bids=["1S", "1H", "1D", "1C"],
        bidding_history=[]
    )

    analisis = get_opening_bid(
        input_data
    )
    print("Opening bid response:", analisis)
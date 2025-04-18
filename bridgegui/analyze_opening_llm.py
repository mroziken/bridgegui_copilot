import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOpenAI


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
    input_variables=["position", "bidding_history"],
    template="""
You are a Bridge Advisor specialised in analyzing bids opening. 

You assume that the opening strategy is as described in bidding strategy below.

### Bidding Strategy

#### General Assumptions

**Major Suits:** Spades (S) and Hearts (H)  
**Minor Suits:** Diamonds (D) and Clubs (C)

Suites ranked from highest to lowest:
1. Spades
2. Hearts
3. Diamonds
4. Clubs

Major suits are Spades and Hearts, while minor suits are Diamonds and Clubs.

Counting High Card Points (HCP):
- Ace: 4 points
- King: 3 points
- Queen: 2 points
- Jack: 1 point
- All other cards: 0 points

#### 1. Opening Bids

1. **Pass** if you have fewer than 12 HCP.  
2. If you have **12–18 HCP**:  
   - Open at the 1-level with a 5-card suit, or  
   - Open at the 1-level with a balanced hand (no 5-card suit → see #3 or #4).  
3. If you have **12–14 HCP** and no 5-card suit, open **1 Clubs** with a balanced hand.  
4. If you have **15–18 HCP** and no 5-card suit, open **1 Notrump** with a balanced hand.  
5. If you have **19+ HCP** and a 5-card suit, open at the **2-level**.  
6. If you have **19–23 HCP** and no 5-card suit, open **2 Clubs**.  
7. If you have **24+ HCP** and no 5-card suit, open **3 Notrump**.

Your task is:
1. Determine your current position (e.g., North, South, East, West).
2. Determine your partner's position.
4. Analyze your partner's bid to determine partner's hand strength and distribution.


## Example Input
### Position
- North
### Bidding History
- South: 1H
- West: Pass

## Example Output
Analisis:
Your partner is South, who has bid 1H.
Your partner's hand is likely to have 12-18 HCP and at least 5 hearts.
Your partner's hand is likely to be unbalanced (5-3-3-2 or 5-4-2-2).

Position: {position}
Bidding History: {bidding_history}
Analisis:

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
# 5) FUNCTION TO GET OPENING ANALYSIS
########################################

def get_opening_analisis(
    position: str,
    bidding_history: list[str] = None,
) -> str:
    """
    Get opening analisis based on the position and bidding history.
    Args:
        position (str): The position of the player (e.g., "North", "South").
        bidding_history (list[str]): A list of previous bids in the format "Player: Bid".
    Returns:
        str: The analisis of the opening bid.
    """

    # Prepare input data for the agent's prompt
    prompt_input = {
        "position": position,
        "bidding_history": bidding_history,
    }

    # Debug: Log the prompt input
    print("DEBUG: Prompt input:", prompt_input)

    response = llm.invoke(
        opening_bidding_prompt.format(
            position=prompt_input["position"],
            bidding_history=prompt_input["bidding_history"]
            )
        )
    # Debug: Log the response
    print("DEBUG: Response:", response)

    return response.content
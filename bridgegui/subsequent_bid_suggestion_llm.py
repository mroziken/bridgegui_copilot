import os
from dotenv import load_dotenv
import logging
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

bid_analisis_prompt = PromptTemplate(
    input_variables=["position","your_team_analisis","opponents_bid_analisis", "bidding_history", "allowed_bids"],
    template="""
You are a Bridge Advisor specialised in subsequent bids analisis (after openning and response bids).

You assume that the team follows strategy as described in bidding strategy below.

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



- If you and partner together hold **8+ cards** in a major suit, aim to finalize the contract in that major.  
- If you do **not** have 8+ major suit cards but have a **strong** combined HCP, aim for a Notrump contract.  
- If you do **not** have 8+ major suit cards and a **weak** combined HCP, finalize in a minor suit.  
- Typical combined HCP thresholds for final contracts:  
  - 19–24 HCP → Aim for 3-level  
  - 25–28 HCP → Aim for 4-level  
  - 29–32 HCP → Aim for 5-level  
  - 33–36 HCP → Aim for 6-level (small slam)  
  - 37–40 HCP → Aim for 7-level (grand slam)
- If current highest bid is above your aim contract level then Pass

---


## Exampes
**Example 1:
    User input:
        Position: north
        Your team analisis: Your partner is South, and his first bid was pass but he responded to your opening 2S with 3S which indicates 3-4 cards in spades and 7 to 11 HCP. Your partner has betwen 7-11 HCP. You have 20 HCP. So in total you have between 27-31 HCP. Your partner has 3 to 4 spades. You have 5 spades. So in total you have at least 8 spades. In total you have at least 5 hearts. In total you have at least 3 diamonds. In total you have at least 3 clubs
        opponents analisis: Your opponents are West and East. West has passed. So it is likely that West has 0-12 HCP and no 5-card suit, East has bid 2NT. So it is likely that East has 12-18 HCP and no 5-card suit. West has passed again which indicates that West has below 6 HCP since was not able to respond to East's 2NT bid.
        Bidding History: ["south: Pass","west: Pass", "north 2S", "east: 2NT", "south: 3S", "west: Pass"]
        Allowed Bids: "Pass", "1S", "1NT", "2C", "2D", "2H", "2S", "2NT", "3C", "3D", "3H", "3S", "3NT", "4C", "4D", "4H", "4S", "4NT", "5C", "5D", "5H", "5S", "5NT", "6C", "6D", "6H", "6S","6NT", "7C", "7D", "7H", "7S", "7NT", "X", "XX"]
    Your answer:
        Your and your partner's combined HCP is between 27-31 HCP. You have at least 8 spades. So you should aim for minimu 3-level contract and maximum 4-level contract. Since you have at least 8 spades continue to bid in spades. Current highest bid is 3S by your partner. It is within your target bid level. Recomendation Pass.
**End of Example 1**

**Example 2:
    User input:
        Position: north
        Your team analisis: Your partner is South, and his first bid was pass but he responded to your opening 2S with 3S which indicates 3-4 cards in spades and 7 to 11 HCP. Your partner has betwen 7-11 HCP. You have 20 HCP. So in total you have between 27-31 HCP. Your partner has 3 to 4 spades. You have 5 spades. So in total you have at least 8 spades. In total you have at least 5 hearts. In total you have at least 3 diamonds. In total you have at least 3 clubs
        Opponents analisis: Your opponents are West and East. West has passed. So it is likely that West has 0-12 HCP and no 5-card suit, East has bid 2NT. So it is likely that East has 12-18 HCP and no 5-card suit. West has passed again which indicates that West has below 6 HCP since was not able to respond to East's 2NT bid.
        Bidding History: ["south: Pass","west: Pass", "north 2S", "east: 2NT", "south: 3S", "west: 3NT"]
        Allowed Bids: "Pass", "1S", "1NT", "2C", "2D", "2H", "2S", "2NT", "3C", "3D", "3H", "3S", "3NT", "4C", "4D", "4H", "4S", "4NT", "5C", "5D", "5H", "5S", "5NT", "6C", "6D", "6H", "6S","6NT", "7C", "7D", "7H", "7S", "7NT", "X", "XX"]
    Your answer:
        Your and your partner's combined HCP is between 27-31 HCP. You have at least 8 spades. So you should aim for minimu 3-level contract and maximum 4-level contract. Since you have at least 8 spades continue to bid in spades. Current highest bid is 3NT by your opponent. You are safe to bid 4S since 4s is in your target bid level. 4S is allowed bid. So your bid is 4S.
**End of Example 2**

## End of Examples

Position: {position}
Your team analisis: {your_team_analisis}
Opponents analisis: {opponents_bid_analisis}
Bidding History: {bidding_history}
Allowed Bids: {allowed_bids}
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

def get_subsequent_bid_suggestion(
    position: str,
    your_team_analisis: str,
    opponents_analisis: str,
    allowed_bids: list[str],
    bidding_history: list[str],
) -> str:
    """
    Returns bid suggestion for subsequent bids based on the provided parameters.
    Args:
        position (str): The position of the player (e.g., "North", "South").
        your_team_analisis (str): The analisis of your team.
        opponents_analisis (str): The analisis of the opponents.
        allowed_bids (list[str]): A list of allowed bids.
        bidding_history (list[str]): A list of previous bids in the format "Player: Bid".
    Returns:
        str: The bid suggestion.
    """

    # Prepare input data for the agent's prompt
    prompt_input = {
        "position": position,
        "your_team_analisis": your_team_analisis,
        "opponents_bid_analisis": opponents_analisis,
        "bidding_history": bidding_history,
        "allowed_bids": allowed_bids,
    }

    # Debug: Log the prompt input
    print("DEBUG: Prompt input:", prompt_input)

    response = llm.invoke(
        bid_analisis_prompt.format(
            position=prompt_input["position"],
            your_team_analisis=prompt_input["your_team_analisis"],
            opponents_bid_analisis=prompt_input["opponents_bid_analisis"],
            bidding_history=prompt_input["bidding_history"],
            allowed_bids=prompt_input["allowed_bids"],
            )
        )
    # Debug: Log the response
    print("DEBUG: Response:", response)

    return response.content

# Example: BIDDING PHASE
if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    bid_suggestion = get_subsequent_bid_suggestion(
        position="north",
        your_team_analisis="Your partner is South, and his first bid was pass but he responded to your opening 2S with 3S which indicates 3-4 cards in spades and 7 to 11 HCP. Your partner has between 7-11 HCP. You have 20 HCP. So in total you have between 27-31 HCP. Your partner has 3 to 4 spades. You have 5 spades. So in total you have at least 8 spades. In total, you have at least 5 hearts, 3 diamonds, and 3 clubs. Based on the bidding so far, it seems like you and your partner have a strong hand and could potentially aim for a game or slam contract in spades.", 
        opponents_analisis="Your opponents East has bid 2NT, indicating 12-18 HCP and no 5-card suit. West has passed again, suggesting they have below 6 HCP. In total, your opponents likely have between 12-24 HCP. They may stop bidding at 3NT.",
        allowed_bids=["Pass", "1S", "1NT", "2C", "2D", "2H", "2S", "2NT", "3C", "3D", "3H", "3S", "3NT", "4C", "4D", "4H", "4S", "4NT", "5C", "5D", "5H", "5S", "5NT", "6C", "6D", "6H", "6S","6NT", "7C", "7D", "7H", "7S", "7NT", "X", "XX"],
        bidding_history=["south: Pass","west: Pass", "north 2S", "east: 2NT", "south: 3S", "west: 4NT"],  
    )
    print("Bid suggestion:", bid_suggestion)

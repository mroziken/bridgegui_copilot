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
    input_variables=["position","perspective","previouse_analisis", "last_n_bids"],
    template="""
You are a Bridge Advisor specialised in analyzing bridge bidding situation of {perspective} team. 

You assume that the team follows strategy as described in bidding strategy below.

### Bidding Strategy

#### General Assumptions

**Major Suits:** Spades (S) and Hearts (H)  
**Minor Suits:** Diamonds (D) and Clubs (C)

Suits ranked from highest to lowest:
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

#### 2. Responses to Partner’s Opening Bid

**Case A: Partner opened 1 Clubs**  
1. 0–6 HCP → Pass  
2. 7–12 HCP + 4+ Major → Bid 1 of that major  
3. 7–12 HCP + no 4+ Major but 5+ Diamonds → Bid 1 Diamonds  
4. 7–10 HCP + no 4+ Major but 6+ Clubs → Bid 2 Clubs  
5. 11–12 HCP + no 4+ Major but 6+ Clubs → Bid 3 Clubs  
6. 7–10 HCP + no 4+ Major, no 5+ Diamonds, no 6+ Clubs → Bid 1 Notrump  
7. 11–12 HCP + no 4+ Major, no 5+ Diamonds, no 6+ Clubs → Bid 2 Notrump  
8. 13+ HCP + 5+ Spades/Hearts/Diamonds → Jump-shift (2 of the suit)  
9. 13+ HCP + no 5+ major/diamonds but 7+ Clubs → Bid 5 Clubs  
10. 13+ HCP + no 5+ major/diamonds but 4 Spades/Hearts → Bid 1 of that major  
11. 13+ HCP + no 4+ major, no 5+ diamonds, no 7+ clubs → Bid 3 Notrump  

**Case B: Partner opened 1 Diamonds**  
1. 0–6 HCP → Pass  
2. 7–12 HCP + 4+ Major → Bid 1 of that major  
3. 7–10 HCP + no 4+ Major but 4+ Diamonds → Bid 2 Diamonds  
4. 11–12 HCP + no 4+ Major but 4+ Diamonds → Bid 3 Diamonds  
5. 7–10 HCP + no 4+ Major, no 4+ Diamonds → Bid 1 Notrump  
6. 11–12 HCP + no 4+ Major, no 4+ Diamonds → Bid 2 Notrump  
7. 13+ HCP + 5+ Spades/Hearts/Clubs → Jump-shift (2 of the suit)  
8. 13+ HCP + no 5+ major/club but 4 Spades/Hearts → Bid 1 of that major  
9. 13+ HCP + no 4+ major but 6+ Diamonds → Bid 5 Diamonds  
10. 13+ HCP + no 4+ major, no 6+ Diamonds → Bid 3 Notrump  

**Case C: Partner opened 1 Hearts**  
1. 0–6 HCP → Pass  
2. 7–10 HCP + 3+ Hearts → Bid 2 Hearts  
3. 11–12 HCP + 3+ Hearts → Bid 3 Hearts  
4. 13–18 HCP + 3+ Hearts → Bid 4 Hearts  
5. No 3+ Hearts but 7–12 HCP + 4+ Spades → Bid 1 Spade  
6. No 3+ Hearts but 7–10 HCP + no 4+ Spades → Bid 1 Notrump  
7. No 3+ Hearts but 11–12 HCP + no 4+ Spades → Bid 2 Notrump  
8. No 3+ Hearts but 13+ HCP + 5+ Diamonds/Clubs/Spades → Jump-shift (2 of the suit)  
9. No 3+ Hearts but 13+ HCP + no 5+ side suit but 4 Spades → Bid 1 Spade  
10. No 3+ Hearts, 13+ HCP, no suitable suit → Bid 3 Notrump  

**Case D: Partner opened 1 Spades**  
1. 0–6 HCP → Pass  
2. 7–10 HCP + 3+ Spades → Bid 2 Spades  
3. 11–12 HCP + 3+ Spades → Bid 3 Spades  
4. 13–18 HCP + 3+ Spades → Bid 4 Spades  
5. No 3+ Spades but 7–10 HCP + 4+ Hearts → Bid 1 Notrump  
6. No 3+ Spades but 11–12 HCP + 4+ Hearts → Bid 2 Notrump  
7. No 3+ Spades but 13+ HCP + 5+ Diamonds/Clubs/Hearts → Jump-shift (2 of the suit)  
8. No 3+ Spades + 13+ HCP + no 5+ side suit → Bid 3 Notrump  

**Case E: Partner opened 1 Notrump**  
1. 0–7 HCP + no 5+ major or 6+ minor → Pass  
2. 8–9 HCP + no 5+ major or 6+ minor → Bid 2 Notrump  
3. 10–15 HCP + no 5+ major or 6+ minor → Bid 3 Notrump  
4. 16–17 HCP + no 5+ major or 6+ minor → Bid 4 Notrump  
5. 18–20 HCP + no 5+ major or 6+ minor → Bid 6 Notrump  
6. 5+ Spades → Transfer via 2 Hearts (partner rebids 2 Spades)  
7. 5+ Hearts → Transfer via 2 Diamonds (partner rebids 2 Hearts)  
8. 6+ Diamonds → Transfer via 3 Clubs (partner rebids 3 Diamonds)  
9. 6+ Clubs → Transfer via 3 Spades (partner rebids 3 Clubs)

---

### 3. Additional Guidelines

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
        Perspective: Your team
        Previous analisis: Your partner opened with Pass. So it is likely that your partner has 0-12 HCP and no 5-card suit. You have 20 HCP. So in total you have between 20-32 HCP and at least 5 spades. In total you have at least 5 hearts. In total you have at least 3 diamonds. In total you have at least 3 clubs. Your last bid was 2S to indicate to your partner strong hand with 5 spades and 20 HCP.,
        Last 4 bids: ["north 2S", "east: 2NT", "south: 3S", "west: Pass"]
    Your answer:
        Your partner is South, and his first bid was pass but he responded to your opening 2S with 3S which indicates 3-4 cards in spades and 7 to 11 HCP
        Your partner has betwen 7-11 HCP. You have 20 HCP. So in total you have between 27-31 HCP.
        Your partner has 3 to 4 spades. You have 5 spades. So in total you have at least 8 spades.
        In total you have at least 5 hearts. In total you have at least 3 diamonds. In total you have at least 3 clubs
**End of Example 1**

**Example 2:
    User input:
        Position: north
        Perspective: Opponents
        Previous analisis: Your opponents are West and East. West has passed. So it is likely that West has 0-12 HCP and no 5-card suit,
        Last 4 bids: ["north 2S", "east: 2NT", "south: 3S", "west: Pass"]
    Your answer:
        Your opponents East has bid 2NT. So it is likely that East has 12-18 HCP and no 5-card suit. West has passed again which indicates that West has below 6 HCP since was not able to respond to East's 2NT bid.
        Assuming that east have 12-18 HCP and west has 0-6 HCP. So in total you have between 12-24 HCP. So probably they will stop bidding at 3NT.
**End of Example 2**

## End of Examples

Position: {position}
Perspective: {perspective}
Previouse analisis: {previouse_analisis}
Last 4 bids: {last_n_bids}
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

def get_bid_analisis(
    position: str,
    perspective: str,
    previouse_analisis: str,
    last_n_bids: list[str] = None,
) -> str:
    """
    Returns updated analisis of based on the previous analisis and last n bids.
    Args:
        previouse_analisis (str): The analisis of the previous bids.
        last_n_bids (list[str], optional): The last n bids. Defaults to None.
    Returns:
        str: The updated analisis.
    """

    # Prepare input data for the agent's prompt
    prompt_input = {
        "position": position,
        "perspective": perspective,
        "previouse_analisis": previouse_analisis,
        "last_n_bids": last_n_bids,
    }

    # Debug: Log the prompt input
    print("DEBUG: Prompt input:", prompt_input)

    response = llm.invoke(
        bid_analisis_prompt.format(
            position=prompt_input["position"],
            perspective=prompt_input["perspective"],
            previouse_analisis=prompt_input["previouse_analisis"],
            last_n_bids=prompt_input["last_n_bids"]
            )
        )
    # Debug: Log the response
    print("DEBUG: Response:", response)

    return response.content

# Example: BIDDING PHASE
if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    analisis = get_bid_analisis(
        position="north",
        perspective="Your",
        previouse_analisis="Your partner opened with Pass. So it is likely that your partner has 0-12 HCP and no 5-card suit. You have 20 HCP. So in total you have between 20-32 HCP and at least 5 spades. In total you have at least 5 hearts. In total you have at least 3 diamonds. In total you have at least 3 clubs. Your last bid was 2S to indicate to your partner strong hand with 5 spades and 20 HCP.",
        last_n_bids=["north 2S", "east: 2NT", "south: 3H", "west: Pass"],  
    )
    print("Bid analisis:", analisis)

    logging.basicConfig(level=logging.DEBUG)
    analisis = get_bid_analisis(
        position="north",
        perspective="Opponents",
        previouse_analisis="Your opponents are West and East. West has passed. So it is likely that West has 0-12 HCP and no 5-card suit.",
        last_n_bids=["north 2S", "east: 2NT", "south: 3H", "west: Pass"],  
    )
    print("Bid analisis:", analisis)
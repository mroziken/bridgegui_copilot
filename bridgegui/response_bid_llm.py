import os
from dotenv import load_dotenv
from langchain_community.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain_community.chat_models import ChatOpenAI
import logging


########################################
# 1) DEFINE OUR CUSTOM BRIDGE TOOLS
########################################
    
########################################
# 2) WRAP THE TOOLS AS LANGCHAIN TOOLS
########################################

########################################
# 3) SET UP THE PROMPT FOR THE AGENT
########################################

response_bidding_prompt = PromptTemplate(
    input_variables=["partners_opening_bid_analysis", "your_hand_analysis"],
    template="""
You are a Bridge Advisor specialised in responses to opening bid. 

You assume that the response to opening strategy is as described in bidding strategy below.

## Responses to Partner’s Opening Bid Strategy

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

## Example Input
### Partner's Opening Bid analysis
- Your partner is South, who has bid 1H. Your partner's hand is likely to have 12-18 HCP and at least 5 hearts. Your partner's hand is likely to be unbalanced (5-3-3-2 or 5-4-2-2).
### Your hand analisis
- You have 8 HCP. 4 Spades, 3 Hearts, 2 Diamonds, and 4 Clubs. 

## Example Output
Analisis:
Your partner is South, who has bid 1H.
Your partner has betwen 12-18 HCP. You have 8 HCP. So you have a total of 20-26 HCP.
Your partner has at least 5 hearts. You have 3 hearts. So you have a total of 8 hearts.
Based on analisis of your partners opening and your hand analisis you should bid 2 Hearts.

Partner's Opening Bid analysis: {partners_opening_bid_analysis}
Your hand analisis: {your_hand_analysis}
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
# 5) EXAMPLE USAGE
########################################

def get_response_analisis(
    partners_opening_bid_analysis: str,
    your_hand_analysis: str,
) -> str:
    """
    Returns the response analisis for the given partners opening bid analisis and your hand analisis.
    Args:
        partner_opening_bid_analysis (str): The analisis of the partner's opening bid.
        your_hand_analysis (str): The analisis of your hand.
    Returns:
        str: The response analisis.
    """

    # Prepare input data for the agent's prompt
    prompt_input = {
        "partners_opening_bid_analysis": partners_opening_bid_analysis,  # Corrected key
        "your_hand_analysis": your_hand_analysis,
    }

    # Debug: Log the prompt input
    print("DEBUG: Prompt input:", prompt_input)

    response = llm.invoke(
        response_bidding_prompt.format(
            partners_opening_bid_analysis=prompt_input["partners_opening_bid_analysis"],
            your_hand_analysis=prompt_input["your_hand_analysis"]
            )
        )
    # Debug: Log the response
    print("DEBUG: Response:", response)

    return response.content 

# Example: BIDDING PHASE
if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    analisis = get_response_analisis(
        partners_opening_bid_analysis="Your partner is South, who has bid 1S. Your partner's hand is likely to have 12-18 HCP and at least 5 hearts. Your partner's hand is likely to be unbalanced (5-3-3-2 or 5-4-2-2).",
        your_hand_analysis="You have 8 HCP. 4 Spades, 3 Hearts, 2 Diamonds, and 4 Clubs.",  
    )
    print("Response bid analisis:", analisis)
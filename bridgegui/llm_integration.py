import json
import logging

from openai import OpenAI
from bridgegui.bridge_broker_agent import get_bridge_advice

class LLMIntegration:

    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def get_allowed_bidding(self, allowed_bidding):
        prompt = self._get_allowed_bidding_prompt(allowed_bidding)
        response = self.client.chat.completions.create(model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ],temperature=0)
        return response.choices[0].message.content
    
    def _get_allowed_bidding_prompt(self, allowed_bidding):
        template = '''Convert Allowed Biddings to string format.
        
        Example 1 starts here:
            Allowed Biddings: [type:pass,bid: level: 5,strain:diamonds,type:bid,bid:level: 5,strain:hearts]
            Your answer: pass, 5 diamonds, 5 hearts
        Example 1 ends here

        Allowed Biddings: {allowed_bidding}
        
        '''
        return template.format(allowed_bidding=json.dumps(allowed_bidding, indent=4))


    def get_card_play_suggestion(self, play_from, position, own_hand, partners_hand, trick, allowed_cards, contract, contractors, bids_history, tricks_history, model="gpt-4-turbo"):
        prompt = self._get_card_play_suggestion_prompt(play_from, position, own_hand, partners_hand, trick, allowed_cards, contract, contractors, bids_history, tricks_history)
        response = self.client.chat.completions.create(model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],temperature=0)
        return response.choices[0].message.content
    
    def _get_card_play_suggestion_prompt(self, play_from, position, own_hand, partners_hand, trick, allowed_cards, contract, contractors, bids_history, tricks_history):
        template = '''You are an expert Bridge player. Your position is {position}.

Your task:
1. Read the **hand** you hold, the **partner’s hand** (if known), and the **cards played so far**.
2. From the **allowed cards**, choose the single best card to play according to standard Bridge card-play principles (following suit, analyzing the contract, the bidding, and trick context).
3. Present your reasoning in a structured format and conclude with your final card choice.

---

### **Instructions for Card-Play Logic**

1. **Always follow suit** if you can (unless you have no cards in that suit).  
2. Consider:
   - The **contract** and who declared it.
   - The **bidding** history (which may hint at distribution and strength).
   - The **tricks played so far** and what they reveal about opponents’ and partner’s holdings.
   - Whether you hold or suspect certain **key cards** (e.g., trumps, honors).
   - Potential **strategies** like saving higher cards for later, giving partner a ruff, or forcing declarer to use trump.

---

### **Your Response Format**

**Step 1:** 
- **Identify** the best card to play based on:
  - The current **trick** (which suit is led, and which cards have been played in this trick).
  - The **contract** (trump suit, declarer side).
  - The **bidding** (your and opponents’ strength/distribution indications).
  - The **tricks played so far** (any inferences about what partner or opponents hold).

**Step 2:** 
- **Verify** that your chosen card is in the **allowed cards**. 
- If your chosen card is **not allowed** (e.g., you already played it or it doesn’t exist in your hand), revise your selection to a valid card.

**Step 3:** 
- **Conclusion:** State your final card choice and a concise rationale.

---

### **Example 1** (Demonstration)

- **Play card from:** Your hand (West)  
- **Your hand:** "jack of spades, queen of spades, 2 of diamonds, 9 of spades, king of hearts, 8 of diamonds, 10 of diamonds, 7 of diamonds, 10 of clubs, 4 of clubs, 5 of clubs, 10 of hearts, jack of hearts"  
- **Partner’s hand:** Unknown  
- **Trick:** "Trick 5: North → 2 of spades, East → 3 of spades, South → 4 of spades"  
- **Allowed cards:** "5 of spades, 6 of spades, 7 of spades, 8 of spades, 9 of spades, 10 of spades, jack of spades, queen of spades, king of spades, ace of spades, [etc.]"  
- **Contract:** 3 Spades (Declarer: South)  
- **Contractors:** North–South  
- **Bids history:** "North: 1S, East: pass, South: 2S, West: pass, North: 3S, East: pass, South: pass"  
- **Tricks history:** 
  - Trick 1: N=2♥, E=3♥, S=4♥, W=5♥  
  - Trick 2: N=2♣, E=3♣, S=4♣, W=5♣  
  - Trick 3: N=2♦, E=3♦, S=4♦, W=5♦  
  - Trick 4: N=2♠, E=3♠, S=4♠  

**Your card:**  
1. **Decide on the best card**  
   - You must follow suit (spades) because you still have spades.  
   - Playing a mid-range spade (e.g., 9♠) may preserve higher spades.  
2. **Verify if 9♠ is allowed**  
   - 9♠ appears in the allowed cards list.  
3. **Conclusion**  
   - The best card to play is the 9♠ to keep stronger spades for later.

---

## **Your Input**
- **Play card from:** {play_from}  
- **Your hand:** {own_hand}  
- **Partner’s hand:** {partners_hand}  
- **Trick:** {trick}  
- **Allowed cards:** {allowed_cards}  
- **Contract:** {contract}  
- **Contractors:** {contractors}  
- **Bids history:** {bids_history}  
- **Tricks history:** {tricks_history}

**Now, follow the 3-step response format to select and justify the best card from your allowed options.**
'''

        return template.format(position=position,
                               play_from=play_from,
                               own_hand=json.dumps(own_hand),
                               partners_hand=json.dumps(partners_hand),
                               trick=json.dumps(trick),
                               allowed_cards=json.dumps(allowed_cards, indent=4),
                               contract=json.dumps(contract),
                               contractors=json.dumps(contractors),
                               bids_history=json.dumps(bids_history),
                               tricks_history=json.dumps(tricks_history))
    
    def get_card_play_prompt(self, analysis, allowed_cards):
        logging.info(f"analysis: {analysis}")
        logging.info(f"allowed_cards: {allowed_cards}")
        # Convert allowed_cards to a properly formatted string
        allowed_cards_str = json.dumps(allowed_cards)
        prompt = self._get_card_play_prompt(analysis, allowed_cards_str)
        response = self.client.chat.completions.create(model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ],temperature=0)
        return response.choices[0].message.content
    
    def _get_card_play_prompt(self, analysis, allowed_cards):
        # Check what is the type of allowed_cards
        template = '''You are bridge player. Based on the following analysis, choose the best card to play. 
        Choose the best card to play from allowed cards based on the cards you have in hand, the cards your partner has, the cards played so far, the contract, the bidding and tricks played so far.
        Respond only with json object. The structure of the json object should be as follows:
        {{
            "rank": "rank",
            "suit": "suit"
        }}

        Example 1 starts here:
            Analysis: I would play the 9 of spades
            Allowed cards: "5 of spades, 6 of spades, 7 of spades, 8 of spades, 9 of spades, 10 of spades, jack of spades, queen of spades, king of spades, ace of spades, 2 of diamonds, 3 of diamonds, 4 of diamonds, 5 of diamonds, 6 of diamonds, 7 of diamonds, 8 of diamonds, 9 of diamonds, 10 of diamonds, jack of diamonds, queen of diamonds, king of diamonds, ace of diamonds, 2 of hearts, 3 of hearts, 4 of hearts, 5 of hearts, 6 of hearts, 7 of hearts, 8 of hearts, 9 of hearts, 10 of hearts, jack of hearts, queen of hearts, king of hearts, ace of hearts, 2 of clubs, 3 of clubs, 4 of clubs, 5 of clubs, 6 of clubs, 7 of clubs, 8 of clubs, 9 of clubs, 10 of clubs, jack of clubs, queen of clubs, king of clubs, ace of clubs"
            Card played: {{"rank": "9", "suit": "spades"}}
        Example 1 ends here

        Example 2 starts here:
            Analysis: I would play the 3 of diamonds
            Allowed cards: "5 of spades, 6 of spades, 7 of spades, 8 of spades, 9 of spades, 10 of spades, jack of spades, queen of spades, king of spades, ace of spades, 2 of diamonds, 3 of diamonds, 4 of diamonds, 5 of diamonds, 6 of diamonds, 7 of diamonds, 8 of diamonds, 9 of diamonds, 10 of diamonds, jack of diamonds, queen of diamonds, king of diamonds, ace of diamonds, 2 of hearts, 3 of hearts, 4 of hearts, 5 of hearts, 6 of hearts, 7 of hearts, 8 of hearts, 9 of hearts, 10 of hearts, jack of hearts, queen of hearts, king of hearts, ace of hearts, 2 of clubs, 3 of clubs, 4 of clubs, 5 of clubs, 6 of clubs, 7 of clubs, 8 of clubs, 9 of clubs, 10 of clubs, jack of clubs, queen of clubs, king of clubs, ace of clubs"
            Card played: {{"rank": "3", "suit": "diamonds"}}
        Example 2 ends here

        Analysis: {analysis}
        Allowed cards: {allowed_cards}
        Your card: '''

        return template.format(analysis=analysis,
                               allowed_cards=allowed_cards)



    def get_bid_suggestion(self, position, hand, allowed_bidding, bidding_so_far, model="gpt-4-turbo"):
        prompt = self._get_bid_suggestion_prompt(position, hand, allowed_bidding, bidding_so_far)
        response = self.client.chat.completions.create(model=model,
        messages=[
            {"role": "user", "content": prompt}
        ], temperature=0)
        return response.choices[0].message.content
    
    def get_bid_suggestion_v2(self, position, hand, allowed_bidding, bidding_so_far):
        response = get_bridge_advice(
            position=position,
            hand=hand,
            allowed_bidding=allowed_bidding,
            bidding_so_far=bidding_so_far
        )
        return response

    def _get_bid_suggestion_prompt(self, position, hand, allowed_bidding, bidding_so_far):
        template = '''You are an expert Bridge player. Your position is {position}.

Your task:
1. Read the **hand** you hold and the **bidding so far**.
2. From the **allowed biddings**, choose the single best bid according to the detailed bidding strategy below.
3. Present your reasoning in a structured format and conclude with your final bid.

---

### Bidding Strategy

**Major Suits:** Spades (S) and Hearts (H)  
**Minor Suits:** Diamonds (D) and Clubs (C)

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

---

## **4. Strict Bidding Hierarchy (With Index) and “Pass” Exception**

Use this table to compare *bids* numerically. **Pass** is *not* included here because **Pass** is *always allowed** in Bridge.
0) 1C (1) 1D (2) 1H (3) 1S (4) 1NT (5) 2C (6) 2D (7) 2H (8) 2S (9) 2NT (10) 3C (11) 3D (12) 3H (13) 3S (14) 3NT (15) 4C (16) 4D (17) 4H (18) 4S (19) 4NT (20) 5C (21) 5D (22) 5H (23) 5S (24) 5NT (25) 6C (26) 6D (27) 6H (28) 6S (29) 6NT (30) 7C (31) 7D (32) 7H (33) 7S (34) 7NT


#### **Final-Bid Adjustment Rule**  
1. Identify the **highest bid** so far and find its **index** in the table above.  
2. Determine your **chosen bid** (if not Pass) and find its **index**.  
3. Compare **index(chosen_bid)** vs. **index(highest_bid)**:
   - If **index(chosen_bid) ≤ index(highest_bid)**, you **cannot** place that bid. Instead, you must:
     - **Pass** (always legal), or
     - **Double** (if you think opponents’ contract will fail), or
     - **Bid** something **higher** in the index.  
   - If **index(chosen_bid) > index(highest_bid)**, you can proceed with that bid.

**Note:**  
- **Pass** has no index in the hierarchy because **it is always allowed**, even if the opponents have bid 7-level.  
- Similarly, **Double** is a special call not on the ladder. You can double if your opponents are declaring a contract that you think will go down.

---

## **Your Response Format**

1. **Step 1:** Analyze your hand (HCP, distribution, any special features).  
2. **Step 2:** Analyze the bidding so far (partner’s and opponents’ bids).  
3. **Step 3:** From the **allowed biddings**, select your ideal bid using the above strategy (ignoring the hierarchy for a moment).  
4. **Step 4:** **Apply the Bidding Hierarchy**:  
   - Find the highest bid’s index.  
   - If your chosen bid is **Pass**, you can always pass.  
   - Otherwise, find your chosen bid’s index and compare:  
     - If your index ≤ highest-bid index, you must not place that bid. Instead, pass, double, or choose a higher bid.  
5. **Step 5:** Present your final conclusion (the valid bid).

---

### **Example**  
- **Highest bid so far:** 7 Hearts → index = **32**  
- **Chosen bid:** Pass → **Pass is always legal**. No index check needed.

---

## **Your Input**
- **Hand:** {hand}  
- **Allowed Biddings:** {allowed_bidding}  
- **Bidding so far:** {bidding_so_far}

**Use the 5-step response format.** Remember in Step 4: “Pass” does **not** require an index check and is always allowed.

'''

        prompt = template.format(position=position,
                               hand=json.dumps(hand),
                               allowed_bidding=json.dumps(allowed_bidding, indent=4),
                               bidding_so_far=json.dumps(bidding_so_far))
        
        logging.info(f"_get_bid_suggestion_prompt: {prompt}")

        return prompt
    
    def get_bid_prompt(self, analysis, allowed_bidding, model="gpt-3.5-turbo"):
        # Convert allowed_bidding to a properly formatted string
        allowed_bidding_str = json.dumps(allowed_bidding, indent=4)
        prompt = self._get_bid_prompt(analysis, allowed_bidding_str)
        print(f"prompt: {prompt}")
        response = self.client.chat.completions.create(model=model,
        messages=[
            {"role": "user", "content": prompt}
        ], temperature=0
        )
        print(f"response: {response}")
        return response.choices[0].message.content
    
    def _get_bid_prompt(self, analysis, allowed_bidding):
        logging.debug(f"Allowed bidding structure: {allowed_bidding}")
        template = '''You are bridge player. Based on the following analysis, choose the best bidding. 
        Choose the best bidding from allowed bidding based on the cards you have in hand and the bidding so far.
        Pass if annalysis suggest bidding that is not allowed.
        Respond only with json object. The structure of the json object should be as follows:
        {{
            "type": "bid",
            "bid: {{
                "level": level,
                "strain": "strain"
                }}
        }}

        Example 1:
        Analysis: I would bid 1 spade
        Allowed biddings: "Allowed biddings: pass, 1 clubs, 1 diamonds, 1 hearts, 1 spades, 1 notrump, 2 clubs, 2 diamonds, 2 hearts, 2 spades, 2 notrump, 3 clubs, 3 diamonds, 3 hearts, 3 spades, 3 notrump, 4 clubs, 4 diamonds, 4 hearts, 4 spades, 4 notrump, 5 clubs, 5 diamonds, 5 hearts, 5 spades, 5 notrump, 6 clubs, 6 diamonds, 6 hearts, 6 spades, 6 notrump, 7 clubs, 7 diamonds, 7 hearts, 7 spades, 7 notrump"
        Your bid: {{"type": "bid", "bid": {{"level": 1, "strain": "spades"}}}}

        Example 2:
        Analysis: I would pass        
        Allowed biddings: "Allowed biddings: pass, 1 clubs, 1 diamonds, 1 hearts, 1 spades, 1 notrump, 2 clubs, 2 diamonds, 2 hearts, 2 spades, 2 notrump, 3 clubs, 3 diamonds, 3 hearts, 3 spades, 3 notrump, 4 clubs, 4 diamonds, 4 hearts, 4 spades, 4 notrump, 5 clubs, 5 diamonds, 5 hearts, 5 spades, 5 notrump, 6 clubs, 6 diamonds, 6 hearts, 6 spades, 6 notrump, 7 clubs, 7 diamonds, 7 hearts, 7 spades, 7 notrump"
        Your bid: {{"type": "pass"}}

        Example 3:
        Analysis: I would bid 1 spade
        Allowed biddings: "Allowed biddings: pass, 1 notrump, 2 clubs, 2 diamonds, 2 hearts, 2 spades, 2 notrump, 3 clubs, 3 diamonds, 3 hearts, 3 spades, 3 notrump, 4 clubs, 4 diamonds, 4 hearts, 4 spades, 4 notrump, 5 clubs, 5 diamonds, 5 hearts, 5 spades, 5 notrump, 6 clubs, 6 diamonds, 6 hearts, 6 spades, 6 notrump, 7 clubs, 7 diamonds, 7 hearts, 7 spades, 7 notrump"
        Your bid: {{"type": "pass"}}


        Analysis: {analysis}
        Allowed bidding: {allowed_bidding}
        Your bid: '''

        try:
            return template.format(
                analysis=analysis,
                allowed_bidding=json.dumps(allowed_bidding, indent=4)
            )
        except KeyError as e:
            logging.error(f"KeyError in allowed_bidding: {e}")
            raise
    
    
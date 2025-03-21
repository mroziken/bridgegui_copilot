import json
import logging

from openai import OpenAI

class LLMIntegration:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def get_card_play_suggestion(self, play_from, position, own_hand, partners_hand, trick, allowed_cards, contract, contractors, bids_history, tricks_history):
        prompt = self._get_card_play_suggestion_prompt(play_from, position, own_hand, partners_hand, trick, allowed_cards, contract, contractors, bids_history, tricks_history)
        response = self.client.chat.completions.create(model="gpt-4-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ])
        return response.choices[0].message.content
    
    def _get_card_play_suggestion_prompt(self, play_from, position, own_hand, partners_hand, trick, allowed_cards, contract, contractors, bids_history, tricks_history):
        template = '''You are bridge player. Your position is {position}. 
        Choose the best card to play only from allowed cards based on the cards you have in hand, the cards your partner has (if known), the cards played so far, the contract, the bidding and tricks played so far.

        Formulate final answer in the following steps:
        1. Decide on the best card to play based on the hand, trick, contract, bidding and tricks played so far
        2. Verify if the best card to play is in the allowed cards. If not, revise the card to play.
        3. Formulate conclusion

        Example 1 starts here
            Play card from: your hand
            Own hand: "jack of spades, queen of spades, 2 of diamonds, 9 of spades, king of hearts, 8 of diamonds, 10 of diamonds, 7 of diamonds, 10 of clubs, 4 of clubs, 5 of clubs, 10 of hearts, jack of hearts"
            Partner's hand: Nor known"
            Trick: "trick 5: north: 2 of spades, east: 3 of spades, south: 4 of spades"
            Allowed cards: "5 of spades, 6 of spades, 7 of spades, 8 of spades, 9 of spades, 10 of spades, jack of spades, queen of spades, king of spades, ace of spades, 2 of diamonds, 3 of diamonds, 4 of diamonds, 5 of diamonds, 6 of diamonds, 7 of diamonds, 8 of diamonds, 9 of diamonds, 10 of diamonds, jack of diamonds, queen of diamonds, king of diamonds, ace of diamonds, 2 of hearts, 3 of hearts, 4 of hearts, 5 of hearts, 6 of hearts, 7 of hearts, 8 of hearts, 9 of hearts, 10 of hearts, jack of hearts, queen of hearts, king of hearts, ace of hearts, 2 of clubs, 3 of clubs, 4 of clubs, 5 of clubs, 6 of clubs, 7 of clubs, 8 of clubs, 9 of clubs, 10 of clubs, jack of clubs, queen of clubs, king of clubs, ace of clubs"
            Contract: "3 spades, declarer: south"
            Contractors: "north, south"
            Bids history: "bids history: north: 1 spade, east: pass, south: 2 spades, west: pass, north: 3 spades, east: pass, south: pass"
            Tricks history: "trick1: north: 2 of hearts, east: 3 of hearts, south: 4 of hearts, west: 5 of hearts, trick2: north: 2 of clubs, east: 3 of clubs, south: 4 of clubs, west: 5 of clubs, trick3: north: 2 of diamonds, east: 3 of diamonds, south: 4 of diamonds, west: 5 of diamonds, trick4: north: 2 of spades, east: 3 of spades, south: 4 of spades"
            Your card: 
                Step 1: Decide on the best card to play
                    You are in the West position, and the contract is 3♠ by South. The current trick (trick 5) has started with North playing the 2♠, East playing the 3♠, and South playing the 4♠.Analysis:
                    You must follow suit because you still have spades.
                    Declarer (South) is playing spades—since they are the declarer and spades are trump, they likely have control.
                    Your partner (East) played the 3♠, a low card, which might suggest they don’t have a strong spade holding.
                    Your best play depends on strategy:
                    If you suspect declarer is finessing, play low (e.g., 9♠) to keep higher spades in your hand for later.
                    If you want to put pressure on declarer, play Q♠ or J♠ to force them to use a higher trump.
                    Best Play: Play the 9♠ to minimize risk and keep stronger cards for later.
                Step 2: Verify if the best card to play is in the allowed cards
                    9 of spades is in the allowed cards
                Step 3: Formulate conclusion
                    Play the 9♠
        Example 1 ends here

        Play card from: {play_from}
        Your hand: {own_hand}
        Partner's hand: {partners_hand}
        Trick: {trick}
        Allowed cards: {allowed_cards}
        Contract: {contract}
        Contractors: {contractors}
        Bids history: {bids_history}
        Tricks history: {tricks_history}
        Your card: '''

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
        ])
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



    def get_bid_suggestion(self, position, hand, allowed_bidding, bidding_so_far):
        prompt = self._get_bid_suggestion_prompt(position, hand, allowed_bidding, bidding_so_far)
        response = self.client.chat.completions.create(model="gpt-4-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ])
        return response.choices[0].message.content

    def _get_bid_suggestion_prompt(self, position, hand, allowed_bidding, bidding_so_far):
        template = '''You are bridge player. Your position is {position}. 
        Choose the best bidding only from allowed bidding based on the cards you have in hand and the bidding so far.

        Formulate final answer in the following steps:
        1. Analyze the hand
        2. Analyze the bidding so far
        3. Decide on the best bidding based on the hand and bidding so far
        4. Verify if the best bidding is in the allowed bidding. If not, revise the bidding.
        5. Formulate conclusion

        Example 1 starts here:
            Position: north
            Hand: "jack of spades, queen of spades, 2 of diamonds, 9 of spades, king of hearts, 8 of diamonds, 10 of diamonds, 7 of diamonds, 10 of clubs, 4 of clubs, 5 of clubs, 10 of hearts, jack of hearts"
            Allowed biddings:  pass, 1 clubs, 1 diamonds, 1 hearts, 1 spades, 1 notrump, 2 clubs, 2 diamonds, 2 hearts, 2 spades, 2 notrump, 3 clubs, 3 diamonds, 3 hearts, 3 spades, 3 notrump, 4 clubs, 4 diamonds, 4 hearts, 4 spades, 4 notrump, 5 clubs, 5 diamonds, 5 hearts, 5 spades, 5 notrump, 6 clubs, 6 diamonds, 6 hearts, 6 spades, 6 notrump, 7 clubs, 7 diamonds, 7 hearts, 7 spades, 7 notrump"
            Bidding so far: [south: 1S, west: pass]
            Your bid: To determine the best opening bid, let's evaluate the hand:

            Step 1: Hand Analysis:
            High Card Points (HCP):

            Spades: Q (2), J (1) → 3
            Hearts: K (3), J (1), 10 (0) → 4
            Diamonds: 10 (0), 8 (0), 7 (0), 2 (0) → 0
            Clubs: 10 (0), 5 (0), 4 (0) → 0
            Total HCP: 7
            Distribution:

            Spades: 3
            Hearts: 3
            Diamonds: 4
            Clubs: 3
            Balanced hand (4-3-3-3 or 4-4-3-2)? No.


            A minimum opening bid typically requires at least 12 HCP.
            This hand only has 7 HCP, which is too weak to open at the 1-level.
            With no particularly long suit and low strength, the best action is to pass.

            Step 2: Bidding So Far:
            South opened the bidding with 1S, indicating a 5-card spade suit and 12-19 HCP.
            West passed, suggesting a weak hand with fewer than 6 HCP.
            The bidding is at the 1-level, and the opponents have not bid yet.  The partnership has the opportunity to bid again.

            
            Step 3: Bidding Decision:
            Call: pass

            Step 4: Verify Allowed Bidding: 
            pass is allowed

            step 5: Conclusion: 
            Pass is the best bid for this hand.
        Example 1 ends here
        
        Your hand: {hand}
        Allowed biddings: {allowed_bidding}
        Bidding so far: {bidding_so_far}
        Your bid: '''

        return template.format(position=position,
                               hand=json.dumps(hand),
                               allowed_bidding=json.dumps(allowed_bidding, indent=4),
                               bidding_so_far=json.dumps(bidding_so_far))
    
    def get_bid_prompt(self, analysis, allowed_bidding):
        # Convert allowed_bidding to a properly formatted string
        allowed_bidding_str = json.dumps(allowed_bidding, indent=4)
        prompt = self._get_bid_prompt(analysis, allowed_bidding_str)
        print(f"prompt: {prompt}")
        response = self.client.chat.completions.create(model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
        )
        print(f"response: {response}")
        return response.choices[0].message.content
    
    def _get_bid_prompt(self, analysis, allowed_bidding):
        # Check what is the type of allowed_bidding
        template = '''You are bridge player. Based on the following analysis, choose the best bidding. 
        Choose the best bidding from allowed bidding based on the cards you have in hand and the bidding so far.
        Respond only with json object. The structure of the json object should be as follows:
        {{
            "type": "bid",
            "bid: {{
                "level": "level",
                "strain": "strain"
                }}
        }}

        Example 1:
        Analysis: I would bid 1 spade
        Allowed biddings: "Allowed biddings: pass, 1 clubs, 1 diamonds, 1 hearts, 1 spades, 1 notrump, 2 clubs, 2 diamonds, 2 hearts, 2 spades, 2 notrump, 3 clubs, 3 diamonds, 3 hearts, 3 spades, 3 notrump, 4 clubs, 4 diamonds, 4 hearts, 4 spades, 4 notrump, 5 clubs, 5 diamonds, 5 hearts, 5 spades, 5 notrump, 6 clubs, 6 diamonds, 6 hearts, 6 spades, 6 notrump, 7 clubs, 7 diamonds, 7 hearts, 7 spades, 7 notrump"
        Your bid: {{"type": "bid", "bid": {{"level": "1", "strain": "spades"}}}}

        Example 2:
        Analysis: I would pass        
        Allowed biddings: "Allowed biddings: pass, 1 clubs, 1 diamonds, 1 hearts, 1 spades, 1 notrump, 2 clubs, 2 diamonds, 2 hearts, 2 spades, 2 notrump, 3 clubs, 3 diamonds, 3 hearts, 3 spades, 3 notrump, 4 clubs, 4 diamonds, 4 hearts, 4 spades, 4 notrump, 5 clubs, 5 diamonds, 5 hearts, 5 spades, 5 notrump, 6 clubs, 6 diamonds, 6 hearts, 6 spades, 6 notrump, 7 clubs, 7 diamonds, 7 hearts, 7 spades, 7 notrump"
        Your bid: {{"type": "pass"}}


        Analysis: {analysis}
        Allowed bidding: {allowed_bidding}
        Your bid: '''

        return template.format(analysis=analysis,
                               allowed_bidding=json.dumps(allowed_bidding, indent=4))


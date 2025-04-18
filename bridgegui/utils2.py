"""
Utils for llm and agents
"""

import ast
import re
import json
from bridgegui.analyze_opening_llm import get_opening_analisis  
from bridgegui.response_bid_llm import get_response_analisis
import logging
from typing import List
from bridgegui.schemas import Card

def analyze_partner_opening_bid_function(input_data: str) -> str:
    """
    Analyzes the partner's opening bid and returns a recommendation.
    """
    try:
        # First, try to parse as JSON (in case it ever comes in valid JSON)
        input_dict = json.loads(input_data)
    except json.JSONDecodeError:
        # Fall back to our custom parser if JSON fails
        input_dict = parse_input_data(input_data)

    position = input_dict.get("position")
    bidding_history = input_dict.get("bidding_history")

    response = get_opening_analisis(
        position=position,
        bidding_history=bidding_history,
    )


    # Implement your logic here based on the extracted information
    # For now, just return a placeholder string
    return response

def suggest_response_bid_function(input_data: str) -> str:
    """
    Suggests a response bid based on analisis of the partner's opening bid and your hand analysis.
    Args:
        partners_opening_bid_analysis (str): The analisis of the partner's opening bid.
        your_hand_analysis (str): The analisis of your hand.
    Returns:
        str: The response analisis.
    """
    try:
        # First, try to parse as JSON (in case it ever comes in valid JSON)
        input_dict = json.loads(input_data)
    except json.JSONDecodeError:
        # Fall back to our custom parser if JSON fails
        input_dict = parse_input_data(input_data)

    partners_opening_bid_analysis = input_dict.get("partners_opening_bid_analysis")
    your_hand_analysis = input_dict.get("your_hand_analysis")

    response = get_response_analisis(
        partners_opening_bid_analysis = partners_opening_bid_analysis,
        your_hand_analysis = your_hand_analysis
    )
    # Debug: Log the response
    print("DEBUG: Response:", response)

    # Implement your logic here based on the extracted information
    # For now, just return a placeholder string
    return response

def parse_input_data(input_data: str) -> dict:
    """
    Parses a non-JSON formatted string into a dictionary.
    Expected format: "Key1: Value1, Key2: Value2, ..."
    """
    # Regex pattern to capture key-value pairs, where keys can contain spaces
    pattern = r"([\w\s]+): (.*?)(?=, [\w\s]+:|$)"
    matches = re.findall(pattern, input_data)
    logging.debug(f"Matches: {matches}")
    data = {}
    for key, value in matches:
        key_clean = key.strip().lower().replace(" ", "_")
        try:
            # Try to evaluate the value to convert lists or numbers
            parsed_value = ast.literal_eval(value)
        except Exception:
            parsed_value = value.strip()
        data[key_clean] = parsed_value
    logging.debug(f"Parsed data: {data}")
    return data

def count_hcp(hand: List[Card]) -> int:
    """
    Counts High Card Points (HCP) in the given hand.
    Args:
        hand (list): A list of Card objects representing the hand.
    Returns:
        int: The total HCP in the hand.
    """

    hcp_values = {
        "ace": 4,
        "king": 3,
        "queen": 2,
        "jack": 1
    }

    logging.debug("(count_hcp 1) Input data for bid opening agent: %s", hand)

    total_hcp = 0
    # Iterate through the hand and sum the HCP values
    for card in hand:
        rank = getattr(card, "rank", "").lower()  # Access the 'rank' attribute of the Card object
        if rank in hcp_values:
            total_hcp += hcp_values[rank]
    return total_hcp

def dominant_suit_function(hand: list[Card]) -> str:
    """
    Checks if the hand contains a dominant suit (5 or more cards).
    Args:
        hand (list): A list of dictionaries representing the hand, where each card is a dictionary with 'rank' and 'suit'.
    Returns:
       response (string): The dominant suit if found, otherwise "No dominant suit".
    """
    
    logging.debug("(dominant_suit 1) Input data for bid opening agent: %s", hand)

    suit_counts = {}
    for card in hand:
        suit = getattr(card, "suit", "").lower()
        if suit not in suit_counts:
            suit_counts[suit] = 0
        suit_counts[suit] += 1
    
    # Dominant suid is the suit with at least 5 card. 
    # If there are not 5 card suit then there is not dominant suit. 
    # If you have two dominant suit with same number of cards, prioritize the major suit over the minor suit. 
    # If both suits are major, choose the lower-ranked suit (Hearts over Spades). 
    # If both suits are minor, choose the higher-ranked suit (Diamonds over Clubs).
    # Return type should be string.
    # Check for dominant suits
    dominant_suits = [suit for suit, count in suit_counts.items() if count >= 5]
    if len(dominant_suits) == 0:
        return "No dominant suit"
    elif len(dominant_suits) == 1:
        return dominant_suits[0]
    else:
        # Prioritize major suits over minor suits
        major_suits = ["spades", "hearts"]
        minor_suits = ["diamonds", "clubs"]
        for suit in major_suits:
            if suit in dominant_suits:
                return suit
        for suit in minor_suits:
            if suit in dominant_suits:
                return suit
    return dominant_suits[0]  # Return the first dominant suit if no major/minor preference is found



def is_balanced_hand(clubs: int, diamonds: int, hearts: int, spades: int) -> bool:
    """
    Checks if the hand is balanced (no 5-card suit).
    Args:
        clubs (int): Number of clubs in the hand.
        diamonds (int): Number of diamonds in the hand.
        hearts (int): Number of hearts in the hand.
        spades (int): Number of spades in the hand.
    Returns:
        bool: True if the hand is balanced, False otherwise.
    """
    logging.debug("(is_balanced_hand 1) Input data for bid opening agent: %s", (clubs, diamonds, hearts, spades))


    # Calculate total cards and check for 5-card suits
    total_cards = clubs + diamonds + hearts + spades
    logging.debug("Total cards: %d", total_cards)

    # Check if any suit has 5 or more cards
    if clubs >= 5 or diamonds >= 5 or hearts >= 5 or spades >= 5:
        return False
    return True

def get_suit_distribution(hand: List[Card]) -> str:
    """
    Returns the distribution of suits in the hand.
    Args:
        hand (list): A list of dictionaries representing the hand, where each card is a dictionary with 'rank' and 'suit'.
    Returns:
        string representing suit distribution example: 5-3-3-2, 4-4-4-1, etc.
    """

    logging.debug("(get_suit_distribution 1) Input data for bid opening agent: %s", hand)


    suit_counts = {
        "clubs": 0,
        "diamonds": 0,
        "hearts": 0,
        "spades": 0
    }
    for card in hand:
        suit = getattr(card, "suit", "").lower()
        if suit not in suit_counts:
            suit_counts[suit] = 0
        suit_counts[suit] += 1
    # Create a string representation of the suit distribution
    distribution = f"{suit_counts['clubs']}-{suit_counts['diamonds']}-{suit_counts['hearts']}-{suit_counts['spades']}"
    return distribution

def is_allowed_bid_function(proposed_bid: str, allowed_bids: list, bidding_history: list) -> str:
    """
    Analyzes if the proposed bid is allowed based on the allowed bids and bidding history.
    Args:
        proposed_bid (str): The proposed bid.
        allowed_bids (list[ob]): A list of allowed bids.
        bidding_history (list[str]): A list of previous bids in the format "Player: Bid".
    Returns:
        str: A message indicating whether the proposed bid is allowed or not.
    """
    logging.debug("(is_allowed_bid_function 1) Input data for bid opening agent: %s", (proposed_bid, allowed_bids, bidding_history))

    # Validate input
    if not isinstance(proposed_bid, str):
        raise ValueError("Proposed bid must be a string.")
    
    if not isinstance(allowed_bids, list):
        raise ValueError("Allowed bids must be a list of strings.")
    # Check if allowed bids are strings
    if not all(isinstance(bid, str) for bid in allowed_bids):
        raise ValueError("Allowed bids must be a list of strings.")
    
    if not isinstance(bidding_history, list):
        raise ValueError("Bidding history must be a list of strings.")
    # Check if bidding history is a list of strings
    if not all(isinstance(bid, str) for bid in bidding_history):
        raise ValueError("Bidding history must be a list of strings.")

    

    if proposed_bid in allowed_bids:
        return f"The proposed bid '{proposed_bid}' is allowed."
    else:
        last_bid = None
        last_bid_element = bidding_history[-1] if bidding_history else None
        #Check if proposed bid is same as last bid of your opponent on your left hand side
        if last_bid_element:
            last_bid = last_bid_element.split(":")[-1].strip()
            if proposed_bid == last_bid:
                return f"The proposed bid '{proposed_bid}' is same as last bid of your opponent on your left hand side. You can bid contra (X) to opponents last bid. So your bid is: 'X'"
            else:
                #check if proposed bid was already used in the bidding history
                for bid in bidding_history:
                    if proposed_bid in bid:
                        return f"The proposed bid '{proposed_bid}' was already used in the bidding history. You can not use it again. Your bid is 'Pass'."
                # If the last bid is not found, return a message indicating the issue
                return f"The proposed bid '{proposed_bid}' is not allowed and the last bid of your opponent on your left hand side is not found in the bidding history. Please check the input data."

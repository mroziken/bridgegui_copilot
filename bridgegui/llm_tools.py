from langchain.agents import Tool
from langchain.tools import StructuredTool
from bridgegui.schemas import IsAllowedBidToolInput, AnalyzePartnerOpeningBidToolInput, SuggestResponseBidToolInput
from bridgegui.schemas import Hand, SuitDistribution
from bridgegui.utils2 import count_hcp, dominant_suit_function, is_balanced_hand, get_suit_distribution, is_allowed_bid_function
from bridgegui.utils2 import analyze_partner_opening_bid_function, suggest_response_bid_function

count_hcp_tool = StructuredTool.from_function(
    name="count_hcp_tool",
    func=count_hcp,
    description=(
        "Use this tool to count the High Card Points (HCP) in a hand. "
        "Input should be a list of dictionaries, where each dictionary represents a card with keys: 'rank' and 'suit'. "
        "The 'rank' can be 'ace', 'king', 'queen', 'jack', or a number (e.g., '10'). "
        "The 'suit' can be 'spades', 'hearts', 'diamonds', or 'clubs'. "
        "The function returns the total HCP in the hand."
    ),
    args_schema=Hand
)
dominant_suit_tool = StructuredTool.from_function(
    name="dominant_suit_tool",
    func=dominant_suit_function,
    description=(
        "Use this tool to find the dominant suit in a hand. "
        "Input should be a list of dictionaries, where each dictionary represents a card with keys: 'rank' and 'suit'. "
        "The 'rank' can be 'ace', 'king', 'queen', 'jack', or a number (e.g., '10'). "
        "The 'suit' can be 'spades', 'hearts', 'diamonds', or 'clubs'. "
        "The function returns the the list of suits with at least 5 cards. "
    ),
    args_schema=Hand
)

is_balanced_hand_tool = StructuredTool.from_function(
    name="is_balanced_hand_tool",
    func=is_balanced_hand,
    description=(
        "Use this tool to check if the hand is balanced (no 5-card suit). "
        "Input should be a dictionary with keys 'clubs', 'diamonds', 'hearts', and 'spades', "
        "Each dictionary in the list should represent a card with keys: 'rank' and 'suit'. "
        "The function returns True if the hand is balanced, otherwise False."
    ),
    args_schema=SuitDistribution
)
get_suit_distribution_tool = StructuredTool.from_function(
    name="get_suit_distribution_tool",
    func=get_suit_distribution,
    description=(
        "Use this tool to get the distribution of suits in the hand."
        "Input should be a dictionary with keys 'clubs', 'diamonds', 'hearts', and 'spades', "
        "Each dictionary in the list should represent a card with keys: 'rank' and 'suit'. "
        "The 'rank' can be 'ace', 'king', 'queen', 'jack', or a number (e.g., '10'). "
        "The 'suit' can be 'spades', 'hearts', 'diamonds', or 'clubs'. "
        "The function returns a dictionary with suit names as keys and their counts as values."
    ),
    args_schema=Hand
)

is_allowed_bid_tool = StructuredTool.from_function(
    name="is_allowed_bid_tool",
    func=is_allowed_bid_function,
    description=(
        "Use this tool to check if  proposed bid is allowed, given the: "
        "proposed_bid, allowed_bids, bidding_history "
        "Input should be a dictionary with keys 'proposed_bid', 'allowed_bids', and 'bidding_history'. "
        "The 'proposed_bid' is a string representing the bid to check. "
        "The 'allowed_bids' is a list of strings representing the allowed bids. "
        "The 'bidding_history' is a list of strings representing the history of bids. "
        "The function returns textual explanation of the result."
    ),
    args_schema=IsAllowedBidToolInput
)

analyze_partner_opening_bid_tool = StructuredTool.from_function(
    name="analyze_partner_opening_bid_tool",
    func=analyze_partner_opening_bid_function,
    description=(
        "Use this tool to analyze the partner's opening bid."
    ),
    args_schema=AnalyzePartnerOpeningBidToolInput
)

suggest_response_bid_tool = StructuredTool.from_function(
    name="suggest_response_bid_tool",
    func=suggest_response_bid_function,
    description=(
        "Use this tool to suggest a response bid based on:"
        "partners_opening_bid_analysis and your_hand_analysis"
    ),
    args_schema=SuggestResponseBidToolInput
)
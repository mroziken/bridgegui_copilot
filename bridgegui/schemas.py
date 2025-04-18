from pydantic import BaseModel
from typing import List

class RecognizeBiddingStageInput(BaseModel):
    position: str
    bidding_history: list[str]

class Card(BaseModel):
    rank: str
    suit: str

class OpeningBiddingToolInput(BaseModel):
    position: str
    hand: List[Card]
    bidding_history: List[str]
    allowed_bids: List[str]

class OpeningBiddingToolOutput(BaseModel):
    position: str
    hand: List[Card]
    bidding_history: List[str]
    allowed_bids: List[str]
    hcp: int
    distribution: str
    balanced_hand: bool
    dominant_suit: str
    your_team_analysis: str
    bid_suggestion: str

class OpeningBidToolInput(BaseModel):
    hcp: int
    distribution: str
    balanced_hand: bool
    dominant_suit: str

class OpeningBidToolOutput(BaseModel):
    hcp: int
    distribution: str
    balanced_hand: bool
    dominant_suit: str
    your_team_analysis: str
    bid_suggestion: str

class BiddingAnalysisToolInput(BaseModel):
    position: str
    hand: List[Card]
    bidding_history: List[str]
    allowed_bids: List[str]
    proposed_bid: str

class PlayAnalysisToolInput(BaseModel):
    position: str
    hand: List[Card]
    bidding_history: List[str]
    allowed_bids: List[str]
    proposed_bid: str
    play_history: List[str]

class Hand(BaseModel):
    hand: List[Card]

class HandDistribution(BaseModel):
    clubs: int
    diamonds: int
    hearts: int
    spades: int

class SuitDistribution(BaseModel):
    clubs: int
    diamonds: int
    hearts: int
    spades: int
    
class SuitDistributionInput(BaseModel):
    hand: List[Card]
    distribution: SuitDistribution


class IsAllowedBidToolInput(BaseModel):
    proposed_bid: str
    allowed_bids: List[str]
    bidding_history: List[str]

class AnalyzePartnerOpeningBidToolInput(BaseModel):
    position: str
    hand: List[Card]
    bidding_history: List[str]
    allowed_bids: List[str]
    proposed_bid: str

class SuggestResponseBidToolInput(BaseModel):
    position: str
    hand: List[Card]
    bidding_history: List[str]
    allowed_bids: List[str]
    proposed_bid: str
    partners_opening_bid_analysis: str
    your_hand_analysis: str

class OpeningBiddingToolReponse(BaseModel):
    your_team_analysis: str
    bid_suggestion: str


class getBrdidgeAdviceResponse(BaseModel):
    your_team_analysis: str
    opponent_analysis: str
    bid_suggestion: str
    play_suggestion: str
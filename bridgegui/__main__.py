"""Bridge frontend

This module contains the startpoint for the frontend which is part of the bridge
project. The usage is documented when the script is run with the -h argument.
"""

import argparse
import json
import logging
import re
import sys
import uuid

from PyQt5.QtCore import QSocketNotifier, QTimer, QObject, QCoreApplication
from PyQt5.QtWidgets import (
    QApplication, QHBoxLayout, QMainWindow, QMessageBox, QVBoxLayout, QWidget)
import zmq

import bridgegui.bidding as bidding
import bridgegui.cards as cards
import bridgegui.messaging as messaging
from bridgegui.messaging import sendCommand
import bridgegui.positions as positions
from bridgegui.positions import POSITION_TAGS
import bridgegui.score as score
import bridgegui.tricks as tricks

import os
from dotenv import load_dotenv
from bridgegui.llm_integration import LLMIntegration
from collections import namedtuple
from bridgegui.copilot_widget import Copilot  # Import the Copilot widget
from bridgegui.bridge_broker_agent import get_bridge_advice
from bridgegui.game_label_widget import GameLabel  # Import GameLabel from the appropriate module


HELLO_COMMAND = b'bridgehlo'
GAME_COMMAND = b'game'
JOIN_COMMAND = b'join'
INITGET_COMMAND = b'initget'
GET_COMMAND = b'get'
DEAL_COMMAND = b'deal'
CALL_COMMAND = b'call'
BIDDING_COMMAND = b'bidding'
PLAY_COMMAND = b'play'
TURN_COMMAND = b'turn'
DUMMY_COMMAND = b'dummy'
TRICK_COMMAND = b'trick'
DEALEND_COMMAND = b'dealend'
PLAYER_COMMAND = b'player'

CLIENT_TAG = "client"
POSITION_TAG = "position"
GAME_TAG = "game"
PUBSTATE_TAG = "pubstate"
PRIVSTATE_TAG = "privstate"
SELF_TAG = "self"
POSITION_IN_TURN_TAG = "positionInTurn"
ALLOWED_CALLS_TAG = "allowedCalls"
CALLS_TAG = "calls"
DECLARER_TAG = "declarer"
CONTRACT_TAG = "contract"
ALLOWED_CARDS_TAG = "allowedCards"
CARDS_TAG = "cards"
TRICKS_TAG = "tricks"
VULNERABILITY_TAG = "vulnerability"

class BridgeAutopilot(QObject):
    """Handles the autopilot mode without GUI."""

    def __init__(self, control_socket, event_socket, position, game_uuid,
                 create_game, player_uuid, autopilot, model):
        super().__init__()  # Initialize QObject
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self._control_socket = control_socket
        self._event_socket = event_socket
        self._preferred_position = position
        self._position = position
        self._game_uuid = game_uuid
        self._create_game = create_game
        self._player_uuid = player_uuid if player_uuid else str(uuid.uuid4())
        self._autopilot = True if autopilot else False
        self._model = model
        self._running = True

        # Initialize the timer
        self._timer = QTimer(self)
        self._timer.setInterval(1000)  # Set the interval to 1 second

        self._init_sockets(control_socket, event_socket)

        self._llm_integration_instance = LLMIntegration(self.api_key)
        self._cards = {}
        self._declarer = None
        self._contract = None
        self._contractors = None
        self._bids_history = []
        self._tricks_history = []
        self._current_trick = []


    def _init_sockets(self, control_socket, event_socket):
        logging.info("Initializing message handlers")
        zmqctx = zmq.Context.instance()
        self._socket_notifiers = []
        self._control_socket = control_socket
        self._control_socket_queue = messaging.MessageQueue(
            control_socket, "control socket queue",
            messaging.validateControlReply,
            {
                HELLO_COMMAND: self._handle_hello_reply,
                GAME_COMMAND: self._handle_game_reply,
                JOIN_COMMAND: self._handle_join_reply,
                INITGET_COMMAND: self._handle_init_get_reply,
                GET_COMMAND: self._handle_get_reply,
                CALL_COMMAND: self._handle_call_reply,
                PLAY_COMMAND: self._handle_play_reply,
            })
        self._connect_socket_to_notifier(
            control_socket, self._control_socket_queue)
        self._event_socket = event_socket
        sendCommand(control_socket, HELLO_COMMAND, version="0.1", role=CLIENT_TAG)

    def _is_stale_event(self, counter):
        logging.debug("Checking for stale event. Counter: %r", counter)
        if not counter:
            return False
        elif self._counter and self._counter > counter:
            logging.debug(
                "Stale event, counter: %r, self._counter %r",
                counter, self._counter)
            return True
        else:
            return False

    def _get_event_type(self, name):
        logging.debug("Getting event type for %r", name)
        return self._game_uuid.encode() + b':' + name

    def _init_game(self, game_uuid):
        logging.info("Initializing game %r", game_uuid)
        self._game_uuid = game_uuid
        self._event_socket.setsockopt(zmq.SUBSCRIBE, game_uuid.encode())
        self._event_socket_queue = messaging.MessageQueue(
            self._event_socket, "event socket queue", messaging.validateEventMessage,
            {
                self._get_event_type(DEAL_COMMAND): self._handle_deal_event,
                self._get_event_type(TURN_COMMAND): self._handle_turn_event,
                self._get_event_type(CALL_COMMAND): self._handle_call_event,
                self._get_event_type(BIDDING_COMMAND): self._handle_bidding_event,
                self._get_event_type(PLAY_COMMAND): self._handle_play_event,
                self._get_event_type(DUMMY_COMMAND): self._handle_dummy_event,
                self._get_event_type(TRICK_COMMAND): self._handle_trick_event,
                self._get_event_type(DEALEND_COMMAND): self._handle_dealend_event,
                self._get_event_type(PLAYER_COMMAND): self._handle_player_event,
            })

    def _start_handling_events(self):
        logging.info("Starting event handling")
        self._connect_socket_to_notifier(
            self._event_socket, self._event_socket_queue)

    def _connect_socket_to_notifier(self, socket, message_queue):
        def _handle_message_to_queue():
            if not message_queue.handleMessages():
                logging.error(
                    "Error while receiving message from server. Please see logs."
                )
                self._timer.timeout.disconnect(_handle_message_to_queue)

        socket_notifier = QSocketNotifier(socket.fd, QSocketNotifier.Read, self)
        socket_notifier.activated.connect(_handle_message_to_queue)
        self._timer.timeout.connect(_handle_message_to_queue)
        self._socket_notifiers.append(socket_notifier)

    def _request(self, *args):
        logging.debug("Requesting %r", args)
        sendCommand(
            self._control_socket, GET_COMMAND, game=self._game_uuid,
            player=self._player_uuid, get=args)

    def _send_join_command(self):
        logging.info("Joining game")
        kwargs = {}
        if self._preferred_position:
            kwargs[POSITION_TAG] = self._preferred_position
        if self._game_uuid:
            kwargs[GAME_TAG] = self._game_uuid
        logging.info("Joining game %r", self._game_uuid)
        logging.info("Player %r", self._player_uuid)
        logging.info("Position %r", self._preferred_position)
        sendCommand(
            self._control_socket, JOIN_COMMAND,
            player=self._player_uuid, **kwargs)

    def _send_call_command(self, call):
        logging.info("Making call %r", call)
        sendCommand(
            self._control_socket, CALL_COMMAND, game=self._game_uuid,
            player=self._player_uuid, call=call)

    def _send_play_command(self, card):
        logging.info("Playing card %r", card)
        sendCommand(
            self._control_socket, PLAY_COMMAND, game=self._game_uuid,
            player=self._player_uuid, card=card._asdict())

    def _handle_hello_reply(self, **kwargs):
        logging.info("Handshake successful")
        if self._create_game:
            kwargs = { 'game': self._game_uuid } if self._game_uuid else {}
            sendCommand(self._control_socket, GAME_COMMAND, **kwargs)
        else:
            self._send_join_command()

    def _handle_game_reply(self, game=None, **kwargs):
        logging.info("Created game %r", game)
        self._game_uuid = game
        self._send_join_command()

    def _handle_join_reply(self, game=None, **kwargs):
        logging.info("Joined game %r", game)
        if game:
            self._init_game(game)
            sendCommand(
                self._control_socket, GET_COMMAND, INITGET_COMMAND,
                game=game, player=self._player_uuid)
        else:
            logging.error("Unable to join game")

    def _handle_init_get_reply(self, get=None, counter=None, **kwargs):
        logging.debug("Handling initget reply")
        self._handle_get_reply(get, counter, **kwargs)
        self._start_handling_events()

    def _handle_get_reply(self, get=None, counter=None, **kwargs):
        logging.debug("Handling get reply")
        if counter is not None:
            self._counter = counter
        else:
            logging.warning("No counter included in get reply")
        missing = object()
        pubstate = get.get(PUBSTATE_TAG) or {}
        privstate = get.get(PRIVSTATE_TAG) or {}
        _self = get.get(SELF_TAG) or {}
        position = _self.get(POSITION_TAG, missing)
        if position is not missing and position != self._position:
            self._position = position
            logging.info("Position assigned: %r", position)
        position_in_turn = _self.get(POSITION_IN_TURN_TAG, missing)
        if position_in_turn is not missing:
            logging.info("Position in turn: %r", position_in_turn)
        allowed_calls = _self.get(ALLOWED_CALLS_TAG, missing)
        if allowed_calls is not missing:
            logging.info("Allowed calls: %r", allowed_calls)
        calls = pubstate.get(CALLS_TAG, missing)
        if calls is not missing:
            logging.info("Calls: %r", calls)
        declarer = pubstate.get(DECLARER_TAG, missing)
        contract = pubstate.get(CONTRACT_TAG, missing)
        if declarer is not missing and contract is not missing:
            logging.info("Bidding result: %r, %r", declarer, contract)
        cards = pubstate.get(CARDS_TAG, {})
        cards.update(privstate.get(CARDS_TAG, {}))
        if cards:
            self._cards.update(cards)
            logging.info("Cards: %r", cards)
        # make call to get_bid_suggestion from llm_integration
        logging.info(f"autopilot: {self._autopilot}")
        if allowed_calls is not missing:
            logging.info(f"allowed_calls: {allowed_calls}")
            if allowed_calls:
                logging.info(f"len(allowed_calls): {len(allowed_calls)}")
                if len(allowed_calls) > 1: 
                    logging.info(f"position: {position}")
                    hand = self._cards.get(position, [])
                    logging.info(f"hand: {hand}")
                    logging.info(f"allowed_calls: {allowed_calls}")
                    bids_history = self._bids_history
                    logging.info(f"bids_history: {bids_history}")
                    allowed_biddings = self._llm_integration_instance.get_allowed_bidding(allowed_calls)
                    
                    get_bid_suggestion = get_bridge_advice(
                        position = position, 
                        phase = self._phase, 
                        hand = hand,
                        allowed_bids = allowed_biddings, 
                        bidding_history = bids_history
                        )
                    logging.info(f"get_bid_suggestion: {get_bid_suggestion}")

                    # Directly access the 'output' dictionary
                    output_json = get_bid_suggestion['output']  # No need for json.loads
                    your_team_analysis = output_json.get('your_team_analysis', '')
                    bid_suggestion = output_json.get('bid_suggestion', 'pass')

                    logging.info(f"your_team_analysis: {your_team_analysis}")
                    logging.info(f"bid_suggestion: {bid_suggestion}")
                    if self._autopilot:
                        self._copilot_widget.append_message(f"Analysis: {your_team_analysis}")
                    try:
                        # Remove backticks and extra formatting
                        cleaned_response = get_bid.strip("```json").strip("```").strip()
                        get_bid = json.loads(cleaned_response)
                        logging.info(f"after cleaning get_bid: {get_bid}")
                        # Call _send_call_command to send the bid to the server
                        self._send_call_command(get_bid)
                    except json.JSONDecodeError as e:
                        logging.error(f"Failed to parse JSON from get_bid: {e}")
                    except Exception as e:
                        logging.error(f"Unexpected error while handling get_bid: {e}")
                else:
                    get_bid = allowed_calls[0]
                    logging.info(f"only allowed bid: {get_bid}")
                    self._send_call_command(get_bid)
            else:
                logging.error("Allowed calls list empty ")
        else:
            logging.error("Allowed calls list missing")
        allowed_cards = _self.get(ALLOWED_CARDS_TAG, missing)
        if allowed_cards is not missing:
            logging.info("Allowed cards: %r", allowed_cards)
            if allowed_cards:
                play_from = "Own hand"
                own_hand = self._cards.get(position, [])
                declarer = self._declarer
                contract = self._contract
                contractors = self._contractors
                bids_history = self._bids_history
                tricks_history = self._tricks_history
                if position_in_turn == self._position and declarer == self._position:
                    first_card_from_allowed_cards = allowed_cards[0]
                    if not any(json.dumps(first_card_from_allowed_cards, sort_keys=True) == json.dumps(obj, sort_keys=True) for obj in own_hand):
                        play_from = "Partners hand"
                partners_hand = pubstate.get(CARDS_TAG, {})
                trick= self._current_trick
                logging.info(f"play_from: {play_from}")
                logging.info(f"position: {position}")
                logging.info(f"own_hand: {own_hand}")
                logging.info(f"partners_hand: {partners_hand}")
                logging.info(f"trick: {trick}")
                logging.info(f"allowed_cards: {allowed_cards}")
                logging.info(f"contract: {contract}")
                logging.info(f"contractors: {contractors}")
                logging.info(f"bids_history: {bids_history}")
                logging.info(f"tricks_history: {tricks_history}")
                get_card_play_suggestion = self._llm_integration_instance.get_card_play_suggestion(play_from, position, own_hand, partners_hand, trick, allowed_cards, contract, contractors, bids_history, tricks_history)
                logging.info(f"get_card_play_suggestion: {get_card_play_suggestion}")
                try:
                    if not get_card_play_suggestion:
                        raise ValueError("get_card_play_suggestion is empty or invalid.")
                    
                    get_card_play_prompt = self._llm_integration_instance.get_card_play_prompt(
                        get_card_play_suggestion, allowed_cards
                    )
                    logging.info(f"get_card_play_prompt: {get_card_play_prompt}")

                    # Validate the prompt before parsing
                    if not get_card_play_prompt or not isinstance(get_card_play_prompt, str):
                        raise ValueError("Invalid prompt received from get_card_play_prompt.")

                    # Clean up the response and parse JSON
                    cleaned_response = get_card_play_prompt.strip("```json").strip("```").strip()
                    get_card_play_prompt = json.loads(cleaned_response)
                    logging.info(f"after cleaning get_card_play_prompt: {get_card_play_prompt}")

                    # Call _send_play_command to send the play to the server
                    Card = namedtuple("Card", ["rank", "suit"])
                    card = Card(**get_card_play_prompt)

                    # Convert the Card object to a dictionary for comparison
                    card_dict = card._asdict()

                    if card_dict not in allowed_cards:
                        logging.error(f"Card {card_dict} is not in allowed cards: {allowed_cards}")
                        return
                    self._send_play_command(card)
                except ValueError as e:
                    logging.error(f"Validation error: {e}")
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to parse JSON from get_card_play_prompt: {e}")
                except Exception as e:
                    logging.error(f"Unexpected error while handling get_card_play_prompt: {e}")
        tricks = pubstate.get(TRICKS_TAG, missing)
        if tricks is not missing:
            if tricks:
                logging.info("Tricks: %r", tricks)
                self._tricks_history.append(tricks)
                trick = tricks[-1].get("cards")
            tricks_won = {
                partnership: 0 for partnership in positions.Partnership
            }
            for trick in tricks:
                winner = trick.get("winner")
                if winner:
                    self._current_trick = []
                    tricks_won[positions.partnershipFor(winner)] += 1
        vulnerability = pubstate.get(VULNERABILITY_TAG, missing)

    def _handle_call_reply(self, **kwargs):
        logging.debug("Call successful")

    def _handle_play_reply(self, **kwargs):
        if kwargs.get("status") == "ERR:RV":
            logging.error("Rule violation: Invalid card play")
        else:
            logging.debug("Play successful")

    def _handle_deal_event(self, opener=None, vulnerability=None, counter=None, **kwargs):
        logging.debug("Dealing cards")
        if self._is_stale_event(counter):
            return
        logging.debug("Cards dealt")
        self._request(PUBSTATE_TAG, PRIVSTATE_TAG)

    def _handle_turn_event(self, position=None, counter=None, **kwargs):
        logging.debug("Turn event")
        if self._is_stale_event(counter):
            return
        logging.debug("Position in turn: %r", position)
        if position == self._position:
            logging.debug("Requesting self")
            self._request(SELF_TAG)

    def _handle_call_event(
            self, position=None, call=None, counter=None, **kwargs):
        logging.debug("Call event")
        if self._is_stale_event(counter):
            return
        logging.debug("Call made. Position: %r, Call: %r", position, call)
        self._bids_history.append({position: call})

    def _handle_bidding_event(
            self, declarer=None, contract=None, counter=None, **kwargs):
        logging.debug("Bidding event")
        if self._is_stale_event(counter):
            return
        logging.debug(
            "Bidding completed. Declarer: %r, Contract: %r", declarer, contract)
        self._declarer = declarer
        self._contract = contract
        self._contractors = 'north, south' if declarer == 'north' or declarer == 'south' else 'east, west'

    def _handle_play_event(
            self, position=None, card=None, counter=None, **kwargs):
        logging.debug("Play event") 
        if self._is_stale_event(counter):
            return
        logging.debug("Card played. Position: %r, Card: %r", position, card)
        self._current_trick.append({"position": position, "card": card})

    def _handle_dummy_event(
            self, counter=None, position=None, cards=None, **kwargs):
        logging.debug("Dummy event")
        if self._is_stale_event(counter):
            return
        logging.debug("Dummy hand revealed")

    def _handle_trick_event(self, winner, counter=None, **kwargs):
        logging.debug("Trick event")
        if self._is_stale_event(counter):
            return
        logging.debug("Trick completed. Winner: %r", winner)

    def _handle_dealend_event(self, result, counter=None, **kwargs):
        logging.debug("Deal end event")
        if self._is_stale_event(counter):
            return
        logging.debug("Deal ended. Result: %r", result)

    def _handle_player_event(self, player, position, **kwargs):
        logging.debug("Player joined. Player: %r. Position: %r", player, position)

    def start(self):
        logging.info("Starting autopilot event handling")
        app = QCoreApplication([])  # Use QCoreApplication for the event loop
        self._timer.start()  # Start the timer
        app.exec_()  # Start the event loop

class BridgeWindow(QMainWindow):
    """The main window of the birdge frontend"""

    def __init__(
            self, control_socket, event_socket, position, game_uuid,
            create_game, player_uuid, copilot, model):
        """Initialize BridgeWindow

        Keyword Arguments:
        control_socket -- the control socket used to send commands
        event_socket   -- the event socket used to subscribe events
        position       -- the preferred position
        game_uuid      -- the UUID of the game to be joined (optional)
        create_game    -- flag indicating whether the client should create a new game
        player_uuid    -- the UUID of the player (optional)
        copilot        -- flag indicating whether the client should start in copilot mode
        model          -- the model to be used for copilot mode
        """
        super().__init__()
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self._position = None
        self._preferred_position = position
        self._game_uuid = game_uuid
        self._player_uuid = player_uuid if player_uuid else str(uuid.uuid4())
        self._copilot = True if copilot else False
        self._model = model
        self._create_game = create_game
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._init_sockets(control_socket, event_socket)
        self._init_widgets()
        self.setWindowTitle("Bridge") # TODO: Localization
        self.show()
        self._timer.start()
        self._llm_integration_instance = LLMIntegration(self.api_key)
        self._cards = {}
        self._declarer = None
        self._contract = None
        self._contractors = None
        self._bids_history = []
        self._tricks_history = []
        self._current_trick = []
        self._phase = "bidding"
        

    def _init_sockets(self, control_socket, event_socket):
        logging.info("Initializing message handlers")
        zmqctx = zmq.Context.instance()
        self._socket_notifiers = []
        self._control_socket = control_socket
        self._control_socket_queue = messaging.MessageQueue(
            control_socket, "control socket queue",
            messaging.validateControlReply,
            {
                HELLO_COMMAND: self._handle_hello_reply,
                GAME_COMMAND: self._handle_game_reply,
                JOIN_COMMAND: self._handle_join_reply,
                INITGET_COMMAND: self._handle_init_get_reply,
                GET_COMMAND: self._handle_get_reply,
                CALL_COMMAND: self._handle_call_reply,
                PLAY_COMMAND: self._handle_play_reply,
            })
        self._connect_socket_to_notifier(
            control_socket, self._control_socket_queue)
        self._event_socket = event_socket
        sendCommand(control_socket, HELLO_COMMAND, version="0.1", role=CLIENT_TAG)

    def _init_widgets(self):
        logging.info("Initializing widgets")
        self._central_widget = QWidget(self)
        self._layout = QHBoxLayout(self._central_widget)

        # Bidding layout
        self._bidding_layout = QVBoxLayout()
        self._call_panel = bidding.CallPanel(self._central_widget)
        self._call_panel.callMade.connect(self._send_call_command)
        self._bidding_layout.addWidget(self._call_panel)
        self._call_table = bidding.CallTable(self._central_widget)
        self._bidding_layout.addWidget(self._call_table)
        self._bidding_result_label = bidding.ResultLabel(self._central_widget)
        self._bidding_layout.addWidget(self._bidding_result_label)
        self._tricks_won_label = tricks.TricksWonLabel(self._central_widget)
        self._bidding_layout.addWidget(self._tricks_won_label)
        self._layout.addLayout(self._bidding_layout)

        # Cards area layout
        self._cards_layout = QVBoxLayout()
        self._card_area = cards.CardArea(self._central_widget)
        for hand in self._card_area.hands():
            hand.cardPlayed.connect(self._send_play_command)
        self._cards_layout.addWidget(self._card_area)

        # Add Copilot text box below the cards area
        self._copilot_widget = Copilot(self._central_widget)
        self._cards_layout.addWidget(self._copilot_widget)

        # Add the GameLabel widget
        self._game_label = GameLabel(self._central_widget)
        self._game_label.set_text(f"Game ID: {self._game_uuid}")

        self._layout.addLayout(self._cards_layout)

        # Score table
        self._score_table = score.ScoreTable(self._central_widget)
        self._layout.addWidget(self._score_table)

        self.setCentralWidget(self._central_widget)
        self._counter = None

    def _is_stale_event(self, counter):
        logging.debug("Checking for stale event. Counter: %r", counter)
        if not counter:
            return False
        elif self._counter and self._counter > counter:
            logging.debug(
                "Stale event, counter: %r, self._counter %r",
                counter, self._counter)
            return True
        else:
            return False

    def _get_event_type(self, name):
        logging.debug("Getting event type for %r", name)
        return self._game_uuid.encode() + b':' + name

    def _init_game(self, game_uuid):
        logging.info("Initializing game %r", game_uuid)
        self._game_uuid = game_uuid
        self._game_label.set_text(f"Game ID: {self._game_uuid}")
        self._event_socket.setsockopt(zmq.SUBSCRIBE, game_uuid.encode())
        self._event_socket_queue = messaging.MessageQueue(
            self._event_socket, "event socket queue", messaging.validateEventMessage,
            {
                self._get_event_type(DEAL_COMMAND): self._handle_deal_event,
                self._get_event_type(TURN_COMMAND): self._handle_turn_event,
                self._get_event_type(CALL_COMMAND): self._handle_call_event,
                self._get_event_type(BIDDING_COMMAND): self._handle_bidding_event,
                self._get_event_type(PLAY_COMMAND): self._handle_play_event,
                self._get_event_type(DUMMY_COMMAND): self._handle_dummy_event,
                self._get_event_type(TRICK_COMMAND): self._handle_trick_event,
                self._get_event_type(DEALEND_COMMAND): self._handle_dealend_event,
                self._get_event_type(PLAYER_COMMAND): self._handle_player_event,
            })

    def _start_handling_events(self):
        logging.info("Starting event handling")
        self._connect_socket_to_notifier(
            self._event_socket, self._event_socket_queue)

    def _connect_socket_to_notifier(self, socket, message_queue):
        logging
        def _handle_message_to_queue():
            if not message_queue.handleMessages():
                # TODO: Localization
                QMessageBox.warning(
                    self, "Server error",
                    "Error while receiving message from server. Please see logs.")
                self._timer.timeout.disconnect(_handle_message_to_queue)
        socket_notifier = QSocketNotifier(socket.fd, QSocketNotifier.Read, self)
        socket_notifier.activated.connect(_handle_message_to_queue)
        self._timer.timeout.connect(_handle_message_to_queue)
        self._socket_notifiers.append(socket_notifier)

    def _request(self, *args):
        logging.debug("Requesting %r", args)
        sendCommand(
            self._control_socket, GET_COMMAND, game=self._game_uuid,
            player=self._player_uuid, get=args)

    def _send_join_command(self):
        logging.info("Joining game")
        kwargs = {}
        if self._preferred_position:
            kwargs[POSITION_TAG] = self._preferred_position
        if self._game_uuid:
            kwargs[GAME_TAG] = self._game_uuid
        sendCommand(
            self._control_socket, JOIN_COMMAND,
            player=self._player_uuid, **kwargs)

    def _send_call_command(self, call):
        logging.info("Making call %r", call)
        sendCommand(
            self._control_socket, CALL_COMMAND, game=self._game_uuid,
            player=self._player_uuid, call=call)

    def _send_play_command(self, card):
        logging.info("Playing card %r", card)
        sendCommand(
            self._control_socket, PLAY_COMMAND, game=self._game_uuid,
            player=self._player_uuid, card=card._asdict())

    def _handle_hello_reply(self, **kwargs):
        logging.info("Handshake successful")
        if self._create_game:
            kwargs = { 'game': self._game_uuid } if self._game_uuid else {}
            sendCommand(self._control_socket, GAME_COMMAND, **kwargs)
        else:
            self._send_join_command()

    def _handle_game_reply(self, game=None, **kwargs):
        logging.info("Created game %r", game)
        self._game_uuid = game
        self._send_join_command()
        logging.info("calling setGameId: %r", game)
        self._card_area.setGameId(game)


    def _handle_join_reply(self, game=None, **kwargs):
        logging.info("Joined game %r", game)
        if game:
            self._init_game(game)
            sendCommand(
                self._control_socket, GET_COMMAND, INITGET_COMMAND,
                game=game, player=self._player_uuid)
        else:
            logging.error("Unable to join game")

    def _handle_init_get_reply(self, get=None, counter=None, **kwargs):
        logging.debug("Handling initget reply")
        self._handle_get_reply(get, counter, **kwargs)
        self._start_handling_events()

    def _handle_get_reply(self, get=None, counter=None, **kwargs):
        logging.debug("Handling get reply")
        if counter is not None:
            self._counter = counter
        else:
            logging.warning("No counter included in get reply")
        missing = object()
        pubstate = get.get(PUBSTATE_TAG) or {}
        privstate = get.get(PRIVSTATE_TAG) or {}
        _self = get.get(SELF_TAG) or {}
        position = _self.get(POSITION_TAG, missing)
        if position is not missing and position != self._position:
            self._position = position
            self._card_area.setPlayerPosition(position)
            logging.info("Position assigned: %r", position)
        position_in_turn = _self.get(POSITION_IN_TURN_TAG, missing)
        if position_in_turn is not missing:
            self._card_area.setPositionInTurn(position_in_turn)
            logging.info("Position in turn: %r", position_in_turn)
        allowed_calls = _self.get(ALLOWED_CALLS_TAG, missing)
        if allowed_calls is not missing:
            self._call_panel.setAllowedCalls(allowed_calls)
            logging.info("Allowed calls: %r", allowed_calls)
        calls = pubstate.get(CALLS_TAG, missing)
        if calls is not missing:
            self._call_table.setCalls(calls)
            logging.info("Calls: %r", calls)
        declarer = pubstate.get(DECLARER_TAG, missing)
        contract = pubstate.get(CONTRACT_TAG, missing)
        if declarer is not missing and contract is not missing:
            self._bidding_result_label.setBiddingResult(
                declarer, contract)
            logging.info("Bidding result: %r, %r", declarer, contract)
        cards = pubstate.get(CARDS_TAG, {})
        cards.update(privstate.get(CARDS_TAG, {}))
        if cards:
            self._cards.update(cards)
            self._card_area.setCards(cards)
            logging.info("Cards: %r", cards)
        # make call to get_bid_suggestion from llm_integration
        logging.info(f"copilot: {self._copilot}")
        if allowed_calls is not missing:
            if allowed_calls:
                if (self._copilot):
                    logging.info(f"position: {position}")
                    hand = self._cards.get(position, [])
                    logging.info(f"hand: {hand}")
                    logging.info(f"allowed_calls: {allowed_calls}") 
                    bids_history = self._bids_history
                    logging.info(f"bids_history: {bids_history}")
                    allowed_biddings = self._llm_integration_instance.get_allowed_bidding(allowed_calls)
                    #get_bid_suggestion = self._llm_integration_instance.get_bid_suggestion(position, hand, allowed_biddings, bids_history,self._model)
                    get_bid_suggestion = get_bridge_advice(
                        position = position, 
                        phase = self._phase, 
                        hand = hand,
                        allowed_bids = allowed_biddings, 
                        bidding_history = bids_history
                        )
                    logging.info(f"get_bid_suggestion: {get_bid_suggestion}")

                    # Directly access the 'output' dictionary
                    if isinstance(get_bid_suggestion, dict):
                        your_team_analysis = get_bid_suggestion.get('your_team_analysis', '')
                    elif isinstance(get_bid_suggestion, str):
                        your_team_analysis = get_bid_suggestion
                    else:
                        your_team_analysis = "No analysis available"

                    if self._copilot:
                        self._copilot_widget.append_message(f"Analysis: {your_team_analysis}")
                    logging.info(f"allowed_calls: {allowed_calls}")
            else:
                logging.error("Allowed calls list empty ")
        else:
            logging.error("Allowed calls list missing")
        allowed_cards = _self.get(ALLOWED_CARDS_TAG, missing)
        if allowed_cards is not missing:
            self._card_area.setAllowedCards(allowed_cards)
            logging.info("Allowed cards: %r", allowed_cards)
            #play_from, position, own_hand, partners_hand, trick, allowed_cards, contract, contractors, bids_history, tricks_history
            #play_from = position_in_turn
            if allowed_cards:
                play_from = "Own hand"
                own_hand = self._cards.get(position, [])
                declarer = self._declarer
                contract = self._contract
                contractors = self._contractors
                bids_history = self._bids_history
                tricks_history = self._tricks_history
                if position_in_turn == self._position and declarer == self._position:
                    first_card_from_allowed_cards = allowed_cards[0]
                    if not any(json.dumps(first_card_from_allowed_cards, sort_keys=True) == json.dumps(obj, sort_keys=True) for obj in own_hand):
                        play_from = "Partners hand"
                partners_hand = pubstate.get(CARDS_TAG, {})
                trick= self._current_trick
                logging.info(f"play_from: {play_from}")
                logging.info(f"position: {position}")
                logging.info(f"own_hand: {own_hand}")
                logging.info(f"partners_hand: {partners_hand}")
                logging.info(f"trick: {trick}")
                logging.info(f"allowed_cards: {allowed_cards}")
                logging.info(f"contract: {contract}")
                logging.info(f"contractors: {contractors}")
                logging.info(f"bids_history: {bids_history}")
                logging.info(f"tricks_history: {tricks_history}")
                if (self._copilot):
                    get_card_play_suggestion = self._llm_integration_instance.get_card_play_suggestion(play_from, position, own_hand, partners_hand, trick, allowed_cards, contract, contractors, bids_history, tricks_history)
                    logging.info(f"get_card_play_suggestion: {get_card_play_suggestion}")
                    if self._copilot:
                        self._card_area.displayMessage(get_card_play_suggestion)
        tricks = pubstate.get(TRICKS_TAG, missing)
        if tricks is not missing:
            if tricks:
                logging.info("Tricks: %r", tricks)
                self._tricks_history.append(tricks)
                trick = tricks[-1].get("cards")
                if trick:
                    self._card_area.setTrick(trick)
            tricks_won = {
                partnership: 0 for partnership in positions.Partnership
            }
            for trick in tricks:
                winner = trick.get("winner")
                if winner:
                    self._current_trick = []
                    tricks_won[positions.partnershipFor(winner)] += 1
            self._tricks_won_label.setTricksWon(tricks_won)
        vulnerability = pubstate.get(VULNERABILITY_TAG, missing)
        if vulnerability is not missing:
            self._call_table.setVulnerability(vulnerability)

    def _handle_call_reply(self, **kwargs):
        logging.debug("Call successful")

    def _handle_play_reply(self, **kwargs):
        if kwargs.get("status") == "ERR:RV":
            logging.error("Rule violation: Invalid card play")
        else:
            logging.debug("Play successful")

    def _handle_deal_event(self, opener=None, vulnerability=None, counter=None, **kwargs):
        logging.debug("Dealing cards")
        if self._is_stale_event(counter):
            return
        logging.debug("Cards dealt")
        self._card_area.setPositionInTurn(opener)
        self._call_table.setVulnerability(vulnerability)
        self._bidding_result_label.setBiddingResult(None, None)
        self._request(PUBSTATE_TAG, PRIVSTATE_TAG)
        self._phase = "play"

    def _handle_turn_event(self, position=None, counter=None, **kwargs):
        logging.debug("Turn event")
        if self._is_stale_event(counter):
            return
        logging.debug("Position in turn: %r", position)
        self._card_area.setPositionInTurn(position)
        if position == self._position:
            self._request(SELF_TAG)
        else:
            self._call_panel.setAllowedCalls([])
            self._card_area.setAllowedCards([])

    def _handle_call_event(
            self, position=None, call=None, counter=None, **kwargs):
        logging.debug("Call event")
        if self._is_stale_event(counter):
            return
        logging.debug("Call made. Position: %r, Call: %r", position, call)
        self._call_table.addCall(position, call)
        self._bids_history.append({position: call})

    def _handle_bidding_event(
            self, declarer=None, contract=None, counter=None, **kwargs):
        logging.debug("Bidding event")
        if self._is_stale_event(counter):
            return
        logging.debug(
            "Bidding completed. Declarer: %r, Contract: %r", declarer, contract)
        self._declarer = declarer
        self._contract = contract
        self._contractors = 'north, south' if declarer == 'north' or declarer == 'south' else 'east, west'
        self._bidding_result_label.setBiddingResult(declarer, contract)

    def _handle_play_event(
            self, position=None, card=None, counter=None, **kwargs):
        logging.debug("Play event") 
        if self._is_stale_event(counter):
            return
        logging.debug("Card played. Position: %r, Card: %r", position, card)
        self._card_area.playCard(position, card)
        self._current_trick.append({"position": position, "card": card})

    def _handle_dummy_event(
            self, counter=None, position=None, cards=None, **kwargs):
        logging.debug("Dummy event")
        if self._is_stale_event(counter):
            return
        logging.debug("Dummy hand revealed")
        self._card_area.setCards({ position: cards })

    def _handle_trick_event(self, winner, counter=None, **kwargs):
        logging.debug("Trick event")
        if self._is_stale_event(counter):
            return
        logging.debug("Trick completed. Winner: %r", winner)
        self._tricks_won_label.addTrick(winner)

    def _handle_dealend_event(self, result, counter=None, **kwargs):
        logging.debug("Deal end event")
        if self._is_stale_event(counter):
            return
        logging.debug("Deal ended. Result: %r", result)
        self._score_table.addResult(result)
        self._call_table.setCalls([])

    def _handle_player_event(self, player, position, **kwargs):
        logging.debug("Player joined. Player: %r. Position: %r", player, position)

    def closeEvent(self, event):
        """Handle the window close event"""
        logging.info("Closing main window. Stopping all bot processes.")
        self._card_area._stop_all_bots()  # Call the method to stop all bots
        super().closeEvent(event)  # Call the parent class's closeEvent

def _get_key_from_file(f):
    logging.debug("Reading key from file %r", f)
    if f:
        with f:
            return f.readline().strip()
    return None

def main():
    parser = argparse.ArgumentParser(
        description="A lightweight bridge application")
    parser.add_argument(
        "endpoint",
        help="""Base endpoint of the bridge backend. Follows ZeroMQ transmit
             protocol syntax. For example: tcp://bridge.example.com:5555""")
    parser.add_argument(
        "--server-key-file",
        help="""File to read CURVE server key from. If provided, the sockets are
             setup to use CURVE security mechanism with the given server
             key.""",
        type=argparse.FileType("r")
    )
    parser.add_argument(
        "--secret-key-file",
        help="""File to read CURVE secret key from. If the server key is given, and the
             secret key is not, a new keypair is autogenerated.""",
        type=argparse.FileType("r")
    )
    parser.add_argument(
        "--public-key-file",
        help="""File to read CURVE public key from. If the public key is given, and the
             public key is not, a new keypair is autogenerated.""",
        type=argparse.FileType("r")
    )
    parser.add_argument(
        '--position',
        help="""If provided, the application requests the server to assign the
             given position. If the position is not available (or if the option
             is not given), any position is requested.""")
    parser.add_argument(
        '--game',
        help="""UUID of the game to be joined. The game is not created unless
             --create-game option is also provided.""")
    parser.add_argument(
        '--create-game', action="store_true",
        help="""If given, the application requests the backend to create new
             game. UUID can be optionally given by providing --game option.""")
    parser.add_argument(
        '--player',
        help="""UUID of the player. If omitted, an UUID is generated.""")
    parser.add_argument(
        '--copilot', action="store_true",
        help="""If provided, the application is started in copilot mode.""")
    parser.add_argument(
        '--autopilot', action="store_true",
        help="""If provided, the application is started in autopilot mode.""")
    parser.add_argument(
        '--model',
        help="""The model to use for the autopilot or copilote mode. List of models currently supported: gpt-3.5-turbo, gpt-4-turbo""")
    parser.add_argument(
        "--verbose", "-v", action="count", default=0,
        help="""Increase logging levels. Repeat for even more logging.""")
    args = parser.parse_args()

    logging_level = logging.WARNING
    if args.verbose == 1:
        logging_level = logging.INFO
    elif args.verbose >= 2:
        logging_level = logging.DEBUG
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s', level=logging_level)
    logging.info("Logging level: %r", logging_level)

    logging.info("Initializing sockets")
    zmqctx = zmq.Context.instance()
    endpoint_generator = messaging.endpoints(args.endpoint)
    control_socket = zmqctx.socket(zmq.DEALER)
    curve_server_key = _get_key_from_file(args.server_key_file)
    curve_secret_key = _get_key_from_file(args.secret_key_file)
    curve_public_key = _get_key_from_file(args.public_key_file)
    messaging.setupCurve(control_socket, curve_server_key, curve_secret_key, curve_public_key)
    control_socket.connect(next(endpoint_generator))
    event_socket = zmqctx.socket(zmq.SUB)
    messaging.setupCurve(event_socket, curve_server_key)
    event_socket.connect(next(endpoint_generator))
    model = args.model
    if model is None:
        model = 'gpt-3.5-turbo'
    logging.info(f"Model: {model}")

    if args.autopilot:
        logging.info("Running in autopilot mode without GUI.")
        # Run in headless mode without creating any QWidget
        bridge_autopilot = BridgeAutopilot(
            control_socket, event_socket, args.position, args.game,
            args.create_game, args.player, args.autopilot, model)
        bridge_autopilot.start()
        try:
            while True:
                pass  # Keep the process alive
        except KeyboardInterrupt:
            logging.info("Autopilot mode interrupted by user.")
    else:
        logging.info("Starting main window")
        app = QApplication(sys.argv)
        window = BridgeWindow(
            control_socket, event_socket, args.position, args.game,
            args.create_game, args.player, args.copilot, model)
        code = app.exec_()

        logging.info("Main window closed. Closing sockets.")
        zmqctx.destroy(linger=0)
        return code


if __name__ == "__main__":
    main()

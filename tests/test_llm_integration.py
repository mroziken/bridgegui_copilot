import unittest
from unittest.mock import patch, MagicMock
from bridgegui.llm_integration import LLMIntegration
import os
from dotenv import load_dotenv

class TestLLMIntegration(unittest.TestCase):
    @patch('openai.ChatCompletion.create')
    def test_get_bid_suggestion(self, mock_create):
        # Arrange
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        game_state = "test_game_state"
        expected_prompt = f"Given the following game state, suggest the best bid:\n{game_state}"
        expected_response = "1NT"
        
        mock_create.return_value = MagicMock(choices=[MagicMock(message={'content': expected_response})])
        
        llm_integration = LLMIntegration(api_key)
        
        # Act
        bid_suggestion = llm_integration.get_bid_suggestion(game_state)
        
        # Assert
        self.assertEqual(bid_suggestion, expected_response)
        mock_create.assert_called_once_with(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": expected_prompt}
            ]
        )

if __name__ == '__main__':
    unittest.main()
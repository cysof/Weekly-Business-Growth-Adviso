import unittest
from unittest.mock import patch, MagicMock
import os
from app.services import get_sales_data, generate_insight

class TestGetSalesData(unittest.TestCase):

    @patch('app.services.requests.get')
    @patch('app.services.os.getenv')
    def test_get_sales_data(self, mock_getenv, mock_requests_get):
        # Ensure the API key is set
        """
        Test the get_sales_data function to ensure it correctly retrieves and calculates
        sales revenue for the current and previous weeks using mocked API responses.

        This test mocks the environment variable for the Paystack API key and the requests.get
        method to simulate API responses for current and previous week sales data. It verifies
        that the function returns the expected revenue amounts.

        Mocks:
            - os.getenv: Mocked to return a dummy API key.
            - requests.get: Mocked to return predefined JSON responses for current and previous weeks.

        Asserts:
            - The revenue for the current week is calculated as 600.0.
            - The revenue for the previous week is calculated as 300.0.
        """

        mock_getenv.return_value = "dummy_api_key"

        # Create a mock response for the current week API call
        mock_response_current = MagicMock()
        mock_response_current.json.return_value = {
            'data': [
                {'amount': 10000},
                {'amount': 20000},
                {'amount': 30000}
            ]
        }

        # Create a mock response for the previous week API call
        mock_response_previous = MagicMock()
        mock_response_previous.json.return_value = {
            'data': [
                {'amount': 5000},
                {'amount': 10000},
                {'amount': 15000}
            ]
        }

       
        mock_requests_get.side_effect = [mock_response_current, mock_response_previous]

        # Call the function under test
        data = get_sales_data()
        self.assertEqual(data['revenue'], 600.0)
        self.assertEqual(data['previous_revenue'], 300.0)


    @patch('app.services.get_sales_data')
    def test_generate_insight_with_api_error(self, mock_get_sales_data):
        # Mock API error
        # Test that generate_insight() raises an exception if the
        # get_sales_data() call fails due to an API error.
        mock_get_sales_data.side_effect = Exception('API error')

        # Test generate_insight function with API error
        with self.assertRaises(Exception):
            generate_insight()
            
            
if __name__ == '__main__':
    unittest.main()
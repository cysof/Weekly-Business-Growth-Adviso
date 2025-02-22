from unittest.mock import patch
from app.models import BusinessInsight
from app.services import generate_insight

def test_generate_insight():
    """Test insight generation with mocked data"""
    with patch('app.services.get_sales_data') as mock_get_data:
        # Mock the sales data
        mock_get_data.return_value = {
            "revenue": 115,
            "previous_revenue": 100
        }

        # Call the function
        insight = generate_insight()

        # Verify the insight
        assert isinstance(insight, BusinessInsight)
        assert insight.metric == "Revenue"
        assert "15.0%" in insight.observation
        assert "grew significantly" in insight.observation
        assert "this week" in insight.observation
        assert any(phrase in insight.recommendation for phrase in [
            "Continue current strategy",
            "Identify which products or campaigns drove this growth"
        ])
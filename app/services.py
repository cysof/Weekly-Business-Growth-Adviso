import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app.models import BusinessInsight
import logging

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

def get_sales_data():
    """
    Retrieve sales data from the Paystack API and return it as a dictionary with two keys:
    - revenue: the total revenue for the current week
    - previous_revenue: the total revenue for the previous week

    Returns:
        dict: A dictionary with the revenue and previous revenue.

    Raises:
        ValueError: If the Paystack API key is not found.
        requests.exceptions.RequestException: If the API request fails.
    """
    api_key = os.getenv("PAYSTACK_API_KEY")
    if not api_key:
        raise ValueError("Paystack API key not found in environment variables.")

    today = datetime.now()
    current_week_start = today - timedelta(days=today.weekday())
    previous_week_start = current_week_start - timedelta(days=7)

    base_url = "https://api.paystack.co/transaction"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    params = {
        "status": "success"
    }

    try:
        # Get current and previous week revenue in a single API call
        params["from"] = current_week_start.strftime("%Y-%m-%d")
        params["to"] = today.strftime("%Y-%m-%d")
        current_response = requests.get(base_url, headers=headers, params=params)
        current_response.raise_for_status()
        current_data = current_response.json()

        params["from"] = previous_week_start.strftime("%Y-%m-%d")
        params["to"] = (current_week_start - timedelta(days=1)).strftime("%Y-%m-%d")
        previous_response = requests.get(base_url, headers=headers, params=params)
        previous_response.raise_for_status()
        previous_data = previous_response.json()

        # Calculate current and previous week revenue
        current_revenue = sum(txn['amount'] for txn in current_data['data']) / 100
        previous_revenue = sum(txn['amount'] for txn in previous_data['data']) / 100

        return {
            "revenue": current_revenue,
            "previous_revenue": previous_revenue
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from Paystack API: {e}")
        raise

def generate_insight():
    try:
        data = get_sales_data()
        revenue = data["revenue"]
        prev_revenue = data["previous_revenue"]

        # Calculate the percent change
        if prev_revenue == 0:
            percent_change = 100 if revenue != 0 else 0
        else:
            percent_change = ((revenue - prev_revenue) / prev_revenue) * 100

        # Format the percent change to 1 decimal place
        formatted_change = abs(round(percent_change, 1))

        # Determine insight based on percentage change
        if percent_change < -15:
            observation = f"Revenue dropped significantly by {formatted_change}% this week."
            recommendation = "Run a promotional discount and email re-engagement campaign targeting inactive customers."
        elif percent_change < 0:
            observation = f"Revenue decreased by {formatted_change}% this week."
            recommendation = "Analyze which product categories are underperforming and consider targeted marketing."
        elif percent_change == 0:
            observation = "Revenue remained unchanged from last week."
            recommendation = "Review customer feedback to identify improvement opportunities."
        elif percent_change < 15:
            observation = f"Revenue increased by {formatted_change}% this week."
            recommendation = "Continue current strategy while testing new marketing channels."
        else:
            observation = f"Revenue grew significantly by {formatted_change}% this week."
            recommendation = "Identify which products or campaigns drove this growth and consider scaling them."

        return BusinessInsight(
            metric="Revenue",
            observation=observation,
            recommendation=recommendation
        )

    except Exception as e:
        logger.error(f"Error generating insight: {e}")
        raise
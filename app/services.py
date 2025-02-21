import requests
from app.models import BusinessInsight
from datetime import datetime, timedelta

def get_sales_data():
    """
    Retrieve sales data from an external API (e.g. Stripe) and return it as a dictionary with two keys:
    - revenue: the total revenue for the current week
    - previous_revenue: the total revenue for the previous week
    
    Returns:
        dict: A dictionary with the revenue and previous revenue.
    """
    # Calculate date ranges
    today = datetime.now()
    current_week_start = today - timedelta(days=today.weekday())
    current_week_end = today
    previous_week_start = current_week_start - timedelta(days=7)
    previous_week_end = current_week_start - timedelta(days=1)
    
    # Format dates for API request
    current_start_str = current_week_start.strftime("%Y-%m-%d")
    current_end_str = current_week_end.strftime("%Y-%m-%d")
    previous_start_str = previous_week_start.strftime("%Y-%m-%d")
    previous_end_str = previous_week_end.strftime("%Y-%m-%d")
    
    # API configuration
    api_key = " "  # Store this securely in environment variables
    base_url = "https://api.stripe.com/v1/"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Get current week revenue
    current_params = {
        "created[gte]": current_start_str,
        "created[lte]": current_end_str,
        "status": "succeeded"
    }
    
    try:
        current_response = requests.get(
            f"{base_url}charges", 
            headers=headers,
            params=current_params
        )
        current_response.raise_for_status()
        current_data = current_response.json()
        
        # Calculate current week revenue
        current_revenue = sum(charge['amount'] for charge in current_data['data'])
        
        # Get previous week revenue
        previous_params = {
            "created[gte]": previous_start_str,
            "created[lte]": previous_end_str,
            "status": "succeeded"
        }
        
        previous_response = requests.get(
            f"{base_url}charges", 
            headers=headers,
            params=previous_params
        )
        previous_response.raise_for_status()
        previous_data = previous_response.json()
        
        # Calculate previous week revenue
        previous_revenue = sum(charge['amount'] for charge in previous_data['data'])
        
        return {
            "revenue": current_revenue / 100,  # Convert from cents to dollars
            "previous_revenue": previous_revenue / 100
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        # Return empty values or raise exception based on your error handling strategy
        return {"revenue": 0, "previous_revenue": 0}

def generate_insight():
    """
    Generate a BusinessInsight object based on current sales data.
    
    Returns:
        BusinessInsight: An object with three attributes:
        - metric: The metric being observed (e.g. Revenue).
        - observation: A human-readable sentence describing the observation.
        - recommendation: A human-readable sentence describing a recommended course of action.
    """
    # Get sales data from the external API
    data = get_sales_data()
    
    # Calculate the percent change
    if data["previous_revenue"] > 0:  # Prevent division by zero
        percent_change = ((data["revenue"] - data["previous_revenue"]) / data["previous_revenue"]) * 100
    else:
        percent_change = 100  # If previous revenue was 0, treat as 100% increase
    
    # Format the percent change to 1 decimal place
    formatted_change = abs(round(percent_change, 1))
    
    # Determine insight based on percentage change
    if percent_change < -15:
        return BusinessInsight(
            metric="Revenue",
            observation=f"Revenue dropped significantly by {formatted_change}% this week.",
            recommendation="Run a promotional discount and email re-engagement campaign targeting inactive customers."
        )
    elif percent_change < 0:
        return BusinessInsight(
            metric="Revenue",
            observation=f"Revenue decreased by {formatted_change}% this week.",
            recommendation="Analyze which product categories are underperforming and consider targeted marketing."
        )
    elif percent_change == 0:
        return BusinessInsight(
            metric="Revenue",
            observation="Revenue remained unchanged from last week.",
            recommendation="Review customer feedback to identify improvement opportunities."
        )
    elif percent_change < 10:
        return BusinessInsight(
            metric="Revenue",
            observation=f"Revenue increased by {formatted_change}% this week.",
            recommendation="Continue current strategy while testing new marketing channels."
        )
    else:
        return BusinessInsight(
            metric="Revenue",
            observation=f"Revenue grew significantly by {formatted_change}% this week.",
            recommendation="Identify which products or campaigns drove this growth and consider scaling them."
        )
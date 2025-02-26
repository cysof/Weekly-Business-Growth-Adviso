from apscheduler.schedulers.background import BackgroundScheduler
import app.services as services
import requests
import logging
from datetime import datetime
from app.config import settings

# Configuration
TELEX_WEBHOOK_URL = settings.TELEX_WEBHOOK_URL
MAX_RETRIES = 3
RETRY_DELAY = 60  # seconds

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize scheduler with timezone awareness
scheduler = BackgroundScheduler(timezone="UTC")

def send_weekly_insight():
    """
    Sends a weekly business growth insight to Telex via a webhook.
    
    The insight is generated by `services.generate_insight()` and contains a
    metric observation and a recommended course of action. The insight is
    formatted as a Telex message with a title and body, and is posted to the
    Telex webhook URL with error handling and retries.
    """
    try:
        # Generate the business insight
        insight = services.generate_insight()
        logger.info(f"Generated insight for {insight.metric}: {insight.observation}")
        
        # Format the payload with more structured information
        payload = {
            "text": f"# Weekly Business Insight: {insight.metric}\n\n"
                   f"## 📊 Observation\n{insight.observation}\n\n"
                   f"## ✅ Recommendation\n{insight.recommendation}\n\n"
                   f"_Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M')} UTC_"
        }
        
        # Send the request with retry logic
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    TELEX_WEBHOOK_URL, 
                    json=payload,
                    timeout=10  # Set a reasonable timeout
                )
                response.raise_for_status()
                logger.info(f"Successfully sent insight to Telex. Status code: {response.status_code}")
                return
            except requests.exceptions.RequestException as e:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(f"Attempt {attempt + 1} failed. Retrying in {RETRY_DELAY} seconds... Error: {str(e)}")
                    import time
                    time.sleep(RETRY_DELAY)
                else:
                    raise
    except Exception as e:
        logger.error(f"Failed to send weekly insight: {str(e)}")
        # Consider alerting operations team here for critical failures

def start():
    """
    Starts the scheduler to send weekly business growth insights to Telex.
    
    The scheduler is configured to send the insights every Monday at 9am. The
    insights are generated by `services.generate_insight()` and contain a metric
    observation and a recommended course of action. The insights are formatted
    as a Telex message with a title and body, and are posted to the Telex webhook
    URL.
    """
    try:
        # Add the job to the scheduler with misfire handling
        scheduler.add_job(
            send_weekly_insight, 
            "cron", 
            day_of_week="mon", 
            hour=9,
            misfire_grace_time=3600,  # Allow job to run up to 1 hour late
            id="weekly_business_insight",
            replace_existing=True
        )
        
        # Start the scheduler
        scheduler.start()
        logger.info("Scheduler started successfully. Weekly insights will be sent every Monday at 9:00 UTC")
        
        # Immediately run the job once for testing/verification (optional)
        # send_weekly_insight()
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")
        raise
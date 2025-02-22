import pytest
from unittest.mock import patch, Mock, call
import requests
from datetime import datetime
import logging
import time

# Import the module to test
from app.scheduler import scheduler, send_weekly_insight, start, RETRY_DELAY, MAX_RETRIES


@pytest.fixture
def mock_services():
    """Mock the services.generate_insight() function"""
    with patch('app.services.generate_insight') as mock_generate:
        # Create a mock insight object
        mock_insight = Mock()
        mock_insight.metric = "Customer Retention"
        mock_insight.observation = "Retention rate has increased by 5% this week."
        mock_insight.recommendation = "Continue your email campaign strategy."
        
        # Configure the mock to return the insight
        mock_generate.return_value = mock_insight
        yield mock_generate


@pytest.fixture
def mock_requests():
    """Mock the requests.post() function"""
    with patch('requests.post') as mock_post:
        # Set up a successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        mock_response.raise_for_status.return_value = None
        yield mock_post


@pytest.fixture
def mock_scheduler():
    """Mock the scheduler object"""
    with patch('app.scheduler.scheduler') as mock_scheduler_obj:
        yield mock_scheduler_obj


def test_send_weekly_insight_success(mock_services, mock_requests, caplog):
    """Test the send_weekly_insight function under normal conditions"""
    caplog.set_level(logging.INFO)
    
    # Call the function
    send_weekly_insight()
    
    # Verify that the insight was generated
    mock_services.assert_called_once()
    
    # Verify the request was sent with the correct payload
    mock_requests.assert_called_once()
    args, kwargs = mock_requests.call_args
    
    # Check the URL is correct
    assert 'json' in kwargs
    
    # Verify the payload format
    payload = kwargs['json']
    assert 'text' in payload
    assert 'Weekly Business Insight: Customer Retention' in payload['text']
    assert 'Observation' in payload['text']
    assert 'Recommendation' in payload['text']
    assert 'Retention rate has increased by 5% this week.' in payload['text']
    assert 'Continue your email campaign strategy.' in payload['text']
    assert '_Generated on' in payload['text']
    
    # Check logs
    assert 'Generated insight for Customer Retention' in caplog.text
    assert 'Successfully sent insight to Telex' in caplog.text


def test_send_weekly_insight_with_retries(mock_services, caplog):
    """Test the retry logic when the request fails initially"""
    caplog.set_level(logging.WARNING)
    
    # Create a mock response that fails twice then succeeds
    with patch('requests.post') as mock_post:
        # First two calls raise exceptions, third one succeeds
        mock_post.side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            requests.exceptions.Timeout("Request timed out"),
            Mock(status_code=200, raise_for_status=Mock())
        ]
        
        # Mock sleep to avoid waiting during tests
        with patch('time.sleep') as mock_sleep:
            # Call the function
            send_weekly_insight()
            
            # Verify retry attempts
            assert mock_post.call_count == 3
            
            # Verify sleep was called with the right delay
            assert mock_sleep.call_count == 2
            mock_sleep.assert_has_calls([call(RETRY_DELAY), call(RETRY_DELAY)])
            
            # Check warning logs about retries
            assert "Attempt 1 failed. Retrying" in caplog.text
            assert "Attempt 2 failed. Retrying" in caplog.text


def test_send_weekly_insight_max_retries_exceeded(mock_services, caplog):
    """Test that the function gives up after MAX_RETRIES attempts"""
    caplog.set_level(logging.ERROR)
    
    # Create a mock response that always fails
    with patch('requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.RequestException("Request failed")
        
        # Mock sleep to avoid waiting during tests
        with patch('time.sleep'):
            # Call the function
            send_weekly_insight()
            
            # Verify we attempted exactly MAX_RETRIES times
            assert mock_post.call_count == MAX_RETRIES
            
            # Check error log
            assert "Failed to send weekly insight" in caplog.text


def test_start_scheduler_success(mock_scheduler, caplog):
    """Test that the scheduler starts correctly"""
    caplog.set_level(logging.INFO)
    
    # Call the function
    start()
    
    # Verify the job was added correctly
    mock_scheduler.add_job.assert_called_once()
    args, kwargs = mock_scheduler.add_job.call_args
    
    # Check the job configuration
    assert args[0] == send_weekly_insight
    assert kwargs['day_of_week'] == 'mon'
    assert kwargs['hour'] == 9
    assert kwargs['id'] == 'weekly_business_insight'
    assert kwargs['replace_existing'] is True
    
    # Verify scheduler was started
    mock_scheduler.start.assert_called_once()
    
    # Check success log
    assert "Scheduler started successfully" in caplog.text


def test_start_scheduler_exception(mock_scheduler, caplog):
    """Test error handling when the scheduler fails to start"""
    caplog.set_level(logging.ERROR)
    
    # Make scheduler.start() raise an exception
    mock_scheduler.add_job.side_effect = Exception("Failed to add job")
    
    # Call should raise the exception
    with pytest.raises(Exception) as excinfo:
        start()
    
    # Verify the error message
    assert "Failed to add job" in str(excinfo.value)
    
    # Check error log
    assert "Failed to start scheduler" in caplog.text


@patch('app.scheduler.datetime')
def test_formatted_timestamp(mock_datetime, mock_services, mock_requests):
    """Test that the timestamp is correctly formatted in the message"""
    # Set a fixed datetime for testing
    mock_now = Mock()
    mock_now.strftime.return_value = "2025-02-21 at 09:00"
    mock_datetime.now.return_value = mock_now
    
    # Call the function
    send_weekly_insight()
    
    # Verify the timestamp formatting in the payload
    args, kwargs = mock_requests.call_args
    payload = kwargs['json']
    assert "_Generated on 2025-02-21 at 09:00 UTC_" in payload['text']
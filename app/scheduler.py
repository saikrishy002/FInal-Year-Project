"""
ExpiryGuard — Background Alert Scheduler
==========================================
Uses APScheduler to run periodic alert checks in a background thread.
Alerts are processed every 6 hours and also once at application startup.

Functions:
    init_scheduler   — start the scheduler and attach it to the Flask app.
    stop_scheduler   — gracefully shut down the scheduler.
"""

import logging
from datetime import datetime

# attempt to import APScheduler; if missing, provide helpful error
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
except ImportError:
    BackgroundScheduler = None
    IntervalTrigger = None
    logging.error("APScheduler is not installed. Please run 'pip install apscheduler' or install via requirements.txt.")

from .models import User
from .alert_utils import process_all_user_alerts

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()
app_instance = None  # will be set by init_scheduler

def scheduled_alert_task():
    """
    Scheduled task to process and send alerts for all users.
    Runs at intervals defined in configuration.
    """
    # APScheduler runs in a background thread, so we need to use app context
    if app_instance is None:
        logger.error("App instance not available for scheduled task")
        return
    
    with app_instance.app_context():
        try:
            result = process_all_user_alerts()
            logger.info(f"Scheduled alert processing completed: {result}")
        except Exception as e:
            logger.error(f"Error in scheduled alert task: {e}")

def init_scheduler(app):
    """
    Initialize the APScheduler with the Flask app.
    Schedules alert tasks to run every specified interval.
    """
    global app_instance
    app_instance = app
    
    try:
        # Run alert checks every 6 hours
        scheduler.add_job(
            func=scheduled_alert_task,
            trigger=IntervalTrigger(hours=6),
            id='alert_scheduler',
            name='Process user expiry alerts',
            replace_existing=True,
            misfire_grace_time=15
        )
        
        # Also run at app startup
        scheduler.add_job(
            func=scheduled_alert_task,
            id='startup_alert_check',
            name='Run alert check on startup',
            replace_existing=True
        )
        
        if not scheduler.running:
            scheduler.start()
            logger.info("Alert scheduler started successfully")
        
        return scheduler
    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {e}")
        return None

def stop_scheduler():
    """Stop the scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Alert scheduler stopped")
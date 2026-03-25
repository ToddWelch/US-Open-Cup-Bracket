import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from scraper import scrape_bracket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def run_scrape():
    now = datetime.now()
    logger.info("Scheduled scrape at %s", now.isoformat())
    try:
        scrape_bracket()
        logger.info("Scrape completed at %s", datetime.now().isoformat())
    except Exception as e:
        logger.error("Scrape error: %s", e)


def init_scheduler():
    # Default: every 2 hours
    scheduler.add_job(
        run_scrape,
        CronTrigger(hour="*/2"),
        id="scrape_default",
        replace_existing=True,
    )

    # Game days: every 30 minutes, 6pm-midnight ET
    scheduler.add_job(
        run_scrape,
        CronTrigger(minute="*/30", hour="18-23", timezone="US/Eastern"),
        id="scrape_gameday",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started")

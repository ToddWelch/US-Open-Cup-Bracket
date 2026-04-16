import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

try:
    from .scraper import scrape_bracket, scrape_espn_fast, load_existing, has_games_today
except ImportError:
    from scraper import scrape_bracket, scrape_espn_fast, load_existing, has_games_today

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def run_scrape():
    now = datetime.now()
    logger.info("Full scrape at %s", now.isoformat())
    try:
        scrape_bracket()
        logger.info("Full scrape completed at %s", datetime.now().isoformat())
    except Exception as e:
        logger.error("Full scrape error: %s", e)


def run_fast_poll():
    now = datetime.now()
    logger.info("ESPN fast poll at %s", now.isoformat())
    try:
        existing = load_existing()
        if not has_games_today(existing):
            logger.info("No games today, skipping fast poll")
            return
        scrape_espn_fast()
        logger.info("ESPN fast poll completed at %s", datetime.now().isoformat())
    except Exception as e:
        logger.error("ESPN fast poll error: %s", e)


def init_scheduler():
    # Full scrape (all sources): every 2 hours
    scheduler.add_job(
        run_scrape,
        CronTrigger(hour="*/2"),
        id="scrape_default",
        replace_existing=True,
    )

    # ESPN-only fast poll: every 2 minutes, 6pm-midnight ET on game days
    scheduler.add_job(
        run_fast_poll,
        CronTrigger(minute="*/2", hour="18-23", timezone="US/Eastern"),
        id="scrape_gameday_live",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started")

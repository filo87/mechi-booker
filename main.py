import os
import logging
import time
import schedule
import telebot
from dotenv import load_dotenv
from lib.Booker import Booker, Slot

load_dotenv()

MATCHI_FACILITY_ID = int(os.getenv("MATCHI_FACILITY_ID"))
MATCHI_TOKEN = os.getenv("MATCHI_TOKEN")
TG_TOKEN = os.getenv("TG_TOKEN")
TG_GROUP_ID = int(os.getenv("TG_GROUP_ID"))
HEALTHCHECK_URL = os.getenv("HEALTHCHECK_URL")
BOOK_IN_DAYS = int(os.getenv("BOOK_IN_DAYS"))
BOOK_AT_HOUR = int(os.getenv("BOOK_AT_HOUR"))
BOOK_AT_MIN = int(os.getenv("BOOK_AT_MIN"))

logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)


bot = telebot.TeleBot(TG_TOKEN, parse_mode="MARKDOWN")


def handle_booking(slot: Slot):
    message = f"""*Booking*
    {slot["start"].strftime('%a %-d %b %H:%M')} – {slot["duration"]}min
    {slot["court"]}"""
    bot.send_message(TG_GROUP_ID, message, disable_notification=True)


booker = Booker(MATCHI_TOKEN, MATCHI_FACILITY_ID, handle_booking)

s = (
    schedule.every()
    .day.at("00:00:07")
    .do(booker.get_best_slot_available, BOOK_IN_DAYS, BOOK_AT_HOUR, BOOK_AT_MIN)
)

logging.info(f"Service started, next check at {s.next_run} minutes")

while True:
    logging.debug("Main loop...")
    schedule.run_pending()
    time.sleep(1)

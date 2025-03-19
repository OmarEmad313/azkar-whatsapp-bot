import os
import sys
import time
import logging
import datetime
import json
from pathlib import Path
import pytz

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.sender import WhatsAppSender
from infrastructure.config import get_config
from infrastructure.auth import WhatsAppAuth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/scheduler.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("zikr_scheduler")

class ZikrScheduler:
    """Scheduler for sending zikr messages at specific times"""
    
    def __init__(self):
        self.config = get_config()
        self.sender = None
        self.tracking_file = Path("logs/sent_messages_tracker.json")
        self.sent_today = self._load_tracking_data()
        
        # Load schedule settings from config
        self.timezone = pytz.timezone(self.config.get("Schedule", "timezone", fallback="UTC"))
        
        # Evening schedule
        self.evening_start = int(self.config.get("Schedule", "evening_start_hour", fallback="16"))
        self.evening_end = int(self.config.get("Schedule", "evening_end_hour", fallback="21"))
        
        # Morning schedule
        self.morning_start = int(self.config.get("Schedule", "morning_start_hour", fallback="5"))
        self.morning_end = int(self.config.get("Schedule", "morning_end_hour", fallback="10"))
        
        self.check_interval = int(self.config.get("Schedule", "check_interval", fallback="60"))
        
        # Get recipients
        self.recipients = self._get_recipients()
        
    def _get_recipients(self):
        """Get list of recipients from config"""
        recipient_str = self.config.get("WhatsApp", "scheduled_recipients", 
                                      fallback=self.config.get("WhatsApp", "chat_id"))
        return [r.strip() for r in recipient_str.split(",")]
        
    def _load_tracking_data(self):
        """Load tracking data from file"""
        if not self.tracking_file.exists():
            return {
                "evening": {"last_sent_date": None, "recipients": []},
                "morning": {"last_sent_date": None, "recipients": []}
            }
        
        try:
            with open(self.tracking_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading tracking data: {e}")
            return {
                "evening": {"last_sent_date": None, "recipients": []},
                "morning": {"last_sent_date": None, "recipients": []}
            }
            
    def _save_tracking_data(self):
        """Save tracking data to file"""
        try:
            # Ensure directory exists
            self.tracking_file.parent.mkdir(exist_ok=True)
            
            with open(self.tracking_file, "w") as f:
                json.dump(self.sent_today, f)
        except Exception as e:
            logger.error(f"Error saving tracking data: {e}")
    
    def _is_already_sent_today(self, message_type, recipient):
        """Check if a message has already been sent to recipient today"""
        today_str = datetime.datetime.now(self.timezone).strftime("%Y-%m-%d")
        
        if (self.sent_today.get(message_type, {}).get("last_sent_date") == today_str and
            recipient in self.sent_today.get(message_type, {}).get("recipients", [])):
            return True
        
        return False
        
    def _all_morning_sent_today(self):
        """Check if morning zikr has been sent to all recipients today"""
        for recipient in self.recipients:
            if not self._is_already_sent_today("morning", recipient):
                return False
        return True
        
    def _all_evening_sent_today(self):
        """Check if evening zikr has been sent to all recipients today"""
        for recipient in self.recipients:
            if not self._is_already_sent_today("evening", recipient):
                return False
        return True
    
    def _calculate_next_wakeup_time(self):
        """Calculate the next time the scheduler should wake up"""
        now = datetime.datetime.now(self.timezone)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + datetime.timedelta(days=1)
        
        # Calculate morning and evening start times for today
        morning_start_time = today.replace(hour=self.morning_start, minute=0, second=0)
        evening_start_time = today.replace(hour=self.evening_start, minute=0, second=0)
        
        # Calculate tomorrow's morning start - always use the configured morning_start hour
        tomorrow_morning_start = tomorrow.replace(hour=self.morning_start, minute=0, second=0)
        
        # Check if we're before morning time and morning messages haven't been sent
        if now < morning_start_time and not self._all_morning_sent_today():
            logger.info(f"Scheduling next check at morning start time: {morning_start_time}")
            return morning_start_time
        
        # Check if we're before evening time and evening messages haven't been sent
        if now < evening_start_time and not self._all_evening_sent_today():
            logger.info(f"Scheduling next check at evening start time: {evening_start_time}")
            return evening_start_time
        
        # If we've passed all sending times for today or all messages are sent, 
        # schedule for tomorrow morning at the configured morning start hour
        if (now >= evening_start_time or 
            (self._all_morning_sent_today() and self._all_evening_sent_today())):
            logger.info(f"All messages for today sent or past sending times. " + 
                       f"Scheduling next check for tomorrow at morning start time: {tomorrow_morning_start}")
            return tomorrow_morning_start
        
        # Fallback: check after the default interval
        next_check = now + datetime.timedelta(seconds=self.check_interval)
        logger.info(f"Using default check interval. Next check at: {next_check}")
        return next_check
        
    def _mark_as_sent(self, message_type, recipient):
        """Mark a message as sent to recipient today"""
        today_str = datetime.datetime.now(self.timezone).strftime("%Y-%m-%d")
        
        if message_type not in self.sent_today:
            self.sent_today[message_type] = {"last_sent_date": today_str, "recipients": []}
            
        # If the date is different, reset the recipients list
        if self.sent_today[message_type]["last_sent_date"] != today_str:
            self.sent_today[message_type]["last_sent_date"] = today_str
            self.sent_today[message_type]["recipients"] = []
            
        # Add recipient to the list if not already there
        if recipient not in self.sent_today[message_type]["recipients"]:
            self.sent_today[message_type]["recipients"].append(recipient)
            
        self._save_tracking_data()
    
    def _initialize_sender(self):
        """Initialize the WhatsApp sender if not already"""
        if self.sender is None:
            logger.info("Initializing WhatsApp sender...")
            auth = WhatsAppAuth()
            if not auth.is_authenticated():
                logger.error("Not authenticated with WhatsApp. Please run auth command first.")
                return False
            
            self.sender = WhatsAppSender()
            return True
            
        return True
        
    def _is_in_evening_time(self):
        """Check if current time is in the evening time range"""
        now = datetime.datetime.now(self.timezone)
        hour = now.hour
        return self.evening_start <= hour < self.evening_end
    
    def _is_in_morning_time(self):
        """Check if current time is in the morning time range"""
        now = datetime.datetime.now(self.timezone)
        hour = now.hour
        return self.morning_start <= hour < self.morning_end
    
    def send_evening_zikr(self):
        """Send evening zikr to recipients if in time range and not already sent today"""
        if not self._is_in_evening_time():
            logger.info("Not in evening time range. Skipping evening zikr.")
            return False
            
        if not self._initialize_sender():
            return False
            
        # Get image path from config
        image_path = self.config.get("Content", "evening_image", fallback=None)
        include_text = self.config.getboolean("Content", "include_text_caption", fallback=False)
        
        if not image_path or not os.path.exists(image_path):
            logger.error(f"Evening image not found at {image_path}")
            return False
            
        # Determine recipients that haven't received the message yet
        pending_recipients = []
        for recipient in self.recipients:
            if not self._is_already_sent_today("evening", recipient):
                pending_recipients.append(recipient)
        
        if not pending_recipients:
            logger.info("Evening zikr already sent to all recipients today")
            return False
            
        # Send to pending recipients
        logger.info(f"Sending evening zikr to {len(pending_recipients)} recipients")
        
        try:
            caption = None if not include_text else "Evening Zikr"
            self.sender.send_image_to_multiple(
                chat_ids=pending_recipients,
                image_path=image_path,
                caption=caption
            )
            
            # Mark as sent for each recipient
            for recipient in pending_recipients:
                self._mark_as_sent("evening", recipient)
                
            logger.info(f"Successfully sent evening zikr to {len(pending_recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Error sending evening zikr: {e}")
            return False
    
    def send_morning_zikr(self):
        """Send morning zikr to recipients if in time range and not already sent today"""
        if not self._is_in_morning_time():
            logger.info("Not in morning time range. Skipping morning zikr.")
            return False
            
        if not self._initialize_sender():
            return False
            
        # Get image path from config
        image_path = self.config.get("Content", "morning_image", fallback=None)
        include_text = self.config.getboolean("Content", "include_text_caption", fallback=False)
        
        if not image_path or not os.path.exists(image_path):
            logger.error(f"Morning image not found at {image_path}")
            return False
            
        # Determine recipients that haven't received the message yet
        pending_recipients = []
        for recipient in self.recipients:
            if not self._is_already_sent_today("morning", recipient):
                pending_recipients.append(recipient)
        
        if not pending_recipients:
            logger.info("Morning zikr already sent to all recipients today")
            return False
            
        # Send to pending recipients
        logger.info(f"Sending morning zikr to {len(pending_recipients)} recipients")
        
        try:
            caption = None if not include_text else "Morning Zikr"
            self.sender.send_image_to_multiple(
                chat_ids=pending_recipients,
                image_path=image_path,
                caption=caption
            )
            
            # Mark as sent for each recipient
            for recipient in pending_recipients:
                self._mark_as_sent("morning", recipient)
                
            logger.info(f"Successfully sent morning zikr to {len(pending_recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Error sending morning zikr: {e}")
            return False
    
    def run(self):
        """Run the scheduler loop"""
        logger.info("Starting Zikr scheduler...")
        
        try:
            while True:
                logger.info("Checking schedule...")
                
                # Check and send morning zikr
                self.send_morning_zikr()
                
                # Check and send evening zikr
                self.send_evening_zikr()
                
                # Calculate next wakeup time
                next_wakeup = self._calculate_next_wakeup_time()
                now = datetime.datetime.now(self.timezone)
                
                # Calculate sleep duration in seconds
                sleep_seconds = (next_wakeup - now).total_seconds()
                if sleep_seconds < 0:
                    sleep_seconds = self.check_interval  # Fallback if calculation is negative
                
                logger.info(f"Sleeping until {next_wakeup} ({sleep_seconds:.0f} seconds)")
                time.sleep(sleep_seconds)
                
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")


if __name__ == "__main__":
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    try:
        logger.info("=== Zikr Scheduler Starting ===")
        logger.info(f"Process ID: {os.getpid()}")
        logger.info(f"Working Directory: {os.getcwd()}")
        logger.info(f"Python Path: {sys.executable}")
        
        scheduler = ZikrScheduler()
        scheduler.run()
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}", exc_info=True)
        sys.exit(1)
import argparse
import sys
import os
import signal
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from infrastructure.sender import WhatsAppSender
from infrastructure.auth import WhatsAppAuth
from infrastructure.config import get_config, save_config
from infrastructure.scheduler import ZikrScheduler


def setup_parser():
    """Setup command line argument parser"""
    parser = argparse.ArgumentParser(description="WhatsApp Message Bot")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Auth command
    auth_parser = subparsers.add_parser("auth", help="Authenticate with WhatsApp")
    auth_parser.add_argument("--check", action="store_true", help="Check authentication status")
    
    # Send command
    send_parser = subparsers.add_parser("send", help="Send message")
    send_group = send_parser.add_mutually_exclusive_group(required=True)
    send_group.add_argument("--text", help="Send a text message")
    send_group.add_argument("--image", help="Path to image file to send")
    
    send_parser.add_argument("--chat", help="Chat ID to send to (overrides config)")
    send_parser.add_argument("--chats", help="Comma-separated list of chat IDs")
    send_parser.add_argument("--caption", help="Caption for the image (optional)")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Configure settings")
    config_parser.add_argument("--chat-id", help="Set default chat ID")
    config_parser.add_argument("--headless", choices=["true", "false"], 
                             help="Run browser in headless mode")

    # Scheduler command
    scheduler_parser = subparsers.add_parser("scheduler", help="Run message scheduler")
    scheduler_parser.add_argument("--start", action="store_true", help="Start the scheduler")
    scheduler_parser.add_argument("--daemon", action="store_true", help="Run as daemon process")
    
    return parser


def handle_auth(args):
    """Handle authentication commands"""
    auth = WhatsAppAuth()
    
    if args.check:
        is_auth = auth.is_authenticated()
        print(f"WhatsApp authentication status: {'Authenticated' if is_auth else 'Not authenticated'}")
        return
    
    # Default: wait for authentication
    print("Starting WhatsApp authentication process...")
    auth.wait_for_authentication()


def handle_send(args):
    """Handle send commands"""
    sender = WhatsAppSender()    
    # Determine chat recipients
    chat_ids = []
    if args.chats:
        # Split comma-separated list
        chat_ids = [chat.strip() for chat in args.chats.split(',')]
        print(f"Sending to multiple chats: {', '.join(chat_ids)}")
    elif args.chat:
        chat_ids = [args.chat]
    else:
        # Use default from config
        chat_ids = [get_config().get("WhatsApp", "chat_id")]
    
    if args.image:
        # Sending an image
        caption = None
        if args.caption:
            caption = args.caption

        if len(chat_ids) > 1:
            print(f"Sending image to {len(chat_ids)} chats...")
            sender.send_image_to_multiple(chat_ids=chat_ids, image_path=args.image, caption=caption)
        else:
            sender.send_image(chat_id=chat_ids[0], image_path=args.image, caption=caption)
    if args.text:
        # Sending a text message
        print("HEY HEY HEY",args.text)
        message = args.text
        if len(chat_ids) > 1:
            print(f"Sending text message to {len(chat_ids)} chats...")
            sender.send_message_to_multiple(chat_ids=chat_ids, message=message)
        else:
            sender.send_message(chat_id=chat_ids[0], message=message)


def handle_config(args):
    """Handle configuration commands"""
    config = get_config()
    modified = False
    
    if args.chat_id:
        config.set("WhatsApp", "chat_id", args.chat_id)
        print(f"Default chat ID set to: {args.chat_id}")
        modified = True
    
    if args.headless:
        config.set("WhatsApp", "headless", args.headless)
        print(f"Headless mode set to: {args.headless}")
        modified = True
        
    if args.use_images:
        config.set("Content", "use_images", args.use_images)
        print(f"Use images set to: {args.use_images}")
        modified = True
    
    if modified:
        save_config()
        print("Configuration saved.")


def handle_scheduler(args):
    """Handle scheduler command"""
    if args.start:
        print("Starting Zikr scheduler...")
        
        # Handle running as daemon if requested
        if args.daemon:
            try:
                import daemon
                print("Starting scheduler as daemon process")
                with daemon.DaemonContext():
                    scheduler = ZikrScheduler()
                    scheduler.run()
            except ImportError:
                print("Python-daemon package not installed. Running in foreground.")
                scheduler = ZikrScheduler()
                scheduler.run()
        else:
            # Run in foreground
            scheduler = ZikrScheduler()
            scheduler.run()


def main():
    """Main CLI entry point"""
    parser = setup_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Handle commands
    if args.command == "auth":
        handle_auth(args)
    elif args.command == "send":
        handle_send(args)
    elif args.command == "config":
        handle_config(args)
    elif args.command == "scheduler":
        handle_scheduler(args)


if __name__ == "__main__":
    main()
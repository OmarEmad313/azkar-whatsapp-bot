# **WhatsApp Azkar Bot Documentation**

## **Project Overview**

WhatsApp Azkar Bot is an automated solution for sending Islamic remembrances (azkar/zikr) to individuals or groups via WhatsApp at scheduled times. The bot sends morning and evening remembrances during configured time windows, helping Muslims maintain their daily spiritual practices.

### **Key Features**

- Scheduled sending of morning and evening azkar
- Multiple recipient support
- Configurable time windows based on user timezone
- Image-based messages with optional text captions
- Background operation as a daemon or scheduled task
- Monitoring tools to check service status

## **Installation Instructions**

### **Prerequisites**

- Python 3.6+ (Miniconda/Anaconda recommended)
- Google Chrome browser
- Windows OS (for batch scripts as provided, can be adapted for other platforms)

### **Setup Steps**

1. **Clone the repository**
    
    git clone https://github.com/yourusername/azkar-bot.git
    
    cd azkar-bot
    
2. **Create and activate a conda environment**
    
    conda create -n azkar-bot python=3.9
    
    conda activate azkar-bot
    
3. **Install required packages**
    
    pip install selenium webdriver-manager pytz python-daemon configparser
    
4. **Initialize the project**
    
    python main.py
    
    This will create the necessary directory structure.
    
5. **Update configuration** Edit the config.ini file and set your WhatsApp recipients and preferred schedules.

## **Usage Instructions**

### **Initial Authentication**

Before using the bot, you need to authenticate with WhatsApp Web:

python -m interfaces.cli auth

This will open a Chrome window with WhatsApp Web. Scan the QR code with your phone to authenticate. The session will be saved for future use.

### **Send a Test Message**

To verify everything works, send a test message:

python -m interfaces.cli send --recipient "+1234567890" --message "Test from Azkar Bot"

### **Start the Scheduler**

To start the scheduler in the foreground:

python -m interfaces.cli scheduler --start

To run in background (Linux/Mac):

python -m interfaces.cli scheduler --start --daemon

On Windows, use the provided batch script:

start_scheduler.bat

### **Monitor the Scheduler**

Check if the scheduler is running:

python monitor_scheduler.py

To view recent logs:

python monitor_scheduler.py --logs 20

To terminate the scheduler:

python monitor_scheduler.py --kill

## **Configuration Reference**

The bot is configured using config.ini:

### **[General]**

- `debug` - Enable/disable debug logging (true/false)
- headless - Run browser in headless mode (true/false)

### **[WhatsApp]**

- session_dir - Directory for WhatsApp session data
- `chat_id` - Default recipient for messages
- `scheduled_recipients` - Comma-separated list of recipients for scheduled messages
- headless - Whether to run WhatsApp Web in headless mode

### **[Schedule]**

- timezone - Timezone for scheduling (e.g., "Africa/Cairo")
- `morning_start_hour` - Hour to start checking for morning azkar
- `morning_end_hour` - Hour to stop sending morning azkar
- `evening_start_hour` - Hour to start checking for evening azkar
- `evening_end_hour` - Hour to stop sending evening azkar
- check_interval - Seconds between schedule checks

### **[Content]**

- `morning_image` - Path to morning azkar image
- `evening_image` - Path to evening azkar image
- `include_text_caption` - Whether to include text with images

## **API Documentation**

The project does not provide external APIs but includes these core classes:

### **WhatsAppAuth**

Handles authentication with WhatsApp Web.

- __init__(headless=None, session_dir=None) - Initialize with headless mode and session directory
- create_driver() - Create and configure Chrome WebDriver
- is_authenticated() - Check if WhatsApp Web is authenticated
- wait_for_authentication(timeout_minutes=5) - Wait for QR code scan

### **WhatsAppSender**

Sends messages via WhatsApp.

- Main methods for sending text and image messages

### **ZikrScheduler**

Manages the scheduling of azkar messages.

- run() - Run the scheduler loop
- send_morning_zikr() - Check and send morning remembrances
- send_evening_zikr() - Check and send evening remembrances

## **Contributing Guidelines**

1. **Fork the repository**
2. **Create a feature branch**
    
    git checkout -b feature/your-feature-name
    
3. **Make your changes**
4. **Add tests for new functionality**
5. **Ensure all tests pass**
6. **Submit a pull request**

Please adhere to the existing code style and include appropriate documentation.

## **License Information**

This project is recommended to be licensed under the MIT License, which allows for flexibility while ensuring attribution.

To apply the license:

1. Create a LICENSE file in the repository root
2. Add the standard MIT License text with your copyright information
3. Include license headers in source files

## **Testing**

Run tests with:

python -m unittest discover tests

Ensure WhatsApp authentication is set up before running integration tests.

## **Troubleshooting**

### **Common Issues**

1. **Authentication Failures**
    - Ensure Chrome is properly installed
    - Delete the WhatsApp session directory and try again
    - Check for Chrome WebDriver compatibility issues
2. **Scheduler Not Running**
    - Verify process using monitor_scheduler.py
    - Check the scheduler log in scheduler.log
    - Ensure proper permissions for writing to logs directory
3. **Messages Not Sending**
    - Confirm WhatsApp session is authenticated
    - Verify recipient numbers are in correct international format
    - Check internet connection and WhatsApp Web status
4. **Configuration Issues**
    - Ensure all paths in config.ini are absolute paths
    - Verify timezone settings match your region
    - Check that image files exist at specified paths

## **Roadmap**

### **Planned Features**

- Web interface for easier management
- Support for additional messaging platforms
- Custom scheduling patterns
- Database integration for message tracking
- API endpoints for external integration
- Custom azkar content library

## **System Architecture**

The system follows a modular architecture:

1. **Authentication Module** - Handles WhatsApp Web login
2. **Sender Module** - Manages message sending
3. **Scheduler Module** - Controls timing of message delivery
4. **Configuration Module** - Manages user settings
5. **CLI Interface** - Provides command-line controls
6. **Monitoring Tools** - Tracks scheduler status

These components interact through a simple workflow where the scheduler triggers the sender at appropriate times based on configuration settings.

## **Security Considerations**

1. **WhatsApp Session Data**
    - Session data contains sensitive authentication information
    - Ensure whatsapp-session directory has proper permissions
    - Do not share or expose session data
2. **Recipient Privacy**
    - Phone numbers in config files should be protected
    - Consider encrypting configuration files in production
3. **Browser Automation**
    - WebDriver automation carries inherent security risks
    - Keep Chrome and WebDriver updated
    - Run with minimal required permissions

## **Deployment Instructions**

### **For Windows (Production Deployment)**

1. **Set up as a Windows Scheduled Task**
    - Create a task that runs start_scheduler.bat at system startup
    - Configure "Run whether user is logged in or not"
    - Set recovery options to restart on failure
2. **Configure Log Rotation**
    - Implement a log rotation solution to prevent disk space issues
3. **Service Monitoring**
    - Set up periodic checks using Task Scheduler to run monitor_scheduler.py
    - Configure email alerts for failures

### **For Linux/Unix Systems**

1. **Create a System Service**
    - Create a systemd service file for automatic startup
    - Enable automatic restarts on failure
2. **Log Management**
    - Configure logrotate for log management

## **Changelog**

### **v1.0.0 (Initial Release)**

- Basic scheduling functionality
- Morning and evening azkar support
- Multiple recipient messaging
- WhatsApp Web integration
- Windows compatibility
- Monitoring tools
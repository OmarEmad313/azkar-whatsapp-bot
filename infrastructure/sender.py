import time
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from infrastructure.auth import WhatsAppAuth
from infrastructure.config import get_config


class WhatsAppSender:
    """WhatsApp Web message sender"""
    
    def __init__(self):
        self.auth = WhatsAppAuth()
        self.config = get_config()
        self.driver = None
    
    def send_message(self, chat_id=None, message=None):
        """Send WhatsApp message to specified chat using URL method"""
        if not chat_id:
            chat_id = self.config.get("WhatsApp", "chat_id")
        if not message:
            raise ValueError("Message content is required")
        
        # Use auth to ensure we're logged in first
        print("Checking authentication...")
        self.auth.is_authenticated()
        
        options = self._setup_browser_options()
        
        try:
            print("Creating Chrome driver...")
            self.driver = webdriver.Chrome(options=options)
            
            # Navigate directly to WhatsApp
            print("Opening WhatsApp Web...")
            self.driver.get("https://web.whatsapp.com/")
            
            # Wait for WhatsApp to load
            wait = WebDriverWait(self.driver, 60)
            wait.until(EC.presence_of_element_located((By.ID, "side")))
            print("WhatsApp loaded successfully")
            
            # Take a screenshot
            os.makedirs("logs", exist_ok=True)
            self.driver.save_screenshot("logs/whatsapp_loaded.png")
            
            # Use the URL method with encoded message
            from urllib.parse import quote
            encoded_message = quote(message)
            chat_url = f"https://web.whatsapp.com/send?phone={chat_id.strip('+')}&text={encoded_message}"
            print(f"Opening chat with pre-filled text: {chat_url}")
            self.driver.get(chat_url)
            
            # Wait for chat to load
            print("Waiting for chat to load...")
            time.sleep(15)  # Give ample time
            self.driver.save_screenshot("logs/chat_loaded.png")
            
            # Look for the send button with multiple selectors
            print("Looking for send button...")
            send_selectors = [
                '//span[@data-icon="send"]',
                '//button[@aria-label="Send"]',
                '//div[@role="button" and @aria-label="Send"]',
                '//span[@data-testid="send"]'
            ]
            
            send_btn = None
            for selector in send_selectors:
                try:
                    print(f"Trying send button selector: {selector}")
                    send_btn = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    print(f"Found send button with: {selector}")
                    break
                except Exception:
                    continue
            
            if send_btn:
                # Try multiple click methods just like in the image sender
                try:
                    print("Trying direct click...")
                    send_btn.click()
                except Exception as e:
                    print(f"Direct click failed: {e}")
                    try:
                        print("Trying JavaScript click...")
                        self.driver.execute_script("arguments[0].click();", send_btn)
                    except Exception as e:
                        print(f"JavaScript click failed: {e}")
                        try:
                            print("Trying Actions chain click...")
                            from selenium.webdriver.common.action_chains import ActionChains
                            actions = ActionChains(self.driver)
                            actions.move_to_element(send_btn).click().perform()
                        except Exception as e:
                            print(f"Actions chain click failed: {e}")
                            raise ValueError("Could not click send button with any method")
                
                print("Message sent successfully!")
                time.sleep(5)
                self.driver.save_screenshot("logs/message_sent.png")
            else:
                print("Send button not found")
                # Try pressing Enter as final fallback
                try:
                    print("Trying Enter key as fallback...")
                    from selenium.webdriver.common.action_chains import ActionChains
                    actions = ActionChains(self.driver)
                    actions.send_keys(Keys.ENTER)
                    actions.perform()
                    print("Message possibly sent using Enter key")
                    time.sleep(5)
                except Exception as e:
                    print(f"Enter key fallback failed: {e}")
                    raise ValueError("Could not send message - no send button found and Enter key failed")
            
        except Exception as e:
            print(f"Error during message sending: {e}")
            if self.driver:
                self.driver.save_screenshot("logs/send_error.png")
        finally:
            if self.driver:
                print("Closing browser")
                self.driver.quit()
                self.driver = None

    def send_image(self, chat_id=None, image_path=None, caption=None):
        """Send image via WhatsApp"""
        if not chat_id:
            chat_id = self.config.get("WhatsApp", "chat_id")
        
        # Better image path validation with debugging
        if not image_path:
            raise ValueError("Image path is required")
        
        # Convert to absolute path and normalize
        image_path = os.path.abspath(os.path.expanduser(image_path))
        
        # Debug print to help troubleshoot
        print(f"Checking image path: {image_path}")
        
        if not os.path.exists(image_path):
            # More descriptive error message
            raise ValueError(f"Image file not found: {image_path}")
        
        # Use auth to ensure we're logged in first
        print("Checking authentication...")
        self.auth.is_authenticated()
        
        options = self._setup_browser_options()
        
        try:
            print("Creating Chrome driver...")
            self.driver = webdriver.Chrome(options=options)
            
            # Navigate directly to the specific chat
            chat_url = f"https://web.whatsapp.com/send?phone={chat_id.strip('+')}"
            print(f"Opening chat: {chat_url}")
            self.driver.get(chat_url)
            
            # Wait for WhatsApp to load
            wait = WebDriverWait(self.driver, 60)
            wait.until(EC.presence_of_element_located((By.ID, "side")))
            print("WhatsApp loaded successfully")
            
            # Wait for chat to load
            print("Waiting for chat to load...")
            time.sleep(10)
            self.driver.save_screenshot("logs/chat_loaded.png")
            
            # Try multiple possible selectors for the attachment button
            print("Looking for attachment button...")
            attachment_selectors = [
                # New selectors based on current HTML
                '//button[@title="Attach"]',
                '//button[@data-tab="10"]',
                '//button[contains(@class, "xjb2p0i")]',
                '//span[@data-icon="plus"]/parent::button',
                # Keep some of the old selectors as fallback
                '//div[@title="Attach"]',
                '//div[@aria-label="Attach"]',
                '//span[@data-icon="clip"]',
            ]
            
            attachment_btn = None
            for selector in attachment_selectors:
                try:
                    print(f"Trying selector: {selector}")
                    # Add a longer wait time for the button
                    attachment_btn = WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    # Try to ensure the button is actually clickable
                    WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    print(f"Found attachment button with selector: {selector}")
                    break
                except Exception as e:
                    print(f"Selector failed: {selector}")
                    continue
            
            if not attachment_btn:
                raise ValueError("Could not find attachment button with any known selector")
            
            # Take screenshot before clicking
            self.driver.save_screenshot("logs/before_attachment_click.png")
            
            # Try multiple click methods
            try:
                print("Trying direct click...")
                attachment_btn.click()
            except Exception as e:
                print(f"Direct click failed: {e}")
                try:
                    print("Trying JavaScript click...")
                    self.driver.execute_script("arguments[0].click();", attachment_btn)
                except Exception as e:
                    print(f"JavaScript click failed: {e}")
                    try:
                        print("Trying Actions chain click...")
                        from selenium.webdriver.common.action_chains import ActionChains
                        actions = ActionChains(self.driver)
                        actions.move_to_element(attachment_btn).click().perform()
                    except Exception as e:
                        print(f"Actions chain click failed: {e}")
                        raise ValueError("Could not click attachment button with any method")
            
            # Add a longer wait after clicking
            time.sleep(3)
            self.driver.save_screenshot("logs/after_attachment_click.png")
            
            # Try multiple input selectors
            print("Looking for image input...")
            input_selectors = [
                '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]',
                '//input[@accept="*"]',
                '//input[@type="file"]'
            ]
            
            image_input = None
            for selector in input_selectors:
                try:
                    print(f"Trying input selector: {selector}")
                    image_input = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                    print(f"Found image input with selector: {selector}")
                    break
                except Exception as e:
                    print(f"Input selector failed: {selector}")
                    continue
            
            if not image_input:
                raise ValueError("Could not find image input with any known selector")
            
            # Send the file path directly to the input element
            print(f"Attaching image: {image_path}")
            image_input.send_keys(image_path)
            
            # Wait for image to upload and show preview
            print("Waiting for image to upload...")
            time.sleep(5)
            self.driver.save_screenshot("logs/image_uploaded.png")
            
            # Add caption if needed
            if caption:
                print("Adding caption...")
                caption_selector_options = [
                    '//div[contains(@class, "copyable-text selectable-text")][@data-tab="10"]',
                    '//div[contains(@class, "copyable-text")][@contenteditable="true"]',
                    '//div[@role="textbox"]'
                ]
                
                caption_field = None
                for selector in caption_selector_options:
                    try:
                        caption_field = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                        break
                    except:
                        continue
                
                if caption_field:
                    caption_field.click()
                    time.sleep(1)
                    caption_field.send_keys(caption)
                    time.sleep(1)
                else:
                    print("Caption field not found, continuing without caption")
            
            # Find send button
            print("Looking for send button...")
            send_selectors = [
                '//span[@data-icon="send"]',
                '//button[@aria-label="Send"]',
                '//div[@role="button" and @aria-label="Send"]',
                '//span[@data-testid="send"]'
            ]
            
            send_btn = None
            for selector in send_selectors:
                try:
                    send_btn = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    print(f"Found send button with selector: {selector}")
                    break
                except:
                    continue
            
            if not send_btn:
                raise ValueError("Could not find send button")
            
            print("Sending image...")
            self.driver.execute_script("arguments[0].click();", send_btn)
            
            # Wait to confirm sending
            time.sleep(5)
            self.driver.save_screenshot("logs/image_sent.png")
            print("Image sent successfully!")
            
        except Exception as e:
            print(f"Error sending image: {e}")
            if self.driver:
                self.driver.save_screenshot("logs/image_error.png")
        finally:
            if self.driver:
                print("Closing browser")
                self.driver.quit()
                self.driver = None

    def send_message_to_multiple(self, chat_ids, message):
        """Send the same message to multiple chat IDs using URL method"""
        if not chat_ids:
            raise ValueError("At least one chat ID is required")
        if not message:
            raise ValueError("Message content is required")
        
        # Initialize browser once
        options = self._setup_browser_options()
        try:
            print("Creating Chrome driver (one-time for multiple chats)...")
            self.driver = webdriver.Chrome(options=options)
            
            # Navigate to WhatsApp Web once
            print("Opening WhatsApp Web...")
            self.driver.get("https://web.whatsapp.com/")
            
            # Wait for WhatsApp to load
            wait = WebDriverWait(self.driver, 60)
            wait.until(EC.presence_of_element_located((By.ID, "side")))
            print("WhatsApp loaded successfully")
            
            # Use the URL method for all chats
            for i, chat_id in enumerate(chat_ids):
                try:
                    print(f"Processing recipient {i+1}/{len(chat_ids)}: {chat_id}")
                    
                    # Use the URL method with encoded message
                    from urllib.parse import quote
                    encoded_message = quote(message)
                    chat_url = f"https://web.whatsapp.com/send?phone={chat_id.strip('+')}&text={encoded_message}"
                    print(f"Opening chat with pre-filled text: {chat_url}")
                    self.driver.get(chat_url)
                    
                    # Wait for chat to load
                    print("Waiting for chat to load...")
                    time.sleep(15)
                    self.driver.save_screenshot(f"logs/chat_{i+1}_loaded.png")
                    
                    # Look for the send button with multiple selectors
                    print("Looking for send button...")
                    send_selectors = [
                        '//span[@data-icon="send"]',
                        '//button[@aria-label="Send"]',
                        '//div[@role="button" and @aria-label="Send"]',
                        '//span[@data-testid="send"]'
                    ]
                    
                    send_btn = None
                    for selector in send_selectors:
                        try:
                            print(f"Trying send button selector: {selector}")
                            send_btn = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                            print(f"Found send button with: {selector}")
                            break
                        except Exception:
                            continue
                    
                    if send_btn:
                        # Try multiple click methods
                        try:
                            print("Trying direct click...")
                            send_btn.click()
                        except Exception as e:
                            print(f"Direct click failed: {e}")
                            try:
                                print("Trying JavaScript click...")
                                self.driver.execute_script("arguments[0].click();", send_btn)
                            except Exception as e:
                                print(f"JavaScript click failed: {e}")
                                try:
                                    print("Trying Actions chain click...")
                                    from selenium.webdriver.common.action_chains import ActionChains
                                    actions = ActionChains(self.driver)
                                    actions.move_to_element(send_btn).click().perform()
                                except Exception as e:
                                    print(f"Actions chain click failed: {e}")
                                    print(f"⚠️ Could not send to {chat_id} - all click methods failed")
                                    continue
                    
                        print(f"✓ Message sent to {chat_id}")
                        time.sleep(3)  # Wait before moving to next recipient
                        self.driver.save_screenshot(f"logs/message_sent_{i+1}.png")
                    else:
                        print(f"⚠️ Send button not found for {chat_id}")
                        # Try pressing Enter as final fallback
                        try:
                            print("Trying Enter key as fallback...")
                            from selenium.webdriver.common.action_chains import ActionChains
                            actions = ActionChains(self.driver)
                            actions.send_keys(Keys.ENTER)
                            actions.perform()
                            print(f"Enter key pressed for {chat_id}")
                            time.sleep(3)
                        except Exception as e:
                            print(f"Enter key fallback failed: {e}")
                            print(f"⚠️ Could not send to {chat_id} - no send button found and Enter key failed")
                    
                except Exception as e:
                    print(f"⚠️ Failed to send to {chat_id}: {e}")
                    self.driver.save_screenshot(f"logs/error_chat_{i+1}.png")
                    # Continue with next recipient
        
        except Exception as e:
            print(f"Error during batch message sending: {e}")
            if self.driver:
                self.driver.save_screenshot("logs/batch_send_error.png")
        finally:
            if self.driver:
                print("Closing browser")
                self.driver.quit()
                self.driver = None

    def send_image_to_multiple(self, chat_ids, image_path, caption=None):
        """Send the same image to multiple chat IDs in a single browser session"""
        if not chat_ids:
            raise ValueError("At least one chat ID is required")
        
        # Validate image path
        if not image_path:
            raise ValueError("Image path is required")
        
        # Convert to absolute path and normalize
        image_path = os.path.abspath(os.path.expanduser(image_path))
        print(f"Using image: {image_path}")
        
        if not os.path.exists(image_path):
            raise ValueError(f"Image file not found: {image_path}")
        
        # Initialize browser once
        options = self._setup_browser_options()
        try:
            print(f"Creating Chrome driver for sending image to {len(chat_ids)} chats...")
            self.driver = webdriver.Chrome(options=options)
            
            # Navigate to WhatsApp Web once
            print("Opening WhatsApp Web...")
            self.driver.get("https://web.whatsapp.com/")
            
            # Wait for WhatsApp to load
            wait = WebDriverWait(self.driver, 60)
            wait.until(EC.presence_of_element_located((By.ID, "side")))
            print("WhatsApp loaded successfully")
            
            # Send to each chat
            for i, chat_id in enumerate(chat_ids):
                try:
                    print(f"Processing recipient {i+1}/{len(chat_ids)}: {chat_id}")
                    
                    # Navigate to specific chat
                    chat_url = f"https://web.whatsapp.com/send?phone={chat_id.strip('+')}"
                    self.driver.get(chat_url)
                    
                    # Wait for chat to load
                    print("Waiting for chat to load...")
                    time.sleep(10)
                    
                    # Try multiple possible selectors for the attachment button
                    print("Looking for attachment button...")
                    attachment_selectors = [
                        '//button[@title="Attach"]',
                        '//button[@data-tab="10"]',
                        '//span[@data-icon="attach-menu-plus"]/parent::button',
                        '//span[@data-icon="plus"]/parent::button',
                        '//div[@title="Attach"]',
                        '//div[@aria-label="Attach"]',
                    ]
                    
                    attachment_btn = None
                    for selector in attachment_selectors:
                        try:
                            attachment_btn = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                            print(f"Found attachment button with: {selector}")
                            break
                        except Exception as e:
                            continue
                    
                    if not attachment_btn:
                        print(f"⚠️ Could not find attachment button for {chat_id}, skipping")
                        continue
                    
                    # Click attachment button (try multiple methods)
                    try:
                        attachment_btn.click()
                    except Exception:
                        try:
                            self.driver.execute_script("arguments[0].click();", attachment_btn)
                        except Exception:
                            from selenium.webdriver.common.action_chains import ActionChains
                            actions = ActionChains(self.driver)
                            actions.move_to_element(attachment_btn).click().perform()
                    
                    # Wait for attachment options to appear
                    time.sleep(2)
                    
                    # Look for file input
                    input_selectors = [
                        '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]',
                        '//input[@type="file"]'
                    ]
                    
                    image_input = None
                    for selector in input_selectors:
                        try:
                            image_input = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                            break
                        except:
                            continue
                    
                    if not image_input:
                        print(f"⚠️ Could not find image input for {chat_id}, skipping")
                        continue
                    
                    # Upload image
                    image_input.send_keys(image_path)
                    print("Image attached, waiting for upload...")
                    time.sleep(4)
                    
                    # Add caption if provided
                    if caption:
                        caption_selectors = [
                            '//div[@contenteditable="true"][@data-tab="10"]',
                            '//div[contains(@class,"copyable-text selectable-text")][@contenteditable="true"]',
                            '//div[@role="textbox"]'
                        ]
                        
                        caption_field = None
                        for selector in caption_selectors:
                            try:
                                caption_field = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                                break
                            except:
                                continue
                        
                        if caption_field:
                            caption_field.click()
                            time.sleep(1)
                            for char in caption:
                                caption_field.send_keys(char)
                                time.sleep(0.01)
                        else:
                            print("Caption field not found, continuing without caption")
                    
                    # Find and click send button
                    send_selectors = [
                        '//span[@data-icon="send"]',
                        '//button[@aria-label="Send"]',
                        '//div[@role="button" and @aria-label="Send"]'
                    ]
                    
                    send_btn = None
                    for selector in send_selectors:
                        try:
                            send_btn = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                            break
                        except:
                            continue
                    
                    if not send_btn:
                        print(f"⚠️ Could not find send button for {chat_id}, skipping")
                        continue
                    
                    # Send the image
                    self.driver.execute_script("arguments[0].click();", send_btn)
                    print(f"✓ Image sent to {chat_id}")
                    
                    # Wait before processing next recipient
                    time.sleep(4)
                    
                except Exception as e:
                    print(f"⚠️ Failed to send image to {chat_id}: {e}")
    
        except Exception as e:
            print(f"Error during batch image sending: {e}")
            if self.driver:
                self.driver.save_screenshot("logs/batch_image_error.png")
        finally:
            if self.driver:
                print("Closing browser")
                self.driver.quit()
                self.driver = None

    def _setup_browser_options(self):
        """Set up common browser options"""
        options = webdriver.ChromeOptions()
        
        # Check headless setting from config
        headless = self.config.get("WhatsApp", "headless", fallback="true") == "true"
        if headless:
            options.add_argument("--headless")
            print("Running in headless mode")
        else:
            print("Running in visible mode")
        
        # Disable features that might cause problems
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        
        # Explicitly disable hardware acceleration
        options.add_argument("--disable-accelerated-2d-canvas")
        options.add_argument("--disable-accelerated-jpeg-decoding")
        options.add_argument("--disable-accelerated-mjpeg-decode")
        options.add_argument("--disable-accelerated-video-decode")
        options.add_argument("--disable-gpu-compositing")
        
        # Add SSL options
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--allow-insecure-localhost")
        
        # Set window size
        options.add_argument("--window-size=1280,800")
        
        # Use persistent session
        session_dir = self.config.get("WhatsApp", "session_dir", fallback="./whatsapp-session")
        session_path = Path(session_dir).absolute()
        session_path.mkdir(exist_ok=True)
        options.add_argument(f"user-data-dir={session_path}")
        
        return options
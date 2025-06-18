from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
import os
import logging
from datetime import datetime
import random

class AnyElementVisible:
    """
    Custom expected condition to wait for any one of a list of elements to be visible.
    """
    def __init__(self, locators_with_types):
        # locators_with_types should be a list of tuples, e.g., [(By.CSS_SELECTOR, ".class1"), (By.ID, "id2")]
        self.locators_with_types = locators_with_types
        self.found_locator_info = None

    def __call__(self, driver):
        for by, locator_str in self.locators_with_types:
            try:
                element = driver.find_element(by, locator_str)
                if element.is_displayed():
                    self.found_locator_info = f"{by}='{locator_str}'"
                    # print(f"✓ Found visible course content with indicator: {self.found_locator_info}") # Optional: print here
                    return element  # Return the first visible element found
            except (NoSuchElementException, StaleElementReferenceException):
                continue
        return False

def handle_consent_popup(driver):
    """
    Handle Google consent/agreement popup after successful login
    """
    try:
        print("=== Handling Consent Popup ===")
        
        # Wait a moment for popup to appear
        time.sleep(2)
        
        # Multiple strategies to find and click consent button
        consent_strategies = [
            # Strategy 1: By input type and value
            ("input[type='submit'][value='Tôi hiểu']", "css"),
            ("input[type='submit'][value*='hiểu']", "css"),
            ("input[type='submit'][value*='đồng ý']", "css"),
            
            # Strategy 2: By XPath with text
            ("//input[@value='Tôi hiểu']", "xpath"),
            ("//button[contains(text(), 'Tôi hiểu')]", "xpath"),
            ("//input[@value[contains(., 'hiểu')]]", "xpath"),
            
            # Strategy 3: By classes from your HTML
            ("input.MK9CEd.MVpUfe", "css"),
            ("input[jsname='M2UYVd']", "css"),
            ("input[jscontroller='VXdfxd']", "css"),
            
            # Strategy 4: Generic submit buttons
            ("input[type='submit']", "css"),
            ("button[type='submit']", "css"),
            
            # Strategy 5: By form context
            ("form input[type='submit']", "css"),
            ("form button[type='submit']", "css")
        ]
        
        consent_clicked = False
        
        for selector, method in consent_strategies:
            try:
                print(f"Trying selector: {selector}")
                
                if method == "xpath":
                    elements = driver.find_elements(By.XPATH, selector)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    try:
                        # Check if element is visible and interactable
                        if element.is_displayed() and element.is_enabled():
                            
                            # Get button text/value to verify it's the right button
                            button_text = (element.get_attribute('value') or 
                                         element.text or 
                                         element.get_attribute('aria-label') or '').lower()
                            
                            print(f"Found button with text: '{button_text}'")
                            
                            # Check if it's likely a consent button
                            consent_keywords = ['hiểu', 'đồng ý', 'agree', 'accept', 'continue', 'ok']
                            if any(keyword in button_text for keyword in consent_keywords) or not button_text:
                                
                                print(f"✓ Clicking consent button: '{button_text}'")
                                
                                # Scroll to element
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(0.5)
                                
                                # Try to click
                                try:
                                    element.click()
                                    print("✓ Successfully clicked with regular click")
                                except:
                                    try:
                                        driver.execute_script("arguments[0].click();", element)
                                        print("✓ Successfully clicked with JavaScript")
                                    except:
                                        continue
                                
                                consent_clicked = True
                                break
                                
                    except Exception as e:
                        print(f"Error with element: {e}")
                        continue
                
                if consent_clicked:
                    break
                    
            except Exception as e:
                print(f"Strategy failed: {selector} - {e}")
                continue
        
        if consent_clicked:
            print("✓ Consent popup handled successfully")
            time.sleep(3)  # Wait for page to process
            
            # Check final URL
            final_url = driver.current_url
            print(f"Final URL after consent: {final_url}")
            
            return True
        else:
            print("No consent popup found or couldn't click it")
            return False
            
    except Exception as e:
        print(f"Error in consent handling: {e}")
        return False

def handle_oauth_consent(driver):
    """
    Handle Google OAuth consent popup with Continue/Cancel buttons
    """
    try:
        print("=== Handling OAuth Consent Popup ===")
        
        # Wait for the consent popup to appear
        time.sleep(2)
        
        # Check if we're on Google consent page
        current_url = driver.current_url
        if 'accounts.google.com' not in current_url:
            print("Not on Google consent page")
            return False
        
        # Look for the consent dialog
        consent_dialog_selectors = [
            "div[role='dialog']",
            ".VfPpkd-Jh9lGc",  # Based on your HTML
            "[data-is-touch-wrapper='true']",
            ".oauth-consent-dialog"
        ]
        
        dialog_found = False
        for selector in consent_dialog_selectors:
            try:
                dialog = driver.find_element(By.CSS_SELECTOR, selector)
                if dialog.is_displayed():
                    print(f"✓ Found consent dialog with selector: {selector}")
                    dialog_found = True
                    break
            except:
                continue
        
        if not dialog_found:
            print("Consent dialog not found")
            return False
        
        # Multiple strategies to find Continue button
        continue_strategies = [
            # Strategy 1: By button text (most reliable)
            ("//button[contains(text(), 'Continue')]", "xpath"),
            ("//button[contains(text(), 'Tiếp tục')]", "xpath"),  # Vietnamese
            ("//span[contains(text(), 'Continue')]/parent::button", "xpath"),
            ("//div[contains(text(), 'Continue')]/parent::button", "xpath"),
            
            # Strategy 2: By specific classes from your HTML (blue Continue button)
            ("button.VfPpkd-LgbsSe.VfPpkd-LgbsSe-OWXEXe-INsAgc", "css"),  # Blue button
            ("button.VfPpkd-LgbsSe-OWXEXe-dgl2Hf.Rj2Mlf.OLiIxf.PDpWxe.P62QJc.LQeN7.BqKGqe.pIzcPc.TrZEUc.lw1w4b", "css"),
            ("div.VfPpkd-Jh9lGc button:last-child", "css"),  # Last button in dialog (usually Continue)
            
            # Strategy 3: By button position and color
            ("button[style*='background']", "css"),  # Colored buttons
            ("button[jscontroller='soHxf']", "css"),  # Material Design button controller
            ("button[jsname='LgbsSe']:not([style*='Cancel'])", "css"),
            
            # Strategy 4: Generic approaches
            ("div[role='dialog'] button:nth-last-child(1)", "css"),  # Last button in dialog
            ("div[role='dialog'] button[type='button']:last-of-type", "css"),
            (".VfPpkd-Jh9lGc button:not(:first-child)", "css"),  # Not the first button (Cancel)
        ]
        
        continue_clicked = False
        
        for selector, method in continue_strategies:
            try:
                print(f"Trying Continue button selector: {selector}")
                
                if method == "xpath":
                    buttons = driver.find_elements(By.XPATH, selector)
                else:
                    buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for button in buttons:
                    try:
                        # Check if button is visible and enabled
                        if button.is_displayed() and button.is_enabled():
                            
                            # Get button text and attributes
                            button_text = (button.text or 
                                         button.get_attribute('aria-label') or 
                                         button.get_attribute('title') or '').lower().strip()
                            
                            button_html = button.get_attribute('outerHTML').lower()
                            
                            print(f"Found button with text: '{button_text}'")
                            
                            # More precise identification of Continue button
                            is_continue_button = False
                            
                            # Check by text content
                            if button_text in ['continue', 'tiếp tục', 'đồng ý']:
                                is_continue_button = True
                                print("✓ Identified as Continue button by text")
                            
                            # Check if it's likely Continue (not Cancel)
                            elif ('cancel' not in button_text and 'hủy' not in button_text and 
                                  ('continue' in selector.lower() or 'last' in selector or 
                                   'blue' in selector or button_text == '')):
                                is_continue_button = True
                                print("✓ Identified as Continue button by position/style")
                            
                            # Additional check: Continue button is usually styled differently
                            elif ('background' in button_html or 'color' in button_html):
                                if 'cancel' not in button_text and 'hủy' not in button_text:
                                    is_continue_button = True
                                    print("✓ Identified as Continue button by styling")
                            
                            if is_continue_button:
                                print(f"✓ Clicking Continue button: '{button_text or 'styled button'}'")
                                
                                # Scroll to button to ensure it's in view
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                                time.sleep(0.5)
                                
                                # Highlight button briefly (for debugging)
                                try:
                                    driver.execute_script("arguments[0].style.border='3px solid red';", button)
                                    time.sleep(0.5)
                                    driver.execute_script("arguments[0].style.border='';", button)
                                except:
                                    pass
                                
                                # Try multiple click methods
                                click_success = False
                                
                                # Method 1: Regular click
                                try:
                                    button.click()
                                    click_success = True
                                    print("✓ Successfully clicked with regular click")
                                except Exception as e:
                                    print(f"Regular click failed: {e}")
                                
                                # Method 2: JavaScript click
                                if not click_success:
                                    try:
                                        driver.execute_script("arguments[0].click();", button)
                                        click_success = True
                                        print("✓ Successfully clicked with JavaScript")
                                    except Exception as e:
                                        print(f"JavaScript click failed: {e}")
                                
                                # Method 3: Action chains click
                                if not click_success:
                                    try:
                                        ActionChains(driver).move_to_element(button).click().perform()
                                        click_success = True
                                        print("✓ Successfully clicked with ActionChains")
                                    except Exception as e:
                                        print(f"ActionChains click failed: {e}")
                                
                                if click_success:
                                    continue_clicked = True
                                    break
                                
                    except Exception as e:
                        print(f"Error processing button: {e}")
                        continue
                
                if continue_clicked:
                    break
                    
            except Exception as e:
                print(f"Continue button strategy failed: {selector} - {e}")
                continue
        
        if continue_clicked:
            print("✓ OAuth consent Continue button clicked successfully")
            
            # Wait for redirect back to OpenEdu
            print("Waiting for redirect back to OpenEdu...")
            
            for i in range(15):  # Wait up to 15 seconds
                time.sleep(1)
                current_url = driver.current_url
                print(f"Current URL: {current_url}")
                
                if 'openedu' in current_url.lower():
                    print("🎉 Successfully redirected back to OpenEdu!")
                    return True
                elif i == 14:
                    print("Redirect taking longer than expected...")
            
            return True # Assuming success if OAuth redirect is slow but login was ok
        else:
            print("❌ Could not find or click Continue button")
            
            # Take screenshot for debugging
            driver.save_screenshot("oauth_consent_debug.png")
            print("Screenshot saved for debugging OAuth consent")
            
            return False
            
    except Exception as e:
        print(f"Error in OAuth consent handling: {e}")
        return False

def handle_two_step_consent_process(driver):
    """
    Handle the complete two-step consent process:
    1. First: "Tôi hiểu" button (Vietnamese consent)
    2. Second: "Continue" button (OAuth consent)
    """
    try:
        print("=== HANDLING TWO-STEP CONSENT PROCESS ===")
        
        # STEP 1: Handle "Tôi hiểu" consent popup
        print("\n--- STEP 1: Looking for 'Tôi hiểu' popup ---")
        step1_success = handle_consent_popup(driver)
        
        if step1_success:
            print("✅ STEP 1 completed: 'Tôi hiểu' button clicked")
            time.sleep(4)  # Wait for OAuth popup to appear
        else:
            print("⚠️  STEP 1: No 'Tôi hiểu' popup found, proceeding to step 2")
        
        # STEP 2: Handle "Continue" OAuth consent popup  
        print("\n--- STEP 2: Looking for OAuth 'Continue' popup ---")
        step2_success = handle_oauth_consent(driver)
        
        if step2_success:
            print("✅ STEP 2 completed: 'Continue' button clicked")
            time.sleep(3)
        else:
            print("⚠️  STEP 2: No 'Continue' popup found")
        
        # Final verification
        final_url = driver.current_url
        print(f"\n🎯 Final URL after two-step consent: {final_url}")
        
        if 'openedu' in final_url.lower():
            print("🎉 SUCCESS: Returned to OpenEdu after complete consent process!")
            return True
        elif 'google' in final_url.lower():
            print("⚠️  Still on Google page - may need manual intervention")
            return False
        else:
            print(f"❓ Unexpected final destination: {final_url}")
            return False
            
    except Exception as e:
        print(f"❌ Error in two-step consent process: {e}")
        return False

def access_openedu_course():
    # URL to access
    url = "https://openedu.net/vi/courses/ai-mastery-lam-chu-tuong-lai-tang-nang-suat-gap-x-chi-trong-ngay-90668?ref_by=ASCAwBpPnx5OWIlO"
    
    # Chrome options for better compatibility
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Set user agent to appear more like a real browser
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Additional headless optimizations
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Execute script to avoid detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Navigate to the website
        print(f"Accessing: {url}")
        driver.get(url)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        
        # Wait for the page to fully load by checking for common elements
        try:
            # Wait for the course title or main content to load
            course_element = wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            print("Page loaded successfully!")
            
            # Get page title
            page_title = driver.title
            print(f"Page title: {page_title}")
            
            # Example: Find and print course information
            try:
                # Look for course title
                course_title = driver.find_element(By.TAG_NAME, "h1").text
                print(f"Course title: {course_title}")
            except:
                print("Could not find course title")
            
            # Example: Find course description or other elements
            try:
                # Look for course description (this selector might need adjustment)
                description_elements = driver.find_elements(By.CSS_SELECTOR, "p, .description, .course-description")
                if description_elements:
                    print("Course description found:")
                    for elem in description_elements[:3]:  # Print first 3 paragraphs
                        text = elem.text.strip()
                        if text:
                            print(f"- {text[:100]}...")
            except:
                print("Could not find course description")
            
            # Example: Find enrollment button or course access elements
            try:
                buttons = driver.find_elements(By.CSS_SELECTOR, "button, .btn, a[href*='enroll'], a[href*='register']")
                if buttons:
                    print("Found interactive elements:")
                    for button in buttons[:5]:  # Show first 5 buttons
                        text = button.text.strip()
                        if text:
                            print(f"- Button: {text}")
            except:
                print("Could not find buttons")
            
            # Take a screenshot (optional)
            driver.save_screenshot("openedu_course_page.png")
            print("Screenshot saved as 'openedu_course_page.png'")
            
            # Wait a bit to see the page (if running with GUI)
            time.sleep(3)
            
        except Exception as e:
            print(f"Error waiting for page elements: {e}")
            
    except Exception as e:
        print(f"Error occurred: {e}")
        
    finally:
        # Close the browser
        try:
            driver.quit()
            print("Browser closed successfully")
        except:
            pass

def interact_with_course_page():
    """
    More advanced example with specific interactions
    """
    url = "https://openedu.net/vi/courses/ai-mastery-lam-chu-tuong-lai-tang-nang-suat-gap-x-chi-trong-ngay-90668?ref_by=ASCAwBpPnx5OWIlO"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Additional headless optimizations
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        
        wait = WebDriverWait(driver, 10)
        
        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Example: Scroll down to load more content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        
                    # Click on "Đăng nhập để học" button
        try:
            # Wait for the login button to be present and clickable
            login_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Đăng nhập để học')]"))
            )
            print("Found 'Đăng nhập để học' button")
            
            # Scroll to the button to ensure it's visible
            driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
            time.sleep(1)
            
            # Click the button
            login_button.click()
            print("Successfully clicked 'Đăng nhập để học' button")
            
            # Wait for the login form or redirect to appear
            time.sleep(3)
            
            # Check if we're redirected to login page
            current_url = driver.current_url
            print(f"Current URL after click: {current_url}")
            
            # Look for login form elements
            try:
                login_form = driver.find_element(By.CSS_SELECTOR, "form, .login-form, input[type='email'], input[type='password']")
                print("Login form detected on the page")
            except:
                print("No login form found - might have been redirected or popup appeared")
                
        except Exception as e:
            print(f"Could not find or click 'Đăng nhập để học' button: {e}")
            
            # Alternative: Try finding button by class or data attributes
            try:
                alternative_selectors = [
                    "button[data-action='loginRequired']",
                    "button.bg-primary",
                    "button[type='button']",
                    ".btn-primary"
                ]
                
                for selector in alternative_selectors:
                    try:
                        alt_button = driver.find_element(By.CSS_SELECTOR, selector)
                        if "đăng nhập" in alt_button.text.lower() or "học" in alt_button.text.lower():
                            print(f"Found alternative button with selector: {selector}")
                            alt_button.click()
                            print("Successfully clicked alternative button")
                            time.sleep(3)
                            break
                    except:
                        continue
                        
            except Exception as alt_e:
                print(f"Alternative button search also failed: {alt_e}")
        
        # Extract all text content from the page
        page_text = driver.find_element(By.TAG_NAME, "body").text
        print(f"Page content length: {len(page_text)} characters")
        
        # Save page source for analysis
        with open("openedu_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("Page source saved to 'openedu_page_source.html'")
        
        time.sleep(5)
        
    except Exception as e:
        print(f"Error in interaction: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass

def click_login_button():
    """
    Specific function to click the 'Đăng nhập để học' button
    """
    url = "https://openedu.net/vi/courses/ai-mastery-lam-chu-tuong-lai-tang-nang-suat-gap-x-chi-trong-ngay-90668?ref_by=ASCAwBpPnx5OWIlO"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Additional headless optimizations
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print(f"Loading page: {url}")
        driver.get(url)
        
        wait = WebDriverWait(driver, 15)
        
        # Wait for page to load completely
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)
        
        # Multiple strategies to find and click the login button
        button_found = False
        
        # Strategy 1: Find by exact text
        try:
            login_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Đăng nhập để học')]"))
            )
            print("Strategy 1: Found button by text")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", login_button)
            time.sleep(1)
            login_button.click()
            button_found = True
            print("✓ Successfully clicked 'Đăng nhập để học' button using Strategy 1")
        except:
            print("Strategy 1 failed")
        
        # Strategy 2: Find by data attributes (based on the HTML you showed)
        if not button_found:
            try:
                login_button = driver.find_element(By.CSS_SELECTOR, "button[data-action='loginRequired']")
                print("Strategy 2: Found button by data-action attribute")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", login_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", login_button) # Using JS click
                button_found = True
                print("✓ Successfully clicked button using Strategy 2")
            except:
                print("Strategy 2 failed")
        
        # Strategy 3: Find by class names
        if not button_found:
            try:
                selectors = [
                    "button.bg-primary",
                    "button.text-primary-foreground", 
                    "button[type='button'].bg-primary",
                    ".bg-primary[data-action]"
                ]
                
                for selector in selectors:
                    try:
                        login_button = driver.find_element(By.CSS_SELECTOR, selector)
                        button_text = login_button.text.lower()
                        if any(word in button_text for word in ['đăng nhập', 'học', 'login']):
                            print(f"Strategy 3: Found button with selector: {selector}")
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", login_button)
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", login_button) # Using JS click
                            button_found = True
                            print("✓ Successfully clicked button using Strategy 3")
                            break
                    except:
                        continue
                        
            except Exception as e:
                print(f"Strategy 3 failed: {e}")
        
        # Strategy 4: Find all buttons and filter by text
        if not button_found:
            try:
                all_buttons = driver.find_elements(By.TAG_NAME, "button")
                for button in all_buttons:
                    try:
                        button_text = button.text.lower()
                        if 'đăng nhập' in button_text and 'học' in button_text:
                            print("Strategy 4: Found button by scanning all buttons")
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", button) # Using JS click
                            button_found = True
                            print("✓ Successfully clicked button using Strategy 4")
                            break
                    except:
                        continue
            except Exception as e:
                print(f"Strategy 4 failed: {e}")
        
        if button_found:
            # Wait for response after clicking
            time.sleep(5)
            
            # Check what happened after clicking
            current_url = driver.current_url
            print(f"Current URL after clicking: {current_url}")
            
            # Look for login form or any changes
            try:
                # Check if there's a login form
                login_elements = driver.find_elements(By.CSS_SELECTOR, 
                    "input[type='email'], input[type='password'], .login-form, form")
                
                if login_elements:
                    print("✓ Login form appeared - button click was successful!")
                    
                    # Look for Google login button
                    try:
                        # Multiple strategies to find Google login button
                        google_login_found = False
                        
                        # Strategy 1: Find by text content
                        google_selectors = [
                            "//button[contains(text(), 'Đăng nhập với Google')]",
                            "//button[contains(text(), 'Google')]",
                            "//a[contains(text(), 'Đăng nhập với Google')]",
                            "//div[contains(text(), 'Đăng nhập với Google')]"
                        ]
                        
                        for selector in google_selectors:
                            try:
                                google_button = driver.find_element(By.XPATH, selector)
                                print(f"Found Google login button with selector: {selector}")
                                
                                # Scroll to button and click
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", google_button)
                                time.sleep(1)
                                google_button.click()
                                google_login_found = True
                                print("✓ Successfully clicked 'Đăng nhập với Google' button")
                                break
                            except:
                                continue
                        
                        # Strategy 2: Find by CSS classes or attributes
                        if not google_login_found:
                            css_selectors = [
                                "button[class*='google']",
                                "button[data-provider='google']",
                                ".google-login",
                                "button:has(img[alt*='Google'])",
                                "button:has(svg)",  # Google buttons often have SVG icons
                            ]
                            
                            for selector in css_selectors:
                                try:
                                    google_button = driver.find_element(By.CSS_SELECTOR, selector)
                                    button_text = google_button.text.lower()
                                    
                                    # Check if it's likely a Google login button
                                    if 'google' in button_text or 'gg' in button_text:
                                        print(f"Found Google login button with CSS selector: {selector}")
                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", google_button)
                                        time.sleep(1)
                                        google_button.click()
                                        google_login_found = True
                                        print("✓ Successfully clicked Google login button")
                                        break
                                except:
                                    continue
                        
                        # Strategy 3: Look for buttons with Google-related images or icons
                        if not google_login_found:
                            try:
                                # Find buttons that contain images or SVGs that might be Google icons
                                all_buttons_on_form = driver.find_elements(By.TAG_NAME, "button")
                                all_links_on_form = driver.find_elements(By.TAG_NAME, "a")
                                all_clickable_on_form = all_buttons_on_form + all_links_on_form
                                
                                for element in all_clickable_on_form:
                                    try:
                                        # Check if element contains Google-related content
                                        element_html = element.get_attribute('outerHTML').lower()
                                        element_text = element.text.lower()
                                        
                                        if ('google' in element_html or 'google' in element_text or 
                                            'gg' in element_text or 'gmail' in element_html):
                                            print("Found potential Google login element by content analysis")
                                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                            time.sleep(1)
                                            element.click()
                                            google_login_found = True
                                            print("✓ Successfully clicked Google login element")
                                            break
                                    except:
                                        continue
                                        
                            except Exception as e:
                                print(f"Strategy 3 failed: {e}")
                        
                        if google_login_found:
                            print("Waiting for Google login redirect...")
                            time.sleep(5)
                            
                            # Check if we're redirected to Google login
                            current_url_after_google_click = driver.current_url
                            print(f"Current URL after Google login click: {current_url_after_google_click}")
                            
                            if 'google' in current_url_after_google_click.lower() or 'accounts.google.com' in current_url_after_google_click:
                                print("✓ Successfully redirected to Google login page")
                                
                                # Wait for Google login page to load
                                try:
                                    google_email_field = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
                                    )
                                    print("✓ Google login page loaded - email field found")
                                    
                                except Exception as e:
                                    print(f"Could not find Google email field: {e}")
                            else:
                                print("Not redirected to Google - might be popup or different flow")
                                
                        else:
                            print("❌ Could not find Google login button")
                            
                            # Take screenshot for debugging
                            driver.save_screenshot("google_button_not_found.png")
                            print("Screenshot saved for debugging Google button")
                        
                    except Exception as e:
                        print(f"Error handling Google login: {e}")
                    
                    # Also try to find regular email and password fields as backup
                    try:
                        email_field = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
                        password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                        print("✓ Found regular email and password fields as backup")
                        
                    except:
                        print("Could not find standard login fields")
                        
                else:
                    print("No login form detected - might have redirected or popup appeared")
                    
            except Exception as e:
                print(f"Error checking for login form: {e}")
        else:
            print("❌ Could not find or click the login button with any strategy")
            
            # Take screenshot for debugging
            driver.save_screenshot("button_not_found_debug.png")
            print("Screenshot saved for debugging")
        
        # Keep browser open for a moment to see results
        time.sleep(10)
        
    except Exception as e:
        print(f"Error occurred: {e}")
        
    finally:
        try:
            driver.quit()
            print("Browser closed")
        except:
            pass

def complete_google_login_flow():
    """
    Complete flow: Click 'Đăng nhập để học' then 'Đăng nhập với Google'
    """
    url = "https://openedu.net/vi/courses/ai-mastery-lam-chu-tuong-lai-tang-nang-suat-gap-x-chi-trong-ngay-90668?ref_by=ASCAwBpPnx5OWIlO"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Additional headless optimizations
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("=== STEP 1: Loading OpenEdu course page ===")
        driver.get(url)
        
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)
        
        print("=== STEP 2: Clicking 'Đăng nhập để học' button ===")
        
        # Find and click the main login button
        login_button_clicked = False
        
        strategies = [
            ("Text-based search", "//button[contains(text(), 'Đăng nhập để học')]"),
            ("Data attribute", "button[data-action='loginRequired']"),
            ("Class-based", "button.bg-primary")
        ]
        
        for strategy_name, selector in strategies:
            try:
                if selector.startswith("//"):
                    button = driver.find_element(By.XPATH, selector)
                else:
                    button = driver.find_element(By.CSS_SELECTOR, selector)
                
                print(f"✓ Found login button using {strategy_name}")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(1)
                button.click()
                login_button_clicked = True
                print("✓ Successfully clicked 'Đăng nhập để học' button")
                break
                
            except Exception as e:
                print(f"✗ {strategy_name} failed: {e}")
                continue
        
        if not login_button_clicked:
            print("❌ Could not click the main login button")
            return
        
        print("=== STEP 3: Waiting for login form to appear ===")
        time.sleep(5)
        
        # Check for login form
        try:
            login_form = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form, .modal, .login-form, input[type='email']"))
            )
            print("✓ Login form detected")
        except:
            print("❌ Login form not detected")
            driver.save_screenshot("no_login_form.png")
            return
        
        print("=== STEP 4: Looking for 'Đăng nhập với Google' button ===")
        
        google_button_clicked = False
        
        # Multiple strategies to find Google login button
        google_strategies = [
            ("XPath text search", "//button[contains(text(), 'Đăng nhập với Google')]"),
            ("XPath partial text", "//button[contains(text(), 'Google')]"),
            ("XPath with span", "//button//span[contains(text(), 'Google')]"),
            ("Link text search", "//a[contains(text(), 'Đăng nhập với Google')]"),
            ("CSS with Google", "button[class*='google' i]"), # Case-insensitive class search
            ("Data provider", "button[data-provider='google']"),
        ]
        
        for strategy_name, selector in google_strategies:
            try:
                if selector.startswith("//"):
                    google_button = driver.find_element(By.XPATH, selector)
                else:
                    google_button = driver.find_element(By.CSS_SELECTOR, selector)
                
                print(f"✓ Found Google login button using {strategy_name}")
                print(f"Button text: '{google_button.text}'")
                
                # Scroll to button and click
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", google_button)
                time.sleep(2)
                
                # Try regular click first
                try:
                    google_button.click()
                except:
                    # If regular click fails, try JavaScript click
                    driver.execute_script("arguments[0].click();", google_button)
                
                google_button_clicked = True
                print("✓ Successfully clicked 'Đăng nhập với Google' button")
                break
                
            except Exception as e:
                print(f"✗ {strategy_name} failed: {e}")
                continue
        
        # If standard strategies fail, try scanning all elements
        if not google_button_clicked:
            print("=== STEP 4B: Scanning all clickable elements ===")
            try:
                all_elements = driver.find_elements(By.CSS_SELECTOR, "button, a, div[onclick], span[onclick]")
                
                for element in all_elements:
                    try:
                        element_text = element.text.lower()
                        element_html = element.get_attribute('outerHTML').lower()
                        
                        if (('google' in element_text and 'đăng nhập' in element_text) or
                            ('google' in element_html and ('login' in element_html or 'sign' in element_html)) or
                            ('gg' in element_text and len(element_text) < 50)): # Short text with 'gg'
                            
                            print(f"✓ Found potential Google button: '{element.text[:50]}'")
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(1)
                            element.click()
                            google_button_clicked = True
                            print("✓ Successfully clicked Google login element")
                            break
                            
                    except:
                        continue
                        
            except Exception as e:
                print(f"Element scanning failed: {e}")
        
        if not google_button_clicked:
            print("❌ Could not find or click Google login button")
            driver.save_screenshot("google_button_not_found_complete.png")
            print("Screenshot saved for debugging")
            return
        
        print("=== STEP 5: Handling Google login redirect ===")
        time.sleep(5)
        
        current_url = driver.current_url
        print(f"Current URL: {current_url}")
        
        if 'google' in current_url.lower() or 'accounts.google.com' in current_url:
            print("✓ Successfully redirected to Google login!")
            
            try:
                # Wait for Google email input
                email_input = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='email'], input#identifierId"))
                )
                print("✓ Google email field is ready")
                
                # Enter Google email/phone
                google_email = "Vanthanhduyt0bra@saigon.bh.edu.vn"  # Replace with your email
                email_input.clear()
                email_input.send_keys(google_email)
                print(f"✓ Entered email: {google_email}")
                
                # Click Next button
                try:
                    next_button = driver.find_element(By.ID, "identifierNext")
                    next_button.click()
                    print("✓ Clicked Next button")
                except:
                    # Alternative selectors for Next button
                    next_selectors = [
                        "button[jsname='LgbsSe']", # Common Google button jsname
                        "//button[.//span[contains(text(),'Next') or contains(text(),'Tiếp theo')]]", # XPath for button with Next/Tiếp theo span
                        "//button[contains(text(), 'Next')]",
                        "//span[contains(text(), 'Next')]/parent::button"
                    ]
                    
                    next_clicked_alt = False
                    for selector in next_selectors:
                        try:
                            if selector.startswith("//"):
                                next_btn = driver.find_element(By.XPATH, selector)
                            else:
                                next_btn = driver.find_element(By.CSS_SELECTOR, selector)
                            next_btn.click()
                            print("✓ Clicked Next button (alternative method)")
                            next_clicked_alt = True
                            break
                        except:
                            continue
                    if not next_clicked_alt: print("Failed to click Next button with alternatives.")

                
                # Wait for password page
                time.sleep(3)
                
                try:
                    password_input = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='password'], input[name='password'], input[name='Passwd']"))
                    )
                    print("✓ Password field is ready")
                    
                    # Enter password
                    google_password = "Truong3979"  # Replace with your password
                    password_input.clear()
                    password_input.send_keys(google_password)
                    print("✓ Entered password")
                    
                    # Click Next/Sign in button
                    try:
                        signin_button = driver.find_element(By.ID, "passwordNext")
                        signin_button.click()
                        print("✓ Clicked Sign in button")
                    except:
                        # Alternative selectors for Sign in button
                        signin_selectors = [
                            "button[jsname='LgbsSe']", # Common Google button jsname
                            "//button[.//span[contains(text(),'Next') or contains(text(),'Tiếp theo')]]", # XPath for button with Next/Tiếp theo span
                            "//button[contains(text(), 'Next')]",
                            "//span[contains(text(), 'Next')]/parent::button"
                        ]
                        signin_clicked_alt = False
                        for selector in signin_selectors:
                            try:
                                if selector.startswith("//"):
                                    signin_btn = driver.find_element(By.XPATH, selector)
                                else:
                                    signin_btn = driver.find_element(By.CSS_SELECTOR, selector)
                                signin_btn.click()
                                print("✓ Clicked Sign in button (alternative method)")
                                signin_clicked_alt = True
                                break
                            except:
                                continue
                        if not signin_clicked_alt: print("Failed to click Sign In button with alternatives.")

                    
                    # Wait for login completion
                    time.sleep(5)
                    
                    # Check if we're back to OpenEdu or still on Google
                    final_url = driver.current_url
                    print(f"Final URL: {final_url}")
                    
                    if 'openedu' in final_url.lower():
                        print("🎉 Successfully logged in and returned to OpenEdu!")
                    elif 'google' in final_url.lower():
                        print("Still on Google - might need 2FA or additional verification")
                    else:
                        print(f"Redirected to: {final_url}")
                        
                except Exception as pwd_e:
                    print(f"Password step failed: {pwd_e}")
                    print("Manual password entry required")
                
            except Exception as e:
                print(f"Error on Google page: {e}")
        else:
            print("Not redirected to Google - checking for popup or iframe")
            
            # Check for popup window if exists
            if len(driver.window_handles) > 1:
                driver.switch_to.window(driver.window_handles[-1]) # Switch to the last opened window
                print("Switched to popup window")
                time.sleep(3) # Wait for popup to load
                
                current_popup_url = driver.current_url
                print(f"Popup URL: {current_popup_url}")
                if 'google' in current_popup_url.lower():
                    print("✓ Google login in popup window!")
                    # Repeat login steps if necessary within the popup context
                else:
                    driver.switch_to.window(driver.window_handles[0]) # Switch back if not Google
            
            # Check for iframe
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                try:
                    driver.switch_to.frame(iframe)
                    if 'google' in driver.page_source.lower(): # Check content if URL doesn't change
                        print("✓ Google login in iframe!")
                        # Repeat login steps if necessary within the iframe context
                        break 
                    driver.switch_to.default_content()
                except:
                    driver.switch_to.default_content()
                    continue
                        
        # Keep browser open to see the result
        print("Keeping browser open for 30 seconds...")
        time.sleep(30)
        
    except Exception as e:
        print(f"Error in complete flow: {e}")
        
    finally:
        try:
            driver.quit()
            print("Browser closed")
        except:
            pass

def start_course(driver):
    """
    Click the "Bắt đầu khoá học" button to start the course
    """
    try:
        print("=== STARTING COURSE ===")
        
        # Wait for page to load completely
        time.sleep(3)
        
        # Multiple strategies to find "Bắt đầu khoá học" button
        start_course_strategies = [
            # Strategy 1: By exact Vietnamese text
            ("//button[contains(text(), 'Bắt đầu khoá học')]", "xpath"),
            ("//button[text()='Bắt đầu khoá học']", "xpath"),
            ("//button[contains(text(), 'Bắt đầu khóa học')]", "xpath"),  # Alternative spelling
            
            # Strategy 2: By button with "start" related text
            ("//button[contains(text(), 'Bắt đầu')]", "xpath"),
            ("//button[contains(text(), 'Start')]", "xpath"),
            ("//button[contains(text(), 'Begin')]", "xpath"),
            
            # Strategy 3: By CSS classes and data attributes from your HTML
            ("button[data-action='default']", "css"),
            ("button[id='enroll_course']", "css"),
            ("button.bg-primary[type='button']", "css"),
            ("button.select-none.inline-flex.items-center.justify-center", "css"),
            
            # Strategy 4: By button text content matching pattern
            ("button[data-slot='button']", "css"),
            ("button.text-primary-foreground", "css"),
            
            # Strategy 5: Generic course enrollment buttons
            (".course-start-btn", "css"),
            (".enroll-btn", "css"),
            (".start-course", "css"),
            ("button[class*='enroll']", "css"),
            ("button[class*='start']", "css")
        ]
        
        start_clicked = False
        
        for selector, method in start_course_strategies:
            try:
                print(f"Trying start course selector: {selector}")
                
                if method == "xpath":
                    buttons = driver.find_elements(By.XPATH, selector)
                else:
                    buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for button in buttons:
                    try:
                        # Check if button is visible and enabled
                        if button.is_displayed() and button.is_enabled():
                            
                            # Get button text to verify it's the start course button
                            button_text = (button.text or 
                                         button.get_attribute('aria-label') or 
                                         button.get_attribute('title') or '').strip()
                            
                            print(f"Found button with text: '{button_text}'")
                            
                            # Check if it's the "Bắt đầu khoá học" button
                            is_start_button = False
                            
                            start_keywords = [
                                'bắt đầu khoá học', 'bắt đầu khóa học', 'bắt đầu',
                                'start course', 'start', 'begin course', 'begin',
                                'enroll', 'join course', 'access course'
                            ]
                            
                            button_text_lower = button_text.lower()
                            if any(keyword in button_text_lower for keyword in start_keywords):
                                is_start_button = True
                                print("✓ Identified as start course button by text")
                            elif not button_text and ('enroll' in selector or 'start' in selector or 'default' in selector):
                                # If no text but selector suggests it's a start button
                                is_start_button = True
                                print("✓ Identified as start course button by selector")
                            
                            if is_start_button:
                                print(f"✓ Clicking start course button: '{button_text or 'course start button'}'")
                                
                                # Scroll to button
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                                time.sleep(1)
                                
                                # Highlight for debugging
                                try:
                                    driver.execute_script("arguments[0].style.border='3px solid orange';", button)
                                    time.sleep(0.5)
                                    driver.execute_script("arguments[0].style.border='';", button)
                                except:
                                    pass
                                
                                # Try multiple click methods
                                click_success = False
                                
                                # Method 1: Regular click
                                try:
                                    button.click()
                                    click_success = True
                                    print("✓ Successfully clicked start course with regular click")
                                except Exception as e:
                                    print(f"Regular click failed: {e}")
                                
                                # Method 2: JavaScript click
                                if not click_success:
                                    try:
                                        driver.execute_script("arguments[0].click();", button)
                                        click_success = True
                                        print("✓ Successfully clicked start course with JavaScript")
                                    except Exception as e:
                                        print(f"JavaScript click failed: {e}")
                                
                                # Method 3: ActionChains click
                                if not click_success:
                                    try:
                                        ActionChains(driver).move_to_element(button).click().perform()
                                        click_success = True
                                        print("✓ Successfully clicked start course with ActionChains")
                                    except Exception as e:
                                        print(f"ActionChains click failed: {e}")
                                
                                if click_success:
                                    start_clicked = True
                                    break
                                
                    except Exception as e:
                        print(f"Error processing start button: {e}")
                        continue
                
                if start_clicked:
                    break
                    
            except Exception as e:
                print(f"Start course strategy failed: {selector} - {e}")
                continue
        
        if start_clicked:
            print("✅ Start course button clicked successfully!")
            
            # Wait for course to load
            print("✅ Start course button clicked successfully!")
            print("Waiting for course content to load...")
            
            # Wait for course content to load using custom Expected Condition
            print("Waiting for course content to load (up to 30 seconds)...")
            wait_for_course_content = WebDriverWait(driver, 30) # Total 30 seconds timeout
            course_content_found = False
            final_course_indicator_found = "None" # Default to string "None"

            course_indicators_with_types = [
                (By.CSS_SELECTOR, ".video-player"), (By.CSS_SELECTOR, ".lesson-content"), 
                (By.CSS_SELECTOR, ".course-video"), (By.CSS_SELECTOR, ".module"), 
                (By.CSS_SELECTOR, ".chapter"), (By.CSS_SELECTOR, ".lesson"), 
                (By.CSS_SELECTOR, ".course-material"), (By.CSS_SELECTOR, "video"),
                (By.CSS_SELECTOR, "iframe[src*='youtube']"), (By.CSS_SELECTOR, "iframe[src*='vimeo']"),
                (By.CSS_SELECTOR, "[data-testid='lesson-navigation']"), 
                (By.CSS_SELECTOR, "[data-testid='course-player-container']")
            ]
            
            custom_ec = AnyElementVisible(course_indicators_with_types)
            try:
                print("  Attempting to find any specified course indicator...")
                visible_element = wait_for_course_content.until(custom_ec)
                if visible_element: 
                    course_content_found = True
                    final_course_indicator_found = custom_ec.found_locator_info # Get info from the EC instance
                    print(f"✓ Found visible course content with indicator: {final_course_indicator_found}")
            except TimeoutException:
                print("  No specified course indicators found or visible within 30 seconds timeout.")
            except Exception as e_custom_wait:
                print(f"  Error during custom wait for course indicators: {e_custom_wait}")

            current_url_after_content_check = driver.current_url
            print(f"URL after content check: {current_url_after_content_check}")

            if course_content_found:
                print(f"🎉 Successfully accessed course content (verified by visible indicator: {final_course_indicator_found})!")
            else:
                # Fallback: Check if URL changed to a deeper path, suggesting a lesson page
                base_course_url_prefix = "/vi/courses/"
                if base_course_url_prefix in current_url_after_content_check:
                    path_after_courses = current_url_after_content_check.split(base_course_url_prefix, 1)[1]
                    path_segments = [seg for seg in path_after_courses.split('?')[0].split('/') if seg] # Get non-empty segments, remove query params
                    
                    new_url_path_parts = len(path_segments) # Count segments in the course-specific part of the URL
                    # A base course page might have 1 segment (course-slug)
                    # A lesson page usually has more (course-slug/lesson-group-id/lesson-item-id)
                    # The initial URL for a course page like "https://openedu.net/vi/courses/course-slug" has 1 segment after "/vi/courses/"
                    # The logged URL "https://openedu.net/vi/courses/ai-mastery.../vQ0fynAgwx3RhRLq/KoVMXVMxIzDCRYEW" has 3 segments after /vi/courses/
                    
                    # We need to compare against the number of segments of the *course* page, not the absolute URL.
                    # Let's assume the URL before clicking "Start Course" was the main course page.
                    # A more robust way would be to get the URL *before* the click and compare its segment count.
                    # For now, a simple check: if more than 1 segment after course slug, it's likely a lesson.
                    # The logged URL had 3 segments: [ai-mastery..., vQ0fynAgwx3RhRLq, KoVMXVMxIzDCRYEW]
                    
                    if new_url_path_parts > 1: # If more than just the course slug itself
                        last_segment = path_segments[-1]
                        if len(last_segment) > 5 and any(c.isalnum() for c in last_segment): # Heuristic for ID-like segment
                            print("✓ Course page URL changed to what appears to be a lesson/module page.")
                            print("  Assuming course content is loading or accessible based on URL structure.")
                            course_content_found = True 
                        else:
                            print(f"URL changed, but last segment '{last_segment}' doesn't look like a typical lesson ID.")
                    else:
                        print("URL structure is not deep enough for a lesson page after course name.")
                
                if not course_content_found:
                    print("⚠️ Course content indicators not found and URL did not change as expected for a lesson page.")
                    driver.save_screenshot("course_content_not_found.png")
                    print("Screenshot saved: course_content_not_found.png")
            
            return course_content_found 
        else:
            print("❌ Could not find or click start course button")
            driver.save_screenshot("start_course_button_fail.png")
            print("Screenshot saved for debugging start course button: start_course_button_fail.png")
            return False
            
    except Exception as e:
        print(f"❌ Error in start_course process: {e}")
        driver.save_screenshot("start_course_error.png")
        print("Screenshot saved: start_course_error.png")
        return False

def handle_google_login_credentials(driver, email, password):
    """
    Helper function to handle Google login with credentials
    """
    try:
        print("=== Google Login Credential Entry ===")
        
        # Step 1: Enter email
        print("Waiting for email field...")
        email_input = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='email'], input#identifierId, input[name='identifier']"))
        )
        
        # Clear any existing text and enter email
        email_input.clear()
        time.sleep(1)
        email_input.send_keys(email)
        print(f"✓ Entered email: {email}")
        
        # Step 2: Click Next button
        print("Looking for Next button...")
        next_button_clicked = False
        
        next_button_selectors = [
            "#identifierNext",
            "button[jsname='LgbsSe']",
            "//button[@id='identifierNext']",
            "//span[text()='Next']/parent::button",
            "//div[@id='identifierNext']",
            "button:contains('Next')" # jQuery style, might not work directly in Selenium
        ]
        
        for selector in next_button_selectors:
            try:
                if selector.startswith("//"):
                    next_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                elif ":contains" in selector: # Basic handling for contains-like selector
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    for btn in buttons:
                        if "Next" in btn.text:
                            next_btn = btn
                            break
                    else: continue # If no button found, try next selector
                else:
                    next_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                
                # Try clicking the button
                try:
                    next_btn.click()
                except:
                    driver.execute_script("arguments[0].click();", next_btn)
                
                next_button_clicked = True
                print("✓ Clicked Next button")
                break
                
            except Exception as e:
                print(f"Next button selector failed: {selector} - {e}")
                continue
        
        if not next_button_clicked:
            print("❌ Could not find Next button")
            return False
        
        # Step 3: Wait for password page and enter password
        print("Waiting for password field...")
        time.sleep(3)
        
        try:
            # Multiple selectors for password field based on the HTML structure you showed
            password_selectors = [
                "input[type='password']",
                "input[name='password']", 
                "input[name='Passwd']",
                "input#password",
                "input.whsOnd.zHQkBf",  # Based on your HTML
                "input[jsname='YPqjbf']",  # Based on your HTML
                "input[autocomplete='current-password']"
            ]
            
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    print(f"✓ Found password field with selector: {selector}")
                    break
                except:
                    continue
            
            if not password_input:
                print("❌ Could not find password field")
                return False
            
            # Clear and enter password
            password_input.clear()
            time.sleep(1)
            
            # Click on the password field to ensure it's focused
            password_input.click()
            time.sleep(0.5)
            
            # Type password slowly to avoid detection
            for char in password:
                password_input.send_keys(char)
                time.sleep(0.1)  # Small delay between characters
            
            print("✓ Entered password")
            
            # Optional: Verify password was entered
            entered_value = password_input.get_attribute('value')
            if len(entered_value) == len(password):
                print("✓ Password length verification passed")
            else:
                print(f"⚠️  Password length mismatch: expected {len(password)}, got {len(entered_value)}")
            
            # Step 4: Click Sign in/Next button
            print("Looking for Sign in button...")
            time.sleep(1)
            
            signin_button_clicked = False
            
            # Multiple selectors for the sign in button
            signin_selectors = [
                "#passwordNext",
                "button[jsname='LgbsSe']",
                "//button[@id='passwordNext']",
                "//span[text()='Next']/parent::button",
                "//span[text()='Tiếp theo']/parent::button",  # Vietnamese
                "//div[@id='passwordNext']",
                "button[type='submit']",
                "input[type='submit']",
                "//button[contains(@class, 'VfPpkd-LgbsSe')]"
            ]
            
            for selector in signin_selectors:
                try:
                    if selector.startswith("//"):
                        signin_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        signin_btn = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    # Scroll to button and click
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", signin_btn)
                    time.sleep(0.5)
                    
                    try:
                        signin_btn.click()
                    except:
                        # If regular click fails, try JavaScript click
                        driver.execute_script("arguments[0].click();", signin_btn)
                    
                    signin_button_clicked = True
                    print(f"✓ Clicked Sign in button using selector: {selector}")
                    break
                    
                except Exception as e:
                    print(f"Sign in button selector failed: {selector} - {e}")
                    continue
            
            # Alternative: Press Enter key if button click fails
            if not signin_button_clicked:
                print("Trying Enter key as alternative...")
                try:
                    password_input.send_keys(Keys.RETURN)
                    signin_button_clicked = True
                    print("✓ Used Enter key to submit")
                except Exception as e:
                    print(f"Enter key failed: {e}")
            
            if not signin_button_clicked:
                print("❌ Could not find or click Sign in button")
                return False
            
            # Step 5: Wait for login completion or 2FA
            print("Waiting for login completion...")
            time.sleep(5)
            
            current_url = driver.current_url
            print(f"Current URL after login attempt: {current_url}")
            
            # Check for various post-login scenarios
            if 'openedu' in current_url.lower():
                print("🎉 Successfully logged in and returned to OpenEdu!")
                
                # Check for consent/agreement popup and handle it
                try:
                    print("Checking for consent popup...")
                    handle_consent_popup(driver) # Call the refactored function
                except Exception as e:
                    print(f"Error handling consent popup: {e}")
                
                return True
                
            elif 'myaccount.google.com' in current_url or 'accounts.google.com/signin/oauth' in current_url or 'accounts.google.com' in current_url:
                print("✓ Google login successful, processing OAuth...")
                
                # First try to handle OAuth consent popup if it appears
                oauth_handled = handle_oauth_consent(driver)
                
                if oauth_handled:
                    print("✓ OAuth consent handled successfully")
                    # After OAuth consent, we should be back on OpenEdu
                    time.sleep(3)
                    final_url = driver.current_url
                    if 'openedu' in final_url.lower():
                        print("🎉 Returned to OpenEdu after OAuth consent!")
                        return True
                
                # If no OAuth consent popup, wait for regular OAuth redirect
                for i in range(15):  # Wait up to 15 seconds
                    time.sleep(1)
                    current_url_oauth_wait = driver.current_url
                    print(f"Waiting for OAuth redirect... URL: {current_url_oauth_wait}")
                    
                    if 'openedu' in current_url_oauth_wait.lower():
                        print("🎉 OAuth completed, returned to OpenEdu!")
                        return True
                    elif i == 14:
                        print("OAuth taking longer than expected...")
                        
                return True # Assuming success if OAuth redirect is slow but login was ok
            elif 'challenge' in current_url or 'verify' in current_url or '2fa' in current_url or 'signin/v2/challenge' in current_url:
                print("⚠️  Two-factor authentication required")
                print("Please complete 2FA manually in the browser")
                
                # Wait for user to complete 2FA
                print("Waiting for 2FA completion (60 seconds)...")
                for i in range(60):
                    time.sleep(1)
                    current_url_2fa_wait = driver.current_url
                    if 'openedu' in current_url_2fa_wait.lower():
                        print("🎉 2FA completed, returned to OpenEdu!")
                        return True
                    elif 'myaccount.google.com' in current_url_2fa_wait:
                        print("✓ 2FA completed, processing OAuth...")
                        # Potentially call OAuth handler again if needed
                        handle_oauth_consent(driver)
                        return True
                        
                return True # Assume 2FA will be handled
            elif 'google.com' in current_url:
                print("Still on Google page - checking for errors or additional steps")
                
                # Check for error messages
                try:
                    error_selectors = [
                        ".LXRPh",  # Common error message class
                        ".dEOOab", 
                        "[data-error-code]",
                        ".Ekjuhf",  # Password error
                        ".GNkfBe",  # General error
                        ".k6Zj8d .jibhHc"  # Error text
                    ]
                    
                    for selector in error_selectors:
                        try:
                            error_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            for error in error_elements:
                                if error.text and error.is_displayed():
                                    print(f"⚠️  Error message: {error.text}")
                        except:
                            continue
                            
                except Exception as e:
                    print(f"Error checking failed: {e}")
                
                return False
            else:
                print(f"Unexpected redirect to: {current_url}")
                return False
                
        except Exception as pwd_e:
            print(f"❌ Password step failed: {pwd_e}")
            return False
            
    except Exception as e:
        print(f"❌ Google login failed: {e}")
        return False

def handle_consent_popups(driver): # This function seems to be a more general handler
    """
    Handle consent popups that may appear after Google login (could be "Tôi hiểu" or OAuth "Continue")
    This function attempts to handle both types of popups that might appear sequentially or independently.
    """
    try:
        print("=== Handling Consent Popups (General) ===")
        
        # Wait a moment for popups to appear
        time.sleep(3)
        
        # Attempt to handle the "Tôi hiểu" style consent first
        print("--- Checking for 'Tôi hiểu' style consent ---")
        handled_toi_hieu = handle_consent_popup(driver) # Specific "Tôi hiểu" handler
        if handled_toi_hieu:
            print("✓ 'Tôi hiểu' style consent handled.")
            time.sleep(3) # Wait for potential next popup
        else:
            print("No 'Tôi hiểu' style consent found or handled.")

        # Attempt to handle the OAuth "Continue" style consent
        print("--- Checking for OAuth 'Continue' style consent ---")
        current_url_before_oauth = driver.current_url
        if 'accounts.google.com' in current_url_before_oauth:
            handled_oauth = handle_oauth_consent(driver) # Specific OAuth "Continue" handler
            if handled_oauth:
                print("✓ OAuth 'Continue' style consent handled.")
                time.sleep(3) # Wait for redirect
            else:
                print("No OAuth 'Continue' style consent found or handled on Google page.")
        else:
            print("Not on a Google page, skipping OAuth 'Continue' style consent check.")
            
        final_url = driver.current_url
        print(f"Final URL after general consent handling: {final_url}")
        
        # Return true if we are back on OpenEdu or if at least one consent was handled
        if 'openedu' in final_url.lower() or handled_toi_hieu or ( 'accounts.google.com' in current_url_before_oauth and handled_oauth):
            return True
        return False
            
    except Exception as e:
        print(f"Error in general consent popups handling: {e}")
        return False

def setup_logging():
    """
    Setup logging to track the automation process for multiple emails
    """
    log_filename = f"openedu_automation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return log_filename

def read_emails_from_file(filename="emails.txt"):
    """
    Read emails from a text file
    Returns a list of emails
    """
    try:
        if not os.path.exists(filename):
            print(f"❌ File {filename} not found. Creating example file...")
            # Create example file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# Add your Google emails here, one per line\n")
                f.write("# Lines starting with # will be ignored\n")
                f.write("example1@gmail.com\n")
                f.write("example2@saigon.bh.edu.vn\n")
                f.write("# Add more emails below\n")
            print(f"✓ Created example {filename} file. Please add your emails and run again.")
            return []
        
        emails = []
        with open(filename, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    # Basic email validation
                    if '@' in line and '.' in line.split('@')[-1]:
                        emails.append(line)
                        print(f"✓ Added email {len(emails)}: {line}")
                    else:
                        print(f"⚠️  Line {line_num}: Invalid email format: {line}")
        
        print(f"📧 Total valid emails found: {len(emails)}")
        return emails
        
    except Exception as e:
        print(f"❌ Error reading emails file: {e}")
        return []

def process_multiple_emails(emails_file="emails.txt", password="Truong3979"):
    """
    Process multiple emails from a file in batches of 10 with random sleep intervals
    """
    # Setup logging
    log_file = setup_logging()
    logging.info("="*50)
    logging.info("Starting OpenEdu automation for multiple emails")
    logging.info(f"Log file: {log_file}")
    
    # Read emails from file
    emails = read_emails_from_file(emails_file)
    
    if not emails:
        logging.error("No valid emails found. Exiting.")
        return
    
    # Statistics tracking
    total_emails = len(emails)
    successful_logins = 0
    failed_logins = 0
    results = []
    
    logging.info(f"Processing {total_emails} emails with password: {'*' * len(password)}")
    
    # Process emails in batches of 10
    batch_size = 10
    for batch_start in range(0, len(emails), batch_size):
        batch_end = min(batch_start + batch_size, len(emails))
        current_batch = emails[batch_start:batch_end]
        
        print("\n" + "="*80)
        print(f"🔄 PROCESSING BATCH {batch_start//batch_size + 1} (Emails {batch_start + 1}-{batch_end})")
        print("="*80)
        logging.info(f"Starting batch {batch_start//batch_size + 1} (Emails {batch_start + 1}-{batch_end})")
        
        # Process each email in the current batch
        for index, email in enumerate(current_batch, batch_start + 1):
            print("\n" + "-"*60)
            print(f"🔄 PROCESSING EMAIL {index}/{total_emails}: {email}")
            print("-"*60)
            
            logging.info(f"Starting automation for email {index}/{total_emails}: {email}")
            
            try:
                # Run the complete login process for this email
                success = complete_login_with_credentials(email, password)
                
                if success:
                    successful_logins += 1
                    result_status = "SUCCESS"
                    print(f"✅ SUCCESS: Email {index}/{total_emails} - {email}")
                    logging.info(f"SUCCESS: {email} - Login and course access completed")
                else:
                    failed_logins += 1
                    result_status = "FAILED"
                    print(f"❌ FAILED: Email {index}/{total_emails} - {email}")
                    logging.warning(f"FAILED: {email} - Login or course access failed")
                
                results.append({
                    'email': email,
                    'status': result_status,
                    'index': index
                })
                
            except Exception as e:
                failed_logins += 1
                result_status = "ERROR"
                error_msg = str(e)
                print(f"💥 ERROR: Email {index}/{total_emails} - {email}: {error_msg}")
                logging.error(f"ERROR: {email} - Exception occurred: {error_msg}")
                
                results.append({
                    'email': email,
                    'status': result_status,
                    'error': error_msg,
                    'index': index
                })
            
            # Add delay between emails in the batch
            if index < batch_end:
                delay_seconds = 10
                print(f"⏳ Waiting {delay_seconds} seconds before next email...")
                logging.info(f"Waiting {delay_seconds} seconds before processing next email")
                time.sleep(delay_seconds)
        
        # After processing a batch, if there are more emails, add random sleep
        if batch_end < len(emails):
            sleep_minutes = random.randint(1, 60)
            print(f"\n💤 Batch complete. Sleeping for {sleep_minutes} minutes before next batch...")
            logging.info(f"Batch {batch_start//batch_size + 1} complete. Sleeping for {sleep_minutes} minutes")
            time.sleep(sleep_minutes * 60)  # Convert minutes to seconds
    
    # Final summary
    print("\n" + "="*80)
    print("🏁 FINAL SUMMARY")
    print("="*80)
    print(f"📊 Total emails processed: {total_emails}")
    print(f"✅ Successful logins: {successful_logins}")
    print(f"❌ Failed logins: {failed_logins}")
    print(f"📈 Success rate: {(successful_logins/total_emails)*100:.1f}%")
    
    logging.info("="*50)
    logging.info("FINAL SUMMARY")
    logging.info(f"Total emails: {total_emails}")
    logging.info(f"Successful: {successful_logins}")
    logging.info(f"Failed: {failed_logins}")
    logging.info(f"Success rate: {(successful_logins/total_emails)*100:.1f}%")
    
    # Detailed results
    print("\n📋 DETAILED RESULTS:")
    logging.info("DETAILED RESULTS:")
    for result in results:
        status_emoji = "✅" if result['status'] == "SUCCESS" else ("❌" if result['status'] == "FAILED" else "💥")
        print(f"{status_emoji} {result['index']:2d}. {result['email']} - {result['status']}")
        logging.info(f"{result['index']:2d}. {result['email']} - {result['status']}")
        if 'error' in result:
            print(f"    Error: {result['error']}")
            logging.info(f"    Error: {result['error']}")
    
    # Save results to file
    results_file = f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(results_file, 'w', encoding='utf-8') as f:
            f.write(f"OpenEdu Automation Results - {datetime.now()}\n")
            f.write("="*50 + "\n")
            f.write(f"Total emails: {total_emails}\n")
            f.write(f"Successful: {successful_logins}\n")
            f.write(f"Failed: {failed_logins}\n")
            f.write(f"Success rate: {(successful_logins/total_emails)*100:.1f}%\n")
            f.write("\nDetailed Results:\n")
            f.write("-"*30 + "\n")
            for result in results:
                f.write(f"{result['index']:2d}. {result['email']} - {result['status']}\n")
                if 'error' in result:
                    f.write(f"    Error: {result['error']}\n")
        
        print(f"📄 Results saved to: {results_file}")
        logging.info(f"Results saved to: {results_file}")
        
    except Exception as e:
        print(f"⚠️  Could not save results file: {e}")
        logging.warning(f"Could not save results file: {e}")
    
    # Save successful emails to success_mail.txt
    successful_emails = [result['email'] for result in results if result['status'] == 'SUCCESS']
    success_file = "success_mail.txt"
    
    try:
        with open(success_file, 'w', encoding='utf-8') as f:
            f.write(f"# Successful emails from OpenEdu automation\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total successful: {len(successful_emails)} out of {total_emails}\n")
            f.write(f"# Success rate: {(len(successful_emails)/total_emails)*100:.1f}%\n")
            f.write("\n")
            
            if successful_emails:
                for email in successful_emails:
                    f.write(f"{email}\n")
                print(f"✅ Successful emails saved to: {success_file} ({len(successful_emails)} emails)")
                logging.info(f"Successful emails saved to: {success_file} ({len(successful_emails)} emails)")
            else:
                f.write("# No successful emails found\n")
                print(f"⚠️  No successful emails to save to {success_file}")
                logging.warning(f"No successful emails to save")
        
    except Exception as e:
        print(f"⚠️  Could not save success file: {e}")
        logging.warning(f"Could not save success file: {e}")
    
    # Also save failed emails for reference
    failed_emails = [result for result in results if result['status'] in ['FAILED', 'ERROR']]
    failed_file = "failed_mail.txt"
    
    try:
        with open(failed_file, 'w', encoding='utf-8') as f:
            f.write(f"# Failed emails from OpenEdu automation\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total failed: {len(failed_emails)} out of {total_emails}\n")
            f.write("\n")
            
            if failed_emails:
                for result in failed_emails:
                    f.write(f"{result['email']}")
                    if 'error' in result:
                        f.write(f" # Error: {result['error']}")
                    f.write("\n")
                print(f"❌ Failed emails saved to: {failed_file} ({len(failed_emails)} emails)")
                logging.info(f"Failed emails saved to: {failed_file} ({len(failed_emails)} emails)")
            else:
                f.write("# No failed emails found\n")
        
    except Exception as e:
        print(f"⚠️  Could not save failed file: {e}")
        logging.warning(f"Could not save failed file: {e}")
    
    print(f"📄 Full log saved to: {log_file}")
    
    return results

def complete_login_with_credentials(email, password):
    """
    Complete login flow with actual credentials
    Modified to return success/failure status
    """
    url = "https://openedu.net/vi/courses/ai-mastery-lam-chu-tuong-lai-tang-nang-suat-gap-x-chi-trong-ngay-90668?ref_by=ASCAwBpPnx5OWIlO"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Additional headless optimizations
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
    chrome_options.add_argument("--disable-extensions")  # Disable extensions
    chrome_options.add_argument("--disable-plugins")  # Disable plugins
    chrome_options.add_argument("--window-size=1920,1080")  # Set window size for headless
    chrome_options.add_argument("--disable-images")  # Disable image loading for faster performance
    
    driver = None # Initialize driver to None for finally block
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Step 1-4: Same as before (load page, click login buttons)
        print(f"=== Starting login process for: {email} ===")
        logging.info(f"Loading OpenEdu page for {email}")
        driver.get(url)
        
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(3)
        
        # Click main login button
        print("=== Looking for main login button ===")
        
        login_strategies = [
            ("//button[contains(text(), 'Đăng nhập để học')]", "xpath"),
            ("button[data-action='loginRequired']", "css"),
            ("button.bg-primary", "css"),
            ("//button[contains(text(), 'Đăng nhập')]", "xpath"),
            ("//button[contains(text(), 'Login')]", "xpath"),
            ("button[type='button']", "css")
        ]
        
        login_clicked = False
        for i, (selector, method) in enumerate(login_strategies):
            try:
                print(f"Strategy {i+1}: Trying {method} selector: {selector}")
                
                if method == "xpath":
                    buttons = driver.find_elements(By.XPATH, selector)
                else:
                    buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                
                print(f"Found {len(buttons)} elements")
                
                for j, button in enumerate(buttons):
                    try:
                        if button.is_displayed() and button.is_enabled():
                            button_text = button.text.lower()
                            print(f"  Button {j+1}: '{button_text[:50]}'")
                            
                            # Check if it's likely the main login button
                            if ('đăng nhập' in button_text and 'học' in button_text) or \
                               ('login' in button_text) or \
                               (not button_text and 'loginRequired' in selector):
                                
                                print(f"  🎯 Clicking main login button: '{button_text[:30] or 'login button'}'")
                                
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                                time.sleep(1)
                                
                                # Try multiple click methods
                                try:
                                    button.click()
                                    login_clicked = True
                                    print("  ✅ Successfully clicked with regular click")
                                    break
                                except:
                                    try:
                                        driver.execute_script("arguments[0].click();", button)
                                        login_clicked = True
                                        print("  ✅ Successfully clicked with JavaScript")
                                        break
                                    except:
                                        continue
                                        
                    except Exception as e:
                        print(f"  Error with button {j+1}: {e}")
                        continue
                
                if login_clicked:
                    break
                    
            except Exception as e:
                print(f"Strategy {i+1} failed: {e}")
                continue
        
        if not login_clicked:
            print("❌ Could not click main login button")
            logging.error(f"Could not click main login button for {email}")
            return False
        
        print("✅ Main login button clicked, waiting for login form...")
        logging.info(f"Main login button clicked for {email}")
        time.sleep(8)  # Increased wait time for login form to fully load
        
        # Wait for login form/modal to appear
        print("=== Waiting for login form to appear ===")
        login_form_detected = False
        
        # Try to detect login form/modal
        login_form_selectors = [
            ".modal", ".popup", ".dialog", ".login-form", ".auth-form",
            "form", "[role='dialog']", ".overlay", ".login-modal",
            "input[type='email']", "input[type='password']", 
            "button[data-provider]", ".social-login"
        ]
        
        for selector in login_form_selectors:
            try:
                elements = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if elements:
                    print(f"✓ Login form detected with selector: {selector}")
                    login_form_detected = True
                    break
            except:
                continue
        
        if not login_form_detected:
            print("⚠️  No login form detected, but continuing...")
        
        # Take screenshot of current state
        screenshot_name = f"after_main_login_click_{email.replace('@', '_at_').replace('.', '_')}.png"
        driver.save_screenshot(screenshot_name)
        print(f"Screenshot saved: {screenshot_name}")
        
        # Click Google login button with comprehensive strategies
        print("=== Looking for Google login button ===")
        
        google_strategies = [
            # Strategy 1: Vietnamese text variations
            ("//button[contains(text(), 'Đăng nhập với Google')]", "xpath"),
            ("//button[contains(text(), 'Google')]", "xpath"),
            ("//a[contains(text(), 'Đăng nhập với Google')]", "xpath"),
            ("//span[contains(text(), 'Đăng nhập với Google')]/parent::button", "xpath"),
            ("//div[contains(text(), 'Đăng nhập với Google')]/parent::button", "xpath"),
            
            # Strategy 2: English text variations
            ("//button[contains(text(), 'Sign in with Google')]", "xpath"),
            ("//button[contains(text(), 'Login with Google')]", "xpath"),
            ("//button[contains(text(), 'Continue with Google')]", "xpath"),
            
            # Strategy 3: Data attributes and classes
            ("button[data-provider='google']", "css"),
            ("button[data-action*='google']", "css"),
            ("a[data-provider='google']", "css"),
            (".google-login", "css"),
            (".btn-google", "css"),
            ("button[class*='google']", "css"),
            ("a[class*='google']", "css"),
            
            # Strategy 4: Look for buttons with Google icons/images
            ("button svg", "css"), # Check for SVG inside button
            
            # Strategy 5: Generic social login patterns
            (".social-login button", "css"),
            (".oauth-button", "css"),
            ("button[type='button']:not([data-action='loginRequired'])", "css"),
            
            # Strategy 6: Look in modal/popup content
            (".modal button", "css"),
            (".popup button", "css"),
            (".login-form button", "css"),
            (".auth-buttons button", "css")
        ]
        
        google_clicked = False
        
        for i, (selector, method) in enumerate(google_strategies):
            try:
                print(f"Strategy {i+1}: Trying {method} selector: {selector}")
                
                if method == "xpath":
                    buttons = driver.find_elements(By.XPATH, selector)
                else:
                    buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                
                print(f"Found {len(buttons)} elements with this selector")
                
                for j, button in enumerate(buttons):
                    try:
                        if button.is_displayed() and button.is_enabled():
                            # Get button text and attributes for analysis
                            button_text = (button.text or 
                                         button.get_attribute('aria-label') or 
                                         button.get_attribute('title') or 
                                         button.get_attribute('alt') or '').lower()
                            
                            button_html = button.get_attribute('outerHTML').lower()
                            
                            print(f"  Button {j+1}: text='{button_text[:50]}', tag='{button.tag_name}'")
                            
                            # Check if this is likely a Google login button
                            is_google_button = False
                            
                            # Text-based identification
                            google_keywords = ['google', 'gg', 'gmail']
                            login_keywords = ['đăng nhập', 'sign in', 'login', 'continue', 'tiếp tục']
                            
                            has_google = any(keyword in button_text for keyword in google_keywords)
                            has_login = any(keyword in button_text for keyword in login_keywords)
                            
                            if has_google and (has_login or not button_text):
                                is_google_button = True
                                print(f"    ✓ Identified by text: Google + login keywords")
                            
                            # HTML-based identification
                            elif 'google' in button_html and ('login' in button_html or 'auth' in button_html or 'oauth' in button_html):
                                is_google_button = True
                                print(f"    ✓ Identified by HTML: Google + auth keywords")
                            
                            # Icon/image-based identification (check for img/svg tags within)
                            elif (button.find_elements(By.TAG_NAME, "img") and 'google' in button_html) or \
                                 (button.find_elements(By.TAG_NAME, "svg") and len(button_text) < 20): # SVG often has no text
                                is_google_button = True
                                print(f"    ✓ Identified by icon/image")
                            
                            # Provider attribute identification
                            elif button.get_attribute('data-provider') == 'google':
                                is_google_button = True
                                print(f"    ✓ Identified by data-provider attribute")
                            
                            if is_google_button:
                                print(f"    🎯 Attempting to click Google button: '{button_text[:30] or 'icon button'}'")
                                
                                # Scroll to button
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                                time.sleep(1)
                                
                                # Highlight button for debugging
                                try:
                                    driver.execute_script("arguments[0].style.border='3px solid red';", button)
                                    time.sleep(0.5)
                                    driver.execute_script("arguments[0].style.border='';", button)
                                except:
                                    pass
                                
                                # Try multiple click methods
                                click_methods = [
                                    ("regular click", lambda: button.click()),
                                    ("javascript click", lambda: driver.execute_script("arguments[0].click();", button)),
                                    ("action chains", lambda: ActionChains(driver).move_to_element(button).click().perform())
                                ]
                                
                                for method_name, click_func in click_methods:
                                    try:
                                        click_func()
                                        google_clicked = True
                                        print(f"    ✅ Successfully clicked Google button using {method_name}")
                                        break
                                    except Exception as e_click:
                                        print(f"    ❌ {method_name} failed: {e_click}")
                                        continue
                                
                                if google_clicked:
                                    break
                                    
                    except Exception as e_button_proc:
                        print(f"  Error processing button {j+1}: {e_button_proc}")
                        continue
                
                if google_clicked:
                    break
                    
            except Exception as e_strategy:
                print(f"Strategy {i+1} failed: {e_strategy}")
                continue
        
        # If all strategies fail, try scanning all clickable elements
        if not google_clicked:
            print("=== Fallback: Scanning all clickable elements ===")
            try:
                all_clickable = driver.find_elements(By.CSS_SELECTOR, "button, a, div[onclick], span[onclick], input[type='button'], input[type='submit']")
                print(f"Found {len(all_clickable)} clickable elements")
                
                for k, element in enumerate(all_clickable):
                    try:
                        if element.is_displayed() and element.is_enabled():
                            element_text = (element.text or element.get_attribute('value') or '').lower()
                            element_html = element.get_attribute('outerHTML').lower()
                            
                            # Look for Google-related content
                            if (('google' in element_text and len(element_text) < 100) or
                                ('google' in element_html and ('login' in element_html or 'auth' in element_html)) or
                                ('gg' in element_text and len(element_text) < 50)):
                                
                                print(f"Fallback found potential Google element {k+1}: '{element_text[:50]}'")
                                
                                # Try to click
                                try:
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                    time.sleep(1)
                                    element.click()
                                    google_clicked = True
                                    print("✅ Successfully clicked Google element in fallback")
                                    break
                                except:
                                    try:
                                        driver.execute_script("arguments[0].click();", element)
                                        google_clicked = True
                                        print("✅ Successfully clicked Google element with JS in fallback")
                                        break
                                    except:
                                        continue
                                        
                    except:
                        continue
                        
            except Exception as e_fallback:
                print(f"Fallback scanning failed: {e_fallback}")
        
        if not google_clicked:
            print("❌ Could not click Google login button with any method")
            logging.error(f"Could not click Google login button for {email}")
            
            # Save page source and screenshot for debugging
            debug_screenshot = f"google_button_not_found_{email.replace('@', '_at_').replace('.', '_')}.png"
            driver.save_screenshot(debug_screenshot)
            
            return False
        
        print("✅ Google login button clicked successfully!")
        logging.info(f"Google login button clicked for {email}")
        
        time.sleep(5)
        
        # Handle popup window if exists
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])
            print("Switched to Google login popup")
        
        # Step 5: Use credentials to login
        success = handle_google_login_credentials(driver, email, password)
        
        if success:
            print(f"🎉 Login process completed successfully for {email}!")
            logging.info(f"Login process completed successfully for {email}")
            
            # Wait a bit more and check final status
            time.sleep(5)
            
            # Switch back to main window if needed (if popup was used for Google login)
            if 'accounts.google.com' not in driver.current_url and len(driver.window_handles) > 1:
                 if driver.current_window_handle != driver.window_handles[0]:
                    driver.switch_to.window(driver.window_handles[0])
                    print("Switched back to main window")
            
            # Handle the complete two-step consent process using the general handler
            print("=== STARTING GENERAL CONSENT PROCESS ===")
            consent_success = handle_consent_popups(driver) # Use the general handler
            
            if consent_success:
                print("✅ General consent process completed successfully!")
                logging.info(f"Consent process completed for {email}")
            else:
                print("⚠️  General consent process had issues or no popups found.")
                logging.warning(f"Consent process had issues for {email}")
            
            final_url = driver.current_url
            print(f"Final URL: {final_url}")
            
            if 'openedu' in final_url:
                print("✓ Successfully returned to OpenEdu course page")
                
                # Check if we're now logged in
                try:
                    user_elements = driver.find_elements(By.CSS_SELECTOR, 
                        ".user-name, .profile, .avatar, [data-testid='user-menu'], .user-info")
                    if user_elements:
                        print("✓ User appears to be logged in!")
                        
                        # Try to find user name or email
                        for element in user_elements:
                            text = element.text.strip()
                            if text and '@' in text:
                                print(f"Logged in as: {text}")
                                break
                            elif text:
                                print(f"User info: {text}")
                                break
                                
                except Exception as e_login_status:
                    print(f"Could not verify login status: {e_login_status}")
                    
                # FINAL STEP: Click "Bắt đầu khoá học" to start the course
                print("\n=== FINAL STEP: STARTING THE COURSE ===")
                course_started = start_course(driver)
                
                if course_started:
                    print("🎉 Course started successfully!")
                    print("🎓 You are now ready to learn!")
                    logging.info(f"Course started successfully for {email}")
                    return True
                else:
                    print("⚠️  Could not automatically start course - may need manual click")
                    logging.warning(f"Could not start course automatically for {email}")
                    return False
                    
                # Check if we can access the course content now
                try:
                    course_elements_check = driver.find_elements(By.CSS_SELECTOR, 
                        ".course-content, .lesson, .video, .start-course, .continue-course")
                    if course_elements_check:
                        print("✓ Course content is now accessible!")
                        return True
                except:
                    pass
                    
            else:
                print(f"Final destination: {final_url}")
                logging.warning(f"Final destination not OpenEdu for {email}: {final_url}")
                return False
                
        else:
            print(f"❌ Login process failed for {email}")
            logging.error(f"Login process failed for {email}")
            
            # Take screenshot for debugging
            debug_screenshot = f"login_failed_{email.replace('@', '_at_').replace('.', '_')}.png"
            driver.save_screenshot(debug_screenshot)
            print(f"Debug screenshot saved: {debug_screenshot}")
            return False
        
    except Exception as e_complete_login:
        print(f"Error in complete login for {email}: {e_complete_login}")
        logging.error(f"Exception in complete login for {email}: {e_complete_login}")
        return False
        
    finally:
        if driver:
            try:
                # Keep browser open for a short time for inspection (only for first email)
                time.sleep(2)
                driver.quit()
                print(f"Browser closed for {email}")
            except:
                pass

# Example usage with your credentials
if __name__ == "__main__":
    print("🚀 Starting COMPLETE OpenEdu automation process for MULTIPLE EMAILS...")
    print("📋 Process overview:")
    print("1. Read emails from emails.txt file")
    print("2. For each email:")
    print("   - Load OpenEdu course page")
    print("   - Click 'Đăng nhập để học'")
    print("   - Click 'Đăng nhập với Google'")
    print("   - Enter Google email")
    print("   - Enter Google password")
    print("   - Handle consent popups (e.g., 'Tôi hiểu', OAuth 'Continue')")
    print("   - Click 'Bắt đầu khoá học' (start course)")
    print("   - Access course content")
    print("3. Generate summary report")
    print("="*50)
    
    # Configuration
    EMAILS_FILE = "emails.txt"  # File containing emails, one per line
    GOOGLE_PASSWORD = "Truong3979"  # Same password for all emails
    
    # Run automation for multiple emails
    results = process_multiple_emails(EMAILS_FILE, GOOGLE_PASSWORD)
    
    print("🎉 Complete automation process finished for all emails!")

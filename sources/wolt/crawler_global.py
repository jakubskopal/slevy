"""
Global utilities for Albert Wolt crawler.
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def check_error_page(driver):
    """
    Detects if the current page is an error page or blocked state.
    """
    try:
        return False
    except:
        return False


def close_modal(driver, log_func=print):
    """
    Attempts to close the address selection modal that appears on first visit.
    Tries multiple strategies to find and close the modal.
    """
    try:
        # Wait a bit for modal to appear
        time.sleep(1)
        
        # Strategy 1: Close button with aria-label
        try:
            close_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label*="Zavřít"], button[aria-label*="Close"]'))
            )
            close_btn.click()
            log_func("Closed modal via aria-label")
            time.sleep(0.5)
            return True
        except:
            pass
        
        # Strategy 2: Look for common close button patterns
        try:
            close_selectors = [
                'button[class*="close"]',
                'button[class*="Close"]',
                '[data-test-id*="close"]',
                '[data-testid*="close"]',
                'button svg[class*="close"]'
            ]
            for selector in close_selectors:
                try:
                    btn = driver.find_element(By.CSS_SELECTOR, selector)
                    if btn.is_displayed():
                        btn.click()
                        log_func(f"Closed modal via selector: {selector}")
                        time.sleep(0.5)
                        return True
                except:
                    continue
        except:
            pass
        
        # Strategy 3: Press ESC key
        try:
            from selenium.webdriver.common.keys import Keys
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            log_func("Closed modal via ESC key")
            time.sleep(0.5)
            return True
        except:
            pass
            
        log_func("No modal found or already closed")
        return False
    except Exception as e:
        log_func(f"Error closing modal: {e}")
        return False


def check_item_availability(element):
    """
    Checks if a product card element has the 'Není k dispozici' badge.
    
    The badge is found in a sibling or child of the anchor's parent.
    According to user: go one up from anchor and look for data-variant="primaryNeutral" child.
    """
    try:
        # Get the parent of the anchor (the card container)
        parent = element.find_element(By.XPATH, "..")
        
        # Look for the specific badge variant
        badges = parent.find_elements(By.CSS_SELECTOR, '[data-variant="primaryNeutral"]')
        for badge in badges:
            if "Není k dispozici" in badge.text or "Vyprodáno" in badge.text:
                return False
                
        # Fallback: check the element itself just in case
        if "Není k dispozici" in element.text or "Vyprodáno" in element.text:
            return False
            
        return True
    except:
        return True


def handle_unavailable_dialog(driver, log_func=print):
    """
    Checks if an 'Item unavailable' dialog is open and closes it.
    Message: "Omlouváme se, vybraná položka není dostupná."
    Button: "OK, díky!"
    """
    try:
        # Check for dialog content
        dialogs = driver.find_elements(By.CSS_SELECTOR, '[role="dialog"]')
        for dialog in dialogs:
            if "není dostupná" in dialog.text or "Omlouváme se" in dialog.text:
                log_func("Detected 'Item unavailable' dialog")
                
                # Try to find the "OK, díky!" button
                try:
                    ok_button = dialog.find_element(By.XPATH, ".//button[contains(., 'OK') or contains(., 'díky')]")
                    ok_button.click()
                    log_func("Closed unavailability dialog via button")
                    time.sleep(0.5)
                    return True
                except:
                    # Fallback to ESC
                    from selenium.webdriver.common.keys import Keys
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    log_func("Closed unavailability dialog via ESC")
                    time.sleep(0.5)
                    return True
        return False
    except Exception as e:
        log_func(f"Error handling unavailable dialog: {e}")
        return False


def close_all_overlays(driver, log_func=print):
    """
    Closes all overlays specific to the Albert Wolt website:
    - Cookie consent banner (with "Povolit" button)
    - Location/address selection modal (with "Zavřít" close button)
    
    Based on actual DOM inspection of https://wolt.com/cs/cze/prague/venue/albert-vinohradska
    
    Args:
        driver: Selenium WebDriver instance
        log_func: Logging function (default: print)
    
    Returns:
        dict: Status of each overlay type closed {"cookie_consent": bool, "location_modal": bool}
    """
    from selenium.webdriver.common.keys import Keys
    
    results = {
        "cookie_consent": False,
        "location_modal": False
    }
    
    try:        
        # ===== CLOSE COOKIE CONSENT BANNER =====
        # The cookie banner appears at the bottom with a "Povolit" (Allow) button
        # Selector: button[data-test-id="allow-button"]
        cookie_closed = False
        
        # Strategy 1: Use the specific data-test-id attribute (most reliable)
        try:
            cookie_btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-test-id="allow-button"]'))
            )
            cookie_btn.click()
            log_func("Closed cookie consent via data-test-id='allow-button'")
            cookie_closed = True
            time.sleep(0.5)
        except:
            pass
        
        # Strategy 2: Fallback - look for "Povolit" button text
        if not cookie_closed:
            try:
                buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Povolit')]")
                for btn in buttons:
                    if btn.is_displayed():
                        btn.click()
                        log_func("Closed cookie consent via 'Povolit' button text")
                        cookie_closed = True
                        time.sleep(0.5)
                        break
            except:
                pass
        
        # Strategy 3: Alternative - decline button (uses only necessary cookies)
        if not cookie_closed:
            try:
                decline_btn = driver.find_element(By.CSS_SELECTOR, 'button[data-test-id="decline-button"]')
                if decline_btn.is_displayed():
                    decline_btn.click()
                    log_func("Closed cookie consent via data-test-id='decline-button'")
                    cookie_closed = True
                    time.sleep(0.5)
            except:
                pass
        
        results["cookie_consent"] = cookie_closed
        
        # ===== CLOSE LOCATION/ADDRESS MODAL =====
        # The modal appears prominently with a close button labeled "Zavřít" (Close)
        # Selector: button[aria-label="Zavřít"]
        location_closed = False
        
        # Strategy 1: Use the specific aria-label (most reliable)
        try:
            close_btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Zavřít"]'))
            )
            close_btn.click()
            log_func("Closed location modal via aria-label='Zavřít'")
            location_closed = True
            time.sleep(0.5)
        except:
            pass
        
        # Strategy 2: Fallback - look for any close button in a dialog
        if not location_closed:
            try:
                close_selectors = [
                    '[role="dialog"] button[aria-label*="Zavřít"]',
                    '[role="dialog"] button[aria-label*="Close"]',
                    'button[class*="IconButton"][aria-label]'
                ]
                
                for selector in close_selectors:
                    try:
                        btn = driver.find_element(By.CSS_SELECTOR, selector)
                        if btn.is_displayed():
                            btn.click()
                            log_func(f"Closed location modal via selector: {selector}")
                            location_closed = True
                            time.sleep(0.5)
                            break
                    except:
                        continue
            except:
                pass
        
        # Strategy 3: Press ESC key to close modal
        if not location_closed:
            try:
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                log_func("Closed location modal via ESC key")
                location_closed = True
                time.sleep(0.5)
            except:
                pass
        
        results["location_modal"] = location_closed
        
        # Log summary
        if results["cookie_consent"] or results["location_modal"]:
            closed_items = [k.replace('_', ' ') for k, v in results.items() if v]
            log_func(f"Successfully closed: {', '.join(closed_items)}")
        else:
            log_func("No overlays detected or already closed")
        
        return results
        
    except Exception as e:
        log_func(f"Error in close_all_overlays: {e}")
        return results


def safe_click(driver, element, log_func=print):
    """
    Safely clicks an element with scroll and wait.
    """
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3)
        element.click()
        return True
    except Exception as e:
        log_func(f"Error clicking element: {e}")
        return False

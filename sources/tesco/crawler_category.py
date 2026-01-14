import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

START_URL = "https://nakup.itesco.cz/groceries/cs-CZ/"

def click_btn(driver, selector, timeout=10):
    """
    Waits for an element to be clickable and clicks it with a JS scroll first.
    """
    try:
        wait = WebDriverWait(driver, timeout)
        btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
        time.sleep(0.3)
        btn.click()
        return True
    except: return False



def wait_for_category_page_ready(driver, log_func=print):
    """
    Waits for the category listing to fully load by checking for the pagination result count or product links.
    """
    # Wait for page load - look for specific elements indicating content is loaded
    try:
        WebDriverWait(driver, 10, 0.1).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="pagination-result-count"], a.gyT8MW_titleLink'))
        )
        time.sleep(1.0) # Small buffer for layout settlement
        return True
    except:
         log_func(f"Timeout waiting for category content to load")
         return False

def navigate_to_category(driver, cat_name, log_func=print):
    """
    Navigates to the main grocery page, handles cookies, opens the department menu,
    and drills down to the specified category.
    """
    driver.get(START_URL)
    time.sleep(1)
    
    # Reject cookies if prompt is displayed
    if not click_btn(driver, 'button#onetrust-reject-all-handler', timeout=3):
        click_btn(driver, 'button.ot-pc-refuse-all-handler', timeout=1)
    
    # Open menu - prioritized strategy based on investigation
    menu_clicked = False
    
    # Primary strategy: Direct JS click on the main ID (most reliable)
    try:
        btn = driver.find_element(By.CSS_SELECTOR, '#primary-nav-all-departments')
        driver.execute_script("arguments[0].click();", btn)
        menu_clicked = True
    except Exception as e:
        log_func(f"[{cat_name}] Primary menu click failed: {e}")
    
    # Fallback: Accessibility label
    if not menu_clicked:
        if click_btn(driver, 'button[aria-label="Všechny kategorie"]', timeout=3):
            menu_clicked = True

    if not menu_clicked:
        log_func(f"[{cat_name}] Could not click All Departments menu")
        return False

    time.sleep(2.0) # Wait for animation/render

    try:
        # Try to find the link with Wait - Use partial link text to safely handle whitespace
        wait = WebDriverWait(driver, 5)
        # Find all links and filter by text to be sure
        links = driver.find_elements(By.CSS_SELECTOR, ".ddsweb-local-navigation__submenu-item")
        cat_link = None
        for l in links:
            if cat_name in l.text: # looser match
                cat_link = l
                break
        
        if not cat_link:
            # Fallback
            cat_link = wait.until(EC.visibility_of_element_located((By.PARTIAL_LINK_TEXT, cat_name)))

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cat_link)
        time.sleep(0.5)
        # Click the item (submenu trigger) - prefer button inside if exists
        try:
            btn_in_link = cat_link.find_element(By.TAG_NAME, "button")
            driver.execute_script("arguments[0].click();", btn_in_link)
        except:
            driver.execute_script("arguments[0].click();", cat_link)
        time.sleep(1.0)
        
        # Now find the target "Show all" link scoped to this menu item
        target_link = None
        try:
            # cat_link is likely 'li > a' or 'li > button'
            # We need to find the parent 'li' and then the 'ul' inside it content
            parent_li = cat_link.find_element(By.XPATH, "./ancestor::li")
            # Find links in this LI
            sub_links = parent_li.find_elements(By.TAG_NAME, "a")
            
            for sl in sub_links:
                    txt = sl.get_attribute("innerText").strip()
                    # Check for standard "Show all" text
                    if "Zobrazit vše" in txt or "Vše v" in txt:
                        target_link = sl
                        break
            
            # If not found specific "Show all", maybe fallback to one that matches category name?
            if not target_link:
                    for sl in sub_links:
                        if cat_name in sl.get_attribute("innerText"):
                            target_link = sl
                            break
        except Exception as e:
            log_func(f"[{cat_name}] Error scouring submenu: {e}")
        
        if target_link:
            log_func(f"[{cat_name}] Clicking sub-link: {target_link.text}")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_link)
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", target_link)
        else:
            log_func(f"[{cat_name}] Could not find navigation link (All/Name) after opening menu.")

        if not wait_for_category_page_ready(driver, log_func):
            log_func(f"[{cat_name}] Failed to load category page content")
            return False
            
        return True
    except Exception as e:
        log_func(f"[{cat_name}] Failed to find category link: {e}")
        return False

def get_product_links(driver):
    """
    Scrapes the current view for product detail links using the specific class 'a.gyT8MW_titleLink'.
    """
    try:
        links = driver.find_elements(By.CSS_SELECTOR, 'a.gyT8MW_titleLink')
        hrefs = [l.get_attribute('href') for l in links if l.get_attribute('href') and '/products/' in l.get_attribute('href')]
        return hrefs
    except:
        return []

def click_product_link(driver, href):
    """
    Finds a product link by matching its href and clicks it.
    """
    try:
        current_links = driver.find_elements(By.CSS_SELECTOR, 'a.gyT8MW_titleLink')
        target = None
        for cl in current_links:
            if cl.get_attribute('href') == href:
                target = cl
                break
        
        if target:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target)
            time.sleep(0.1)
            target.click()
            return True
    except:
        pass
    return False

def click_next_page(driver):
    """
    Finds and clicks the 'Next' pagination button if it is available and not disabled.
    """
    next_btn = None
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, 'a[aria-label="Další"], a[rel="next"]')
    except: pass

    if next_btn and next_btn.is_displayed() and "disabled" not in next_btn.get_attribute("class"):
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", next_btn)
        return True
    return False

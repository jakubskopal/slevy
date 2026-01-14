
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def debug_submenu():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,1024")
    options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        url = "https://nakup.itesco.cz/groceries/cs-CZ/"
        print(f"Navigating to {url}")
        driver.get(url)
        time.sleep(2)
        
        # Cookie consent
        try:
            btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "onetrust-reject-all-handler")))
            btn.click()
            print("Rejected cookies.")
        except: pass
        time.sleep(1)

        # Open menu
        print("Opening menu...")
        try:
            btn = driver.find_element(By.CSS_SELECTOR, '#primary-nav-all-departments')
            driver.execute_script("arguments[0].click();", btn)
        except Exception as e:
            print(f"Failed to click menu: {e}")
            return
        time.sleep(2)

        # Click "Ovoce a zelenina"
        cat_name = "Ovoce a zelenina"
        print(f"Clicking category: {cat_name}")
        
        links = driver.find_elements(By.CSS_SELECTOR, ".ddsweb-local-navigation__submenu-item")
        cat_link = None
        for l in links:
            if cat_name in l.text:
                cat_link = l
                break
        
        if not cat_link:
            print("Category link not found via submenu-item selector! Trying partial text...")
            try:
                cat_link = driver.find_element(By.PARTIAL_LINK_TEXT, cat_name)
            except:
                print("Not found at all.")
                return

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cat_link)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", cat_link)
        print("Clicked category.")
        time.sleep(2.0)
        
        # Inspect what links are visible now
        print("\n--- Links containing 'vše' or 'All' ---")
        visible_links = driver.find_elements(By.TAG_NAME, "a")
        found_any = False
        for l in visible_links:
            if l.is_displayed():
                txt = l.text.strip()
                if "vše" in txt.lower() or "all" in txt.lower() or cat_name in txt:
                     print(f"Link: '{txt}' | Class: {l.get_attribute('class')} | Href: {l.get_attribute('href')}")
                     found_any = True
        
        if not found_any:
            print("No 'vše' links found.")
        
        # Dump screenshot? No, just text.

    finally:
        driver.quit()

if __name__ == "__main__":
    debug_submenu()

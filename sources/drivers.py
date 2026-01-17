
import os
import random
import threading
import uuid
import glob
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

# Global cache for driver paths to prevent API rate limits
_CACHED_GECKO_PATH = None
_CACHED_CHROME_PATH = None
_DRIVER_INSTALL_LOCK = threading.Lock()

def _get_or_install_driver(browser_type):
    global _CACHED_GECKO_PATH, _CACHED_CHROME_PATH
    
    is_firefox = browser_type.lower() == 'firefox'
    cached_path = _CACHED_GECKO_PATH if is_firefox else _CACHED_CHROME_PATH
    
    if cached_path:
        return cached_path
        
    with _DRIVER_INSTALL_LOCK:
        cached_path = _CACHED_GECKO_PATH if is_firefox else _CACHED_CHROME_PATH
        if cached_path:
            return cached_path
            
        try:
            if is_firefox:
                path = GeckoDriverManager().install()
                _CACHED_GECKO_PATH = path
            else:
                path = ChromeDriverManager().install()
                _CACHED_CHROME_PATH = path
            return path
        except Exception as e:
            print(f"Failed to install driver ({e}), searching offline cache...")
            driver_name = "geckodriver" if is_firefox else "chromedriver"
            wdm_path = os.path.expanduser(f"~/.wdm/drivers/{driver_name}")
            found = glob.glob(f"{wdm_path}/**/{driver_name}", recursive=True)
            
            if found:
                path = found[-1]
                print(f"Found offline driver: {path}")
                if is_firefox:
                    _CACHED_GECKO_PATH = path
                else:
                    _CACHED_CHROME_PATH = path
                return path
            else:
                raise e

def create_driver(headless=False, browser_type='chrome'):
    """
    Creates and configures a WebDriver instance.
    """
    if browser_type.lower() == 'firefox':
        # Use a unique local tmp directory for each driver to avoid conflicts
        local_tmp = os.path.abspath(os.path.join("data", "sessions", f"tmp_gecko_{uuid.uuid4()}"))
        os.makedirs(local_tmp, exist_ok=True)
        
        options = webdriver.FirefoxOptions()
        if headless:
            options.add_argument("--headless")
        
        # Must copy environment to preserve PATH
        env = os.environ.copy()
        env["TMPDIR"] = local_tmp
        
        executable_path = _get_or_install_driver('firefox')

        driver = webdriver.Firefox(
            service=FirefoxService(executable_path, env=env),
            options=options
        )
        driver.set_window_size(1280, 1024)
        return driver
    
    # Default to Chrome
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,1024")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Random window position for visibility
    x = random.randint(0, 500)
    y = random.randint(0, 500)
    options.add_argument(f"--window-position={x},{y}")
    options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36")
    
    executable_path = _get_or_install_driver('chrome')

    driver = webdriver.Chrome(
        service=ChromeService(executable_path),
        options=options
    )
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

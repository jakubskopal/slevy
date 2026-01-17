
import os
import random
import threading
import uuid
import glob
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options
import logging
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

logger = logging.getLogger(__name__)

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
            logger.warning(f"Failed to install driver ({e}), searching offline cache...")
            driver_name = "geckodriver" if is_firefox else "chromedriver"
            wdm_path = os.path.expanduser(f"~/.wdm/drivers/{driver_name}")
            found = glob.glob(f"{wdm_path}/**/{driver_name}", recursive=True)
            
            if found:
                path = found[-1]
                logger.info(f"Found offline driver: {path}")
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


import queue

class DriverPool:
    def __init__(self, factory_func, max_size=0):
        """
        Thread-safe pool for reusing WebDriver instances.
        
        Args:
            factory_func: Function to create a new driver instance.
            max_size: Maximum number of drivers to hold in the pool (0 = unlimited).
        """
        self.factory_func = factory_func
        self.max_size = max_size
        self._pool = queue.Queue(maxsize=max_size)
        self._created_count = 0
        self._lock = threading.Lock()
        self._active_drivers = set()

    def acquire(self):
        """
        Retrieves a driver from the pool or creates a new one if empty.
        """
        try:
            # Try to get an idle driver (non-blocking)
            driver = self._pool.get_nowait()
            # Optional: Check if driver is still alive?
            # For now, assume it is. If it crashed, usage will raise exception and we handle it.
            return driver
        except queue.Empty:
            # Create new driver
            with self._lock:
                self._created_count += 1
            driver = self.factory_func()
            with self._lock:
                self._active_drivers.add(driver)
            return driver

    def release(self, driver):
        """
        Returns a driver to the pool for reuse.
        """
        if driver is None:
            return

        try:
            # Reset driver state if possible (clear cookies, etc)
            # This is important for some sites, but for maintaining session (if desired) we might not want to.
            # User note: "drivers will be kept alive and reused". 
            # We'll just delete cookies to be safe/clean per task?
            # User didn't specify, but usually "reuse" for scraping implies reusing the *browser instance*.
            # If we want to simulate "fresh" user, we clear cookies.
            # If we want to keep session, we don't. 
            # Given we are scraping public data, clearing cookies is safer to avoid tracking accumulation.
            driver.delete_all_cookies()
        except:
            # If driver is dead, don't return to pool
            self._discard(driver)
            return

        try:
            self._pool.put_nowait(driver)
        except queue.Full:
            # If pool is full (shouldn't happen if unlimited), just close it
            self._discard(driver)

    def _discard(self, driver):
        with self._lock:
            if driver in self._active_drivers:
                self._active_drivers.remove(driver)
        try:
            driver.quit()
        except:
            pass

    def quit_all(self):
        """
        Closes all drivers in the pool and currently active ones (best effort).
        """
        # Close idle drivers
        while not self._pool.empty():
            try:
                driver = self._pool.get_nowait()
                self._discard(driver)
            except:
                pass
        
        # Close active drivers? 
        # We can't force close active drivers easily without tracking them and potentially disrupting threads.
        # But we track them in _active_drivers.
        with self._lock:
            for driver in list(self._active_drivers):
                try:
                    driver.quit()
                except:
                    pass
            self._active_drivers.clear()

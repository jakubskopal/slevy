"""
Albert Wolt Crawler: Parallel Selenium-based crawler for Albert Vinohradská on Wolt.
Navigates through categories and products, handling infinite scroll pagination.
"""
import os
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor

from . import crawler_category






VENUES = {
    "albert": {
        "name": "Albert",
        "url": "https://wolt.com/cs/cze/prague/venue/albert-vinohradska",
        "dir": "data/albert_raw"
    },
    "billa": {
        "name": "Billa",
        "url": "https://wolt.com/cs/cze/prague/venue/billa-malesice",
        "dir": "data/billa_raw"
    },
    "globus": {
        "name": "Globus",
        "url": "https://wolt.com/cs/cze/prague/venue/globus-sterboholy",
        "dir": "data/globus_raw"
    }
}


class CrawlerState:
    def __init__(self, filepath):
        self.filepath = filepath
        self.lock = threading.Lock()
        self.data = self.load()

    def load(self):
        """
        Loads the crawler state from the JSON file.
        """
        default = {
            "categories": [],
            "tree": {}
        }
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                    default["categories"] = data.get("categories", [])
                    default["tree"] = data.get("tree", {})
            except:
                pass
        return default

    def save(self):
        """
        Persists the current state to disk atomically.
        """
        with self.lock:
            # Reload from disk to merge changes
            on_disk = {}
            if os.path.exists(self.filepath):
                try:
                    with open(self.filepath, 'r') as f:
                        on_disk = json.load(f)
                except:
                    pass
            
            # Merge categories
            disk_cats = on_disk.get("categories", [])
            merged_cats = list(set(self.data["categories"]) | set(disk_cats))
            self.data["categories"] = merged_cats
            
            # Merge tree
            disk_tree = on_disk.get("tree", {})
            def merge_trees(d1, d2):
                for k, v in d2.items():
                    if k in d1 and isinstance(d1[k], dict) and isinstance(v, dict):
                        merge_trees(d1[k], v)
                    else:
                        d1[k] = v
            merge_trees(self.data["tree"], disk_tree)
            
            # Save
            to_save = {
                "categories": self.data["categories"],
                "tree": self.data["tree"]
            }
            
            temp_path = self.filepath + ".tmp"
            with open(temp_path, 'w') as f:
                json.dump(to_save, f, indent=2)
            os.replace(temp_path, self.filepath)

    def mark_category(self, category_url, cat_names=None):
        """
        Marks a category as discovered and builds the category tree.
        """
        with self.lock:
            if category_url not in self.data["categories"]:
                self.data["categories"].append(category_url)
            
            if cat_names:
                curr = self.data["tree"]
                for name in cat_names:
                    if name not in curr:
                        curr[name] = {}
                    curr = curr[name]


class GlobalCounter:
    def __init__(self, limit):
        self.limit = limit
        self.count = 0
        self.lock = threading.Lock()
    
    def increment(self):
        with self.lock:
            self.count += 1
            return self.count <= self.limit if self.limit > 0 else True

    def is_reached(self):
        with self.lock:
            return self.limit > 0 and self.count >= self.limit


class WoltWorker:
    def __init__(self, state, start_url, raw_data_dir, driver_pool, global_counter, console=None):
        self.start_url = start_url
        self.state = state
        self.console = console
        self.base_dir = raw_data_dir
        self.global_counter = global_counter
        self.driver_pool = driver_pool
        self.driver = driver_pool.acquire()

    def log(self, msg):
        """
        Logs a message to the console handler or standard output.
        """
        if self.console:
            self.console.log(msg)
        else:
            print(msg)

    def crawl_category(self, cat_names, cat_url, log_func, limit=0):
        """
        Crawls a single category, scrolling to load all products and visiting each one.
        
        Returns:
            bool: True if successful, False if retry needed
        """
        if self.global_counter.is_reached():
            return True

        log_func(f"Worker starting category: {' > '.join(cat_names)}", notice=True)
        
        # Navigate to category
        if not crawler_category.navigate_to_category(self.driver, cat_url, log_func):
            return False
        
        products = crawler_category.scroll_and_load_all_products(
            self.driver, 
            self.base_dir, 
            cat_names, 
            log_func, 
            self.global_counter, 
            console=self.console
        )     
        log_func(f"Found {len(products)} total products")
            
        # Save progress
        self.state.save()
        log_func(f"Worker finished category")
        return True

    def quit(self):
        """
        Releases the browser driver instance back to the pool.
        """
        self.driver_pool.release(self.driver)


def run_worker(cat_info, state, start_url, raw_data_dir, console, driver_pool, global_counter, index, limit):
    """
    Worker entry point for crawling a single category with restart on failure.
    """
    cat_names, cat_url = cat_info
    time.sleep(index % 5)  # Stagger starts
    
    # Define common log method with category prefix
    prefix = f"[{' < '.join(cat_names)}] "
    def log_func(msg, notice=False):
        full_msg = f"{prefix}{msg}"
        if console:
            console.log(full_msg, notice=notice)
        else:
            print(full_msg)
    
    while True:
        if global_counter.is_reached():
             break

        worker = WoltWorker(state, start_url, raw_data_dir, driver_pool, global_counter, console=console)
        try:
            success = worker.crawl_category(cat_names, cat_url, log_func, limit=limit)
            if success:
                break
            else:
                log_func("Task failed. Restarting category...")
        except Exception as e:
            log_func(f"Critical error: {e}. Restarting...")
        finally:
            worker.quit()
        
        time.sleep(5)  # Cooldown before restart






class WoltCrawler:
    def __init__(self, start_url, raw_data_dir, driver_factory, workers=2, limit=0, console=None):
        self.start_url = start_url
        self.raw_data_dir = raw_data_dir
        self.workers = workers
        self.driver_factory = driver_factory
        self.limit = limit
        self.console = console  # Console passed from main
        self.global_counter = GlobalCounter(limit)
        
        from drivers import DriverPool
        self.pool = DriverPool(driver_factory)
        
        # Ensure output dir exists
        os.makedirs(self.raw_data_dir, exist_ok=True)
        
        state_path = os.path.join(self.raw_data_dir, "crawler_state.json")
        self.state = CrawlerState(state_path)

    def run(self):
        """
        Discovers categories, scans for total count, and spawns worker threads.
        """
        # Discover categories
        log_func = self.console.log if self.console else print
        log_func(f"Discovering categories for {self.start_url}...")
        
        # We can use the pool for discovery too
        temp_driver = self.pool.acquire()
        try:
            categories = crawler_category.discover_categories(temp_driver, self.start_url, log_func)
        finally:
            self.pool.release(temp_driver)
        
        if not categories:
            log_func("No categories found!")
            return
        
        # Save discovered categories
        for cat_names, cat_url in categories:
            self.state.mark_category(cat_url, cat_names=cat_names)
        self.state.save()
        
        log_func(f"Found {len(categories)} categories. Starting Crawl Phase...")
        
        # CRAWL PHASE
        try:
            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                # We map using the pool instead of factory now
                executor.map(
                    lambda x: run_worker(x[1], self.state, self.start_url, self.raw_data_dir, self.console, self.pool, self.global_counter, x[0], self.limit),
                    enumerate(categories)
                )
        finally:
            self.pool.quit_all()





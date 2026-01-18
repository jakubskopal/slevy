"""
Tesco Crawler: Parallel Selenium-based crawler.
Navigates exclusively by clicking. Supports multi-window parallelism and resume.
"""
import os
import time
import gzip
import urllib.parse
import json
import threading


from . import crawler_category
from .crawler_product import extract_product_data, wait_for_product_page_ready


# Categories to crawl
CATEGORIES = [
    "Ovoce a zelenina",
    "Mléčné, vejce a margaríny",
    "Pekárna",
    "Maso a lahůdky",
    "Mražené",
    "Trvanlivé",
    "Nápoje",
    "Speciální výživa",
    "Úklid",
    "Drogerie",
    "Dítě",
    "Zvíře",
    "Domov a zábava"
]

class CrawlerState:
    def __init__(self, filepath="data/tesco_raw/tesco_state.json"):
        self.filepath = filepath
        self.lock = threading.Lock()
        self.data = self.load()

    def load(self):
        """
        Loads the crawler state from the JSON file, preserving only processed products and the category tree structure.
        """
        default = {
            "processed_products": [],
            "tree": {} # Hierarchy
        }
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                    # Only preserve products and tree
                    default["processed_products"] = data.get("processed_products", [])
                    default["tree"] = data.get("tree", {})
            except: pass
        return default

    def save(self):
        """
        Persists the current state (processed products and hierarchy tree) to disk atomically.
        """
        with self.lock:
            # Atomic-ish persistence: reload from disk to ensure we don't lose
            # changes from other parallel workers/processes
            on_disk = {}
            if os.path.exists(self.filepath):
                try:
                    with open(self.filepath, 'r') as f:
                         on_disk = json.load(f)
                except: pass
            
            # Merge processed_products list
            disk_prods = on_disk.get("processed_products", [])
            merged_products = list(set(self.data["processed_products"]) | set(disk_prods))
            self.data["processed_products"] = merged_products
            
            # Merge Tree
            disk_tree = on_disk.get("tree", {})
            def merge_trees(d1, d2):
                for k, v in d2.items():
                    if k in d1 and isinstance(d1[k], dict) and isinstance(v, dict):
                        merge_trees(d1[k], v)
                    else:
                        d1[k] = v
            merge_trees(self.data["tree"], disk_tree)
            
            # Only save products and tree
            to_save = {
                "processed_products": self.data["processed_products"],
                "tree": self.data["tree"]
            }
            
            temp_path = self.filepath + ".tmp"
            with open(temp_path, 'w') as f:
                json.dump(to_save, f, indent=2)
            os.replace(temp_path, self.filepath)

    def mark_product(self, href, breadcrumbs=None):
        """
        Marks a product URL as processed and updates the category tree with its breadcrumbs.
        """
        with self.lock:
            if href not in self.data["processed_products"]:
                self.data["processed_products"].append(href)
            
            if breadcrumbs:
                curr = self.data["tree"]
                for b in breadcrumbs:
                    if b not in curr:
                        curr[b] = {}
                    curr = curr[b]






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


class TescoWorker:
    def __init__(self, state, console=None, base_dir="data/tesco_raw", driver_pool=None, global_counter=None):
        self.start_url = "https://nakup.itesco.cz/groceries/cs-CZ/"
        self.state = state
        self.console = console
        self.base_dir = base_dir
        self.global_counter = global_counter
        self.driver_pool = driver_pool
        self.driver = driver_pool.acquire()

    # extract_product_data moved to crawler_product.py

    def log(self, msg, notice=False):
        """
        Logs a message to the console handler or standard output.
        """
        if self.console:
            self.console.log(msg, notice=notice)
        else:
            print(msg)

    def crawl_category(self, cat_name, limit=0):
        """
        Crawls a single category, navigating through pagination and visiting individual product pages
        to extract data. returns True if successful, False if a retry is needed.
        """
        if self.global_counter and self.global_counter.is_reached():
             return True

        self.log(f"Worker starting category: {cat_name}", notice=True)
        if not crawler_category.navigate_to_category(self.driver, cat_name, self.log):
            return False

        page_num = 1
        # Always start from page 1


        while True:
            # Check global limit
            if self.global_counter and self.global_counter.is_reached():
                 self.log(f"[{cat_name}] Global limit reached. Stopping.")
                 return True

            if "Access Denied" in self.driver.page_source:
                self.log(f"[{cat_name}] Access Denied. Cooling down...")
                time.sleep(60)
                self.driver.refresh()
                continue

            hrefs = crawler_category.get_product_links(self.driver)
            if not hrefs:
                 # If we found no products on page 1, might be empty category or error.
                 # If page > 1, it might be end of list, but usually next_page check handles that.
                 # If we are here, something might be wrong with loading.
                 if page_num == 1:
                     self.log(f"[{cat_name}] No products found on page 1. Potentially failed load.")
                     return False
                 break

            self.log(f"[{cat_name}] Page {page_num}: Found {len(hrefs)} products")
            
            products_in_cat = 0
            for idx, href in enumerate(hrefs):
                if limit > 0 and products_in_cat >= limit:
                   self.log(f"[{cat_name}] Reached limit of {limit} products.")
                   return True

                if href in self.state.data["processed_products"]:
                    continue
                
                try:
                    if crawler_category.click_product_link(self.driver, href):
                        if not wait_for_product_page_ready(self.driver, self.log):
                            self.log(f"[{cat_name}/{page_num}] Failed to load product page for {href}")
                            # If product page fails, we might want to restart category or continue. 
                            # User said "if a category OR product page do not load properly... interrupted" implies restart.
                            return False
                        
                        # Extract data directly from DOM
                        preparsed_data = extract_product_data(self.driver)
                        
                        # Extract breadcrumbs (also included in preparsed_data for convenience)
                        breadcrumbs = preparsed_data.get('breadcrumbs', [])
                        
                        # Save with preparsed data
                        filename = self.save_html(self.driver.page_source, self.driver.current_url, preparsed_data)
                        
                        # Logging
                        product_id = href.split('/')[-1]
                        prod_name = preparsed_data.get('name', 'Unknown')


                        self.log(f"[{cat_name}/{page_num}] {prod_name}")

                        self.state.mark_product(href, breadcrumbs=breadcrumbs)
                        products_in_cat += 1
                        
                        if self.console:
                            total_prod = len(self.state.data["processed_products"])
                            
                            # Dynamically update total if we exceed it
                            if hasattr(self.console, 'total') and total_prod >= self.console.total:
                                self.console.total = total_prod + 500
                                
                            self.console.update(total_prod, stats=f"Cats: --/{len(CATEGORIES)}")
                        
                        # Increment global counter
                        if self.global_counter:
                            if not self.global_counter.increment():
                                self.log(f"[{cat_name}] Global limit reached. Stopping.")
                                return True

                        self.driver.back()
                        if not crawler_category.wait_for_category_page_ready(self.driver, self.log):
                             self.log(f"[{cat_name}] Failed to reload category listing")
                             return False
                except Exception as e:
                    self.log(f"[{cat_name}/{page_num}] Product error: {e}")
                    # If error is severe enough, return False to restart
                    return False
            
            if limit > 0 and products_in_cat >= limit:
                 return True

            # Save progress after finishing page
            self.state.save()

            if crawler_category.click_next_page(self.driver):
                self.log(f"[{cat_name}] Moving to page {page_num + 1}...")
                
                # Wait for load using specific elements
                if not crawler_category.wait_for_category_page_ready(self.driver, self.log):
                    self.log(f"[{cat_name}] Failed to load next page content") 
                    return False
                
                page_num += 1
                self.state.save()
            else:
                self.log(f"[{cat_name}] No next page found. Completing category.")
                if self.console:
                    total_prod = len(self.state.data["processed_products"])
                    self.console.update(total_prod, stats=f"Cats: --/{len(CATEGORIES)}")
                self.state.save()
                break

        self.log(f"Worker finished category: {cat_name}")
        return True

    def save_html(self, content, url, preparsed_data=None):
        """
        Compresses and saves the HTML content to a gzipped file, including metadata in a header comment.
        """
        parsed = urllib.parse.urlparse(url)
        name = parsed.path.strip('/').replace('/', '_')
        filepath = os.path.join(self.base_dir, name + ".html.gz")
        
        meta = {
            "origin_url": url,
            "preparsed": preparsed_data or {}
        }
        # Save meta as a JSON comment at the top
        comment = f"<!-- META_JSON: {json.dumps(meta, ensure_ascii=False)} -->\n".encode('utf-8')
        
        temp_path = filepath + ".tmp"
        with gzip.open(temp_path, 'wb') as f:
            f.write(comment + content.encode('utf-8'))
        os.replace(temp_path, filepath)
        return filepath

    def quit(self):
        """
        Releases the browser driver instance back to the pool.
        """
        self.driver_pool.release(self.driver)

def run_worker(cat_name, state, console, driver_pool, global_counter, index, limit):
    """
    Worker entry point that manages the lifecycle of a single category crawl, including
    restarts on failure.
    """
    # Reduced stagger
    time.sleep(index * 1)
    
    while True:
        if global_counter and global_counter.is_reached():
             break

        worker = TescoWorker(state, console=console, driver_pool=driver_pool, global_counter=global_counter)
        try:
            success = worker.crawl_category(cat_name, limit=limit)
            if success:
                break
            else:
                console.log(f"[{cat_name}] Task failed or interrupted. Restarting category from scratch in new window...")
        except Exception as e:
            console.log(f"[{cat_name}] Critical worker error: {e}. Restarting...")
        finally:
            worker.quit()
        
        time.sleep(5) # Cooldown before restart



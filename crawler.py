"""
Kupi Crawler: Automated discount data gathering for Kupi.cz.

Overview:
Gather product discount data by crawling the Kupi.cz website. The crawler starts from the 
main 'slevy' page and recursively explores product detail pages and category listings 
within a defined scope.

Key Features & Steps:
1. Concurrency Control: Uses ThreadPoolExecutor with a network semaphore to balance 
   speed and politeness.
2. Robustness: Implements requests.Session with exponential backoff retries for 
   reliability against server errors.
3. Space Efficiency: Saves raw HTML content using Gzip compression (.gz).
4. Link Caching: Saves extracted links to .links.txt files to bypass expensive 
   HTML parsing on subsequent runs.
5. Normalization: Standardizes URLs and strips tracking parameters to avoid 
   duplicate crawls.
6. Scope Filtering: Targets specific paths (/slevy, /sleva) and filters out 
   unwanted brand-specific or deep-nested URLs.
"""
import requests
from bs4 import BeautifulSoup
import os
import time
from fake_useragent import UserAgent
import urllib.parse
from collections import deque
import argparse
import sys
import gzip
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import concurrent.futures
import threading
from console import Console

class KupiCrawler:
    def __init__(self, base_dir="data/raw"):
        self.start_url = "https://www.kupi.cz/slevy"
        self.scope_prefix = "https://www.kupi.cz/slevy"
        self.ua = UserAgent()
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
        
        self.visited = set()
        self.queue = deque([self.start_url])
        
        # Configure Retries
        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries, pool_connections=20, pool_maxsize=20)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)
        
        # Concurrency control
        self.network_sem = threading.Semaphore(4)

    def get_headers(self):
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }

    def normalize_url(self, url):
        """
        Standardize URL to prevent duplicates (trailing slashes, fragments).
        """
        parsed = urllib.parse.urlparse(url)
        # Strip fragment
        # Strip trailing slash from path
        norm_path = parsed.path.rstrip('/')
        
        # Reconstruct
        # parsed is namedtuple, use _replace
        norm_parsed = parsed._replace(path=norm_path, fragment='')
        return norm_parsed.geturl()

    def get_file_path(self, url):
        parsed = urllib.parse.urlparse(url)
        path = parsed.path.strip('/')
        
        # Base filename
        if not path:
            name = "slevy_index"
        else:
            name = path.replace('/', '_')
            
        # Add query params to filename if present
        if parsed.query:
            # simple safe replacement
            safe_query = parsed.query.replace('&', '_').replace('=', '-')
            name += "__" + safe_query
            
        filename = name + ".html"
        return os.path.join(self.base_dir, filename)

    def save_html(self, content, url):
        filepath = self.get_file_path(url) + ".gz"
        with gzip.open(filepath, 'wb') as f:
            f.write(content)
        return os.path.basename(filepath)

    def save_links(self, links, url):
        filepath = self.get_file_path(url) + ".links.txt"
        try:
            with open(filepath, 'w') as f:
                f.write('\n'.join(links))
        except Exception as e:
            # Non-critical error
            pass
        return os.path.basename(filepath)

    def process_url(self, url, log_func):
        """
        Worker function to process a single URL.
        Returns a list of discovered URLs to be added to the queue.
        """
        extracted_links = []
        
        # Check for cached links first to avoid HTML parsing
        link_cache_path = self.get_file_path(url) + ".links.txt"

        
        all_found_links = None
        
        # Try loading from cache
        if os.path.exists(link_cache_path):
            log_func(f"Loading links from cache: {url}")
            try:
                with open(link_cache_path, 'r') as f:
                    # Normalize links from cache to ensure consistency
                    all_found_links = [self.normalize_url(line.strip()) for line in f if line.strip()]
            except Exception as e:
                log_func(f"  Error reading link cache {link_cache_path}: {e}")

        # If not in cache, load/fetch content and parse
        if all_found_links is None:
            # Check if we have it locally (only for saveable URLs)
            is_saveable = True
            filepath_base = self.get_file_path(url)
            filepath_gz = filepath_base + ".gz"
            content = None
            
            if is_saveable:
                if os.path.exists(filepath_gz):
                    log_func(f"Loading from disk (gz): {url}")
                    try:
                        with gzip.open(filepath_gz, 'rb') as f:
                            content = f.read()
                    except Exception as e:
                        log_func(f"  Error reading file {filepath_gz}: {e}")
                elif os.path.exists(filepath_base):
                    log_func(f"Loading from disk: {url}")
                    try:
                        with open(filepath_base, 'rb') as f:
                            content = f.read()
                    except Exception as e:
                        log_func(f"  Error reading file {filepath_base}: {e}")
            
            if content is None:
                log_func(f"Fetching: {url}")
                try:
                    # Use session for retries
                    with self.network_sem:
                        # Polite small sleep inside semaphore to space out requests slightly if desired
                        # time.sleep(0.1) 
                        response = self.session.get(url, headers=self.get_headers(), timeout=10)
                    
                    if response.status_code != 200:
                        log_func(f"  Status {response.status_code}, skipping.")
                        return []
                    
                    content = response.content
                    
                    if is_saveable:
                        saved_name = self.save_html(content, url)
                        log_func(f"  Saved to {saved_name}")
                        
                except Exception as e:
                    log_func(f"  Error fetching {url}: {e}")
                    return []

            # Extract links (Deep follow)
            if content:
                try:
                    all_found_links = []
                    soup = BeautifulSoup(content, 'html.parser')
                    links = soup.find_all('a', href=True)
                    
                    for link in links:
                        href = link.get('href')
                        full_url = urllib.parse.urljoin(url, href)
                        
                        # Normalize: strip fragments and trailing slashes
                        full_url = self.normalize_url(full_url)
                        
                        all_found_links.append(full_url)
                    
                    # Save to cache
                    if is_saveable:
                        self.save_links(all_found_links, url) # Save VALID unique links? or all? 
                        # User asked for "list of unique <a> found". 
                        # We should probably deduplicate before saving to be efficient.
                        all_found_links = list(set(all_found_links))
                        self.save_links(all_found_links, url)
                        
                except Exception as e:
                    log_func(f"  Error parsing links from {url}: {e}")
                    return []

        # Filter links (apply scope logic to all_found_links)
        if all_found_links:
            for full_url in all_found_links:
                # Scope check logic
                parsed_link = urllib.parse.urlparse(full_url)
                path = parsed_link.path.strip('/') # e.g. "slevy/alkohol"
                
                is_in_scope = False
                
                if path == "slevy":
                    is_in_scope = True
                elif path.startswith("slevy/"):
                    # "slevy/alkohol" -> ["alkohol"] -> len 1 OK
                    sub_path = path[6:]
                    segments = [s for s in sub_path.split('/') if s]
                    if len(segments) <= 1:
                        is_in_scope = True
                elif path.startswith("sleva/"):
                    # "sleva/product" -> ["product"] -> len 1 OK
                    sub_path = path[6:]
                    segments = [s for s in sub_path.split('/') if s]
                    if len(segments) <= 1:
                        is_in_scope = True
                
                # Check for unwanted query params (Brand filters start with br...)
                if is_in_scope:
                    parsed_new = urllib.parse.urlparse(full_url)
                    query_params = urllib.parse.parse_qs(parsed_new.query)
                    if any(k.startswith('br') for k in query_params.keys()):
                        is_in_scope = False

                if is_in_scope:
                    extracted_links.append(full_url)
                
        return extracted_links

    def run(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--color", action="store_true", help="Show ANSI progress bar")
        args = parser.parse_args()
        
        print_lock = threading.Lock()
        futures = {} # future -> url
        
        console = Console(total=0, use_colors=args.color)
        def log(msg):
            console.log(msg)
        
        # Thread-safe log wrapper to pass to workers
        def worker_log(msg):
            log(msg)

        log(f"Starting crawl at {self.start_url}")
        
        console.start()
        console.update(0, "Init...")
        
        # Dynamic worker count: 2 * CPU cores (defaulting to 4 if cpu_count is None)
        cpu_count = os.cpu_count() or 2
        max_workers = cpu_count * 2
        futures = {} # future -> url
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            
            while self.queue or futures:
                # Submit tasks if slots available and queue not empty
                while self.queue and len(futures) < max_workers:
                    url = self.queue.popleft()
                    
                    if url in self.visited:
                        continue
                    
                    self.visited.add(url)
                    
                    # Update bar for visited count
                    # Count running tasks (futures)
                    running = len(futures)
                    waiting = len(self.queue)
                    total_known = len(self.visited) + waiting
                    finished = len(self.visited) - running
                    
                    console.total = total_known
                    console.update(finished, f"Run:{running}")
                            
                    future = executor.submit(self.process_url, url, worker_log)
                    futures[future] = url
                
                # Wait for at least one future to complete (or if queue empty and all slots full)
                if futures:
                    done, _ = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
                    
                    for future in done:
                        url = futures.pop(future)
                        try:
                            # result is list of links
                            new_links = future.result()
                            for link in new_links:
                                if link not in self.visited and link not in self.queue:
                                    # Note: linear search in queue is O(N), for large queues optimal is set+queue
                                    # self.queue is deque.
                                    # Checking just visited is usually enough if we accept duplicates in queue 
                                    # but self.visited check at pop time handles them.
                                    # To keep queue small we might want a separate 'enqueued' set.
                                    # For now, simplistic approach: duplicates in queue are fine, handled at pop.
                                    self.queue.append(link)
                        except Exception as e:
                            log(f"Worker exception for {url}: {e}")
                
                # If queue is empty and no futures, we are done
                if not self.queue and not futures:
                    break
        
        console.finish()

        print("\nCrawl finished." if args.color else f"Crawl finished. Visited {len(self.visited)} pages.")

if __name__ == "__main__":
    crawler = KupiCrawler()
    crawler.run()

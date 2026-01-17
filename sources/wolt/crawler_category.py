"""
Category navigation and pagination for Albert Wolt crawler.
"""
import time
import gzip
import os
import re
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from . import crawler_global
from . import crawler_product


def get_filename_from_url(url):
    """
    Generates a safe filename from a product URL.
    
    Args:
        url: Product URL containing itemid
    
    Returns:
        str: Filename (e.g., "product_64ca0b7c.html.gz")
    """
    # Extract product ID from URL (e.g., "itemid-12345")
    match = re.search(r'itemid-([a-zA-Z0-9]+)', url)
    if match:
        product_id = match.group(1)
        return f"product_{product_id}.html.gz"
    else:
        # Fallback: use hash of URL
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        return f"product_{url_hash}.html.gz"


def save_html_to_file(html_content, url, raw_data_dir, category_info=None, log_func=print):
    """
    Saves HTML content to a gzipped file in the raw_data_dir directory with metadata.
    
    Args:
        html_content: HTML string to save
        url: Product URL (used to generate filename)
        raw_data_dir: Directory to save the file in
        category_info: List of category breadcrumbs (e.g., ['OVOCE A ZELENINA', 'OVOCE'])
        log_func: Logging function
    
    Returns:
        str: Path to saved file, or None if failed
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(raw_data_dir, exist_ok=True)
        
        # Get filename from URL
        filename = get_filename_from_url(url)
        filepath = os.path.join(raw_data_dir, filename)
        
        # Prepare metadata
        import json
        meta = {
            "origin_url": url,
            "category": category_info or []
        }
        
        # Create JSON comment header (similar to Tesco crawler)
        comment = f"<!-- META_JSON: {json.dumps(meta, ensure_ascii=False)} -->\n"
        
        # Save as gzipped HTML with metadata header
        temp_path = filepath + ".tmp"
        with gzip.open(temp_path, 'wt', encoding='utf-8') as f:
            f.write(comment)
            f.write(html_content)
        
        os.replace(temp_path, filepath)
        log_func(f"Saved HTML to: {filepath}")
        return filepath
        
    except Exception as e:
        log_func(f"Error saving HTML: {e}")
        return None



def wait_for_category_page_ready(driver, log_func=print):
    """
    Waits for the category page to fully load with products visible.
    """
    try:
        # Wait for product items to appear
        WebDriverWait(driver, 10, 0.1).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR, 
                '[data-test-id="ItemCard"], [data-test-id="CardLinkButton"], a[href*="itemid-"]'
            ))
        )
        
        if crawler_global.check_error_page(driver):
            log_func("Detected error page during category load")
            return False
        
        time.sleep(0.5)
        return True
    except:
        log_func("Timeout waiting for category content to load")
        return False


def navigate_to_category(driver, category_url, log_func=print):
    """
    Navigates to a specific category page and handles any modals.
    
    Args:
        driver: Selenium WebDriver instance
        category_url: Full URL to the category page
        log_func: Logging function
    
    Returns:
        bool: True if navigation successful, False otherwise
    """
    try:
        driver.get(category_url)
        
        # Wait for category page to load
        if not wait_for_category_page_ready(driver, log_func):
            log_func(f"Failed to load category page: {category_url}")
            return False

        crawler_global.close_all_overlays(driver, log_func)

        
        return True
    except Exception as e:
        log_func(f"Error navigating to category: {e}")
        return False


def discover_categories(driver, start_url, log_func=print):
    """
    Discovers all leaf category URLs by expanding root categories.
    
    The Wolt page has a two-level category hierarchy:
    - Root categories (with icons) can be clicked to reveal subcategories
    - Leaf categories (without icons) are the actual product categories
    - Each root category has a "Všechny položky" (All items) link that should be excluded
    
    Returns:
        list: List of tuples (category_name, category_url) for leaf categories only
    """
    leaf_categories = []
    seen_urls = set()
    
    try:
        # Navigate to main page
        driver.get(start_url)
        time.sleep(1)

        crawler_global.close_all_overlays(driver, log_func)
        
        # Find all root category links (those with icons/images)
        # Using stable data-test-id selector
        root_selector = 'a[data-test-id^="navigation-bar-"][href*="/items/"]:has(img)'
        root_links = driver.find_elements(By.CSS_SELECTOR, root_selector)
        
        log_func(f"Found {len(root_links)} root categories to expand")
        
        # Process each root category
        for i in range(len(root_links)):
            try:
                # Re-find root links each iteration (DOM changes after clicking)
                root_links = driver.find_elements(By.CSS_SELECTOR, root_selector)
                
                if i >= len(root_links):
                    break
                    
                root_link = root_links[i]
                root_text = root_link.text.strip()
                root_href = root_link.get_attribute('href')
                
                log_func(f"Expanding root category: {root_text}")
                
                # Scroll into view and click to expand
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", root_link)
                time.sleep(0.2)
                
                crawler_global.safe_click(driver, root_link)
                time.sleep(0.5)  # Wait for subcategories to appear in DOM
                
                # Find all leaf categories (without icons)
                leaf_selector = 'a[data-test-id^="navigation-bar-"][href*="/items/"]:not(:has(img))'
                leaf_links = driver.find_elements(By.CSS_SELECTOR, leaf_selector)
                
                # Track if we found any valid sub-categories for this root
                root_has_children = False
                
                # Collect leaf categories, excluding "Všechny položky"
                for leaf_link in leaf_links:
                    try:
                        leaf_text = leaf_link.text.strip()
                        leaf_href = leaf_link.get_attribute('href')
                        
                        # Skip "Všechny položky" (All items) link
                        if leaf_text == "Všechny položky" or leaf_href == root_href:
                            continue
                        
                        # Skip if already seen
                        if leaf_href in seen_urls:
                            continue
                        
                        seen_urls.add(leaf_href)
                        leaf_categories.append(([root_text, leaf_text], leaf_href))
                        root_has_children = True
                        log_func(f"  Found leaf category: {leaf_text}")
                        
                    except Exception as e:
                        log_func(f"  Error processing leaf link: {e}")
                        continue
                
                # If no children found (or all were skipped/seen), treat root as leaf
                if not root_has_children:
                    if root_href not in seen_urls:
                        seen_urls.add(root_href)
                        leaf_categories.append(([root_text], root_href))
                        log_func(f"  Treating root as leaf: {root_text}")
                
            except Exception as e:
                log_func(f"Error processing root category {i}: {e}")
                continue
        
        log_func(f"Total leaf categories discovered: {len(leaf_categories)}")
        return leaf_categories
        
    except Exception as e:
        log_func(f"Error discovering categories: {e}")
        return []




def iterate_category_products(driver, log_func, callback, max_scrolls=50):
    """
    Generic iteration logic for a category page.
    Scrolls, finds new products, and invokes callback for each.
    
    Args:
        driver: Selenium WebDriver
        log_func: Logging function
        callback: Function(driver, product_element, product_url) -> None
        max_scrolls: Limit scrolls
    """
    scroll_count = 0
    processed_urls = set()
    
    while scroll_count < max_scrolls:
        # Get current product links
        products = driver.find_elements(By.CSS_SELECTOR, 'a[data-test-id="CardLinkButton"]')
        
        current_batch_urls = []
        for p in products:
            try:
                h = p.get_attribute('href')
                if h:
                    current_batch_urls.append(h)
            except:
                continue

        log_func(f"Scroll {scroll_count + 1}: Found {len(products)} product links visible")

        found_new = False
        
        # Process each product by URL
        for href in current_batch_urls:
            # Skip if already processed
            if not href or href in processed_urls:
                continue
            
            processed_urls.add(href)
            found_new = True

            # Re-acquire element
            try:
                href_suffix = href.split('/')[-1]
                link = driver.find_element(By.CSS_SELECTOR, f'a[data-test-id="CardLinkButton"][href$="{href_suffix}"]')
                # Focus
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
            except Exception:
                log_func(f"Could not find element for {href}, skipping...")
                continue
            
            # Invoke Callback
            try:
                callback(driver, link, href)
            except Exception as e:
                log_func(f"Error in callback for {href}: {e}")
                continue

        # Check if new products loaded
        if not found_new:
            log_func(f"No new products after {scroll_count + 1} scrolls. Finished loading.")
            break
        
        scroll_count += 1
    
    if scroll_count >= max_scrolls:
        log_func(f"Reached maximum scroll limit ({max_scrolls})")


def scroll_and_load_all_products(driver, raw_data_dir, category_info=None, log_func=print, global_counter=None, max_scrolls=50, console=None):
    """
    Full crawl: visits each product, saves HTML.
    """
    product_data_list = []
    
    def save_callback(d, element, href):
        # Check global limit
        if global_counter and global_counter.is_reached():
             return

        # Skip if already saved (optimization)
        filename = get_filename_from_url(href)
        filepath = os.path.join(raw_data_dir, filename)
        if os.path.exists(filepath):
            log_func(f"Skipping (already saved): {href}")
            return

        # Check availability
        if not crawler_global.check_item_availability(element):
            log_func(f"Skipping (not available): {href}")
            return
        
        # Check limit increment
        if global_counter and not global_counter.increment():
            log_func("Global limit reached.")
            return

        log_func(f"Clicking product: {href}")
        
        try:
            crawler_global.safe_click(d, element)
            
            if crawler_global.handle_unavailable_dialog(d, log_func):
                return

            if crawler_product.wait_for_product_page_ready(d, log_func):
                html_content = d.page_source
                saved_path = save_html_to_file(html_content, href, raw_data_dir, category_info, log_func)
                
                if saved_path:
                    product_data_list.append({'product_url': href, 'saved_file': saved_path})
                    log_func(f"Saved product HTML: {href}")
                    if console:
                        console.increment()
                else:
                    log_func(f"Failed to save HTML for: {href}")
            else:
                log_func(f"Failed to load product page for: {href}")
            
            # Close modal
            try:
                d.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                try:
                    WebDriverWait(d, 5).until(
                        EC.invisibility_of_element_located((By.CSS_SELECTOR, '.cb_ModalBase_Backdrop_954'))
                    )
                except:
                    pass
                time.sleep(0.3)
            except:
                pass
                
        except Exception as e:
            log_func(f"Error processing product: {e}")
            # Recovery
            try:
                d.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(0.5)
            except:
                pass

    iterate_category_products(driver, log_func, save_callback, max_scrolls)
    return product_data_list


def click_product_link(driver, href):
    # Legacy/Unused maybe, but keeping for compatibility if imported elsewhere
    try:
        links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="itemid-"]')
        for link in links:
            if link.get_attribute('href') == href:
                crawler_global.safe_click(driver, link)
                time.sleep(0.5)
                return True
        return False
    except:
        return False

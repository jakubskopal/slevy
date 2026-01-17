from selenium.webdriver.common.by import By

def check_error_page(driver):
    """
    Checks if the current page is a generic error page (e.g., 'Jejda...').
    Returns True if it is an error page, False otherwise.
    """
    try:
        h1_header = driver.find_element(By.TAG_NAME, "h1")
        if h1_header and "jejda" in h1_header.text.lower():
            return True
    except:
        pass
    return False

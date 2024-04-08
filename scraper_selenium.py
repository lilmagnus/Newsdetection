from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import os
import time

# PLAYWRIGHT
def get_document_links(driver, url, link_to_click_xpath, document_links_xpath, load_more_button_xpath, max_attempts=5):
    # Navigate to the URL
    driver.get(url)
    time.sleep(3)
    first_attempts = 0
    while first_attempts < max_attempts:
        try:
            # Wait for the 'Load More' button to become clickable
            load_more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, load_more_button_xpath))
            )
            # Scroll to the 'Load More' button and click it
            driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
            load_more_button.click()
            # Wait for the page to load more content
            time.sleep(6)
        except Exception as e:
            print("No more 'Load More' buttons or error occurred:", e)
            break

        first_attempts += 1

    # Click the specified link to open the page with documents
    link_to_click = driver.find_element("xpath", link_to_click_xpath)
    time.sleep(3)
    link_to_click.click()

    # Wait for the page to load
    time.sleep(5)

    second_attempts = 0
    while second_attempts < max_attempts:
        try:
            # Wait for the 'Load More' button to become clickable
            load_more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, load_more_button_xpath))
            )
            # Scroll to the 'Load More' button and click it
            driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
            load_more_button.click()
            # Wait for the page to load more content
            time.sleep(6)
        except Exception as e:
            print("No more 'Load More' buttons or error occurred:", e)
            break

        second_attempts += 1

    # Find all document links and collect hrefs
    document_links = driver.find_elements("xpath", document_links_xpath)
    document_hrefs = [link.get_attribute('href') for link in document_links]

    # Close the driver
    driver.quit()
    
    return document_hrefs

def download_document(href, download_dir='modules/2news/njordsveg'): # Definer mappe å lagre i
    # Send a GET request to the URL
    response = requests.get(href)
    
    if response.status_code == 200:
        # Extract the filename from the URL (if possible)
        filename = href.split('/')[-1]
        
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'  # Add .pdf extension if not present

        # Create the full file path
        file_path = os.path.join(download_dir, filename)
        
        # Create the download directory if it doesn't exist
        os.makedirs(download_dir, exist_ok=True)

        # Write the content to a PDF file
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded: {filename}")
    else:
        print(f"Failed to download from {href}")
def main():
    # Set up the initial WebDriver
    driver = webdriver.Firefox()

    try:
        # Define parameters
        #url = 'https://innsyn.tromso.kommune.no/byggsak/dato/2020-03-25' # Kraemer
        #link_to_click_xpath = "//a[text()='20/6238-1']"

        #url = 'https://innsyn.tromso.kommune.no/byggsak/dato/2020-04-23' # Moxy
        #link_to_click_xpath = "//a[text()='20/7761-1']"

        #url = 'https://innsyn.tromso.kommune.no/byggsak/dato/2023-11-06' # Skippergata
        #link_to_click_xpath = "//a[text()='23/18130-1']"
        
        #url = 'https://innsyn.tromso.kommune.no/byggsak/dato/2023-10-17' # Rekvikvegen
        #link_to_click_xpath = "//a[text()='23/16933-1']"

        #url = 'https://innsyn.tromso.kommune.no/byggsak/dato/2023-10-20' # Fløylia
        #link_to_click_xpath = "//a[text()='22/7190-1']"

        #url = 'https://innsyn.tromso.kommune.no/byggsak/dato/2019-11-27' # Innlandsvegen 485
        #link_to_click_xpath = "//a[text()='20/8015-1']"

        #url = 'https://innsyn.tromso.kommune.no/byggsak/dato/2024-01-03' # Trudvanvegen 19
        #link_to_click_xpath = "//a[text()='23/11346-14']"

        #url = 'https://innsyn.tromso.kommune.no/byggsak/dato/2024-02-16' # Heilovegen 23, Hotell til bolig
        #link_to_click_xpath = "//a[text()='23/13964-1']"

        #url = '' # Conrad Holmboes veg 17
        #link_to_click_xpath = "//a[text()='23/19795-4']"
        
        #url = 'https://innsyn.tromso.kommune.no/byggsak/dato/2024-03-20' # Ymse dritt / Morildvegen
        #link_to_click_xpath = "//a[text()='24/5738-1']"
        
        #url = 'https://innsyn.tromso.kommune.no/byggsak/dato/2024-03-20' # Ymse dritt / Fagerlivegen
        #link_to_click_xpath = "//a[text()='24/5732-1']"
        
        #url = 'https://innsyn.tromso.kommune.no/byggsak/dato/2024-03-20' # Ymse dritt / Hochlinvegen
        #link_to_click_xpath = "//a[text()='23/15449-5']"
        
        #url = 'https://innsyn.tromso.kommune.no/byggsak/dato/2024-03-27' # Ymse dritt / Synnavinden
        #link_to_click_xpath = "//a[text()='24/6165-1']"
        
        #url = 'https://innsyn.tromso.kommune.no/byggsak/dato/2024-03-27' # Ymse dritt / Klokkargårdsbakken
        #link_to_click_xpath = "//a[text()='23/9857-5']"
        
        url = 'https://innsyn.tromso.kommune.no/byggsak/dato/2024-03-27' # Ymse dritt / Njords veg
        link_to_click_xpath = "//a[text()='22/8031-9']"

        document_links_xpath = "//a[contains(@href, 'dokumentbestilling/getDocument?dokid=')]"
        load_more_button_xpath = "//a[text()='Flere resultater']"
        
        # Get document links and close the initial driver
        document_hrefs = get_document_links(driver, url, link_to_click_xpath, document_links_xpath, load_more_button_xpath, max_attempts=5)
        
        # Download each document in a separate driver instance
        for href in document_hrefs:
            download_document(href)

    except Exception as e:
        print(f"An error occurred: {e}")

    print("="*20,"FINISHED","="*20)
if __name__ == "__main__":
    main()

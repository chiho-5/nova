# import os
# import requests
# from bs4 import BeautifulSoup



# # paywall_sites = [
# #     "barrons.com", "nytimes.com", "wsj.com", "theguardian.com"
# # ]

# google_api_key = "AIzaSyCKqi-C3NKUVdB5VxewJuUaR4mtVHCOerI" 
# search_engine_id = "11415ca8aea244e57"  
# search_url = "https://www.googleapis.com/customsearch/v1"

# class WebSearchFeature:
# 	def __init__(
# 		self,num=2,
# 		api_key=google_api_key,
# 		search_url=search_url,
# 		id = search_engine_id
# 		):
# 		super().__init__()
# 		self.num = num
# 		self.api_key = api_key
# 		self.search_url = search_url
# 		self.id = id
# 		self.trusted_sites = ['wikipedia.org', 'bbc.com', 'bbc.co.uk']  # Add more trusted domains if needed
# 		self.paywall_keywords = ['paywall', 'subscription required', 'subscribe now', 'premium content']

# 	def is_paywalled(self, url):
# 	    try:
# 	        # Whitelist trusted domains
# 	        if any(trusted_site in url for trusted_site in self.trusted_sites):
# 	            return False

# 	        # Fetch the content of the URL
# 	        response = requests.get(url, timeout=10)
	        
# 	        # Check for unauthorized or forbidden access
# 	        if response.status_code in [401, 403]:
# 	            return True

# 	        # Parse the HTML content
# 	        soup = BeautifulSoup(response.text, 'html.parser')

# 	        # Check for paywall keywords in the page text
# 	        page_text = soup.get_text(separator=" ").lower()
# 	        if any(keyword in page_text for keyword in self.paywall_keywords):
# 	            return True

# 	        # Optionally check for specific paywall elements (e.g., known div classes or IDs)
# 	        # paywall_elements = ['paywall', 'subscribe-banner']
# 	        # if any(soup.find(class_=element) for element in paywall_elements):
# 	        #     return True

# 	        # If no paywall detected, return False
# 	        return False

# 	    except requests.exceptions.RequestException as e:
# 	        # Log the error and assume the URL is not paywalled
# 	        print(f"Error fetching {url}: {e}")
# 	        return False  # Treat inaccessible URLs as not paywalled

# 	def search_web(self,query):  
# 	    params = {
# 	        "key": self.api_key,
# 	        "cx": self.id,
# 	        "q": query,
# 	        "num": self.num
# 	    }
	    
# 	    response = requests.get(self.search_url, params=params)
# 	    if response.status_code == 200:
# 	        results = response.json()
# 	        # Extract URLs from the search results
# 	        urls = [item['link'] for item in results.get('items', [])]
# 	        return urls
# 	    else:
# 	        print(f"Error: {response.status_code}, {response.text}")
# 	        return []


# 	def scrape_content(self,url):
# 	    try:
# 	        response = requests.get(url)
# 	        soup = BeautifulSoup(response.text, 'html.parser')
# 	        text = soup.get_text()
# 	        return text
# 	    except Exception as e:
# 	        print(f"Error scraping {url}: {e}")
# 	        return ""


import os
import requests
from bs4 import BeautifulSoup

google_api_key = "AIzaSyCKqi-C3NKUVdB5VxewJuUaR4mtVHCOerI"
search_engine_id = "11415ca8aea244e57"
search_url = "https://www.googleapis.com/customsearch/v1"

class WebSearchFeature:
    def __init__(self, num=1, api_key=google_api_key, search_url=search_url, id=search_engine_id):
        self.num = num
        self.api_key = api_key
        self.search_url = search_url
        self.id = id
        self.trusted_sites = ['wikipedia.org', 'bbc.com', 'bbc.co.uk']  # Trusted domains
        self.paywall_keywords = ['paywall', 'subscription required', 'subscribe now', 'premium content']

    def is_paywalled(self, url):
        """Quickly determine if the URL is paywalled."""
        try:
            # Whitelist trusted domains
            if any(trusted_site in url for trusted_site in self.trusted_sites):
                return False  # Trust trusted domains

            # Fetch content with a timeout to prevent slow websites from hanging the request
            response = requests.get(url, timeout=5)
            if response.status_code in [401, 403]:
                return True  # Unauthorized or forbidden access

            # Only parse text content if necessary
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text(separator=" ").lower()

            # Check for paywall keywords in the page text
            if any(keyword in page_text for keyword in self.paywall_keywords):
                return True

            return False

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return False

    def search_web(self, query):
        """Perform a search and return URLs."""
        params = {
            "key": self.api_key,
            "cx": self.id,
            "q": query,
            "num": self.num
        }
        
        try:
            response = requests.get(self.search_url, params=params, timeout=5)
            response.raise_for_status()  # Raises HTTPError for bad responses
            results = response.json()
            urls = [item['link'] for item in results.get('items', [])]
            return urls
        except requests.exceptions.RequestException as e:
            print(f"Error during web search: {e}")
            return []

    def scrape_content(self, url):
        """Scrape content from a single URL."""
        try:
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator=" ")
            return text
        except requests.exceptions.RequestException as e:
            print(f"Error scraping {url}: {e}")
            return ""


# result = WebSearchFeature()
# print(result.search_web('what is huggingface'))
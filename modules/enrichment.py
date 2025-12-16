import requests
from serpapi import GoogleSearch
import os
from dotenv import load_dotenv

load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

def check_scientific_intent(author_name, keyword="toxicity"):
    """
    Searches OpenAlex for recent papers (Free).
    """
    try:
        url = f"https://api.openalex.org/works?search={author_name} {keyword}&filter=from_publication_date:2023-01-01"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            count = data['meta']['count']
            titles = [r['title'] for r in data['results'][:3]] if count > 0 else []
            return (True, count, titles) if count > 0 else (False, 0, [])
            
    except Exception as e:
        print(f"OpenAlex Error: {e}")
        
    return False, 0, []


def check_funding_signal(company_name):
    """
    Checks Google News via SerpApi for funding signals.
    """
    if not SERPAPI_KEY: 
        return False, "No API Key"

    try:
        params = {
            "api_key": SERPAPI_KEY,
            "engine": "google",
            "q": f"{company_name} raises funding OR Series A OR Series B",
            "tbm": "nws", 
            "num": 3
        }
        
        search = GoogleSearch(params)
        results = search.get_dict().get("news_results", [])
        
        for news in results:
            snippet = news.get("snippet", "").lower()
            if "million" in snippet or "raised" in snippet:
                return True, f"{news.get('date', 'Recent')}: {news.get('title')}"
                
    except Exception as e:
        print(f"Funding Check Error: {e}")
        
    return False, "No recent funding found"


def get_linkedin_data(name, company_name):
    """
    Uses SerpApi to find the LinkedIn profile via Google and parse the snippet.
    Replaces Proxycurl.
    """
    if not SERPAPI_KEY:
        return {"city": "Unknown", "role": "Unknown"}

    try:
       
        query = f'site:linkedin.com/in/ "{name}" "{company_name}"'
        
        params = {
            "api_key": SERPAPI_KEY,
            "engine": "google",
            "q": query,
            "num": 1 
        }
        
        search = GoogleSearch(params)
        results = search.get_dict().get("organic_results", [])
        
        if not results:
            return {"city": "Unknown", "role": "Not Found"}

       
        top_result = results[0]
        title = top_result.get("title", "")  
        snippet = top_result.get("snippet", "") 

        
        extracted_data = {}
        
      
        parts = title.split("-")
        if len(parts) >= 2:
            extracted_data["role"] = parts[1].strip()  
        else:
            extracted_data["role"] = title 

       
        if "·" in snippet:
            extracted_data["city"] = snippet.split("·")[0].strip()
        else:
            extracted_data["city"] = "Location in Bio"

        return extracted_data

    except Exception as e:
        print(f"LinkedIn Search Error: {e}")
        return {"city": "Error", "role": "Error"}
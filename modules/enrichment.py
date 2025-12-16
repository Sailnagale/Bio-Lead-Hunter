import requests
from serpapi import GoogleSearch
from duckduckgo_search import DDGS
import os
from dotenv import load_dotenv

load_dotenv()
try:
    import streamlit as st
    SERPAPI_KEY = st.secrets.get("SERPAPI_KEY")
except:
    SERPAPI_KEY = os.getenv("SERPAPI_KEY")


def discover_new_leads(role, location):
    """
    1. Tries SerpApi (Best for Title + Location).
    2. Tries DuckDuckGo (Free Backup).
    3. FALLBACK: OpenAlex API (Finds REAL authors publishing on the topic).
    """
    leads = []
    
    
    if SERPAPI_KEY:
        try:
          
            query = f'site:linkedin.com/in/ "{role}" "{location}"'
            params = {"api_key": SERPAPI_KEY, "engine": "google", "q": query, "num": 5}
            search = GoogleSearch(params)
            results = search.get_dict().get("organic_results", [])
            
            for result in results:
                title_text = result.get("title", "")
                parts = title_text.split(" - ")
                name = parts[0].strip() if len(parts) > 0 else "Unknown"
                if len(parts) >= 3:
                    job_title = parts[1].strip()
                    company = parts[2].split("|")[0].strip()
                elif len(parts) == 2:
                    job_title = parts[1].split("|")[0].strip()
                    company = "Unknown"
                else:
                    job_title = role
                    company = "Unknown"
                leads.append({"Name": name, "Title": job_title, "Company": company, "Location": location})
        except:
            pass

  
    if not leads:
        try:
           
            with DDGS() as ddgs:
                query = f'site:linkedin.com/in/ {role} {location}'
                results = list(ddgs.text(query, max_results=5))
                for r in results:
                    title = r['title']
                    parts = title.split(" - ")
                    name = parts[0].strip()
                    job_title = parts[1].strip() if len(parts) > 1 else role
                    leads.append({"Name": name, "Title": job_title, "Company": "LinkedIn Profile", "Location": location})
        except:
            pass

    
    if not leads:
        try:
            
            topic = role.replace("Director of ", "").replace("Head of ", "").replace("Scientist", "").strip()
            if len(topic) < 3: topic = "Toxicity" 
            
            
            url = f"https://api.openalex.org/works?search={topic}&filter=from_publication_date:2023-01-01&per-page=5"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                for work in data.get('results', []):
                   
                    if work.get('authorships'):
                        author_data = work['authorships'][0]
                        author_name = author_data['author']['display_name']
                        
                       
                        institutions = author_data.get('institutions', [])
                        company = institutions[0]['display_name'] if institutions else "Research Institution"
                        
                       
                        country = institutions[0].get('country_code', 'Global') if institutions else "Global"
                        
                        leads.append({
                            "Name": author_name,
                            "Title": f"Lead Researcher ({topic})", 
                            "Company": company,
                            "Location": country
                        })
        except Exception as e:
            print(f"OpenAlex Discovery Failed: {e}")

   
    is_science_fallback = (len(leads) > 0 and "Lead Researcher" in leads[0]['Title'])
    return leads, is_science_fallback


def check_scientific_intent(author_name, keyword="toxicity"):
    try:
        url = f"https://api.openalex.org/works?search={author_name} {keyword}&filter=from_publication_date:2023-01-01"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            count = data['meta']['count']
            titles = [r['title'] for r in data['results'][:3]] if count > 0 else []
            return (True, count, titles) if count > 0 else (False, 0, [])
    except:
        pass
    return False, 0, []


def check_funding_signal(company_name):
    if not SERPAPI_KEY: return False, "No API Key"
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
    except:
        pass
    return False, "No recent funding found"


def get_linkedin_data(name, company_name):
    return {"city": "Unknown", "role": "Unknown"}
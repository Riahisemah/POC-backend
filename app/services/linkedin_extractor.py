import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import re
from copy import copy
import time

logger = logging.getLogger(__name__)

PROFILE_STRUCTURE = {
    "name": "",
    "current_title": "",
    "sector": "Technology",
    "years_experience": 0,
    "experiences": []
}

def extract_linkedin_scrapingbee(url):
    """Extraction LinkedIn avec ScrapingBee - version corrigée"""
    
    import os
    api = os.getenv('SCRAPINGBEE_API_KEY')
    if not api:
        return {"error": "ScrapingBee API key not configured"}
    print("api : ", api )
    params = {
        'api_key': api,
        'url': url,
        'render_js': 'true',
        'wait': '3000',
        'wait_for': '.pv-top-card-section, .profile-detail',
        'premium_proxy': 'true',
        'country_code': 'us',
        'block_resources': 'false',
        'return_page_source': 'true'
    }
    
    try:
        print(f"Tentative de scraping avec ScrapingBee: {url}")
        
        response = requests.get(
            'https://app.scrapingbee.com/api/v1/',
            params=params,
            timeout=30,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        print(f"Statut ScrapingBee: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            result = soup
            print('soop : ', result)
            #result = parse_linkedin_advanced(soup)
            
            # Vérification que des données ont été extraites
            if result.get('name') or result.get('experiences'):
                return result
            else:
                return {"error": "Aucune donnée extraite - le sélecteur peut avoir changé"}
                
        elif response.status_code == 401:
            return {"error": "Erreur d'authentification ScrapingBee - vérifiez votre clé API"}
            
        elif response.status_code == 403:
            return {"error": "Accès refusé - LinkedIn a bloqué la requête"}
            
        else:
            error_msg = f"Erreur ScrapingBee {response.status_code}"
            try:
                error_data = response.json()
                error_msg = error_data.get('message', error_msg)
            except:
                error_msg = response.text[:200] if response.text else error_msg
            return {"error": error_msg}
            
    except requests.Timeout:
        return {"error": "Timeout lors du scraping"}
    except Exception as e:
        return {"error": f"Erreur ScrapingBee: {str(e)}"}

def fallback_extraction_methods(url):
    """Méthodes de fallback si ScrapingBee échoue"""
    
    methods = [
        try_zenrows_extraction,
        try_local_parsing,
        try_alternative_selectors
    ]
    
    for method in methods:
        try:
            result = method(url)
            if result and not result.get('error'):
                return result
        except Exception as e:
            logger.warning(f"Fallback method {method.__name__} failed: {e}")
            continue
    
    return {"error": "Toutes les méthodes d'extraction ont échoué"}

def try_zenrows_extraction(url):
    """Essaie ZenRows comme fallback"""
    # Votre code ZenRows existant ici
    pass

def try_local_parsing(url):
    """Tentative de parsing local simple (sans JS)"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return parse_linkedin_advanced(soup)
    except:
        return {"error": "Local parsing failed"}
def parse_linkedin_advanced(soup):
    """Advanced parsing with multiple fallback selectors and date calculation - tested on 2025 LinkedIn structure"""
    profile = copy(PROFILE_STRUCTURE)
    
    # Name - multiple selectors (2025 compatible)
    name_selectors = [
        'h1.text-heading-xlarge',
        '.pv-top-card-section__name',
        'h1.profile-topcard-person-entity__name',
        'h1'
    ]
    for selector in name_selectors:
        elem = soup.select_one(selector)
        if elem and (name := elem.get_text(strip=True)):
            profile["name"] = name
            break
    
    # Current Title - multiple selectors
    title_selectors = [
        'div.text-body-medium',
        '.pv-top-card-section__headline',
        'h2.profile-topcard-person-entity__headline',
        '.top-card-layout__headline'
    ]
    for selector in title_selectors:
        elem = soup.select_one(selector)
        if elem and (title := elem.get_text(strip=True)):
            profile["current_title"] = title
            # Infer sector from title
            title_lower = title.lower()
            if any(word in title_lower for word in ['software', 'engineer', 'tech', 'developer']):
                profile["sector"] = "Technology"
            elif any(word in title_lower for word in ['finance', 'bank', 'investment']):
                profile["sector"] = "Finance"
            elif any(word in title_lower for word in ['health', 'medical', 'pharma']):
                profile["sector"] = "Healthcare"
            else:
                profile["sector"] = "Unknown"
            break
    
    # Experiences - target experience section with robust selectors
    total_years = 0.0
    exp_section = soup.find('section', {'id': 'experience-collapse'}) or soup.select_one('[data-section="experience"]')
    if exp_section:
        # Find experience list items (updated for 2025: often in ul > li with artdeco or pv-entity classes)
        exp_items = exp_section.select('li.artdeco-list__item, .pv-profile-section__card-item, .pv-entity__position-group, li.pv-entity__position-group-pager', limit=5)
        
        for item in exp_items:
            try:
                # Role: Usually h3 or .pv-entity__summary-info
                role_elem = item.select_one('h3, .pv-entity__summary-info, .t-16.t-bold')
                role_text = role_elem.get_text(strip=True) if role_elem else None
                
                # Company: span with secondary-title or org-name
                company_elem = item.select_one('.pv-entity__secondary-title, .t-14.t-black--light.t-normal, span.org-name')
                company_text = company_elem.get_text(strip=True) if company_elem else None
                
                # Dates: h4 with date-range
                dates_elem = item.select_one('h4.pv-entity__date-range, .t-14.t-black--light.t-normal, span.pv-entity__bullet-item-v2')
                dates_text = dates_elem.get_text(strip=True) if dates_elem else ""
                
                if role_text and company_text and dates_text:
                    # Parse dates: e.g., "Jan 2020 - Present" or "Jan 2020 - Dec 2023"
                    date_match = re.search(r'([A-Za-z]{3} \d{4})\s*[-–]\s*(Present|[A-Za-z]{3} \d{4})', dates_text)
                    if date_match:
                        start = date_match.group(1)
                        end = date_match.group(2)
                        duration = f"{start} - {end}"
                        end_date_str = end if end != "Present" else datetime.now().strftime("%b %Y")
                        
                        exp = {
                            "company": company_text,
                            "role": role_text,
                            "duration": duration,
                            "start_date": start,
                            "end_date": end_date_str
                        }
                        profile["experiences"].append(exp)
                        
                        # Calculate years accurately (including partial for current roles)
                        try:
                            s_match = re.match(r'(\w{3}) (\d{4})', start)
                            if s_match:
                                s_month, s_year = s_match.groups()
                                s_date = datetime(int(s_year), month_to_num(s_month), 1)
                                
                                if end == "Present":
                                    e_date = datetime.now()
                                else:
                                    e_match = re.match(r'(\w{3}) (\d{4})', end)
                                    if e_match:
                                        e_month, e_year = e_match.groups()
                                        e_date = datetime(int(e_year), month_to_num(e_month), 1)
                                
                                years = (e_date - s_date).days / 365.25
                                total_years += max(0, years)
                        except ValueError:
                            pass  # Skip if date parse fails
            
            except Exception as parse_err:
                logger.warning(f"Parse error for exp item: {parse_err}")
                continue
    
    profile["years_experience"] = round(total_years, 1)
    return profile
# import streamlit as st
# import pandas as pd
# from io import BytesIO
# import os
# import time
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.common.exceptions import TimeoutException
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from bs4 import BeautifulSoup
# from groq import Groq
# from langgraph.graph import StateGraph
# from typing import TypedDict, Optional, List, Dict
# from selenium_stealth import stealth
# from fake_useragent import UserAgent
# from tavily import TavilyClient
# import json
# import requests
# import re
# from urllib.parse import urlencode

# # ------------------------- CONFIGURATION -------------------------
# # Set your Groq API key (replace with your valid key)
# groq_api_key = "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"
# if not groq_api_key.strip():
#     raise ValueError("Please provide a valid Groq API key.")
# client = Groq(api_key=groq_api_key)

# # Set your Tavily API key (replace with your valid key)
# tavily_api_key = "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"
# tavily_client = TavilyClient(tavily_api_key)

# # Dictionary mapping fields to search keywords.
# FIELD_KEYWORDS = {
#     "Data Science": "data scientist",
#     "Human Resources": "human resources",
#     "Digital Transformation": "digital transformation",
#     "Cyber Security": "cyber security",
#     "FinTech": "fintech",
#     "Project Management": "project management",
#     "Strategic Management": "strategic management",
#     "Business Management": "business management",
#     "Fintech": "fintech",
#     "General Management": "general management",
#     "Product Management": "product management"
# }

# # Global field for relevance; will be updated for each domain.
# FIELD = "data science"  # default

# # ------------------------- JOB STATE DEFINITION -------------------------
# class JobState(TypedDict):
#     Title: str
#     Company: str
#     Experience: str
#     Description: str
#     is_relevant: Optional[str]
#     is_competitor: Optional[str]
#     job_tier: Optional[str]

# # ------------------------- Tavily API HELPER FUNCTIONS -------------------------
# def search_with_tavily(query: str) -> str:
#     try:
#         response = tavily_client.search(query=query, max_results=1)
#         if "results" in response and response["results"]:
#             return response["results"][0]["url"]
#         else:
#             raise KeyError("Key 'results' not found or empty in response")
#     except Exception as e:
#         print(f"Error during Tavily search for query '{query}': {e}")
#         return ""

# def get_company_career_page(company_name: str) -> str:
#     career_query = f"{company_name} careers"
#     career_url = search_with_tavily(career_query)
#     if career_url:
#         return career_url
#     else:
#         homepage_query = company_name
#         homepage_url = search_with_tavily(homepage_query)
#         if homepage_url:
#             return homepage_url
#     return ""

# # ------------------------- LANGGRAPH WORKFLOW FUNCTIONS -------------------------
# def check_relevance(state: JobState) -> JobState:
#     prompt = f"""
#     Job Title: {state['Title']}
#     Company: {state['Company']}
#     Description: {state['Description']}
#     Determine if this is a genuine job posting relevant to {FIELD}.
#     Respond with JSON in the format: {{"is_relevant": "Yes" or "No"}}
#     """
#     try:
#         response = client.chat.completions.create(
#             messages=[{"role": "user", "content": prompt}],
#             model="llama-3.3-70b-versatile"
#         )
#         result = json.loads(response.choices[0].message.content.strip())
#         state["is_relevant"] = result.get("is_relevant", "No")
#     except Exception as e:
#         print(f"Error in check_relevance for '{state['Title']}':", e)
#         state["is_relevant"] = "No"
#     return state

# def check_competitor_with_fallback(state: JobState) -> JobState:
#     prompt = f"""
#     Job Company: {state['Company']}
#     Determine if this job posting is from a competitor edtech company from the following:
#     BYJU'S, Unacademy, Vedantu, Toppr, UpGrad, Simplilearn, WhiteHat Jr., Classplus, Embibe, EduGorilla, iQuanta, TrainerCentral, Meritnation, Testbook, Edukart, Adda247, CollegeDekho, Leverage Edu, Next Education, Infinity Learn.
#     If you are uncertain, respond with: {{"is_competitor": "No"}}.
#     Ensure your output is strictly valid JSON.
#     """
#     max_retries = 5
#     delay = 5
#     for attempt in range(max_retries):
#         try:
#             response = client.chat.completions.create(
#                 messages=[{"role": "user", "content": prompt}],
#                 model="llama-3.3-70b-versatile"
#             )
#             raw_content = response.choices[0].message.content.strip()
#             if not raw_content:
#                 raise ValueError("Empty response")
#             result = json.loads(raw_content)
#             state["is_competitor"] = result.get("is_competitor", "No")
#             return state
#         except Exception as e:
#             print(f"Error in check_competitor for '{state['Company']}' on attempt {attempt+1}: {e}")
#             time.sleep(delay)
#     state["is_competitor"] = "No"
#     return state

# def determine_tier(state: JobState) -> JobState:
#     prompt = f"""
#     Job Title: {state['Title']}
#     Experience: {state['Experience']}
#     Description: {state['Description']}
#     Determine the job tier as Fresher, Mid, or Senior.
#     Respond with JSON in the format: {{"job_tier": "Fresher" or "Mid" or "Senior"}}
#     """
#     try:
#         response = client.chat.completions.create(
#             messages=[{"role": "user", "content": prompt}],
#             model="llama-3.3-70b-versatile"
#         )
#         result = json.loads(response.choices[0].message.content.strip())
#         state["job_tier"] = result.get("job_tier", "N/A")
#     except Exception as e:
#         print(f"Error in determine_tier for '{state['Title']}':", e)
#         state["job_tier"] = "N/A"
#     return state

# def build_job_workflow() -> StateGraph:
#     graph = StateGraph(JobState)
#     graph.add_node("check_relevance", check_relevance)
#     graph.add_node("check_competitor", check_competitor_with_fallback)
#     graph.add_node("determine_tier", determine_tier)
#     graph.add_edge("check_relevance", "check_competitor")
#     graph.add_edge("check_competitor", "determine_tier")
#     graph.set_entry_point("check_relevance")
#     graph.set_finish_point("determine_tier")
#     return graph

# def process_job(job: dict, field: str) -> Optional[dict]:
#     global FIELD
#     FIELD = field  # Update global field for relevance check
    
#     state: JobState = {
#         "Title": job.get("Title", ""),
#         "Company": job.get("Company", ""),
#         "Experience": job.get("Experience", ""),
#         "Description": job.get("Description", ""),
#         "is_relevant": None,
#         "is_competitor": None,
#         "job_tier": None,
#     }
    
#     graph = build_job_workflow()
#     compiled_graph = graph.compile()
#     result_state = compiled_graph.invoke(state)
    
#     if (result_state.get("is_relevant", "").lower() == "yes" and
#         result_state.get("is_competitor", "").lower() == "no"):
#         job["Job Tier"] = result_state.get("job_tier", "N/A")
#         career_url = get_company_career_page(job.get("Company", ""))
#         if career_url:
#             job["Job Link"] = career_url
#             return job
#         else:
#             print(f"Dropping job '{job.get('Title')}' because no website was found for {job.get('Company')}")
#             return None
#     else:
#         return None

# # ------------------------- SELENIUM & BEAUTIFULSOUP FUNCTIONS -------------------------
# def setup_webdriver():
#     options = webdriver.ChromeOptions()
#     options.add_argument('--window-size=1920,1080')
#     options.add_argument('--headless')
#     options.add_argument('--no-sandbox')
#     options.add_argument('--disable-gpu')
#     options.add_argument('--disable-dev-shm-usage')
#     desktop_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
#     options.add_argument(f'user-agent={desktop_ua}')
#     options.add_experimental_option("excludeSwitches", ["enable-automation"])
#     options.add_experimental_option('useAutomationExtension', False)
#     options.add_argument("--disable-blink-features=AutomationControlled")
#     driver = webdriver.Chrome(options=options)
#     stealth(driver,
#             languages=["en-US", "en"],
#             vendor="Google Inc.",
#             platform="Win32",
#             webgl_vendor="Intel Inc.",
#             renderer="Intel Iris OpenGL Engine",
#             fix_hairline=True)
#     driver.implicitly_wait(10)
#     return driver

# def extract_jobs(soup):
#     job_list = []
#     job_wrappers = soup.select("div.srp-jobtuple-wrapper")
#     for wrapper in job_wrappers:
#         job = wrapper.select_one("div.cust-job-tuple")
#         if not job:
#             continue
#         title_elem = job.select_one("a.title")
#         company_elem = job.select_one("a.comp-name, a.subTitle")
#         exp_elem = job.select_one("span.expwdth, li.experience")
#         sal_elem = job.select_one("span.sal-wrap, li.salary")
#         loc_elem = job.select_one("span.locWdth, li.location")
#         desc_elem = job.select_one("span.job-desc, div.job-description")
#         posted_elem = job.select_one("span.fleft.postedDate, span.job-post-day")
#         link_elem = job.select_one("a.title")
        
#         job_list.append({
#             'Title': title_elem.get_text(strip=True) if title_elem else 'N/A',
#             'Company': company_elem.get_text(strip=True) if company_elem else 'N/A',
#             'Experience': exp_elem.get_text(strip=True) if exp_elem else 'N/A',
#             'Salary': sal_elem.get_text(strip=True) if sal_elem else 'Not disclosed',
#             'Location': loc_elem.get_text(strip=True) if loc_elem else 'N/A',
#             'Description': desc_elem.get_text(strip=True) if desc_elem else 'N/A',
#             'Posted Date': posted_elem.get_text(strip=True) if posted_elem else 'N/A',
#             'Skills': ', '.join([tag.get_text(strip=True) for tag in job.select("li.tag, li.tag-li")]),
#             'Job Link': link_elem["href"] if link_elem and link_elem.has_attr("href") else 'N/A'
#         })
#     return job_list

# def get_page_source(driver):
#     scroll_pause_time = 2
#     screen_height = driver.execute_script("return window.screen.height;")
#     i = 1
#     while True:
#         driver.execute_script(f"window.scrollTo(0, {screen_height} * {i});")
#         i += 1
#         time.sleep(scroll_pause_time)
#         scroll_height = driver.execute_script("return document.body.scrollHeight;")
#         if (screen_height * i) > scroll_height:
#             break
#     return BeautifulSoup(driver.page_source, 'html.parser')

# # ------------------------- HELPER FUNCTION: FILTER JOBS -------------------------
# def is_job_recent(posted_date: str) -> bool:
#     pd_lower = posted_date.lower()
#     if any(term in pd_lower for term in ["just now", "few hours", "today", "1 day", "2 days", "3 days"]):
#         return True
#     if "day" in pd_lower:
#         return False
#     return True

# # ------------------------- MAIN SCRAPING FUNCTION -------------------------
# def scrape_jobs_for_domain(domain: str) -> pd.DataFrame:
#     global FIELD
#     FIELD = domain.lower()
#     search_keyword = FIELD_KEYWORDS[domain]
    
#     driver = setup_webdriver()
#     base_url = "https://www.naukri.com/jobs-in-india "
#     params = {
#         "k": search_keyword,
#         "l": "india",
#         "jobAge": "1"
#     }
#     url = f"{base_url}?{urlencode(params)}"
    
#     driver.get(url)
#     try:
#         WebDriverWait(driver, 20).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, "div.srp-jobtuple-wrapper"))
#         )
#     except TimeoutException:
#         pass
    
#     time.sleep(5)
#     soup = get_page_source(driver)
#     job_list = extract_jobs(soup)
#     driver.quit()
    
#     final_jobs = []
#     for job in job_list:
#         processed = process_job(job, domain)
#         if processed and is_job_recent(processed.get("Posted Date", "")):
#             final_jobs.append(processed)
    
#     return pd.DataFrame(final_jobs)

# # ------------------------- EXCEL EXPORT FUNCTION -------------------------
# def to_excel(df):
#     output = BytesIO()
#     with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
#         df.to_excel(writer, index=False)
#     return output.getvalue()

# # ------------------------- MAIN STREAMLIT APP -------------------------
# def main():
#     st.set_page_config(page_title="Job Scraper", layout="wide")
#     st.title("🌐 Job Scraper - Domain Specific")
#     st.markdown("Select a job domain to scrape and download Excel results")
    
#     # Domain selection
#     col1, col2 = st.columns([3, 1])
#     with col1:
#         selected_domain = st.selectbox("Select Job Domain", options=list(FIELD_KEYWORDS.keys()))
#     with col2:
#         st.markdown("<br>", unsafe_allow_html=True)
#         start_scrape = st.button("🔍 Scrape Jobs", use_container_width=True)
    
#     if 'scraped_data' not in st.session_state:
#         st.session_state.scraped_data = None
    
#     if start_scrape:
#         with st.spinner(f"Scraping jobs for {selected_domain}... This may take 1-2 minutes"):
#             df = scrape_jobs_for_domain(selected_domain)
#             if not df.empty:
#                 st.session_state.scraped_data = df
#                 st.session_state.domain = selected_domain
#                 st.success(f"Found {len(df)} relevant jobs for {selected_domain}")
#             else:
#                 st.warning("No relevant jobs found for this domain")
    
#     # Display results and download button
#     if st.session_state.scraped_data is not None:
#         domain = st.session_state.domain
#         df = st.session_state.scraped_data
        
#         st.markdown(f"### 📋 {domain} Jobs Results")
#         st.dataframe(df, use_container_width=True)
        
#         excel_data = to_excel(df)
#         st.download_button(
#             label="📥 Download Excel",
#             data=excel_data,
#             file_name=f"Filtered_Naukri_{domain.replace(' ', '_')}_Jobs.xlsx",
#             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#         )

# if __name__ == "__main__":
#     main()


import streamlit as st
import pandas as pd
from io import BytesIO
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from groq import Groq
from langgraph.graph import StateGraph
from typing import TypedDict, Optional, List, Dict
from selenium_stealth import stealth
from fake_useragent import UserAgent
from tavily import TavilyClient
import json
import requests
import re
from urllib.parse import urlencode


# ------------------------- JOB STATE DEFINITION -------------------------
class JobState(TypedDict):
    Title: str
    Company: str
    Experience: str
    Description: str
    is_relevant: Optional[str]
    is_competitor: Optional[str]
    job_tier: Optional[str]


# Dictionary mapping fields to search keywords.
FIELD_KEYWORDS = {
    "Data Science": "data scientist",
    "Human Resources": "human resources",
    "Digital Transformation": "digital transformation",
    "Cyber Security": "cyber security",
    "FinTech": "fintech",
    "Project Management": "project management",
    "Strategic Management": "strategic management",
    "Business Management": "business management",
    "Fintech": "fintech",
    "General Management": "general management",
    "Product Management": "product management"
}


# Global field for relevance; will be updated per domain.
FIELD = "data science"


# ------------------------- Tavily API HELPER FUNCTIONS -------------------------
def search_with_tavily(query: str, tavily_client: TavilyClient) -> str:
    try:
        response = tavily_client.search(query=query, max_results=1)
        if "results" in response and response["results"]:
            return response["results"][0]["url"]
        else:
            raise KeyError("Key 'results' not found or empty in response")
    except Exception as e:
        print(f"Error during Tavily search for query '{query}': {e}")
        return ""


def get_company_career_page(company_name: str, tavily_client: TavilyClient) -> str:
    career_query = f"{company_name} careers"
    career_url = search_with_tavily(career_query, tavily_client)
    if career_url:
        return career_url
    else:
        homepage_query = company_name
        homepage_url = search_with_tavily(homepage_query, tavily_client)
        if homepage_url:
            return homepage_url
    return ""


# ------------------------- LANGGRAPH WORKFLOW FUNCTIONS -------------------------
def check_relevance(state: JobState, client: Groq) -> JobState:
    prompt = f"""
    Job Title: {state['Title']}
    Company: {state['Company']}
    Description: {state['Description']}
    Determine if this is a genuine job posting relevant to {FIELD}.
    Respond with JSON in the format: {{"is_relevant": "Yes" or "No"}}
    """
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile"
        )
        result = json.loads(response.choices[0].message.content.strip())
        state["is_relevant"] = result.get("is_relevant", "No")
    except Exception as e:
        print(f"Error in check_relevance for '{state['Title']}':", e)
        state["is_relevant"] = "No"
    return state


def check_competitor_with_fallback(state: JobState, client: Groq) -> JobState:
    prompt = f"""
    Job Company: {state['Company']}
    Determine if this job posting is from a competitor edtech company from the following:
    BYJU'S, Unacademy, Vedantu, Toppr, UpGrad, Simplilearn, WhiteHat Jr., Classplus, Embibe, EduGorilla, iQuanta, TrainerCentral, Meritnation, Testbook, Edukart, Adda247, CollegeDekho, Leverage Edu, Next Education, Infinity Learn.
    If you are uncertain, respond with: {{"is_competitor": "No"}}.
    Ensure your output is strictly valid JSON.
    """
    max_retries = 5
    delay = 5
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile"
            )
            raw_content = response.choices[0].message.content.strip()
            if not raw_content:
                raise ValueError("Empty response")
            result = json.loads(raw_content)
            state["is_competitor"] = result.get("is_competitor", "No")
            return state
        except Exception as e:
            print(f"Error in check_competitor for '{state['Company']}' on attempt {attempt+1}: {e}")
            time.sleep(delay)
    state["is_competitor"] = "No"
    return state


def determine_tier(state: JobState, client: Groq) -> JobState:
    prompt = f"""
    Job Title: {state['Title']}
    Experience: {state['Experience']}
    Description: {state['Description']}
    Determine the job tier as Fresher, Mid, or Senior.
    Respond with JSON in the format: {{"job_tier": "Fresher" or "Mid" or "Senior"}}
    """
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile"
        )
        result = json.loads(response.choices[0].message.content.strip())
        state["job_tier"] = result.get("job_tier", "N/A")
    except Exception as e:
        print(f"Error in determine_tier for '{state['Title']}':", e)
        state["job_tier"] = "N/A"
    return state


def build_job_workflow(client: Groq) -> StateGraph:
    graph = StateGraph(JobState)

    def wrapped_check_relevance(state: JobState):
        return check_relevance(state, client)

    def wrapped_check_competitor(state: JobState):
        return check_competitor_with_fallback(state, client)

    def wrapped_determine_tier(state: JobState):
        return determine_tier(state, client)

    graph.add_node("check_relevance", wrapped_check_relevance)
    graph.add_node("check_competitor", wrapped_check_competitor)
    graph.add_node("determine_tier", wrapped_determine_tier)
    graph.add_edge("check_relevance", "check_competitor")
    graph.add_edge("check_competitor", "determine_tier")
    graph.set_entry_point("check_relevance")
    graph.set_finish_point("determine_tier")
    return graph


def process_job(job: dict, field: str, client: Groq, tavily_client: TavilyClient) -> Optional[dict]:
    global FIELD
    FIELD = field  # Update global field for relevance check
    state: JobState = {
        "Title": job.get("Title", ""),
        "Company": job.get("Company", ""),
        "Experience": job.get("Experience", ""),
        "Description": job.get("Description", ""),
        "is_relevant": None,
        "is_competitor": None,
        "job_tier": None,
    }
    graph = build_job_workflow(client)
    compiled_graph = graph.compile()
    result_state = compiled_graph.invoke(state)
    if (result_state.get("is_relevant", "").lower() == "yes" and
        result_state.get("is_competitor", "").lower() == "no"):
        job["Job Tier"] = result_state.get("job_tier", "N/A")
        career_url = get_company_career_page(job.get("Company", ""), tavily_client)
        if career_url:
            job["Job Link"] = career_url
            return job
        else:
            print(f"Dropping job '{job.get('Title')}' because no website was found for {job.get('Company')}")
            return None
    else:
        return None


# ------------------------- SELENIUM & BEAUTIFULSOUP FUNCTIONS -------------------------
def setup_webdriver():
    options = webdriver.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    desktop_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
    options.add_argument(f'user-agent={desktop_ua}')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)
    driver.implicitly_wait(10)
    return driver


def extract_jobs(soup):
    job_list = []
    job_wrappers = soup.select("div.srp-jobtuple-wrapper")
    for wrapper in job_wrappers:
        job = wrapper.select_one("div.cust-job-tuple")
        if not job:
            continue
        title_elem = job.select_one("a.title")
        company_elem = job.select_one("a.comp-name, a.subTitle")
        exp_elem = job.select_one("span.expwdth, li.experience")
        sal_elem = job.select_one("span.sal-wrap, li.salary")
        loc_elem = job.select_one("span.locWdth, li.location")
        desc_elem = job.select_one("span.job-desc, div.job-description")
        posted_elem = job.select_one("span.fleft.postedDate, span.job-post-day")
        link_elem = job.select_one("a.title")
        job_list.append({
            'Title': title_elem.get_text(strip=True) if title_elem else 'N/A',
            'Company': company_elem.get_text(strip=True) if company_elem else 'N/A',
            'Experience': exp_elem.get_text(strip=True) if exp_elem else 'N/A',
            'Salary': sal_elem.get_text(strip=True) if sal_elem else 'Not disclosed',
            'Location': loc_elem.get_text(strip=True) if loc_elem else 'N/A',
            'Description': desc_elem.get_text(strip=True) if desc_elem else 'N/A',
            'Posted Date': posted_elem.get_text(strip=True) if posted_elem else 'N/A',
            'Skills': ', '.join([tag.get_text(strip=True) for tag in job.select("li.tag, li.tag-li")]),
            'Job Link': link_elem["href"] if link_elem and link_elem.has_attr("href") else 'N/A'
        })
    return job_list


def get_page_source(driver):
    scroll_pause_time = 2
    screen_height = driver.execute_script("return window.screen.height;")
    i = 1
    while True:
        driver.execute_script(f"window.scrollTo(0, {screen_height} * {i});")
        i += 1
        time.sleep(scroll_pause_time)
        scroll_height = driver.execute_script("return document.body.scrollHeight;")
        if (screen_height * i) > scroll_height:
            break
    return BeautifulSoup(driver.page_source, 'html.parser')


# ------------------------- HELPER FUNCTION: FILTER JOBS -------------------------
def is_job_recent(posted_date: str) -> bool:
    pd_lower = posted_date.lower()
    if any(term in pd_lower for term in ["just now", "few hours", "today", "1 day", "2 days", "3 days"]):
        return True
    if "day" in pd_lower:
        return False
    return True


# ------------------------- MAIN SCRAPING FUNCTION -------------------------
def scrape_jobs_for_domain(domain: str, client: Groq, tavily_client: TavilyClient) -> pd.DataFrame:
    global FIELD
    FIELD = domain.lower()
    search_keyword = FIELD_KEYWORDS[domain]
    driver = setup_webdriver()
    base_url = "https://www.naukri.com/jobs-in-india  "
    params = {
        "k": search_keyword,
        "l": "india",
        "jobAge": "1"
    }
    url = f"{base_url}?{urlencode(params)}"
    driver.get(url)
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.srp-jobtuple-wrapper"))
        )
    except TimeoutException:
        pass
    time.sleep(5)
    soup = get_page_source(driver)
    job_list = extract_jobs(soup)
    driver.quit()
    final_jobs = []
    for job in job_list:
        processed = process_job(job, domain, client, tavily_client)
        if processed and is_job_recent(processed.get("Posted Date", "")):
            final_jobs.append(processed)
    return pd.DataFrame(final_jobs)


# ------------------------- EXCEL EXPORT FUNCTION -------------------------
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()


# ------------------------- MAIN STREAMLIT APP -------------------------
def main():
    st.set_page_config(page_title="Job Scraper", layout="wide")
    st.title("🌐 Job Scraper - Domain Specific")
    st.markdown("Select a job domain to scrape and download Excel results")

    # User input for API keys
    groq_api_key = st.text_input("Enter your Groq API Key:", type="password")
    tavily_api_key = st.text_input("Enter your Tavily API Key:", type="password")

    if not groq_api_key or not tavily_api_key:
        st.warning("Please enter both Groq and Tavily API keys to proceed.")
        return

    try:
        client = Groq(api_key=groq_api_key)
        tavily_client = TavilyClient(tavily_api_key)
    except Exception as e:
        st.error(f"Failed to initialize API clients: {e}")
        return

    # Domain selection
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_domain = st.selectbox("Select Job Domain", options=list(FIELD_KEYWORDS.keys()))
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        start_scrape = st.button("🔍 Scrape Jobs", use_container_width=True)

    if 'scraped_data' not in st.session_state:
        st.session_state.scraped_data = None

    if start_scrape:
        with st.spinner(f"Scraping jobs for {selected_domain}... This may take 1-2 minutes"):
            df = scrape_jobs_for_domain(selected_domain, client, tavily_client)
            if not df.empty:
                st.session_state.scraped_data = df
                st.session_state.domain = selected_domain
                st.success(f"Found {len(df)} relevant jobs for {selected_domain}")
            else:
                st.warning("No relevant jobs found for this domain")

    # Display results and download button
    if st.session_state.scraped_data is not None:
        domain = st.session_state.domain
        df = st.session_state.scraped_data
        st.markdown(f"### 📋 {domain} Jobs Results")
        st.dataframe(df, use_container_width=True)
        excel_data = to_excel(df)
        st.download_button(
            label="📥 Download Excel",
            data=excel_data,
            file_name=f"Filtered_Naukri_{domain.replace(' ', '_')}_Jobs.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


if __name__ == "__main__":
    main()

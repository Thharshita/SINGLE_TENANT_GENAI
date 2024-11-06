import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from src.logger import logger
from src.data_processing.text_processing import process_raw_text, generate_embedding
from src.scrapers.web_scraper_selenium import selenium_fetch_links, extract_contents_selenium
from src.data_processing.text_processing import process_text, process_tat
from tenacity import retry, stop_after_attempt, wait_exponential
from src.constant import PROXY, UNWANTED_DOMAINS, UNWANTED_PREFIXES, UNWANTED_URLS
from src.utils import get_database
import time
from typing import Tuple, List, Any, Dict


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def fetch_links(url) -> Tuple[int, List[str], str]:
    """
    Fetches links from a URL with retries.

    Args:
        url (str): URL to fetch links from.

    Returns:
        Tuple[int, List[str], str]: Link status, list of links, and Selenium usage indicator.
    """
    try:
        logger.info("Fetching links")
        selenium="NO"
        
        response = requests.get(url,
            proxies=PROXY, 
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10)
        
        # Check response status code
        if response.status_code != 200:
            return 0, {"status": 0, "message": f"Invalid status code: {response.status_code}", "result": "Link is not valid"}, "NO"
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        if response.status_code == 200:
            list_of_links=[url]
            
            links = soup.find_all('a', href=True)
            #logger.info(f"links:{links}")
            extracted_links = [urljoin(url, link['href']) for link in links if is_valid_link(url, link['href'])]
            
            # Check if links require Selenium
            if "https://www.enable-javascript.com/" in extracted_links or not extracted_links:
                logger.info("Passing to selenium for link extraction")
                selenium='YES'
                link_status, list_links= await selenium_fetch_links(url)
                return link_status, list_links, selenium

            list_of_links = [url] + extracted_links 
            list_of_links=set(list_of_links)
            final_list_of_links=list(list_of_links)
            
            logger.info(f"extracted_links:{final_list_of_links}")
            logger.info(f"extracted_links lenght:{len(final_list_of_links)}")
           
            return 1, final_list_of_links, selenium

    except Exception as e:
        logger.error(f"Error while fetching link{url}: {str(e)}")
        logger.info("Trying Selenium after failing BeautifulSoup")
        
        selenium='YES'
        link_status, list_links= await selenium_fetch_links(url)
        return link_status, list_links, selenium



def is_valid_link(base_url: str, link: str) -> bool:
    """
    Checks if a link is valid.

    Args:
        base_url (str): Base URL.
        link (str): Link to validate.

    Returns:
        bool: True if link is valid, False otherwise.
    """
    logger.info("\nValidating link")
    
    if link.startswith(tuple(UNWANTED_PREFIXES)) or any(domain in link for domain in UNWANTED_DOMAINS) or link in UNWANTED_URLS:
        return False
    
    if not link.startswith('http'): #which is just a path , not a complete link
        link = urljoin(base_url, link)
    
    logger.info(f"base_url: {base_url}")
    logger.info(f"link: {link}")
    
    parsed_link = urlparse(link)
    base_domain = urlparse(base_url).netloc
    logger.info(f"parsed_link netloc:{parsed_link.netloc}")
    logger.info(f"base_domain netloc: {base_domain}")
    
    # if parsed_link.netloc != base_domain and not parsed_link.netloc.endswith('.' + base_domain):
    if parsed_link.netloc != base_domain :
        return False
    
    return True

async def extract_contents(
    links: List[str], 
    use_selenium: str, 
    crawl_application_name: str, 
    crawl_application_id: str, 
    crawl_link: str
) -> Dict[str, Any]:
    
    """
    Extracts content from links.

    Args:
        links (List[str]): List of links to extract content from.
        use_selenium (str): Whether to use Selenium.
        crawl_application_name (str): Application name.
        crawl_application_id (str): Application ID.
        crawl_link (str): Main link whose sublinks will sldo be extracted 

    Returns:
        Dict[str, Any]: { "status": 1,"message": "Pragraph and embedding stored in database","result": "","total_time": 89.33447694778442}
    """

    try:
        logger.info("Inside extract content")
        logger.info("Links: {}".format(links))
        logger.info("use_selenium: {}".format(use_selenium))

        if use_selenium=="YES":
            insertion_response=await extract_contents_selenium(links, crawl_application_name, crawl_application_id,crawl_link)
            return insertion_response
            
        db=get_database()
        Total_Links=len(links)
        header_footer= "yes"
        processed_links=0
        start_time=time.time()

        for link in links[0:72]:
            try:
                response = requests.get(link)
                content = response.content
                
            
                parsed_content = BeautifulSoup(content, 'html.parser')
                
                if header_footer == "no":
                    header_footer = "yes"
                    
                    text_content = parsed_content.get_text()

                    cleaned_raw_text=process_raw_text(text_content)
                    if cleaned_raw_text==0:
                        return {"status":0 , "message":"Unable to clean text", "result":cleaned_raw_text}

                    
                    raw_text={
                            "link": link,
                            "content": cleaned_raw_text,
                            # "corpus_embedding":generate_embedding(cleaned_raw_text)
                        }
    
                    logger.info(f"Text from link {link} extracted")
                    processed_links += 1

                    storing_response = db.store_raw_corpus([raw_text], crawl_application_name, 
                                                    crawl_application_id,crawl_link)
                    if storing_response["status"]==0:
                          return storing_response

                    paragraphs_list, link_list, embeddings_list = process_text([raw_text])
                    if paragraphs_list==0:
                        return {"status":0 , "message":"Unable to process text", "result":embeddings_list}
                    
                    insert_response=db.insert_paragraph_embeddings(paragraphs_list, link_list, embeddings_list,
                                                            crawl_application_name, crawl_application_id,crawl_link)
                    if insert_response["status"]==0:
                        return insert_response

                else:
                    header_tags = parsed_content.find_all('header')
                    for header_tag in header_tags:
                        header_tag.decompose()
                    
                    footer_tags = parsed_content.find_all('footer')
                    for footer_tag in footer_tags:
                        footer_tag.decompose()

                    title_tags = parsed_content.find_all('title')
                    for title_tag in title_tags:
                        title_tag.decompose()

                    for skip_content in parsed_content.find_all("a", class_="visually-hidden focusable"):
                        skip_content.decompose()

                    for slider in parsed_content.find_all("div", class_="slider-social"):
                        slider.decompose()

                    for sidebar_capt in parsed_content.find_all("div", class_="fixed-slider-capt"):
                        sidebar_capt.decompose()

                    text_content = parsed_content.get_text()
                    cleaned_raw_text=process_raw_text(text_content)
                    if cleaned_raw_text==0:
                        return {"status":0 , "message":"Unable to clean text", "result":cleaned_raw_text}
                    
                    raw_text={
                            "link": link,
                            "content": cleaned_raw_text}
                            # "corpus_embedding":generate_embedding(cleaned_raw_text)}

                    logger.info(f"Text from link {link} extracted")
                    processed_links += 1

                    storing_response = db.store_raw_corpus([raw_text], crawl_application_name, 
                                                    crawl_application_id,crawl_link)
                    if storing_response["status"]==0:
                          return storing_response

                    paragraphs_list, link_list, embeddings_list = process_text([raw_text])
                    if paragraphs_list==0:
                        return {"status":0 , "message":"Unable to process text", "result":embeddings_list}
                    
                    insert_response=db.insert_paragraph_embeddings(paragraphs_list, link_list, embeddings_list,
                                                            crawl_application_name, crawl_application_id,crawl_link)
                    if insert_response["status"]==0:
                        return insert_response  #{"status":1, "message": "Pragraph and embedding stored in database","result":""}

            except TimeoutError:
                logger.error(f"Timeout error occurred for link: {link}")
                continue
            
            except requests.RequestException as e:
                logger.error(f"An error occurred for link: {link}: {str(e)}")
                continue
            
        logger.info(f"Total links:{Total_Links}, Total scraped links:{processed_links}")  
        end_time = time.time()

        total_time=process_tat(start_time, end_time)
        logger.info(f"Total time taken for embedding and storing:{total_time}")
        insert_response["total_time"]=total_time
        return insert_response
        
    except Exception as e:
        logger.error(f"An error occurred while crawling raw text website: {str(e)}")
        return {"status":0 , "message":"Unable to process text", "result":str(e)}


async def check_link(url):
    try:
        logger.info("Checking links")
        logger.info(f"url: {url}")
        selenium="NO"

        response = requests.get(url,
            proxies=PROXY, 
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10)
        
        # Check response status code
        if response.status_code != 200:
            return 0, {"status": 0, "message": f"Invalid status code: {response.status_code}", "result": "Link is not valid"}, "NO"
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        if response.status_code == 200:
            list_of_links=[url]
            
            links = soup.find_all('a', href=True)
            #logger.info(f"links:{links}")
            extracted_links = [urljoin(url, link['href']) for link in links if is_valid_link(url, link['href'])]
            
            # Check if links require Selenium
            if "https://www.enable-javascript.com/" in extracted_links or not extracted_links:
                logger.info("Passing to selenium for link extraction")
                selenium='YES'
    
            return 1, list_of_links, selenium

    except Exception as e:
        logger.error(f"Error while fetching link{url}: {str(e)}")
        logger.info("Trying Selenium after failing BeautifulSoup")
        
        selenium='YES'
        return 1, list_of_links, selenium


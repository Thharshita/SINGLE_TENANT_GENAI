from src.scrapers.web_scraper_bs import fetch_links, extract_contents
from src.logger import logger
from src import schema
from fastapi import Query,APIRouter, Depends
from src.logger import logger
from src.config import DATABASE_TYPE, chroma_host, chroma_port
from src.utils import get_database
from src.config import application_name, application_id, element_id, chroma_store_entire_page_collection, chroma_paragraph_embedding_collection
from src.oauth2 import get_current_user
from src.database_types.chroma_db_database import ebase

router=APIRouter(tags=["SCRAPE"])
import validators

@router.post("/scrape_link/")
async def scrape_link_data(crawl: schema.Name_link, current_user_uuid:dict=Depends(get_current_user))-> dict:
    """
    Scrapes link data and saves it to 2 the database {page data, chunksdata}.

    Args:
        crawl (schema.Name_link): Link to scrape.
        current_user_uuid (dict): Current user's UUID.

    Returns:
        dict: {"status":1, "message": "Pragraph and embedding stored in database","result":"","tat":12} or error
    """
    try:
        # Validate URL
        if not validators.url(crawl.element_id):
            return {"status":0, "message":"Invalid URL", "result":"Please add url in given format {https://moneyview.in/}"}
        
        if crawl.element_id.endswith("/"):
            crawl.element_id=crawl.element_id[:-1]
        
        # Check user authentication
        if current_user_uuid["status"] == 0:
            return current_user_uuid
        
        # Fetch links
        link_status, links, use_selenium = await fetch_links(crawl.element_id)  #array of link
        if link_status==0:
            return links
        
        response= await extract_contents(links, use_selenium, application_name, application_id,crawl.element_id)
        return response
    
    except Exception as e:
        logger.info(f"An error occurred while scraping: {str(e)}")
        return {"status":0 , "message":"", "result":str(e)}
    

@router.post("/delete_chunkdata")
async def delete_item_by_metadata(element_id, current_user_uuid:dict=Depends(get_current_user)):
    try:
        if current_user_uuid["status"] == 0:
            return current_user_uuid
        db=get_database()
        result=await db.delete_content(application_id, element_id)
        return result    
    except Exception as e:
        logger.error(f"An error occurred while deleting the item: {str(e)}")
        return str(e)

@router.post("/delete_page_content")
async def delete_document(element_id, current_user_uuid:dict=Depends(get_current_user)):
    try:
        if current_user_uuid["status"] == 0:
            return current_user_uuid
        db=get_database()
        result=await db.delete_content(application_id, element_id,chroma_store_entire_page_collection)
        return result    
    except Exception as e:
        logger.error(f"An error occurred while deleting the item: {str(e)}")
        return str(e)
    
@router.post("/check_page_data")
async def get_page_data( current_user_uuid:dict=Depends(get_current_user)):
    try:
        if current_user_uuid["status"] == 0:
            return current_user_uuid
        db=get_database()
        client= db.connect()
        collection = client.get_or_create_collection(name=chroma_store_entire_page_collection, embedding_function=ebase)
        data=collection.get()
        if data['ids']==[]:
            logger.error(f"No data found")
            return {"status":0,"message":"Data not exists","result":""}
        
        return {"status":1,"message": "", "result": data}
    except Exception as e:
        logger.error("Exception occured while delting user %s", str(e))
        return {"status":0, "message":"","result":str(e)}


@router.post("/check_chunks_data")
async def get_chunks_data(current_user_uuid:dict=Depends(get_current_user)):
    try:
        if current_user_uuid["status"] == 0:
            return current_user_uuid
        db=get_database()
        client= db.connect()
        collection = client.get_or_create_collection(name=chroma_paragraph_embedding_collection, embedding_function=ebase)
        data=collection.get()
        if data['ids']==[]:
            logger.error(f"No data found")
            return {"status":0,"message":"Data not exists","result":""}
        
        return {"status":1,"message": "", "result": data}
    except Exception as e:
        logger.error("Exception occured while delting user %s", str(e))
        return {"status":0, "message":"","result":str(e)}

  
@router.get("/show_all_data")
async def show_all_data():
    try: 
        db= get_database()
        client= db.connect()         
        # collection=client.get_or_create_collection(name=pdf_collection)
        # existing_admin=collection.get(where={"email":admin_username})
        # logger.info(f"Existing_admin:{existing_admin}")
        # if existing_admin['ids']==[]:
        #     logger.error("Unauthorized admin ")
        #     return {"Admin not valid"}
        #     # raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
        #     #                     detail=f"ADMIN NOT VALID")
        collection=client.get_or_create_collection(name=chroma_paragraph_embedding_collection, embedding_function=ebase)
        data=collection.get()
        # logger.info(f"\n existing_file_data:{data}")
        if data['ids']==[]:
            logger.error(f"No data found")
            return {"status":0,"message":"Data not exists","result":""}
        
        return {"status":1,"message": "", "result": data}
    except Exception as e:
        logger.error("Exception occured while delting user %s", str(e))
        return {"status":0, "message":"","result":str(e)}


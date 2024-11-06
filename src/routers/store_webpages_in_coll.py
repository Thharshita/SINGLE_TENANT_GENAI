from src.scrapers.web_scraper_bs import fetch_links, extract_contents, check_link
from src.logger import logger
from src import schema
from fastapi import Query,APIRouter, Depends
from src.logger import logger
from src.config import application_name, application_id, website_collection, website_collection_hindi
from src.data_processing.store_complete_link_content import process_store_webpage
from src.utils import get_password_hash, get_database
import validators
from src.database_types.chroma_db_database import ebase

router=APIRouter(tags=["Store_Complete_Webpage"])
# , current_user_uuid:dict=Depends(get_current_user)

global_language = "english"

def get_webpage_collection_name_based_on_language() -> str:
    if global_language.lower() == "hindi":
        return website_collection_hindi
    return website_collection

@router.post("/set_language/")
async def set_language(lang: str="english"):
    global global_language
    global_language = lang
    return {"status": 1, "message": "Language set successfully", "result": global_language}


@router.post("/scrape_internal_link/")
async def scrape_and_store_one_link(crawl: schema.Name_link):
    try:
        web_collection=get_webpage_collection_name_based_on_language()
        
        if not validators.url(crawl.internal_link):
            return {"status":0, "message":"Invalid URL", "result":"Please add url in given format {https://moneyview.in/}"}
        # if current_user_uuid["status"] == 0:
        #     return current_user_uuid
        if crawl.internal_link.endswith("/"):
            crawl.internal_link=crawl.internal_link[:-1]

        logger.info("\n only extracting one link")
        link_status, links, use_selenium = await check_link(crawl.internal_link)  #array of link
        if link_status==0:
            return links
        
        response=await process_store_webpage(links, use_selenium, application_name, application_id,crawl.element_id, collection_name= web_collection)
        logger.info(response)

        # return response
        return {"status":1,"message": "", "result": "data scraped successfully"}
        
    
    except Exception as e:
        logger.info(f"An error occurred while scraping: {str(e)}")
        return {"status":0 , "message":"", "result":str(e)}
    
@router.post("/scrape_and_store_webpage/")
async def scrape_and_store_webpages(crawl: schema.main_link):
    try:
        web_collection=get_webpage_collection_name_based_on_language()

        if not validators.url(crawl.element_id):
            return {"status":0, "message":"Invalid URL", "result":"Please add url in given format {https://moneyview.in/}"}
        
        if crawl.element_id.endswith("/"):
            crawl.element_id=crawl.element_id[:-1]
        # if current_user_uuid["status"] == 0:
        #     return current_user_uuid
        link_status, links, use_selenium = await fetch_links(crawl.element_id)  #array of link
        if link_status==0:
            return links
        
        response=await process_store_webpage(links, use_selenium, application_name, application_id,crawl.element_id, web_collection)
        return response
    
    except Exception as e:
        logger.info(f"An error occurred while scraping: {str(e)}")
        return {"status":0 , "message":"", "result":str(e)}
    
@router.get("/get_link_data")
async def get_information(link:str):
    try: 
        web_collection=get_webpage_collection_name_based_on_language()
        logger.info(f"\n get-link-data running from {web_collection}")
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
        collection=client.get_or_create_collection(name=web_collection, embedding_function=ebase)
        data=collection.get(where={"$and":[{"is_deleted":0},{"sub_link": link}]})
        # logger.info(f"\n existing_file_data:{data}")
        if data['ids']==[]:
            logger.error(f"No data found")
            return {"status":0,"message":"Data not exists","result":""}
        
        return {"status":1,"message": "", "result": data}
    except Exception as e:
        logger.error("Exception occured while delting user %s", str(e))
        return {"status":0, "message":"","result":str(e)}

# , current_user_uuid:dict=Depends(get_current_user)
@router.post("/delete_webpage")
async def delete_item_by_metadata(internal_link):
    try:
        web_collection=get_webpage_collection_name_based_on_language()
        # if current_user_uuid["status"] == 0:
        #     return current_user_uuid
        db=get_database()
        client=db.connect()
            
        collection = client.get_collection(name=web_collection, embedding_function=ebase)
        available_linkdata=collection.get(where={"$and":[{"sub_link":internal_link},{ "is_deleted":0}]})
        
        if available_linkdata['ids']==[]:
            return {"status":0, "message":"contentid not founds" ,"result":""}
        logger.info("Deleting")

        # result=collection.delete(where=
        #     {
        #     "sub_link": {
        #         "$eq": internal_link}
        #     }
        # )

        result= db.mark_deleted(web_collection, available_linkdata)
        logger.info(f"delte:{result}")
        
        return {"status": 1, "message": "Success", "result":"Content deleted successfuly"} 
    except Exception as e:
        logger.error(f"An error occurred while deleting the item: {str(e)}")
        return str(e)
    
@router.post("/delete_website")
async def delete_item_by_metadata(element_id):
    try:
        web_collection=get_webpage_collection_name_based_on_language()
        # if current_user_uuid["status"] == 0:
        #     return current_user_uuid
        db=get_database()
        client=db.connect()
            
        collection = client.get_collection(name=web_collection, embedding_function=ebase)
        logger.info("Deleting")

        available_content= collection.get(where={"$and":[{"content_id":element_id}, {"is_deleted":0}]})
        if available_content['ids']==[]:
            return {"status":0, "message":"contentid not found" ,"result":""}
        
        result= db.mark_deleted(web_collection,available_content)

        # result=collection.delete(where=
        #     {
        #     "content_id": {
        #         "$eq": element_id }
        #     }
        # )
        logger.info(f"delte:{result}")
        
        return {"status": 1, "message": "Content deleted successfuly", "result":result} 
    except Exception as e:
        logger.error(f"An error occurred while deleting the item: {str(e)}")
        return str(e)
    
   
@router.get("/show_all_data")
async def show_all_data():
    try: 
        web_collection=get_webpage_collection_name_based_on_language()
        logger.info(f"\n show all data running from {web_collection}")
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
        collection=client.get_or_create_collection(name=web_collection,embedding_function=ebase)
        data=collection.get()
        # logger.info(f"\n existing_file_data:{data}")
        if data['ids']==[]:
            logger.error(f"No data found")
            return {"status":0,"message":"Data not exists","result":""}
        
        return {"status":1,"message": "", "result": data}
    except Exception as e:
        logger.error("Exception occured while delting user %s", str(e))
        return {"status":0, "message":"","result":str(e)}


@router.post("/update_link_data")
async def change_link_data(internal_link:str, new_data:str, element_id="https://www.centralbankofindia.co.in/en"):
    try: 
        web_collection=get_webpage_collection_name_based_on_language()
        logger.info("\n change-link-data running")
        db= get_database()
        client= db.connect()            
        collection=client.get_or_create_collection(name=web_collection, embedding_function=ebase)
        data=collection.get(where={"$and": [{"content_id": element_id}, {"sub_link": internal_link}, {"is_deleted":0}]})
        # logger.info(f"\n existing_file_data:{data}")
        if data['ids']==[]:
            logger.error(f"No data found")
            return {"status":0,"message":"Data not exists","result":""}
        
        
        collection.upsert(
            ids=data['ids'],
    # embeddings=[[1.1, 2.3, 3.2], [4.5, 6.9, 4.4], [1.1, 2.3, 3.2], ...],
    # metadatas=[{"chapter": "3", "verse": "16"}, {"chapter": "3", "verse": "5"}, {"chapter": "29", "verse": "11"}, ...],
            documents=[new_data])

        return {"status":1,"message": "", "result": "Data of given link is updated"}
    except Exception as e:
        logger.error("Exception occured while delting user %s", str(e))
        return {"status":0, "message":"","result":str(e)}
    

@router.post("/insert_link_data")
async def insert_link_data(internal_link:str, new_data:str, element_id="https://www.centralbankofindia.co.in/en"):
    try: 
        logger.info("\n insert-link-data running")
        db= get_database()
        client= db.connect()   
        web_collection=get_webpage_collection_name_based_on_language()
         
        collection=client.get_or_create_collection(name=web_collection,embedding_function=ebase)
        data=collection.get(where={"$and": [{"content_id": element_id}, {"sub_link": internal_link}, {"is_deleted":0}]})
        # logger.info(f"\n existing_file_data:{data}")
        if data['ids']!=[]:
            logger.error(f"data already found")
            return {"status":0,"message":"Data exists for this internal link and element_id, pls update","result":""}
        
        raw_text=[{"link":internal_link, "content":new_data}]  #because i already have funcion made to insert link and its data
        
        result=db.store_web_page(raw_text, application_name, application_id, element_id,web_collection)
        return result
       
    except Exception as e:
        logger.error("Exception occured while delting user %s", str(e))
        return {"status":0, "message":"","result":str(e)}
    
@router.get("/show_active_data")
async def show_all_data():
    try: 
        web_collection=get_webpage_collection_name_based_on_language()

        logger.info(f"\n show all data running {website_collection}")
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
        collection=client.get_or_create_collection(name=web_collection)
        data=collection.get(where={"is_deleted":0})
        # logger.info(f"\n existing_file_data:{data}")
        if data['ids']==[]:
            logger.error(f"No data found")
            return {"status":0,"message":"Data not exists","result":""}
        
        return {"status":1,"message": "", "result": data}
    except Exception as e:
        logger.error("Exception occured while delting user %s", str(e))
        return {"status":0, "message":"","result":str(e)}

@router.get("/show_deleted_data")
async def show_all_data():
    try:
        web_collection=get_webpage_collection_name_based_on_language() 
        logger.info(f"\n showing delted data from {web_collection}")
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
        collection=client.get_or_create_collection(name=web_collection, embedding_function=ebase)
        data=collection.get(where={"is_deleted":1})
        # logger.info(f"\n existing_file_data:{data}")
        if data['ids']==[]:
            logger.error(f"No data found")
            return {"status":0,"message":"Data not exists","result":""}
        
        return {"status":1,"message": "", "result": data}
    except Exception as e:
        logger.error("Exception occured while delting user %s", str(e))
        return {"status":0, "message":"","result":str(e)}
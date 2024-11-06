
from src.oauth2 import get_current_user
from fastapi import APIRouter, UploadFile,Depends
from src.logger import logger
from src.oauth2 import get_current_user
from src.pipeline.phi3_demo import get_phi3_response, get_phi3_response_stream
from src.config import general_response_hindi, application_name, application_id, website_collection, website_collection_hindi, chroma_paragraph_embedding_collection, general_response, phi_response_collection
from src.data_processing.store_complete_file_content import extract_and_store
from src.data_processing.store_complete_link_content import process_store_webpage
from src import schema
from src.scrapers.web_scraper_bs import check_link
from src.utils import get_database
from src.pipeline.phi3_demo import store_response_in_collection
from src.database_types.chroma_db_database import ebase

router = APIRouter(tags=["Qna_summary_query"])

# , current_user_uuid:dict=Depends(get_current_user)
#call extract_and_store function in PDF_ingestion class which has class object and call p.process_file_bytes
# extract filetype, Received query, filesize, call store_pdf_Content
#check in pdf_Collection and delete f same content id and project_id 
# #save complete pdf--"documents": [full_text ],
#                 "metadatas":{"project_name":project_name, "project_id":project_id, "content_id":content_id, 
#                 "file_name":file_name,"file_type":file_extension,"created_at":datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")},
#                 "ids":str(uuid.uuid4())
#get_phi_response--->
#store
#response u get :{
#   "status": 1,
#   "message": "success",
#   "generated_response": " Title: Application of Neural Networks in Modeling Traffic Accidents and Recognition for Autonomous Vehicles\n\nAbstract: This paper explores the use of neural networks in modeling traffic accidents and their recognition for autonomous vehicles. The study analyzes various data sets and neural network architectures to develop robust models for accident pattern recognition and prediction. The paper also discusses the integration of these models into autonomous vehicle systems, considering the challenges and limitations associated with the technology.\n\n1. Introduction\n\nWith the advent of autonomous vehicles, the need for advanced methods to model and recognize traffic accidents has become increasingly important. Neural networks, with their ability to learn and generalize from data, have emerged as a powerful tool for this purpose. This paper presents a comprehensive study on the application of neural networks to model traffic accidents and recognition for autonomous vehicles.\n\n2. Data Collection and Preprocessing\n\nThe first",
#   "generated_response_url": "NA",
#   "query_token": "prompt",
#   "output_token": 142,
#   "Tat": 522.4287919998169,
#   "sender_id": "harshita@123"
# }

@router.post("/file_operations")
async def get_query_response(file: UploadFile, file_extension:str, element_id:str, category: str, number_of_question:int=3, query:str="",sender_id="", language="english", current_user_uuid:dict=Depends(get_current_user)):
    try:
        # if current_user_uuid["status"] == 0:
        #     return current_user_uuid
        file_name = file.filename
        logger.info("\n Reading File Bytes")
        file_bytes = await file.read()

        result= await extract_and_store(file_name,file_extension, file_bytes, application_name, application_id, element_id)
        # logger.info(f"result:{result}")
        logger.info(f'Tokens of corpus:{result["Word_tokens"]}')
        corpus= result["Document_text"]
        
        f_result=await get_phi3_response(element_id, category, number_of_question, query, corpus,sender_id=sender_id)
        return f_result

    except Exception as e:
        logger.error(str(e))
        return  {"status":0, "message":"","result":str(e)}


@router.post("/website_operations")
async def scrape_store_generate(crawl_content_id:str,element_id:str, category: str, number_of_question:int=3, 
                        query:str="What is this text about?",sender_id:str="", language:str="hindi",current_user_uuid:dict=Depends(get_current_user)):
    try:
        # if current_user_uuid["status"] == 0:
        #     return current_user_uuid
        logger.info(f"language:{language}")
        logger.info(f"sender_id:{sender_id}")
        logger.info("\n website operation")
        link_status, links, use_selenium = await check_link(element_id)  #array of link
        if link_status==0:
            return links
        
        if language=="hindi":
            web_collection=website_collection_hindi
        else:
            web_collection=website_collection

        response=await process_store_webpage(links, use_selenium, application_name, application_id,crawl_content_id, web_collection)
        logger.info(response)

        # return response
        
        db= get_database()
        client= db.connect()
        collection=client.get_or_create_collection(name=web_collection,embedding_function=ebase)
        data=collection.get(where={"sub_link": element_id})
        if data['ids']==[]:
            logger.error(f"No data found")
            return {"status":0,"message":"Data not exists","result":""}
        
        # logger.info(f'Tokens of corpus:{len(data["documents"].split(" "))}')
        corpus= data["documents"][0]
        
        f_result=await get_phi3_response(element_id, category, number_of_question, query, corpus, sender_id=sender_id, language=language)
        logger.info(f"result:{f_result}")
        return f_result
    except Exception as e:
        logger.info(f"An error occurred while scraping: {str(e)}")
        return {"status":0 , "message":"", "result":str(e)}


#get 3 similar content, combine them and get result out of it
# from src.data_processing.text_processing import generate_embedding, process_tat
# from src.config import application_id, chroma_store_entire_page_collection
# from src.utils import transform_data_pdf, transform_data
# import time

# # limit: int = 2, 
# @router.post('/generate_answer_from_similar_content')
# async def get_generated_answer(query: str, current_user_uuid:dict=Depends(get_current_user)):
#     try:
#         if current_user_uuid["status"] == 0:
#             return current_user_uuid
#         start_time = time.time()
#         # if limit > 10 or limit < 1:
#         #     return {"status_code": 0, "message": "Failure", "error": "Limit Value must be between 1 to 10"}
        
#         db= get_database()
#         limit=3
#         result, match_index = await db.get_cosine_similarity(query, [0], application_id, limit,chroma_paragraph_embedding_collection )
        
#         output=transform_data(result, match_index, "cosine")
#         # logger.info(f"output:{output}")
#         end_time = time.time()
#         time_taken=process_tat(start_time, end_time)
#         logger.info(f"Total time taken for searching:{time_taken}")
#         output["tat"]=time_taken
#         if output["message"]== '': #no similar content
#             return output
        

#         # logger.info(output["result"][0]["matching_content"])
#         corpus=" "
#         for i in range(len(output["result"])):
#             corpus+=''.join((output["result"][i]["matching_content"]))

#         logger.info(f'Number of tokens in corpus:{len(corpus.split(" "))}')

#         f_result=await get_phi3_response("searching", "query",0, query, corpus)
#         f_result["similar_content"] = output
#         return f_result
#     except Exception as e:
#         logger.info(f"An error occurred while scraping: {str(e)}")
#         return {"status":0 , "message":"", "result":str(e)}
    

from src.data_processing.text_processing import generate_embedding, process_tat
from src.config import application_id, chroma_store_entire_page_collection
from src.utils import transform_data_pdf, transform_data
import time
from src.routers.text_identification import text_language

#from web_collection that has only web_page content
import uuid

@router.post('/generate_answer_web_page')
async def get_generated_answer(query: str, sender_id="",language=None,current_user_uuid:dict=Depends(get_current_user)):
    """
    if language is hindi, similarity search from hindi_Collection else english_collection. 
    """
    try:
        if language is None:
            language=text_language(query)
            logger.info(f"the query language is:{language} ")
        
        if language=="hindi":
            web_collection=website_collection_hindi
        else:
            web_collection=website_collection

        logger.info("query: %s", query)
        if current_user_uuid["status"] == 0:
            return current_user_uuid
        start_time = time.time()
   
        query_tokens= len(query.split(" "))
        logger.info(f"Query:{query}")
        logger.info("query tokens: %s", query_tokens)
        db= get_database()
        limit=3
        result, match_index = await db.get_cosine_similarity(query, [0], application_id, limit, web_collection)
        
        output=transform_data(result, match_index, "cosine")
        
        # {"status":1, "message":"", "result": general_response}
        if output["message"]== '': #no similar content
            # response=[{SIMILARITY_RESPONSE[k]:v for k,v in i.items() }for i in transformed_data]
            new_data = {
            "status": output["status"],
            "message": output["message"],
            "generated_response": output["result"],  # Renaming the key
            "generated_response_url":output["result"]
}
            
            return new_data

        sim_links=[]
        for i in range(len(output["result"])):
            logger.info(f'similar text {i} found in page:{output["result"][i]["internal_link"]}')
            sim_links.append(output["result"][i]["internal_link"])
     
        end_time = time.time()
        time_taken=process_tat(start_time, end_time)
        logger.info(f"Total time taken for searching:{time_taken}")
        output["tat"]=time_taken
        
        # logger.info(output["result"][0]["matching_content"])
        corpus=output["result"][0]["matching_content"]

        logger.info(f'Number of tokens in corpus:{len(corpus.split(" "))}')

        f_result=await get_phi3_response("searching", "query",0, query, corpus, query_tokens,sim_links=[sim_links[0]], sender_id=sender_id,language=language)
        #first_similar_links = sim_links[0]
        #gen_resp = output["generated_response"] + "For more infomation visit this link" + str(first_similar_links)
        f_result["similar_links"]=sim_links
        #f_result["generated_response2"]=gen_resp
        
        # f_result["selected_text"]=corpus
        return f_result
    except Exception as e:
        logger.error(str(e))
        return {"status_code": 0, "message": "", "generated_response":str(e), "generated_response_url":str(e)}


from src.pipeline.phi3_demo import  answer_the_question, convert_language, convert_language_to_english
# ,current_user_uuid:dict=Depends(get_current_user)
@router.get('/generate_answer_web_page_2')
async def get_generated_answer_2(query: str, sender_id="", language=""):
    """
    query should be asked in English only.
    only website_Collection is used, if language seleted is Hindi then english response will be converted to hindi.
    """
    try:
        converted_query=query
        # if language is None or language=="hindi":
        query_language=text_language(query)
        logger.info(f"the query language is:{query_language} ")
        
        if query_language=="hindi":
            converted_query=await convert_language_to_english(query, language)
            # converted_query=converted_query[0]
            logger.info(f"converted query  is:{converted_query}")
                        
        
        web_collection=website_collection

        logger.info("query passed to search in db is: %s", converted_query)
        # if current_user_uuid["status"] == 0:
        #     return current_user_uuid
        start_time = time.time()
   
        query_tokens= len(converted_query.split(" "))
        logger.info("query tokens: %s", query_tokens)
        db= get_database()
        limit=3
        result, match_index = await db.get_cosine_similarity(converted_query, [0], application_id, limit, web_collection)
        
        output=transform_data(result, match_index, "cosine")
        
        # {"status":1, "message":"", "result": general_response}
        if output["message"]== '': #no similar content
            # response=[{SIMILARITY_RESPONSE[k]:v for k,v in i.items() }for i in transformed_data]
            new_data = {
            "status": output["status"],
            "message": output["message"],
            "generated_response": output["result"],  # Renaming the key
            "generated_response_url":output["result"]
}        
            return new_data

        sim_links=[]
        for i in range(len(output["result"])):
            logger.info(f'similar text {i} found in page:{output["result"][i]["internal_link"]}')
            sim_links.append(output["result"][i]["internal_link"])
    
        # logger.info(output["result"][0]["matching_content"])
        corpus=output["result"][0]["matching_content"]

        logger.info(f'Number of tokens in corpus:{len(corpus.split(" "))}')

        response=await answer_the_question(corpus, converted_query, "english")
        logger.info("generated response: {}".format(response))
        response= response+ "For more infomation visit this link" + sim_links[0]
        
        if "Unable to understand" in response:     
                return {"status":0, "message": "Insufficient Data", "generated_response":general_response}
        
        
        if language.lower() !="english" :
            response2=await convert_language(response, language)

            logger.info("generated response: {}".format(response))
        
            output_token=len(response2.split(" "))

            insert_response= await store_response_in_collection("searching", "query", 0,converted_query, corpus, response2, output_token, query_tokens, sender_id)

        else:
            output_token=len(response.split(" "))
            insert_response= await store_response_in_collection("searching", "query", 0,converted_query, corpus, response, output_token, query_tokens, sender_id)
        
        end_time = time.time()
        time_taken=process_tat(start_time, end_time)
        logger.info(f"Total time taken for searching:{time_taken}")

        return {"status":1, "message": "success", "generated_response1":response, "generated_response2":response2, "sim_links":sim_links ,"query_token":query_tokens,"output_token": output_token,"Tat":time_taken, "sender_id":sender_id}

        #first_similar_links = sim_links[0]
        #gen_resp = output["generated_response"] + "For more infomation visit this link" + str(first_similar_links)
       
        #f_result["generated_response2"]=gen_resp
        
        # f_result["selected_text"]=corpus
    except Exception as e:
        logger.error(str(e))
        return {"status_code": 0, "message": "", "generated_response":str(e), "generated_response_url":str(e)}


#combining 3 webpage data to get result   
# @router.post('/generate_answer_web_page3')
# async def get_generated_answer3(query: str, current_user_uuid:dict=Depends(get_current_user)):
#     try:
#         if current_user_uuid["status"] == 0:
#             return current_user_uuid
#         start_time = time.time()
   
        
#         db= get_database()
#         limit=3
#         result, match_index = await db.get_cosine_similarity(query, [0], application_id, limit, website_collection)
        
#         output=transform_data(result, match_index, "cosine")
        
#         logger.info(f"output:{output}")
#         sim_links=[]
       
#         for i in range(len(output["result"])):
#             logger.info(f'similar text {i} found in page:{output["result"][i]["internal_link"]}')
#             sim_links.append(output["result"][i]["internal_link"])
     
#         end_time = time.time()
#         time_taken=process_tat(start_time, end_time)
        
#         logger.info(f"Total time taken for searching:{time_taken}")
#         output["searching_tat"]=time_taken
#         if output["message"]== '': #no similar content
#             return output
        
#         logger.info(output["result"][0]["matching_content"])
        
#         corpus=""
#         for i in range(len(output["result"])):
#             corpus+=" ".join(output["result"][i]["matching_content"])
    
#         # corpus=output["result"][0]["matching_content"]

#         logger.info(f'Number of tokens in corpus:{len(corpus.split(" "))}')

#         f_result=await get_phi3_response("searching", "query",0, query, corpus)
#         f_result["similar_links"]=sim_links
#         f_result["selected_text"]=corpus
#         return f_result
#     except Exception as e:
#         logger.error(str(e))
#         return {"status_code": 0, "message": "", "result":str(e)}
  
    
#from chroma_embeddingcollection, applied similarity test on chks and tene 1st recieved page data to generate responsefrom model.
# @router.post('/generate_answer_chunk_page')
# async def get_generated_answer(query: str, sender_id="", current_user_uuid:dict=Depends(get_current_user)):
#     try:
#         if current_user_uuid["status"] == 0:
#             return current_user_uuid
#         start_time = time.time()

#         query_tokens= len(query.split(" "))
       
#         db= get_database()
#         limit=3
#         result, match_index = await db.get_cosine_similarity(query, [0], application_id, limit, chroma_paragraph_embedding_collection)
        
#         output=transform_data(result, match_index, "cosine")
#         logger.info(f"output:{output}")
#         end_time = time.time()
#         time_taken=process_tat(start_time, end_time)
        
#         logger.info(f"Total time taken for searching:{time_taken}")
#         output["tat"]=time_taken
#         if output["message"] == '': #no similar content
#             return output

#         sim_content=[]
#         sim_links=[]
#         sim_page=[]
#         for i in range(len(output["result"])):
#             logger.info(f'similar text {i} found in link:{output["result"][i]["internal_link"]}')
#             logger.info(f'similar text {i} found in page:{output["result"][i]["page_count"]}')
#             logger.info(f'similar text {i} found in content:{output["result"][i]["element_id"]}')
#             sim_links.append(output["result"][i]["internal_link"])
#             sim_content.append(output["result"][i]["element_id"])
#             sim_page.append(output["result"][i]["page_count"])
        
        
#         for i in range(len(output["result"])):
#             sim_links.append(output["result"][i]["internal_link"])

#         page_number=output["result"][0]["page_count"] 
#         content_id=output["result"][0]["element_id"]
#         sub_link=output["result"][0]["internal_link"]
         
#         client = db.connect()
#         collection = client.get_or_create_collection(name=chroma_store_entire_page_collection,embedding_function=ebase)
        
#         data=collection.get(where={"$and": [{"content_id": content_id}, {"sub_link":sub_link},{"page_number": page_number},{"is_deleted":0}]})
    
#         logger.info(f'data:{data}')
#         corpus= data['documents'][0]

#         f_result=await get_phi3_response("searching", "query",0, query, corpus,query_tokens, sim_links=sim_links[0],sender_id="")
#         f_result['links'] = sim_links
#         f_result['content'] = sim_content
#         f_result['page'] = sim_page

#         return f_result
    
#     except Exception as e:
#         logger.info(f"An error occurred while scraping: {str(e)}")
#         return {"status":0 , "message":"", "result":str(e)}
    

from fastapi import FastAPI, WebSocket
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
  
# @router.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     while True:
#         data = await websocket.receive_text()
#         await websocket.send_text(f"Message received: {data}")

@router.post("/websocket_url")
async def all_websocket_url():
    return {"connection established in url":"ws://127.0.0.1:5010/ws/generate_answer,  ws://127.0.0.1:5010/ws/generate_answer_yeild"}


connected_clients = []
@router.websocket("/ws/generate_answer_yeild/")
async def websocket_generate_answer_yeild(websocket: WebSocket, sender_id= "",language=None):
    logger.info(f"WebSocket:{websocket}")
    await websocket.accept()
    connected_clients.append(websocket)

    try:
        logger.info(f"Received sender_id: {sender_id}")

        # # Generate a new UUID if sender_id is empty
        if not sender_id.strip():
            sender_id = str(uuid.uuid4())
            logger.info(f"Generated new sender_id: {sender_id}")

        # await websocket.send_text("Please provide your query:")
        while True:
            
            query = await websocket.receive_text()  # Receive the query from the client
            query_tokens= len(query.split(" "))
            logger.info(f"Received query: {query}")
            
            if language is None:
                language=text_language(query)
            
            if language=="hindi":
                web_collection=website_collection_hindi
            else:
                web_collection=website_collection
            
            start_time = time.time()
            db = get_database()
            limit = 3
            
            result, match_index = await db.get_cosine_similarity(query, [0], application_id, limit, web_collection)
            output = transform_data(result, match_index, "cosine")
            logger.info(f"output:{output}")

            if output["message"] == '':
                for i in general_response:
                    await websocket.send_text(i)
                continue
            
            sim_links = []
            for i in range(len(output["result"])):
                logger.info(f'Similar text found in page: {output["result"][i]["internal_link"]}')
                sim_links.append(output["result"][i]["internal_link"])
                
            end_time = time.time()
            time_taken = end_time - start_time
            logger.info(f"Total time taken for searching: {time_taken}")
            
            corpus = output["result"][0]["matching_content"]
            logger.info(f"corpus: {corpus}")
            logger.info(f'Number of tokens in corpus: {len(corpus.split(" "))}')
   

            # f_result = get_phi3_response("searching", "query", 0, query, corpus, sim_links)
            context = "..."  # Fetch or define your context here
            complete_tokens = []
            async for response in get_phi3_response_stream("searching", "query", 0, query, corpus,sim_links=[sim_links[0]], language=language):
                complete_tokens.append(response["text"])
                await websocket.send_text(response["text"])
             
            output= "".join(complete_tokens)
            logger.info(f"output: {output}")
            output_token= len(output.split(' '))
            insert_response= await store_response_in_collection("searching", "query", 0,query, corpus, output, output_token, query_tokens,sender_id=sender_id)

            # f_result["similar_links"] = sim_links
            
            # await websocket.send_json(f_result)
            # await websocket.send_json({"status": 1, "message": "Finished"})
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        for i in "Websocket disconnected":
            await websocket.send_text(i)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        for i in general_response:
            await websocket.send_text(i)


connected_clients = []
max_history_length=3


@router.websocket("/ws/generate_answer_yeild_2/")
async def websocket_generate_answer_yeild_2(websocket: WebSocket, sender_id= "",language="en",):
    logger.info(f"WebSocket:{websocket}")
    await websocket.accept()
    conversation_history=[]
    connected_clients.append(websocket)

    def update_history(user_message,bot_response):
        conversation_history.append({"user": user_message, "bot": bot_response})
        if len(conversation_history) > max_history_length:
            conversation_history.pop(0)  # Remove the oldest message
        logger.info("History has been updated")

    try:
        logger.info(f"Received sender_id: {sender_id}")

        # # Generate a new UUID if sender_id is empty
        if not sender_id.strip():
            sender_id = str(uuid.uuid4())
            logger.info(f"Generated new sender_id: {sender_id}")

        while True:
            query = await websocket.receive_text()  # Receive the query from the client
            query_tokens= len(query.split(" "))
            logger.info(f"Received query: {query}")
            
            if language=="hi":
                response_language="hindi"
                fixed_response= general_response_hindi
                query=await convert_language_to_english(query, language)
                logger.info(f"converted query  is:{query}")
        
            elif language=="en":
                response_language="english"
                fixed_response= general_response
            
            else :
                query_language=text_language(query)
                logger.info(f"the query language is:{query_language}")
                
                if query_language=="hindi":
                    logger.info(f"the query language is:{query_language}")
                    query=await convert_language_to_english(query, language)
                    logger.info(f"converted query  is:{query}")
                    response_language="hindi"
                    fixed_response= general_response_hindi

                elif query_language=="english":
                    logger.info(f"the query language is:{query_language}")
                    response_language="english"
                    fixed_response= general_response
                
                else:
                    logger.info(f"the query language is:{query_language}")
                    await websocket.send_text(general_response + general_response_hindi)    

            logger.info(f"response_language:{response_language}")
            logger.info(f"fixed_response:{fixed_response}")

            web_collection=website_collection
            
            start_time = time.time()
            db = get_database()
            limit = 3
            
            merge_query= query
            for i in conversation_history[::-1]:
                merge_query+=i["user"]
                logger.info(f"merge_query:{merge_query}")
                
            result, match_index = await db.get_cosine_similarity(merge_query, [0], application_id, limit, web_collection)
            output = transform_data(result, match_index, "cosine")
            logger.info(f"output:{output}")

            if output["message"] == '':
                for i in fixed_response:
                    await websocket.send_text(i)
                continue
            
            sim_links = []
            for i in range(len(output["result"])):
                logger.info(f'Similar text found in page: {output["result"][i]["internal_link"]}')
                sim_links.append(output["result"][i]["internal_link"])
                
            end_time = time.time()
            time_taken = end_time - start_time
            logger.info(f"Total time taken for searching: {time_taken}")
            
            corpus = output["result"][0]["matching_content"]
            # logger.info(f"corpus: {corpus}")
            logger.info(f'Number of tokens in corpus: {len(corpus.split(" "))}')
   
            context = "..."  # Fetch or define your context here
            complete_tokens = []

            if response_language=="english":
                async for response in get_phi3_response_stream("searching", "query", 0, query, corpus,sim_links=[sim_links[0]], language=language):
                    complete_tokens.append(response["text"])
                    await websocket.send_text(response["text"])
                output_token= len(complete_tokens) 
                output= "".join(complete_tokens)
                logger.info(f"output: {output}")
                insert_response= await store_response_in_collection("searching", "query", 0,query, corpus, output, output_token, query_tokens,sender_id=sender_id)
                update_history(query,output)
            else:
                response=await answer_the_question(corpus, query, "english")
                logger.info("generated response: {}".format(response))
                response= response+ " For more infomation visit this link" + sim_links[0]+"."

                if "Unable to understand" in response:     
                    await websocket.send_text(fixed_response)
                    break
            
                # if language.lower() =="hindi" or query_language=="hindi":
                response2=await convert_language(response, fixed_response) #to hindi
                output_token= len(response2.split(' '))
                for i in response2:
                    # logger.info(i)
                    await websocket.send_text(i)
                insert_response= await store_response_in_collection("searching", "query", 0,query, corpus, response2, output_token, query_tokens,sender_id=sender_id)
                update_history(query,output)
        
            logger.info(conversation_history)

    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        for i in "Websocket disconnected":
            await websocket.send_text(i)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        for i in general_response:
            logger.info(i)
            await websocket.send_text(i)



# #same as generate_Ans_web_page, just using websocket
# @router.websocket("/ws/generate_answer")
# async def websocket_generate_answer(websocket: WebSocket):
#     logger.info(f"WebSocket:{websocket}")
#     await websocket.accept()

#     try:
#         while True:
#             query = await websocket.receive_text()  # Receive the query from the client
#             logger.info(f"Received query: {query}")
            
#             # if current_user_uuid["status"] == 0:
#             #     await websocket.send_text("User is not authorized.")
#             #     continue
#             start_time = time.time()
#             db = get_database()
#             limit = 3
            
#             result, match_index = await db.get_cosine_similarity(query, [0], application_id, limit, website_collection)
#             output = transform_data(result, match_index, "cosine")
#             logger.info(f"output:{output}")

#             if output["message"]== '': #no similar content        
#                 await websocket.send_text(general_response)
    
#             sim_links=[]
#             for i in range(len(output["result"])):
#                 logger.info(f'similar text {i} found in page:{output["result"][i]["internal_link"]}')
#                 sim_links.append(output["result"][i]["internal_link"])
         
#             end_time = time.time()
#             time_taken=process_tat(start_time, end_time)
#             logger.info(f"Total time taken for searching:{time_taken}")
#             output["tat"]=time_taken
            
#             # logger.info(output["result"][0]["matching_content"])
#             corpus=output["result"][0]["matching_content"]
    
#             logger.info(f'Number of tokens in corpus:{len(corpus.split(" "))}')
    
#             f_result=await get_phi3_response("searching", "query",0, query, corpus, sim_links=[sim_links[0]])
#             #first_similar_links = sim_links[0]
#             #gen_resp = output["generated_response"] + "For more infomation visit this link" + str(first_similar_links)
#             f_result["similar_links"]=sim_links
#             #f_result["generated_response2"]=gen_resp
            
#             # f_result["selected_text"]=corpus
#             await websocket.send_json(f_result)
#     except WebSocketDisconnect:
#         logger.info("Client disconnected")
#     except Exception as e:
#         logger.error(f"Error: {str(e)}")
#         await websocket.send_text(general_response)

@router.get("/show_all_output")
async def show_all_output():
    try: 
        logger.info("\n show all data running")
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
        collection=client.get_or_create_collection(name=phi_response_collection,embedding_function=ebase)
        data=collection.get()
        # logger.info(f"\n existing_file_data:{data}")
        if data['ids']==[]:
            logger.error(f"No data found")
            return {"status":0,"message":"Data not exists","result":""}
        
        return {"status":1,"message": "", "result": data}
    except Exception as e:
        logger.error("Exception occured while delting user %s", str(e))
        return {"status":0, "message":"","result":str(e)}

from datetime import datetime
@router.get("/summary_of_sender")
async def summary_of_sender(sender_id="", start_date="2024-10-01-15-10-04", end_date="2024-10-07-15-10-04"):
    try:
        
        logger.info(f"start_date: {start_date}, end_date: {end_date}")

        # Parse the date strings into datetime objects
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d-%H-%M-%S")
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d-%H-%M-%S")

        # Convert to Unix timestamps
        start_timestamp = int(start_datetime.timestamp())
        end_timestamp = int(end_datetime.timestamp())

        logger.info("\n\n show all data running")
        db= get_database()
        client= db.connect()         

        collection=client.get_or_create_collection(name=phi_response_collection,embedding_function=ebase)

        if not sender_id:
                    data=collection.get(where={"$and":[{"timestamp":{"$gte": start_timestamp}},{"timestamp":{"$lte": end_timestamp}}]})
        
        elif not start_date or not end_date:
            data=collection.get(where={"sender_id": sender_id, "is_deleted":0})

        else:
            data=collection.get(where={"$and":[{"sender_id":sender_id}, {"timestamp":{"$gte": start_timestamp}},{"timestamp":{"$lte": end_timestamp}}]})

        # data=collection.get(where={"sender_id":sender_id})
        logger.info(f"data: %s" % data)
        # logger.info(f"\n existing_file_data:{data}")  
        if data['ids']==[]:
            logger.error(f"No data found")
            return {"status":0,"message":"Data not exists, Please enter correct filter","result":""}
        total_query_asked=0
        total_tokens_generated=0
        
        min_query_tokens=10000
        max_query_tokens=0
        min_response_generated=10000
        max_response_generated=0

        for i in data['metadatas']:
            logger.info(f"check_date:{type(i['created_at'])}")
            total_query_asked+=1
            total_tokens_generated+= i["output_token"]
            min_query_tokens= min(min_query_tokens,int(i["query_tokens"]))
            max_query_tokens= max(max_query_tokens,int(i["query_tokens"]))
            min_response_generated= min(min_response_generated,int(i["output_token"]))
            max_response_generated= max(max_response_generated,int(i["output_token"]))
        
        output={"total_query_asked": total_query_asked,"min_query_tokens":min_query_tokens, "max_query_tokens":max_query_tokens, "min_response_generated":min_response_generated,
                "max_response_generated":max_response_generated, "total_tokens_generated": total_tokens_generated}
        return {"status":1, "message":"success", "result":output}
    except Exception as e:
        logger.error("Exception occured while sending summary of user %s", str(e))
        return {"status":0, "message":"","result":str(e)}
    
@router.post("/delete_")
async def delete_responses(sender_id=""):
    try:
        # if current_user_uuid["status"] == 0:
        #     return current_user_uuid
        db=get_database()
        client=db.connect()
            
        collection = client.get_collection(name= phi_response_collection,embedding_function=ebase)
        available_linkdata=collection.get(where={"sender_id":sender_id})
        if available_linkdata['ids']==[]:
            return {"status":0, "message":"senderid not founds" ,"result":""}
        logger.info("Deleting")

        result=collection.delete(where=
            {
            "sender_id": {
                "$eq": sender_id}
            }
        )
        logger.info(f"delte:{result}")
        
        return {"status": 1, "message": "Success", "result":"Content deleted successfuly"} 
    except Exception as e:
        logger.error(f"An error occurred while deleting the history: {str(e)}")
        return str(e)

# async def modify_qna(qna_text):
#     # if not qna_text.startswith("[{"):
#     #     qna_text.split("[{")
#     #     qna_text = qna_text[1]
#     # if not qna_text.endswith("}]"):
#     #     qna_text.split("}]")
#     #     qna_text = qna_text[0]
#     # return qna_text
#     logger.info(f"recieved_text:{qna_text}")
    
#     start = qna_text.find('{')
#     end = qna_text.rfind('}') + 1
#     logger.info(f"start:{start},end:{end}")
#     qna_text_corrected = "[" + qna_text[start:end]+"]"
#     logger.info(f"modified_text:{qna_text}")
#     logger.info(f"type :{type(qna_text_corrected)}")
#     qna_text_corrected_list=eval(qna_text_corrected_list)
#     return qna_text_corrected_list

import json
async def modify_qna(qna_text):
    logger.info(f"Received text: {qna_text}")
    
    # Find the start and end of the JSON object
    start = qna_text.find('{')
    end = qna_text.rfind('}') + 1
    
    # Extract the JSON-like string
    if start == -1 or end == -1:
        logger.error("No valid JSON found in the input text.")
        return None  # or handle it as you see fit

    qna_text_corrected = "[" + qna_text[start:end] + "]"
    logger.info(f"Modified text: {qna_text_corrected}")

    try:
        # Use json.loads instead of eval
        qna_text_corrected_list = json.loads(qna_text_corrected)
        logger.info(f"Parsed JSON list: {qna_text_corrected_list}")
        return qna_text_corrected_list
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON.")
        return None 


from src.pipeline.phi3_demo import create_question_and_answer, save_qna_in_file
@router.post("/create_dataset_llm")
async def generate_datasets(count:str=10, language:str="english"):
    try:
        # if current_user_uuid["status"] == 0:
        #     return current_user_uuid
        db=get_database()
        client=db.connect()
            
        collection = client.get_collection(name= website_collection,embedding_function=ebase)
        data=collection.get()
        # logger.info(f"data: {data}")  # debug output
        if data['ids']==[]:
            return {"status":0, "message":"senderid not founds" ,"result":""}
        logger.info("Deleting")

        for i in data["documents"]:
            qna_text=await create_question_and_answer(i,"_",count,language)
            qna_text_modified=await modify_qna(qna_text)
            result = save_qna_in_file(qna_text_modified)
            
            if not result:
                logger.info("Error")
                continue
                # return {"status": 0, "message": "Failed to save Q&A", "result":""}

        return {"status": 1, "message": "Success", "result":"Content added successfuly"} 
    except Exception as e:
        logger.error(f"An error occurred while deleting the history: {str(e)}")
        return str(e)
         
#search result:{'ids': [['d52883c3-90ae-4941-a47f-197885da7eb5', '2da37e53-fec3-42d9-ae8c-196aeb90f06e', '5a986a26-4781-4e2d-9f3d-8f289e98fb00', 'ea4d1570-5d85-4833-b15b-1e03b0b9b435', '2b6e7855-df17-45a5-a87a-febd07ff6d0e']], 'distances': [[1.6360032558441162, 1.6487722396850586, 1.665622591972351, 1.6851296424865723, 1.701249122619629]], 'metadatas': [[{'content_id': 'fastag issuance', 'created_at': '2024-08-20-17-55-51', 'file_type': 'FASTag Issuance to Customers.pdf', 'page_number': 3, 'project_id': 'kms@123', 'project_name': 'Kms', 'sub_link': ''}, {'content_id': 'fastag issuance', 'created_at': '2024-08-20-17-55-51', 'file_type': 'FASTag Issuance to Customers.pdf', 'page_number': 5, 'project_id': 'kms@123', 'project_name': 'Kms', 'sub_link': ''}, {'content_id': 'fastag issuance', 'created_at': '2024-08-20-17-55-51', 'file_type': 'FASTag Issuance to Customers.pdf', 'page_number': 5, 'project_id': 'kms@123', 'project_name': 'Kms', 'sub_link': ''}, {'content_id': 'fastag issuance', 'created_at': '2024-08-20-17-55-51', 'file_type': 'FASTag Issuance to Customers.pdf', 'page_number': 4, 'project_id': 'kms@123', 'project_name': 'Kms', 'sub_link': ''}, {'content_id': 'fastag issuance', 'created_at': '2024-08-20-17-55-51', 'file_type': 'FASTag Issuance to Customers.pdf', 'page_number': 2, 'project_id': 'kms@123', 'project_name': 'Kms', 'sub_link': ''}]], 'embeddings': None, 'documents': [['3', '14.', '15.', '4', '3.']], 'uris': None, 'data': None, 'included': ['metadatas', 'documents', 'distances']}
 
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse
import time
import logging
from src.oauth2 import get_current_user
from fastapi import APIRouter, UploadFile,Depends
from src.logger import logger
from src.oauth2 import get_current_user
from src.pipeline.phi3_demo import get_phi3_response
from src.config import application_name, application_id, website_collection, chroma_paragraph_embedding_collection, general_response
from src.data_processing.store_complete_file_content import extract_and_store
from src.data_processing.store_complete_link_content import process_store_webpage
from src import schema
from src.scrapers.web_scraper_bs import check_link
from src.utils import get_database

from src.data_processing.text_processing import generate_embedding, process_tat
from src.config import application_id, chroma_store_entire_page_collection
from src.utils import transform_data_pdf, transform_data
import time


router = APIRouter(tags=["Qna_summary_query"])

app = FastAPI()

logger = logging.getLogger(__name__)



# WebSocket endpoint
@app.websocket("/ws/generate_answer")
async def websocket_generate_answer(websocket: WebSocket):
    logger.info(f"WebSocket:{websocket}")
    await websocket.accept()

    try:
        while True:
            query = await websocket.receive_text()  # Receive the query from the client
            logger.info(f"Received query: {query}")
            
            # if current_user_uuid["status"] == 0:
            #     await websocket.send_text("User is not authorized.")
            #     continue
            
            start_time = time.time()
            db = get_database()
            limit = 3
            
            result, match_index = await db.get_cosine_similarity(query, [0], application_id, limit, website_collection)
            output = transform_data(result, match_index, "cosine")
            logger.info(f"output:{output}")

            if output["message"] == '':
                response_data = {
                    "status": output["status"],
                    "message": output["message"],
                    "generated_response": output["result"],
                    "generated_response_url": output["result"]
                }
                await websocket.send_json(response_data)
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
            async for response in get_phi3_response("searching", "query", 0, query, corpus,sim_links=[sim_links[0]]):
             
                logger.info(f"response: {response}")
                await websocket.send_text(response["text"])
            # f_result["similar_links"] = sim_links
            
            # await websocket.send_json(f_result)
            # await websocket.send_json({"status": 1, "message": "Finished"})
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await websocket.send_text(f"Error: {str(e)}")

# HTML page for testing the WebSocket connection
@app.get("/")
async def get():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test</title>
    </head>
    <body>
        <h1>WebSocket Test</h1>
        <input type="text" id="queryInput" placeholder="Type your query...">
        <button onclick="sendQuery()">Send</button>
        <ul id="responses"></ul>

        <script>
            const socket = new WebSocket("ws://localhost:8010/ws/generate_answer");

            socket.onmessage = function(event) {
                const responses = document.getElementById("responses");
                const newResponse = document.createElement("li");
                newResponse.textContent = event.data;
                responses.appendChild(newResponse);
            };

            function sendQuery() {
                const input = document.getElementById("queryInput");
                socket.send(input.value);
                input.value = '';
            }
        </script>
    </body>
    </html>
    """)


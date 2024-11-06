from fastapi import FastAPI
from llama_cpp import Llama
import time
import torch
from src.data_processing.text_processing import process_tat
from src.logger import logger
from src.utils import get_database
from src.config import (phi_response_collection, model_path,
                max_input_lenght, cpu_threads_count, gpu_layers_count, query_max_token, summ_max_token,
                qna_max_token, use_device_to_process, general_response,
                query_prompt_english,query_prompt_hindi, qna_prompt_english, qna_prompt_hindi, 
                summary_prompt_english,summary_prompt_hindi)

import datetime
# model_path = "C:/Users/HM/.cache/huggingface/hub/models--microsoft--Phi-3-mini-4k-instruct-gguf/snapshots/999f761fe19e26cf1a339a5ec5f9f201301cbb83/Phi-3-mini-4k-instruct-q4.gguf"
from src.routers.text_identification import text_language

if use_device_to_process=="gpu":
    device = torch.device("cuda" )
    # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
else:
    device = torch.device("cpu")

torch.cuda.set_device(0)
device = torch.device("cuda:0")
torch.cuda.set_device(device) 
torch.cuda.empty_cache()

print("device_type:-",device)
       
llm = Llama(
    model_path=model_path,
    n_ctx= int(max_input_lenght),       # Max sequence length
    n_threads= int(cpu_threads_count),      # Number of CPU threads to use
    n_gpu_layers= int(gpu_layers_count),  # Number of layers to offload to GPU (if available)
    main_gpu=1,
    temperature = 0.0,
    top_p = 0.1
)

logger.info(f" eos eos{llm.token_eos()}")
# llm.to('cuda')
app = FastAPI()

async def answer_the_question_stream(context,query,language):
    logger.info(f"the query language is:{language} ")
    if language=="hindi":
        prompt= query_prompt_hindi.format(context=context, query=query)
    else:
        prompt=query_prompt_english.format(context=context, query=query)
    
    output = llm(
        prompt,
        # f"<|system|>\nTry to find out the answer to the query only using the context information ,Please provide assistance as a representative of Central Bank Of India, If the answer to the query is not found within the context, fifty tokens only, return Unable to understand.<|end|> <|user|>\n context:{context} \n question:{query}<|end|>\n<|assistant|>",
        max_tokens= int(query_max_token),  # Generate up to 256 tokens
        stop=["<|end|>"], 
        echo=False,      # Do not echo the prompt in the output
        stream=True,
        temperature = 0.0,
        top_p = 0.1
    )
    text=" "

    for token in output:
        
        print(token["choices"][0]["text"])
        text += token["choices"][0]["text"] 
        # print(token, end='', flush=True)
        print(" ")
        yield token["choices"][0]
    # logger.info("Wait!! Generating response")

    # logger.info(f"output:{output}")
    # logger.info(f"output_word_count:{len(output.split(''))}")
    # return output["choices"][0]["text"]
    # return text

async def answer_the_question(context,query, language):
    logger.info(f"the query language is:{language} ")
    if language=="hindi":
        prompt= query_prompt_hindi.format(context=context, query=query)
    else:
        prompt= query_prompt_english.format(context=context, query=query)

    logger.info(f"prompt:::{prompt}")

    
    output = llm(
        # f"<|system|>\nYou have been provided with the context and a question, try to find out the answer to the query only using the context information. If the answer to the query is not found within the context, return Unable to understand.<|end|> <|user|>\n context:{context} \n question:{query}<|end|>\n<|assistant|>",
        # f"<|system|>\nTry to find out the answer to the query only using the context information ,Please provide assistance as a representative of Central Bank Of India, If the answer to the query is not found within the context, fifty tokens only, return Unable to understand.<|end|> <|user|>\n context:{context} \n question:{query}<|end|>\n<|assistant|>",
        prompt,
        max_tokens= int(query_max_token),  # Generate up to 256 tokens
        stop=["<|end|>"], 
        echo=False,      # Do not echo the prompt in the output
        temperature = 0.0,
        top_p = 0.1
    )
    logger.info("Wait!! Generating response")
    return output["choices"][0]["text"]


async def create_summary(context,query, language):

    if language=="hindi":
        prompt= summary_prompt_hindi.format(context=context, query=query)
    else:
        prompt=summary_prompt_english.format(context=context, query=query)
    
    output = llm(
        prompt,
        max_tokens= int(summ_max_token),  # Generate up to 256 tokens
        stop=["<|end|>"], 
        echo=False,       # Do not echo the prompt in the output
        temperature = 0.0,
        top_p = 0.1
    )
    logger.info("Wait!! Generating response")
    # logger.info(f"output:{output}")
    # logger.info(f"output_word_count:{len(output.split(''))}")
    return output["choices"][0]["text"]

async def create_question_and_answer(context,query,count,language):
    try:
        logger.info(f"context:{context}, count:{count},language:{language}")
        logger.info(f"create question and answer ")
        # if language=="hindi":
        #     prompt= qna_prompt_hindi.format(context=context, count=count)
        # else:
        #     prompt=qna_prompt_english.format(context=context, count=count)
    
        # logger.info(f"prompt:{prompt}")
        
        # output = llm(
        # "<|system|>\n"
        # "You have been provided with the context. "
        # f"Generate {count} questions with respective answers from given context in format "
        # "[{'question':'','answer':''},{'question':'','answer':''}] like this."
        # "<|end|> "
        # "<|user|>\n"
        # f"Context: {context}"
        # "<|end|>\n"
        # "<|assistant|>",
        output = llm(
            "<|user|>\n"
            "You have been provided with the context. Please generate a list atmost ten question-answer pairs that cover all the information in the context. "
            "The output format should be a JSON array of objects, with each object containing a 'question' and an 'answer'. Make sure to "
            "For example: [{'question':'Example question?','answer':'Example answer.'}, ...] "
            f"Context: {context} "
            "<|end|>\n"
            "<|assistant|>",

            # prompt,
            max_tokens= int(qna_max_token),
            stop=["<|end|>"],
            echo=False,
            temperature = 0.0,
            top_p = 0.1
        )
        logger.info("Wait!! Generating response")
    
        # logger.info(f"output:{output}")
        qna_text = output['choices'][0]['text'].strip()
        # logger.info(f"qna_text:{qna_text}")
        # logger.info(f"qna_text:{type(qna_text)}")
        # logger.info(f"qna_text list:{type(qna_text[0])}")

        # logger.info(f"output_word_count:{len(output.split(''))}")
        return qna_text
    
    except Exception as e:
        logger.error(f"Error while creating quesion and answer in collection: {str(e)}")
        return str(e)

import uuid

async def store_response_in_collection(element_id, category, number_of_question, query, corpus,output,output_token ,query_tokens, sender_id=""):
    logger.info("Inside store_response_in_collection")
    db = get_database()
    client = db.connect()
    collection = client.get_or_create_collection(name=phi_response_collection)
    documents=[corpus]

    current_datetime = datetime.datetime.now()
    logger.info("current_datetime: %s" % current_datetime)
    timestamp = int(current_datetime.timestamp())   #Convert to Unix timestamp for efficient storage
    logger.info("timestamp: %s" % timestamp) 
    
    #datetime.datetime.strptime(...): This is a method that parses a string representation of a date and time into a datetime object.
    # date_time: This variable is expected to be a string that represents a date and time in a specific format.

    #datetime.datetime.strftime(...) used to convert datetime objects to string

    metadatas=[{
        "context":output,
        "category": category,
        "number_of_question": number_of_question,
        "query": query ,
        "query_tokens": query_tokens,
        "sender_id": sender_id,
        "output_token": output_token,
        "created_at":str(current_datetime),
        "timestamp":timestamp 
    }]

    ids=[str(uuid.uuid4())]
    insert_data={
                "documents": documents,
                "metadatas":metadatas,
                "ids":ids
            }
    
    insert_result=db.insert(phi_response_collection, insert_data)
    logger.info(f"Insert response of query: %s" %insert_result)
    return insert_result

   
async def get_phi3_response_stream(element_id, category, number_of_question, query, corpus, sim_links="cbi", language=""):
    try:
        # logger.info(f"corpus:{corpus}")
        final_corpus=corpus +' For more information, you can refer to the following links: ' + ' '.join(sim_links)
        logger.info(f"final_corpus:{final_corpus}")
        logger.info(f"type_of_corpus:{type(corpus)}")
        tokens=len(corpus.split(' '))
        logger.info(f"Tokens in the corpus: {tokens}")
        
        if tokens>int(max_input_lenght):
            logger.info(f"Corpus selected has tokens greater than 4096 , therefore only considering starting 4096 words.")
            corpus = corpus.split(' ')
            final_corpus =' '.join(corpus[:int(max_input_lenght)])
            final_corpus=final_corpus+' For more information, you can refer to the following links: ' + ' '.join(sim_links)
            # logger.info(f"Updated corpus: {corpus}")
            # logger.info(f"len of final corpus {(final_corpus)}")
            # logger.info(f"len of final corpus {len(final_corpus)}")
        
        if category=='query':
            start_time = time.time()
            # rephrase_query= query+ "for central bank of India"
            rephrase_query= query

            
            async for token in answer_the_question_stream(final_corpus, rephrase_query, language):
                yield token
            
        # yield {"status":1, "message": "success", "result": complete_token, "time_taken": time.time() - start_time}
    except Exception as e:
        yield {"status":0, "message": "error", "result":str(e)}
    
async def get_phi3_response(element_id, category, number_of_question, query, corpus, query_tokens=-1, sim_links="NA",  sender_id="", language=""):
    try:
        logger.info(f"get_phi3_response executing: {language}")
        final_corpus=corpus
        logger.info(f"type_of_corpus:{type(corpus)}")
        tokens=len(corpus.split(' '))
        logger.info(f"Tokens in the corpus: {tokens}")

        if sender_id=="":
            sender_id=str(uuid.uuid4())

        if tokens>int(max_input_lenght):
            logger.info(f"Corpus selected has tokens greater than 4096 , therefore only considering starting 4096 words.")
            corpus = corpus.split(' ')
            final_corpus =' '.join(corpus[:int(max_input_lenght)])
            # logger.info(f"Updated corpus: {corpus}")
            # logger.info(f"len of final corpus {(final_corpus)}")
            # logger.info(f"len of final corpus {len(final_corpus)}")
        
        start_time = time.time()

        if category=='query':
            # rephrase_query= query+ "for central bank of India"
            rephrase_query= query
            output = await answer_the_question(final_corpus, rephrase_query,language=language)
            logger.info("sim_links: %s", sim_links)
            generated_response_url = output + ' For more information, you can refer to the following links: ' + ' '.join(sim_links)

            if "Unable to understand" in output:     
                return {"status":0, "message": "Insufficient Data", "generated_response":general_response}
            
        elif category=='summary':
            generated_response_url="NA"
            output = await create_summary(final_corpus, query,language=language)
        
        elif category=="qna":
            logger.info("Generating qna")
            generated_response_url="NA"
            output = await create_question_and_answer(final_corpus, query,number_of_question,language=language)
        
        else:
            return {"status":0, "message": "Invalid Category", "result": "Invalid Category"}
        
        end_time = time.time()
        processing_time = process_tat(start_time, end_time)
        output_token= len(output.split(' '))
        logger.info(f"output_word_count:{output_token}")
        logger.info(f"Total time taken for generating text:{processing_time}")
        insert_response= await store_response_in_collection(element_id, category, number_of_question,query, corpus, output,output_token, query_tokens, sender_id)

        return {"status":1, "message": "success", "generated_response":output, "generated_response_url":generated_response_url ,"query_token":query_tokens,"output_token": output_token,"Tat":processing_time, "sender_id":sender_id}
        
    except Exception as e:
        return {"status":0, "message": "error", "result":str(e)}


print(f"Is CUDA supported by this system? {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
cuda_id = torch.cuda.current_device()
print(f"ID of current CUDA device:{torch.cuda.current_device()}")
print(f"Name of current CUDA device:{torch.cuda.get_device_name(cuda_id)}")



import os
import json
file_path = 'qa_data.json'

list_of_dict= [{'question1': 'What is the purpose of the E-Vehicle (2W) facility for girl students?', 'answer1': 'The purpose of the E-Vehicle (2W) facility for girl students is for the purchase of a new electric vehicle for personal use only, not for hiring or ferrying passengers.'},

{'question2': 'Who is eligible for the Term Loan facility for purchasing an E-Vehicle (2W)?', 'answer2': 'Eligible borrowers are girl students above 18 years of age and up to 28 years of age, with a driving license or learners license for a 2-Wheeler at the time of loan sanction.'},

{'question3': 'What is the maximum loan amount available for the E-Vehicle (2W) purchase?', 'answer3': 'The maximum loan amount available for the E-Vehicle (2W) purchase is Rs. 2.50 Lakh.'},

{'question4': 'What is the maximum repayment period for the E-Vehicle (2W) loan?', 'answer4': 'The maximum repayment period for the E-Vehicle (2W) loan is 72 months.'},

{'question5': 'Are there any restrictions on the number of applicants for the E-Vehicle (2W) loan?', 'answer5': 'Yes, the maximum number of applicants is restricted to two (2).'},

{'question6': 'Is a guarantor required for the E-Vehicle (2W) loan?', 'answer6': 'No, a guarantor is not required for the E-Vehicle (2W) loan.'},

{'question7': 'What is the interest rate range for the E-Vehicle (2W) loan?', 'answer7': 'The interest rate range for the E-Vehicle (2W) loan is between 9.95% and 10.50%, based on the Repo Rate, Spread, and CIC score.'},

{'question8': 'Are E-vehicles exempted from registration requirements under this scheme?', 'answer8': 'No, E-vehicles are not exempted from registration requirements under this scheme.'},

{'question9': 'What is the minimum CIC score required for the E-Vehicle (2W) loan?', 'answer9': 'The minimum CIC score required for the E-Vehicle (2W) loan is 700.'},

{'question10': 'What are the processing and documentation charges for the E-Vehicle (2W) loan?', 'answer10': 'The processing charge is 0.50% of the loan amount, subject to a minimum of Rs. 500 and a maximum of Rs. 2000. There are no documentation charges.'}]

# global count
# count=0
def save_qna_in_file(qna_pairs):
    try:
        logger.info(f"qna_text:{qna_pairs}")
        logger.info("Saving qna pairs in file")
        logger.info(f" qna_pair:{type(qna_pairs)}")
        if os.path.exists(file_path):
            with open(file_path, 'r+') as file:
                data = json.load(file)
                logger.info(type(data)) 
                # data=eval(data)
                # logger.info(type(data))
                logger.info(f"data:{data}")
                data.extend(qna_pairs)
                file.seek(0)#Moves the file cursor back to the start of the file, preparing it for writing.
                json.dump(data, file, indent=4)
                # logger.info("{count} qna stored in file")
                # count+=1
                return True
        else:
            with open(file_path, 'w') as file:
                json.dump(qna_pairs, file, indent=4)
                # logger.info("{count}qna stored in file")
                # count+=1
                return True

    except Exception as e:
        logger.error(f"Error occurred while saving qna pairs in file:{str(e)}")
        return False

# async def convert_language(text,language):
#     try:
#         logger.info(f"get_hindi_text executing")
#         output = llm( 
#             # "<|user|>Please translate the following text into Hindi: You can open a saving bank account by visiting any of our branches in India and submitting the account opening form and relevant documents. Alternatively, you can send the scanned account opening form and required documents to any of our branches by email. The relevant documents include two passport size latest photographs of all account holders, copies of Passport and Residence Visa, and copies of any of the utility bills such asfixed telephone/electricity bill, gas bill, water bill, or council tax bill not older than three months. These documents may show your present residence abroad or yourpermanent address in India. All documents enclosed should be verified by an Official signature and seal/stamp. You may also consider involving your existing banker, a person known to the bank, your employer, or the Indian High Commission/Embassy/Consulate/Notary Public for the process.<|end|><|assistant|>",
#         f"<|user|>दिए गए पाठ को {text} में बदलें: {language}<|end|><|assistant|>",
#         max_tokens= int(query_max_token),  # Generate up to 256 tokens
#         # stop=["<|end|>"], 
#         echo=False,      # Do not echo the prompt in the output
#         temperature = 0,
#         top_p = 0.1
#     )
#         logger.info("Wait!! Generating response")
#         return output["choices"][0]["text"]
    
#     except Exception as e:
#         logger.error(f"Error occurred while translating english response to hindi:{str(e)}")
#         return None
    

from src.pipeline.language_conversion import translator_obj
async def convert_language(text,language):
    try:
        response=translator_obj.translate_text(text,language)
        return response
        
    
    except Exception as e:
        logger.error(f"Error occurred while translating english response to hindi:{str(e)}")
        return None
    
async def convert_language_to_english(text,language):
    try:
        response=translator_obj.translate_text_to_eng(text,language)
        return response
        
    except Exception as e:
        logger.error(f"Error occurred while translating english response to hindi:{str(e)}")
        return None
    

from src.logger import logger
from src import schema
from fastapi import APIRouter
from src.logger import logger
from src.config import application_name, application_id, website_collection
from src.data_processing.store_complete_link_content import process_store_webpage
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd


router=APIRouter(tags=["Text_Identification"])
# , current_user_uuid:dict=Depends(get_current_user)

language={"hi":"hindi", "en": "english"}
          
def text_language(text):
    from langdetect import detect_langs
    try: 
        langs = detect_langs(text) 
        for item in langs: 
            logger.info(item.lang)
            # The first one returned is usually the one that has the highest probability
            return language[item.lang]
        
    except Exception as e:
        logger.info(f"Unable to determine lang: {str(e)}")
        return 0
    

@router.post("/language/")
async def identify_language(text:str):
    result= text_language(text)
    return {"status":1,"message": "", "language":result, "item_probability":item.prob }

analyser = SentimentIntensityAnalyzer()

@router.post("/sentiment_analysis/")
def print_sentiment_scores(tweets:str):
    vadersenti = analyser.polarity_scores(tweets)
    logger.info(pd.Series([vadersenti['pos'], vadersenti['neg'], vadersenti['neu'], vadersenti['compound']]))
    if vadersenti['compound'] >= 0.5:
        return {"status":1 , "message":"", "result":"Positive"}
    elif vadersenti['compound'] > -0.5:
        return {"status":1 , "message":"", "result":"Nuetral"}
    else:
        return {"status":1 , "message":"", "result":"Negative"}
       

# text = 'This goes beyond party lines.  Separating families betrays our values as Texans, Americans and fellow human beings'

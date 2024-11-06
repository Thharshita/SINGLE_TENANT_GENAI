# from transformers import MBartForConditionalGeneration, MBart50TokenizerFast
# from src.logger import logger
# model = MBartForConditionalGeneration.from_pretrained("facebook/mbart-large-50-one-to-many-mmt")
# # import tokenizer


# class Translator():

#     def translate_text(self, text,language):
#         tokenizer = MBart50TokenizerFast.from_pretrained("facebook/mbart-large-50-one-to-many-mmt", src_lang="en_XX")
#         models_input= tokenizer([text],return_tensors="pt", padding=True, truncation=True)
#         generated_tokens=  model.generate(
#         **models_input,
#         forced_bos_token_id=tokenizer.lang_code_to_id["hi_IN"]
#         )
#         translation = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
#         logger.info(translation)

#         return 
    
#     def translate_text_to_eng(self, text,language):
#         tokenizer = MBart50TokenizerFast.from_pretrained("facebook/mbart-large-50-one-to-many-mmt", src_lang="hi_IN")
#         models_input= tokenizer([text],return_tensors="pt", padding=True, truncation=True)
#         generated_tokens=  model.generate(
#         **models_input,
#         forced_bos_token_id=tokenizer.lang_code_to_id["en_XX"]
#         )
#         translation = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
#         logger.info(translation)

#         return translation
# translator_obj=Translator()




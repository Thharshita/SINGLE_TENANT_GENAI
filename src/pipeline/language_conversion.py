import argostranslate.package
import argostranslate.translate

# from_code = "en"
# to_code = "hi"

# argostranslate.package.update_package_index()
# available_packages = argostranslate.package.get_available_packages()

# package_to_install = next(
#     filter(
#         lambda x: x.from_code == from_code and x.to_code == to_code, available_packages
#     )
# )

# argostranslate.package.install_from_path(package_to_install.download())


# from_code = "hi"
# to_code = "en"

# package_to_install = next(
#     filter(
#         lambda x: x.from_code == from_code and x.to_code == to_code, available_packages
#     )
# )

# argostranslate.package.install_from_path(package_to_install.download())

from src.logger import logger

class Translator():

    def translate_text(self, text,language):
        from_code="en"
        to_code="hi"
        translatedText = argostranslate.translate.translate(text, from_code, to_code)
        logger.info(translatedText)
        return translatedText
    
    def translate_text_to_eng(self, text,language):
            from_code="hi"
            to_code="en"
            translatedText = argostranslate.translate.translate(text, from_code, to_code)
            logger.info(translatedText)
            logger.info(type(translatedText))
            return translatedText
    
    
translator_obj=Translator()



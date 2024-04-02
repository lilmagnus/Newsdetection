# main.py
from news_detector import NewsDetector
from text_analysis import TextAnalysis
from cache_manager import CacheManager
from interaction_handler2 import InteractionHandler
from api_client import APIClient
import time
import os
import json

def main():
    # Initialize the NewsDetector - assuming it might process a PDF to get text
    news_detector = NewsDetector()
    cache_manager = news_detector.cache_manager
    api_client = APIClient()

    prompts = '../prompts/prompts4.json'

    general_interaction = InteractionHandler(prompts)
    newsworth_counter = ""
    # Example PDF file path - replace with your actual file path
    folder = ['0news', '1news']
    nummer = 0
    # Process document to extract text
    while nummer < 2:
        for j in folder:
            instructions_calculation = f"""The proper way of answering this is: "{j} - NOT NEWSWORTHY" OR "{j} - NEWSWORTHY". 
                    Some of the texts youre given might not be clear immediately, some might look similar to this:
                    A text that is not newsworthy would write 'IKKE RELEVANT' at the end.
                    Newsworthy texts will give an explanation as to why it could be newsworthy."""
            #for filename in os.listdir(folder_path):
            for filename in os.listdir(j):
                print("="*20, filename.upper(), "="*20)
                check_cache = cache_manager.get_cached_response(j+"/"+filename)
                print(check_cache) # Printer original tekst før behandling
                time.sleep(2)
                if check_cache is not None:
                    cache_categorize = general_interaction.handle_interaction(check_cache)
                    try:
                        print(cache_categorize[1], '\nhalloien')
                    except IndexError:
                        print(cache_categorize, '\nheihei') 
                    # FIKS RESTEN UNDER SÅ PIPELINEN KAN BEGYNNE Å KJØRE OG TESTE
                    #time.sleep(2)
                    #count_assessment = api_client.make_api_request([{"role": "user", "content": f""}])
                    newsworth_counter += j+str(cache_categorize)
                    time.sleep(2)
            nummer += 1

    #extracted_text = news_detector.process_document(folder)
    #print(f"Extracted Text: {extracted_text}")
    print(newsworth_counter)
    calculate_assessments = api_client.make_api_request([{"role": "user", "content": f"Calculate the accuracy of the given list. The text after '0news' should indicate no newsvalue, and the text after '1news' should indicate newsvalue. {newsworth_counter}. Also make a confusion matrix, where True positives are '1news' assessed as newsworthy, True negatives are '0news' assessed as not newsworthy, and so on."}])
    print(calculate_assessments)

    # Initialize TextAnalysis for further analysis on the extracted text
    #text_analyzer = TextAnalysis()
    #analysis_result = text_analyzer.analyze_text(extracted_text)
    #print(f"Analysis Result: {analysis_result}")

if __name__ == "__main__":
    main()
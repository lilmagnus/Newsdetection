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

    prompts = '../prompts/prompts3.json'

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
                    "Based on the categories provided, the summary of the construction permit documents for the hotel project in Tromsø would likely be considered newsworthy due to its classification as a large project, public safety concerns, potential question of legality, and impact on locals." 
                    The above example is newsworthy, as it states: "would likely be considered newsworthy" """
            #for filename in os.listdir(folder_path):
            for filename in os.listdir(j):
                print("="*20, filename.upper(), "="*20)
                check_cache = cache_manager.get_cached_response(j+"/"+filename)
                print(check_cache) # Printer original tekst før behandling
                time.sleep(2)
                if check_cache is not None:
                    cache_categorize = general_interaction.handle_interaction(check_cache)
                    print(cache_categorize, '\nheihei') 
                    # FIKS RESTEN UNDER SÅ PIPELINEN KAN BEGYNNE Å KJØRE OG TESTE
                    #time.sleep(2)
                    count_assessment = api_client.make_api_request([{"role": "system", "content": f"{instructions_calculation}"},
                                                                    {"role": "user", "content": f"Was this assessed as newsworthy or not newsworthy? {cache_categorize}. Count 'potentially newsworthy' as NEWSWORTHY."}])
                    newsworth_counter += count_assessment+'\n'
                    time.sleep(2)
            nummer += 1

    #extracted_text = news_detector.process_document(folder)
    #print(f"Extracted Text: {extracted_text}")

    calculate_assessments = api_client.make_api_request([{"role": "user", "content": f"Calculate the accuracy in percentage. Where it says '0news' the correct prediction would be NOT NEWSWORTHY, where it says '1news' the correct prediction would be NEWSWORTHY. Calculate on this collection: {newsworth_counter}"}])
    print(calculate_assessments)

    # Initialize TextAnalysis for further analysis on the extracted text
    #text_analyzer = TextAnalysis()
    #analysis_result = text_analyzer.analyze_text(extracted_text)
    #print(f"Analysis Result: {analysis_result}")

if __name__ == "__main__":
    main()
# main.py
from news_detector import NewsDetector
from text_analysis import TextAnalysis
from cache_manager import CacheManager
from interaction_handler2 import InteractionHandler
from api_client import APIClient
from document_processing import DocumentProcessing
import time
import os
import json

def main():
    # Initialize the NewsDetector - assuming it might process a PDF to get text
    news_detector = NewsDetector()
    cache_manager = news_detector.cache_manager
    api_client = APIClient()
    document_processing = DocumentProcessing()

    prompts = '../prompts/prompts9.json'
    vurdering_fewshot = """DET SKAL KUN SVARES MED 'NYHETSVERDIG' ELLER 'IKKE NYHETSVERDIG', SOM EKSEMPLENE UNDER VISER.
    Prompt: Hva er denne teksten vurdert som? Basert på gjennomgangen av dokumentet og analysen av nyhetsverdien, er konklusjonen at dette ikke er nyhetsverdig.
    Response: Ikke nyhetsverdig
    
    Prompt: Hva er denne teksten vurdert som? Basert på gjennomgangen av dokumentet og de identifiserte kategoriene, sammen med den opprinnelige oppsummeringen og svarene på de generelle spørsmålene, ser det ut til at dette dokumentet om etableringen av en ny lasterampe i Tromsø med bygging av tekniske installasjoner og et industribygg, godkjent av Arbeidstilsynet for OLAV AAKRE AS med 30 ansatte, er faktisk nyhetsverdig. Det er relevant for lokalmedia som iTromsø da det har innvirkning på nærområdet og potensielt andre samfunnsmedlemmer i Tromsø. Dette vil være av interesse for lokalbefolkningen, og derfor kan det være verdt tiden for en journalist å skrive en nyhetssak om denne byggesaken. 
    Response: Nyhetsverdig
    
    Prompt: Hva er denne teksten vurdert som? Basert på den kritiske gjennomgangen, konkluderer jeg med at dokumentet ikke har nyhetsverdi for lokalavisen iTromsø. Det omhandler en vanlig søknadsprosess for deling av eiendom for boligformål i Tromsø, uten noen overraskelser eller bekymringer for offentlig sikkerhet. Det er heller ingen indikasjon på at dokumentet gjelder et annet sted enn i Tromsø. Derfor bør ikke journalistene bruke tid på å skrive en nyhetssak om dette. 
    Response: Ikke nyhetsverdig
    
    Prompt: Hva er denne teksten vurdert som? Basert på den nye vurderingen, har dokumentet nyhetsverdi med tanke på lokalpåvirkning, samfunnsengasjement og forbedring av trafikksikkerhet i Tromsø. Det viser samarbeid mellom ulike instanser og berører en bredere del av samfunnet. Derfor vil det være passende for en journalist å undersøke saken nærmere og potensielt skrive en nyhetssak om etableringen av gangfeltet på Fylkesveg 862 i Tromsø. 
    Response: Nyhetsverdig
    
    Prompt:
    Dette dokumentet om oppføring av en industribygning med tekniske installasjoner i Tromsø, godkjent av Arbeidstilsynet for OLAV AAKRE AS, involverer 30 ansatte og vil påvirke lokalsamfunnet. Med en oppsummeringslengde på 412 ord og relevante temaer som identifiseres, bør en journalist i iTromsø se videre på saken.
    Basert på den kritiske gjennomgangen av vurderingen kan det være at dokumentet ikke har tilstrekkelig nyhetsverdi for å rettferdiggjøre skrivingen av en nyhetssak. Selv om det omhandler oppføringen av en industribygning med tekniske installasjoner i Tromsø, godkjent av Arbeidstilsynet for OLAV AAKRE AS med involvering av 30 ansatte, kan det hende at saken ikke har den nødvendige nyhetsverdien for å være av interesse for iTromsø. 

    Selv om prosjektet kan ha en visse innvirkning på lokalsamfunnet, kan det hende at det ikke er av tilstrekkelig interesse for leserne til å rettferdiggjøre en nyhetsartikkel. Det er viktig å vurdere om saken er av tilstrekkelig interesse for målgruppen til iTromsø før man investerer tid og ressurser i å lage en nyhetssak. Det kan også være lurt å se på andre relevante nyhetssaker som har høyere nyhetsverdi før man prioriterer denne spesifikke saken. 
    Response: Ikke Nyhetsverdig
    
    Prompt: Denne informasjonen bør ikke anses som nyhetsverdig da den omhandler en vanlig prosess med deling av eiendom for boligformål i Tromsø. Det er ingen indikasjoner på avvik, uventede elementer eller bekymringer for offentlig sikkerhet. Dokumentet fokuserer hovedsakelig på administrative trinn og godkjenning av søknader. 
    Response: Ikke nyhetsverdig
    """
    general_interaction = InteractionHandler(prompts)
    newsworth_counter = []
    # Example PDF file path - replace with your actual file path
    #folder = ['0news', '1news', '2news']
    folder = ['0news', '1news', '2news']
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
                print(check_cache,'\n') # Printer original tekst før behandling
                time.sleep(2)
                if check_cache is not None:
                    cache_categorize = general_interaction.handle_interaction(check_cache)
                    try:
                        print(cache_categorize, '\nhalloien')
                    except IndexError:
                        print(cache_categorize, '\nheihei')
                    last_assessment = cache_categorize.splitlines()[1]
                    count_assessment = api_client.make_api_request([{"role": "system", "content": f"{vurdering_fewshot}"},
                                                                    {"role": "user", "content": f"Hva er denne teksten vurdert som? {last_assessment}"}])
                    newsworth_counter.append(str(j + ' - ' + count_assessment))
                    print(newsworth_counter)
                    time.sleep(2)
                else:
                    process_document = document_processing.summarise_individual_documents(j+"/"+filename)
                    fresh_categorized = general_interaction.handle_interaction(process_document)
                    try:
                        print(fresh_categorized, '\nhalloien')
                    except IndexError:
                        print(fresh_categorized, '\nheihei')
                    
                    last_assessment = fresh_categorized.splitlines()[2]
                    count_assessment = api_client.make_api_request([{"role": "system", "content": f"{vurdering_fewshot}"},
                                                                    {"role": "user", "content": f"Hva er denne teksten vurdert som? {last_assessment}"}])
                    newsworth_counter.append(str(j+' - '+count_assessment))
                    print(newsworth_counter)
                    time.sleep(2)
            nummer += 1

    #extracted_text = news_detector.process_document(folder)
    #print(f"Extracted Text: {extracted_text}")
    #print(newsworth_counter)
    #calculate_assessments = api_client.make_api_request([{"role": "system", "content": f"You will be given a collection of asessments. Each assessment starts with the folder the document belongs to, followed by the document-name, followed by the assessment. FOR EXAMPLE: '1news: musegaten - Basert på ......'. When it starts with '1news', the assessment should indicate newsworth, and if it starts with '0news', the assessment should indicate little or no newsworth. Read through the assessments, and score them as correct if they conclude with what I wrote, or incorrect if it is inconclusive or the opposite of what i wrote."},
    #                                                     {"role": "user", "content": f"Calculate the accuracy of the given 24 assessments. {newsworth_counter}. Also make a confusion matrix, where True positives are '1news' assessed as newsworthy, True negatives are '0news' assessed as not newsworthy, and so on."}])
    #print(calculate_assessments)
    count_correct = 0
    count_incorrect = 0
    for j in newsworth_counter:
        if j == '0news - Ikke nyhetsverdig':
            count_correct += 1
        elif j == '0news - Nyhetsverdig':
            count_incorrect += 1
        elif j == '1news - Nyhetsverdig':
            count_correct += 1
        elif j == '1news - Ikke Nyhetsverdig':
            count_incorrect += 1
        elif j == '2news - Ikke nyhetsverdig':
            count_correct += 1
        elif j == '2news - Nyhetsverdig':
            count_incorrect += 1
        else:
            count_incorrect += 1
    total_count = count_incorrect + count_correct
    print('Riktige vurderte:', count_correct, 'Feilvurderte:', count_incorrect, '\n', 'ACCURACY SCORE = ', (count_correct/total_count)*100, '%')
            
    vurdering_telling_fewshot = """EKESMPLER PÅ HVORDAN MAN TELLER VURDERINGENE:
    Prompt: Regn ut accuracy i prosent på denne listen med vurderinger og tilhørende mappe. Alle vurderinger tilhørende 0news må være vurdert som 'Ikke nyhetsverdig' for å være riktig, alle vurderinger tilhørende 1news må være 'Nyhetsverdig' for å være riktig, og alle vurderinger tilhørende 2news må være 'Ikke nyhetsverdige' for å være riktige. Dette er lista: [0news - Ikke nyhetsverdig, 0news - Ikke nyhetsverdig, 0news - Nyhetsverdig, 1news - Nyhetsverdig, 1news - Nyhetsverdig, 1news - Ikke nyhetsverdig, 1news - Nyhetsverdig, 2news - Ikke nyhetsverdig, 2news - Nyhetsverdig, 2news - Ikke nyhetsverdig]
    Response: I listen er det 10 vurderinger totalt. 0news: 2 av 3 riktige. 1news: 3 av 4 riktige. 2news: 1 av 2 riktige. Totalt er 2+3+1 = 6 riktige, altså 6/10, eller 60%.
    
    Prompt: Regn ut accuracy i prosent på denne listen med vurderinger og tilhørende mappe. Alle vurderinger tilhørende 0news må være vurdert som 'Ikke nyhetsverdig' for å være riktig, alle vurderinger tilhørende 1news må være 'Nyhetsverdig' for å være riktig, og alle vurderinger tilhørende 2news må være 'Ikke nyhetsverdige' for å være riktige. Dette er lista: [0news - Ikke nyhetsverdig, 0news - Ikke nyhetsverdig, 0news - Nyhetsverdig, 0news - Ikke nyhetsverdig, 0news - Ikke nyhetsverdig, 1news - Nyhetsverdig, 1news - Nyhetsverdig, 1news - Ikke nyhetsverdig, 1news - Nyhetsverdig, 1news - Nyhetsverdig, 1news - Ikke nyhetsverdig, 1news - Nyhetsverdig, 2news - Ikke nyhetsverdig, 2news - Nyhetsverdig, 2news - Ikke nyhetsverdig, 2news - Ikke nyhetsverdig, 2news - Nyhetsverdig, 2news - Ikke nyhetsverdig]
    Response: I listen er det 18 vurderinger totalt. 0news: 4 av 5 riktige. 1news: 5 av 7 riktige. 2news: 4 av 6 riktige. Totalt er 4+5+4 = 13 riktige, altså 13/18, eller 72.222%.
    """
    #request_vurdering = api_client.make_api_request([{"role": "system", "content": f"{vurdering_telling_fewshot}"},
    #                                                 {"role": "user", "content": f"Det skal være 30 vurderinger i listen. 9 tilhørende 0news, 15 tilhørende 1news, og 6 tilhørende 2news. Regn ut accuracy i prosent på denne listen med vurderinger og tilhørende mappe. Alle vurderinger tilhørende 0news må være vurdert som 'Ikke nyhetsverdig' for å være riktig, alle vurderinger tilhørende 1news må være 'Nyhetsverdig' for å være riktig, og alle vurderinger tilhørende 2news må være 'Ikke nyhetsverdige' for å være riktige. Dette er lista: {newsworth_counter}"}])
    #print("Accuracy score:\n", request_vurdering)
    
    # Initialize TextAnalysis for further analysis on the extracted text
    #text_analyzer = TextAnalysis()
    #analysis_result = text_analyzer.analyze_text(extracted_text)
    #print(f"Analysis Result: {analysis_result}")

if __name__ == "__main__":
    main()
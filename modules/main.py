# main.py
from cache_manager import CacheManager
from interaction_handler2 import InteractionHandler
from api_client import APIClient
from document_processing import DocumentProcessing
import time
import os
import numpy as np
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    cache_manager = CacheManager()
    api_client = APIClient()
    document_processing = DocumentProcessing()

    prompts = '../prompts/prompts10.json'
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
    
    Prompt: Den gitte teksten basert på utviklingen av boliger og næringslokaler langs Stakkevollvegen og Rektor Horst gate i Tromsø er relevant og nyhetsverdig for lokalavisa iTromsø. Den inneholder informasjon om et stort prosjekt med flere bygninger, fokus på utemiljø, støyhensyn og boligkvalitet, som er av interesse for lokalsamfunnet. 
    Response: Nyhetsverdig
    """
    general_interaction = InteractionHandler(prompts)
    newsworth_counter = []
    accuracy_list = []
    total_acc_list = []

    folder = ['0news', '1news', '2news']
    #folder = ['3news', '4news']
    nummer = 0
    
    while nummer < 3: # Endre nummer for flere/færre gjennomganger per kjøring
        for j in folder:
            instructions_calculation = f"""The proper way of answering this is: "{j} - NOT NEWSWORTHY" OR "{j} - NEWSWORTHY". 
                    Some of the texts youre given might not be clear immediately, some might look similar to this:
                    A text that is not newsworthy would write 'IKKE RELEVANT' at the end.
                    Newsworthy texts will give an explanation as to why it could be newsworthy."""
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
                    last_assessment = cache_categorize
                    count_assessment = api_client.make_api_request([{"role": "system", "content": f"{vurdering_fewshot}"},
                                                                    {"role": "user", "content": f"Hva er denne teksten vurdert som? Se på vurderingen på siste linje. {last_assessment}"}])
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
                    
                    last_assessment = fresh_categorized
                    count_assessment = api_client.make_api_request([{"role": "system", "content": f"{vurdering_fewshot}"},
                                                                    {"role": "user", "content": f"Hva er denne teksten vurdert som? {last_assessment}"}])
                    newsworth_counter.append(str(j+' - '+count_assessment))
                    print(newsworth_counter)
                    time.sleep(2)

        '''
        count_correct = 0
        count_incorrect = 0
        # 3news og 4news
        for j in newsworth_counter:
            if j == '3news - Ikke nyhetsverdig':
                count_correct += 1
            elif j == '3news - Nyhetsverdig':
                count_incorrect += 1
            elif j == '4news - Ikke nyhetsverdig':
                count_incorrect += 1
            elif j == '4news - Nyhetsverdig':
                count_correct += 1
            else:
                count_incorrect += 1
        '''
        count_correct = 0
        count_incorrect = 0
        # 0news, 1news og 2news
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
        total_percent = str((count_correct/total_count)*100) + ' %'
        
        print('Riktige vurderte:', count_correct, 'Feilvurderte:', count_incorrect, '\n', 'ACCURACY SCORE = ', total_percent)
        nummer += 1
        total_acc_list.extend(newsworth_counter)
        newsworth_counter.clear()
        accuracy_list.append(str(nummer) + ' - ' + total_percent)
        
    print(accuracy_list)
    '''
    count_c1 = 0
    count_ic1 = 0
    # 3news og 4news
    for i in total_acc_list:
            if i == '3news - Ikke nyhetsverdig':
                count_c1 += 1
            elif i == '3news - Nyhetsverdig':
                count_ic1 += 1
            elif i == '4news - Ikke nyhetsverdig':
                count_ic1 += 1
            elif i == '4news - Nyhetsverdig':
                count_c1 += 1
            else:
                count_ic1 += 1
    '''
    count_c1 = 0
    count_ic1 = 0
    # 0news, 1news og 2news
    for i in total_acc_list:
            if i == '0news - Ikke nyhetsverdig':
                count_c1 += 1
            elif i == '0news - Nyhetsverdig':
                count_ic1 += 1
            elif i == '1news - Nyhetsverdig':
                count_c1 += 1
            elif i == '1news - Ikke Nyhetsverdig':
                count_ic1 += 1
            elif i == '2news - Ikke nyhetsverdig':
                count_c1 += 1
            elif i == '2news - Nyhetsverdig':
                count_ic1 += 1
            else:
                count_ic1 += 1
    
    last_total_count = count_c1 + count_ic1
    print('TOTALE VURDERINGER: ', len(total_acc_list), '\nTOTALT ANTALL RIKTIGE VURDERTE: ', count_c1, '\nTOTALT ANTALL FEILVURDERTE: ', count_ic1, '\nTOTAL ACCURACY: ', (count_c1/last_total_count)*100, '%')

    # Konverter de tekstuelle beskrivelsene til numeriske klasser
    y_true = []
    y_pred = []

    for entry in total_acc_list:
        parts = entry.split(' - ')
        if parts[0] in ['0news', '2news']:
        #if parts[0] in '3news':
            if parts[1] == 'Ikke nyhetsverdig':
                y_true.append(0)  # True label: Ikke nyhetsverdig
                y_pred.append(0)  # Predicted label: Ikke nyhetsverdig (TN)
            else:
                y_true.append(0)  # True label: Ikke nyhetsverdig
                y_pred.append(1)  # Predicted label: Nyhetsverdig (FP)
        elif parts[0] == '1news':
        #elif parts[0] == '4news':
            if parts[1] == 'Ikke nyhetsverdig':
                y_true.append(1)  # True label: Nyhetsverdig
                y_pred.append(0)  # Predicted label: Ikke nyhetsverdig (FN)
            else:
                y_true.append(1)  # True label: Nyhetsverdig
                y_pred.append(1)  # Predicted label: Nyhetsverdig (TP)

    # Opprett forvirringsmatrisen
    cm = confusion_matrix(y_true, y_pred)

    # Plot forvirringsmatrisen med matplotlib og seaborn
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Ikke nyhetsverdig', 'Nyhetsverdig'], yticklabels=['Ikke nyhetsverdig', 'Nyhetsverdig'])
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Confusion Matrix')
    plt.show() 

if __name__ == "__main__":
    main()
    
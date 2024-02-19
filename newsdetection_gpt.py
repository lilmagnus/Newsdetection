import os
import openai
import time
import requests
import fitz
import hashlib
import json
import random
from spacy.lang.nb.stop_words import STOP_WORDS

HASH_ALGORITHM = 'sha256'
CACHE_FOLDER = 'gpt_cache/'
MODEL = "gpt-3.5-turbo-0125"
BASE_DELAY = 3
LAMBDA = 0.5

class CacheManager:
    def __init__(self, hash_algorithm='sha256', cache_folder='gpt_cache/'):
        self._hash_object = hashlib.new(hash_algorithm)
        self.cache_folder = cache_folder
        if not os.path.exists(cache_folder):
            os.makedirs(cache_folder)

    def get_hash(self, messages):
        hash_object = self._hash_object.copy()
        hash_object.update(json.dumps(messages).encode('utf-8'))
        hash_ = hash_object.hexdigest()
        return hash_

    def get_cached_response(self, messages):
        hash_ = self.get_hash(messages)
        cache_filename = f'{self.cache_folder}/{hash_}.json'
        if os.path.exists(cache_filename):
            print('Reused cached response')
            with open(cache_filename, 'r') as file:
                response = json.load(file)
            return response
        else:
            return None

    def cache_response(self, messages, response):
        hash_ = self.get_hash(messages)
        cache_filename = f'{self.cache_folder}/{hash_}.json'
        with open(cache_filename, 'w') as file:
            json.dump(response, file, indent=4)


class NewsDetector:
    # DELVIS NYTT /// EGEN KLASSE ??
    def __init__(self, api_key, lambda_=LAMBDA, model=MODEL, base_delay=BASE_DELAY):
        self.api_key = api_key
        self.model=model
        self.base_delay=base_delay
        self.lambda_=lambda_
        self._handicap=1
        self.cache_manager = CacheManager()
        openai.api_key = self.api_key
    
    def estimate_token_count(self, text):
        return len(text.split())

    def make_api_request(self, messages, max_response_length=1000):
        retry_count = 0
        max_retries = 5
        backoff_time = 60
        max_tokens = min(max_response_length, 4096)

        while retry_count < max_retries:
            response = self.get_cached_response(messages)
            if response is not None:
                return response # ?????
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo-0125", 
                    #model="ft:gpt-3.5-turbo-1106:personal::8YJrlE2V",
                    #model="gpt-4",
                    #model="gpt-4-1106-preview",
                    #model="gpt-4-vision-preview", # Kan se bilder, kan være nyttig om man bruker PDF fil istedet for tekstfil
                    messages=messages,
                    max_tokens=max_tokens
                )
                return response['choices'][0]['message']['content']
            except openai.error.RateLimitError:
                print("Rate limit exceeded. Waiting", backoff_time, "seconds before retrying...")
                time.sleep(backoff_time)
                retry_count += 1
                backoff_time *= 2
                print("Retrying...")
                #return self.make_api_request(messages, max_tokens)
            except requests.exceptions.RequestException as e:
                print("API request error:", e)
                return None
        
        print("Maximum retries reached. Exiting..")
        return None

    def extract_text_from_pdf(self, pdf_file_path):
        if not pdf_file_path.lower().endswith('.pdf'):
            print(f"Not a PDF file: {pdf_file_path}")
            return None

        text = ''
        with fitz.open(pdf_file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text

    def save_text_to_file(self, text, output_file_path):
        try:
            with open(output_file_path, 'w', encoding='utf-8') as file:
                file.write(text)
        except IOError as e:
            print(f"File write error: {e}")
 
    def summarise_individual_documents(self, folder_path):
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(".pdf"):
                pdf_file_path = os.path.join(folder_path, filename)
                text = self.extract_text_from_pdf(pdf_file_path)
                if text:
                    output_file_path = os.path.splitext(pdf_file_path)[0] + '_output.txt'
                    self.save_text_to_file(text, output_file_path)

        all_summaries = ""
        sum_count = 1
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(".txt"):
                file_path = os.path.join(folder_path, filename)
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()

                print(sum_count, f"Summarizing: {filename}")
                summary = self.summarise_text(text)
                #all_summaries += f"\nDocument: {filename}\n{summary}" # Kanskje se om denne kan køddes med
                all_summaries += summary
                sum_count += 1
        #summ_summ = self.make_api_request([{"role": "user", "content": f"Reduce the length of this summary: {all_summaries}"}])
        print("="*20, "FINISHED", "="*20)
        #print(len(all_summaries))
        # Legg inn kall til categorize metode her, 
        # for å få med vurdering om hvilke kategorier det er snakk om
        if len(all_summaries) > 20000:
            chunked_summaries = self.chunk_summary(all_summaries)
            return self.categorize(chunked_summaries)
        else:
            return self.categorize(all_summaries)

    def chunk_summary(self, text):
        summary = ""
        max_chunk_size = 1500  # Max tokens per chunk -- MÅ VÆRE 2000(?)
        chunk_count = 1
        while text:
            print("Parsing chunk", chunk_count)
            token_count = self.estimate_token_count(text)
            if token_count <= max_chunk_size:
                chunk = text
                text = ""  # Clear the text as we're processing it all in this chunk
            else:
                # Find the largest possible substring within token limit
                chunk = text[:max_chunk_size]
                cut_off_index = chunk.rfind('.') + 1  # Try to cut off at the last full sentence
                if cut_off_index == 0:
                    cut_off_index = text.rfind(' ', 0, max_chunk_size)  # If no period, cut off at the last space

                chunk = text[:cut_off_index].strip()
                text = text[cut_off_index:].strip()  # Remaining text for next iteration
            criterias = """NEIGHBOR DISPUTE,
            PUBLIC SAFETY CONCERNS,
            QUESTION OF LEGALITY,
            LARGE PROJECT; (hotel, apartments, covering a large area, industrial),
            CHANGES IMPACTING LOCALS; (address changes, especially if it involves multiple addresses, decisions being made and later un-made)
            """
            #response = self.make_api_request([{"role": "user", "content": f"Are these summaries of construction permit documents talking about any of these subjects: {criterias}? Parse through the summaries and give a new summary, this time highlight the general subjects and include context : {chunk}"}], max_chunk_size)

            response = self.make_api_request([{"role": "user", "content": f"Reduce the length of the text by removing text that gives no supporting context and text that has already been written, or text repeating or paraphrasing already written text. Also look out for these criteria, if one is mentioned or implied, it would indicate newsworth: {criterias}. Analyze and reduce text in this summary, keep it below 1500 words in total: {chunk}"}])
            #response = self.make_api_request([{"role": "user", "content": f"Reduce the length of the text by removing text that gives no supporting context and text that has already been written, or text repeating or paraphrasing already written text. Analyze and reduce text in this summary, keep it below 1500 words in total: {chunk}"}])
            if response:
                summary += response + "\n\n"
                chunk_count += 1
            else:
                break  # Exit the loop if there's no response
        
        return summary.strip()

    def summarise_text(self, text):
        summary = ""
        max_chunk_size = 2000  # Max tokens per chunk -- MÅ VÆRE 2000(?)
        chunk_count = 1
        while text:
            print("Summarizing chunk:", chunk_count)
            token_count = self.estimate_token_count(text)
            if token_count <= max_chunk_size:
                chunk = text
                text = ""  # Clear the text as we're processing it all in this chunk
            else:
                # Find the largest possible substring within token limit
                chunk = text[:max_chunk_size]
                cut_off_index = chunk.rfind('.') + 1  # Try to cut off at the last full sentence
                if cut_off_index == 0:
                    cut_off_index = text.rfind(' ', 0, max_chunk_size)  # If no period, cut off at the last space

                chunk = text[:cut_off_index].strip()
                text = text[cut_off_index:].strip()  # Remaining text for next iteration

            response = self.make_api_request([{"role": "user", "content": f"Summarize this in 3 sentences or less, mention the date of the document if it is mentioned: {chunk}"}], max_chunk_size)

            if response:
                summary += response + "\n\n"
                chunk_count += 1
            else:
                break  # Exit the loop if there's no response
        
        return summary.strip()
    
    # FIX
    def categorize(self, summaries):
        # Gå mer inn i detalj på hvert punkt hvis det vurderes som TRUE.
        # Få frem hvor omfattende det egentlig er, for å få en bedre
        # vurdering om det faktisk er dramatisk nok til å lage en nyhetssak på
        assess_list = ['PUBLIC SAFETY', 'LARGE PROJECT', 'NEIGHBOR DISPUTE', 'IMPACT ON CITIZENS']
        #assess_list = ['NEIGHBOR DISPUTE']
        assessed = "THEMES IN THE TEXT:"+'\n'
        print("-"*10, "Assessing categories...")
        for i in assess_list:
            #assessment_prompt = self.make_api_request([{"role": "user", "content": f"Check for: {i}, {fewshot_train}"}])
            assessment_prompt = self.make_api_request([{"role": "user", "content": f"Check if the summary given is about: {i}, return a simple '{i} - (TRUE or FALSE, depending on your assessment)': {summaries}"}])
            print(assessment_prompt)
            assessed += assessment_prompt + '\n'
        print("-"*10, "Assessment complete!", "-"*10)
        assessed_summaries = assessed + summaries
        return self.detailed_categories(assessed_summaries)

    def detailed_categories(self, summaries):
        detail_assessed = "DETAILS SURROUNDING SUBJECTS:"+'\n'
        detail_digging = self.make_api_request([{"role": "user", "content": f"If any categories are assessed to be TRUE, give an explanation as to why they are TRUE. If no categories are TRUE, don't change the summary. {summaries}"}])
        detail_assessed += detail_digging
        self.cache_response(summaries, detail_digging)
        return detail_assessed

    def assess_newsworthiness(self, summaries):
        max_chunk_size = 10000
        
        # Kanskje unødvendig
        newsworthiness_criteria = """NEIGHBOR DISPUTE,
            PUBLIC SAFETY CONCERNS,
            QUESTION OF LEGALITY,
            LARGE PROJECT; (hotel, apartments, covering a large area, industrial),
            CHANGES IMPACTING LOCALS; (address changes, especially if it involves multiple addresses, decisions being made and later un-made)
            """ #{newsworthiness_criteria}
        #newsworthiness_criteria = "CRITERIA, MEETING ONE IS ENOUGH: Public safety, meaning there is risk of civilian safety and health surrounding the project. Larger projects, meaning construction of hotels, bigger apartment complexes (over 10 apartments), construction of industry buildings, factories, stores, pubs to name a few (Administrative documents of this nature would be of interest, and therefore considered newsworthy). Multiple complaints from neighbors, or disputes from neighboring properties, multiple neighbors submitting complaints against a project, address changes."
        # Fiks begge disse ^v, ikke bra nok definert
        # Eksemplene trenger mer strukturerte resonnement for hvorfor de er eller ikke er nyhetsverdige
        few_shots = f"""Instruction: Based on the summaries provided below and the defined criteria, determine whether the content is newsworthy.
        

        EXAMPLE 1: 
        The document is a request for a pre-conference meeting regarding a new water treatment building and elevated tank at Tromvik waterworks in Tromsø. Norconsult is recommending the construction of a new facility at a higher location due to technical reasons, and they are seeking to expedite the process for obtaining a building permit. The document also includes details about the existing waterworks and the proposed new location for the facility.

        This is a summary of the minutes of a prior conference. The conference took place on December 15, 2023, and it pertained to the Tromvik waterworks construction project. The attendees included representatives from Norconsult AS and the Tromsø municipality. The discussion covered topics related to dispensation and processing, as well as the need for prioritization due to critical water supply considerations.

        Mart Kure is sending an email to Marianne Melbye and Trond Vestjord with attachments about a pre-conference meeting for Tromvik waterworks. She asks for possible time slots for the meeting in week 50 and provides contact information for further inquiries. The email was sent on December 1, 2023.
        LABEL: NEWSWORTHY: This is newsworthy as it is a matter of public safety.

        EXAMPLE 2:
        Document: Vedtak_output.txt
        Statens vegvesen has received a request for a traffic sign decision from Troms and Finnmark County Municipality for a pedestrian crossing on county road 862 in Tromsø municipality. The decision has been approved for the establishment of the pedestrian crossing and road markings, with the responsibility for installation falling on Troms and Finnmark County Municipality. The decision will be valid once the signs are erected and uncovered, with the date and time of installation to be sent to Statens vegvesen.

        Regine Ada Aasjord Møkleby sent an email on August 16, 2022, regarding the establishment of a pedestrian crossing and road markings on fylkesveg 862. Tromsø kommune has no objections to the plan, but suggests the addition of pedestrian/waiting areas with tactile markings on both sides of the crossing. The email was sent to "Firmapost" and includes contact information for Regine Ada Aasjord Møkleby.

        On Thursday, August 25, 2022, Katrine Johannessen from Statens vegvesen replied to Regine Ada Aasjord Møkleby from Tromsø kommune regarding the establishment of a pedestrian crossing on County Road 862. Katrine addressed previous communication regarding the waiting area and tactile markings, which were not described in the original consultation. She also mentioned that the decision on the sign plan has been made. Regine had previously sent an email on Tuesday, August 16, 2022, stating that Tromsø kommune has no objections to the sign plan but suggested the creation of good pedestrian waiting areas with tactile markings on both sides of the crossing point.

        Statens vegvesen received a request from Troms og Finnmark fylkeskommune for establishing a pedestrian crossing and road marking for county road 862 in Tromsø municipality. The request is based on the need for safe crossings for residents and workers in the area. Statens vegvesen has sent the plan for the pedestrian crossing on county road 862 to Troms politidistrikt and Tromsø kommune for their input, with a deadline of August 17, 2022. 
        LABEL: NOT NEWSWORTHY: This is not newsworthy because it is about establishing a pedestrian crossing, road markings and traffic lights, which isn't something large enough to use time and resources to report on.

        EXAMPLE 3:
        The document is a notice of address changes in the Musègata area with new street names and numbers assigned to different properties, dated January 5, 2023. The address allocation is in accordance with the Property Registration Act and can be appealed within 3 weeks. Property owners are responsible for marking their buildings with the assigned address number, and the official address becomes the property's postal address.This is a document from the Tromsø municipality regarding an objection to a decision made on January 30, 2023. The objection was received on February 2, 2023, and was recorded under case number 23/00026, doc.6. The decision was not appealed by the deadline of February 20, 2023.Statsforvalteren mottok en klage fra Tromsø kommune angående en adresseendring og ga et foreløpig svar dagen etter. De beklager at det vil ta lengre tid å behandle saken enn antatt, og forventer å avgjøre det innen 13.10.2023. Dette ble kommunisert i et brev datert 26.06.2023, fra Liss Wickstrøm Kvam, seniorkonsulent juridisk seksjon.The document is dated 21.03.2023 and is a preliminary response to a complaint from Tromsø municipality about an address change. The response anticipates that the case will be resolved by 20.06.2023 and is being handled by a legal consultant at the Ministry of Justice and Public Security. The sender of the response is Liss Wickstrøm Kvam, a senior consultant at the legal department.On August 3, 2023, the Statsforvalteren in Troms og Finnmark confirmed the decision of Tromsø municipality to change the address for property gnr. 200 bnr. 1003 from Petersborggata 10 to Musègata 15. The decision was based on the municipality's authority to determine official addresses, and the Statsforvalteren found that the municipality had presented valid and relevant arguments for the decision. The decision was considered final and not subject to appeal.The document is a decision regarding official address allocation, dated 13.03.2023. It contains the official address for Johannes Willem Kögeler and addresses for multiple property owners. The decision upholds a previous allocation and specifies the process for appealing the decision.The document is a decision from the City of Tromsø regarding the allocation of official addresses for certain properties on Musègata. The decision was made on January 30th, 2023 and is subject to appeal within 3 weeks. The decision includes the allocation of new addresses for specific properties, and also addresses the process for lodging a complaint about the decision.The document is dated 15.03.2023 and is about a complaint regarding an address change to Musègata, involving multiple property owners. The complaint was in response to a decision made on 30.01.2023 to change the addresses of 6 properties. The municipality's decision was to not uphold the complaint and the case is being sent to the Statsforvalteren in Troms and Finnmark for a final decision. 
        LABEL: NEWSWORTHY: This is newsworthy as it is about addresschanges for multiple properties, which will impact multiple people. Regardless of any other factors, a journalist would find this interesting as it is highly irregular to change addresses like this.

        LABEL the following summaries as newsworthy or not, and give a short explanation. The themes that have been identified beforehand should give a good indication on whether it should be considered newsworthy:
        {summaries}"""
        #newsworthiness_prompt = """Are there indications of newsvalue in this summary?"""
        
        #newsworthiness_query = self.make_api_request([{"role": "system", "content": f"Examples of newsworthy, not newsworthy, and partly newsworthy cases:  {few_shots}"},
        #                                              {"role": "user", "content": f"{newsworthiness_prompt}\n\n{summaries}"}], max_chunk_size)
        newsworthiness_query = self.make_api_request([{"role": "user", "content": few_shots}], max_chunk_size)
        #newsworthiness_query = self.get_response([{"role": "user", "content": few_shots}], max_chunk_size)

        return newsworthiness_query

if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY")
    folder_path = input('Enter the folder path for text documents:')
    news_detector = NewsDetector(api_key)
    all_summaries = news_detector.summarise_individual_documents('Newsdetection/'+folder_path)
    # Først sende "all_summaries" til en egen funksjon
    # Fjerne documentId.txt, andre unødvendige forekomster av ting
    print("\nCompiled Summaries:\n", all_summaries, "\n")
    time.sleep(2)
    newsworthiness = news_detector.assess_newsworthiness(all_summaries)
    print("\nNewsworthiness Assessment:\n", newsworthiness)

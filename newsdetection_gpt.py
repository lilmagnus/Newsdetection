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
    def __init__(self, api_key, lambda_=LAMBDA, model=MODEL, base_delay=BASE_DELAY, hash_algorithm=HASH_ALGORITHM, cache_folder=CACHE_FOLDER):
        self.api_key = api_key
        self.model=model
        self.hash_algorithm = hash_algorithm
        self.cache_folder = cache_folder
        self.base_delay=base_delay
        self.lambda_=lambda_
        self._handicap=1
        self.cache_manager = CacheManager(hash_algorithm=hash_algorithm, cache_folder=cache_folder)
        openai.api_key = self.api_key

        with open('prompts/generelle_prompts.json', 'r') as prompt_fil:
            self.prompts = json.load(prompt_fil)
    
    def estimate_token_count(self, text):
        return len(text.split())

    def make_api_request(self, messages, max_response_length=1000):
        retry_count = 0
        max_retries = 5
        backoff_time = 60
        max_tokens = min(max_response_length, 4096)

        while retry_count < max_retries:
            #response = self.get_response(messages)
            #if response is not None:
            #    return response # ?????
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
            except Exception as r:
                print(f"Error: {r}")
                if retry_count < max_retries:
                    delay = backoff_time * (2 ** (retry_count - 1))
                    print(f"Venter i {delay} sekunder før retry...")
                    time.sleep(delay)
                    return self.make_api_request(messages, max_response_length)
        
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
        self.cache_manager.cache_response(folder_path, all_summaries)
        # Legg inn kall til categorize metode her, 
        # for å få med vurdering om hvilke kategorier det er snakk om
        if len(all_summaries) > 20000:
            chunked_summaries = self.chunk_summary(all_summaries)
            return self.categorize(chunked_summaries)
            #return self.handle_interaction(chunked_summaries)
        else:
            return self.categorize(all_summaries)

    def chunk_summary(self, text):
        summary = ""
        max_chunk_size = 1500  # Max tokens per chunk -- MÅ VÆRE =/- 2000?
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

            #response = self.make_api_request([{"role": "user", "content": f"Reduce the length of the text by removing text that gives no supporting context and text that has already been written, or text repeating or paraphrasing already written text. Also look out for these criteria, if one is mentioned or implied, it would indicate newsworth: {criterias}. Analyze and reduce text in this summary, keep it below 1500 words in total: {chunk}"}])
            #response = self.make_api_request([{"role": "user", "content": f"Reduce the length of the text by removing text that gives no supporting context and text that has already been written, or text repeating or paraphrasing already written text. Analyze and reduce text in this summary, keep it below 1500 words in total: {chunk}"}])
            response = self.make_api_request([{"role": "user", "content": f"Reduce the total length of the text: {chunk}"}])
            
            if response:
                summary += response + "\n\n"
                chunk_count += 1
            else:
                break  # Exit the loop if there's no response
        
        return summary.strip()

    def summarise_text(self, text):
        summary = ""
        max_chunk_size = 1500  # Max tokens per chunk -- MÅ VÆRE 2000(?)
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

            #response = self.make_api_request([{"role": "user", "content": f"Summarize this in 3 sentences or less, mention the date of the document if it is mentioned: {chunk}"}], max_chunk_size)
            response = self.make_api_request([{"role": "user", "content": f"Summarize this: {chunk}"}], max_chunk_size)

            if response:
                summary += response + "\n\n"
                chunk_count += 1
            else:
                break  # Exit the loop if there's no response
        
        return summary.strip()
    
    # FIX ???
    def categorize(self, summaries):
        # Gå mer inn i detalj på hvert punkt hvis det vurderes som TRUE.
        # Få frem hvor omfattende det egentlig er, for å få en bedre
        # vurdering om det faktisk er dramatisk nok til å lage en nyhetssak på
        assess_list = ['PUBLIC SAFETY', 'LARGE PROJECT', 'NEIGHBOR DISPUTE', 'IMPACT ON CITIZENS', 'ADMINISTRATIVE']
        #assess_list = ['NEIGHBOR DISPUTE']
        definitions = """Definitions of the categories:
        PUBLIC SAFETY: Any dangers related to a project which could put citizens health and lives at risk. Routine communication regarding establishment of roadsigns, crosswalks, sidewalks or similar does not fall under this category, unless there is an ongoing dispute or disagreement mentioned.
        LARGE PROJECT: Projects which discuss the construction of buildings larger than a regular house. This category could be identified by detailed plans surrounding a project, where concerns surrounding multiple factors are mentioned. Multiple stakeholders, public feedback and strive for continuous improvement are also identifiers.
        NEIGHBOR DISPUTE: Neighbor(s) submit complaints about a construction project. It is important to look out for whether it is 1 neighbor submitting a complaint, or multiple neighbors.
        IMPACT ON CITIZENS: Determine whether the construction project will impact citizens in a more significant way than just noise from construction. Such impacts would be: Construction requiring roads to be closed for an extended period of time, projects opening up for tourism or a general increase in visitors which would impact local businesses positively, a larger project in a very populated area such as a mall in the city centre, or changes to multiple properties impacting many citizens such as address change or demolition of building, mountain or other natural terrain which would force citizens to take extra precautions. 
        ADMINISTRATIVE: Identify whether the texts are meant to be more behind-the-scenes, with general requests, documentation, approval or denials. This alone will not mean much, which means it must be tied to another category, such as 'administrative work related to a large project'."""
        assessed = "SUBJECTS:\n"
        if len(definitions+summaries) > 13000:
            summaries = self.chunk_summary(summaries)
        print("-"*10, "Assessing categories...")
        '''
        for i in assess_list:
            #assessment_prompt = self.make_api_request([{"role": "user", "content": f"Check if the following text contains elements of: {i}, return a simple '{i} - (TRUE or FALSE, depending on your assessment)': {summaries}"}])
            #assessment_prompt = self.make_api_request([{"role": "user", "content": f"Check the text for talk about {i}. Explain in 50 words how relevant {i} is in the text: {summaries}"}])
            #assessment_prompt = self.make_api_request([{"role": "user", "content": f"These are the definitions for the categories: {definitions}. Check the text for talk about {i}. If there is talk about it, simply answer with the 'TRUE'+{i}. If there isn't any talk about it, answer with 'FALSE'+{i} {summaries}"}])
            #print(assessment_prompt) # Slp disse sammen, legg definitions til som system input
            checking_prompt = self.make_api_request([{"role": "system", "content": f"These are the definitions for the categories: {definitions}."},
                                                     {"role": "user", "content": f"Based on the definitions given, identify the relevancy of {i} in the summarized document. Assess the newsworth of the summarized documents, with your reasoning in mind (MAX 50 words). {summaries}"}])
            #checking_prompt = self.make_api_request([{"role": "system", "content": f"These are the definitions for the categories: {definitions}."},
            #                                         {"role": "user", "content": f"Based on the definitions given, identify the relevancy of {i} in the summarized document. {summaries}"}])
            
            #print(checking_prompt)
            #assessed += assessment_prompt + checking_prompt + '\n'
            assessed += checking_prompt + '\n'
            '''
        checking_prompt = self.handle_interaction(summaries)
        print(checking_prompt)
        #assessed += checking_prompt # <-- Kødder seg her...
        print("-"*10, "Assessment complete!", "-"*10)
        assessed_summaries = assessed + summaries
        if len(assessed_summaries) > 20000:
            chunk_categories = self.chunk_summary(assessed_summaries)
            return self.detailed_categories(chunk_categories)
        else:
            return self.detailed_categories(assessed_summaries)

    def detailed_categories(self, summaries):
        detail_assessed = "DETAILS SURROUNDING SUBJECTS:"+'\n'
        #detail_digging = self.make_api_request([{"role": "user", "content": f"If any categories are assessed to be TRUE, give an explanation as to why they are TRUE. If no categories are TRUE, don't change the summary. {summaries}"}])
        detail_digging = self.make_api_request([{"role": "user", "content": f"Give some more context to the categories already identified: {summaries}"}])
        detail_assessed += detail_digging
        return detail_assessed

    def get_response(self, summaries, max_response_length=1000):
        # Sjekk cache
        cached_response = self.cache_manager.get_cached_response(summaries)
        if cached_response is not None:
            return cached_response
        
        # Hvis ikke i cache
        response = self.make_api_request(summaries, max_response_length)
        return response
    # ORDNE HER
    def get_next_prompt(self, current_prompt_key, answer):
        current_prompt_info = self.prompts.get(current_prompt_key, {})
        next_prompt_key = current_prompt_info.get("responses", {}).get(answer)
        
        if next_prompt_key:
            return self.prompts.get(next_prompt_key, {}).get("prompt")
        else:
            return None
    # ORDNE HER
    def handle_interaction(self, text):
        current_prompt_key = "identify_subjects"  # Starting point
        while current_prompt_key:
            prompt_text = self.prompts.get(current_prompt_key, {}).get("prompt", "")
            response = self.make_api_request([{"role": "user", "content": f"{prompt_text}, {text}"}])
            print(response)
            # Kanskje fyre inn en prompt for å hente ut mer konkrete svar.
            # Til bruk for å bestemme hva som skal spørres om next.
            answer = response
            # API request her for å hente ut enkelt svar fra response her?
            next_prompt_key = self.get_next_prompt(current_prompt_key, answer)
            current_prompt_key = next_prompt_key if next_prompt_key in self.prompts else None

    def assess_newsworthiness(self, summaries):
        max_chunk_size = 10000

        #self.get_response(summaries)

        # Hmmm
        points_category = """Ranking of categories, from most to least likely to make something newsworthy. 
            1. LARGE PROJECT
            2. PUBLIC SAFETY CONCERNS
            3. QUESTION OF LEGALITY
            4. IMPACT ON LOCALS
            5. ADMINISTRATIVE
            6. NEIGHBOR DISPUTE

            If more than one apply, make a decision on whether it would qualify as newsworthy.
            """ #{newsworthiness_criteria}
        #newsworthiness_criteria = "CRITERIA, MEETING ONE IS ENOUGH: Public safety, meaning there is risk of civilian safety and health surrounding the project. Larger projects, meaning construction of hotels, bigger apartment complexes (over 10 apartments), construction of industry buildings, factories, stores, pubs to name a few (Administrative documents of this nature would be of interest, and therefore considered newsworthy). Multiple complaints from neighbors, or disputes from neighboring properties, multiple neighbors submitting complaints against a project, address changes."
        # Fiks begge disse ^v, ikke bra nok definert
        # Eksemplene trenger mer strukturerte resonnement for hvorfor de er eller ikke er nyhetsverdige
        
        few_shots = f"""Instruction: Assess the possible newsworth of the given summary of construction permit documents.
        {points_category}

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

        Label the following summary of construction permit documents in the same fashion as above.
        {summaries}"""
        
        few_shot2 = f""""Instruction: Based on the provided examples, assess the given summary in the same style as the examples.

        EXAMPLE 1:
        Cristina \u00d8ie is applying for a dispensation from the LNFR purpose to build a detached pergola on a developed property in Ramfjordbotn, Troms\u00f8. The pergola will not hinder grazing, is not on cultivable land, is far enough from Storelva river, and will have minimal environmental impact. The application includes attachments showing the location and design of the pergola.The document is a preliminary response to a building application submitted by Cristina Ionica \u00d8ie for a detached building on Breivikeidvegen 2113, dated 10.11.2023. The property is located in an area prone to rock falls, avalanches, and quick clay, requiring documentation of building practices in accordance with the pbl. \u00a728-1 SAK10 \u00a75-4 g. The applicant is requested to provide the necessary documentation within 30 days to avoid rejection of the application."
        LABEL: NOT NEWSWORTHY
        EXPLANATION: Regular, normal application for a building permit.

        EXAMPLE 2:
        "Regarding the construction of a hotel building in Huldervegen 2, there is a complaint from Avinor, with attachments containing assessments and responses to the complaint. The email exchange between Espen Skov Pettersen and Monalf Figenschau on July 17, 2020, discusses the issue and the response to Avinor's complaint about the hotel construction project in Troms\u00f8.The email exchanges are related to a building permit application for a project in Troms\u00f8, with concerns about the flight path regulations and radio navigation systems. Avinor requests updated documentation on the project to assess any changes and ensure compliance. The emails span from February to April 2019.The document is dated 26.05.2020 and discusses a complaint from Avinor regarding a decision about the construction of a hotel building in Troms\u00f8. The planned building is located within the height restriction zone near Troms\u00f8 airport runway, but its height will not conflict with the restrictions. The document also mentions the possibility of a crane being placed on the east side of the hotel by the developer.\n\nThe document, dated 02.05.2019, outlines the requirements for the use of tower cranes and mobile cranes near airports such as Troms\u00f8 lufthavn. It states that a risk analysis must be conducted by a consultant with aviation expertise to determine the safety of crane operations. Approval from Avinor and Luftfartstilsynet is necessary before the cranes can be used, with specific procedures and communication protocols in place for mobile crane operations.\n\nThe document discusses the regulations for reporting and registering aviation obstacles related to the setup and use of cranes, dated 03.06.2019. It also evaluates building restrictions for flight navigation systems at the airport, with a radio technical analysis showing that the hotel building will not negatively affect the systems. There are concerns about using a tower crane for construction due to potential radio technical issues, with the recommendation that crane use be properly assessed and possibly tested at the expense of the developer.\n\nThe document, dated 02.05.2019, addresses the need for a lighting plan for buildings and outdoor areas near Troms\u00f8 Airport to ensure aviation safety. It also discusses the importance of minimum visibility for pilots during landings and the potential risks associated with turbulence caused by nearby structures. Avinor will not approve construction projects that worsen the turbulence situation at the airport, based on EASA requirements.\n\nAvinor is requesting additional requirements be included in the building permit for the hotel in Huldervegen 2 to ensure that the construction does not worsen the turbulence situation at Troms\u00f8 Airport. This includes the need for a flow analysis/turbulence analysis from a reputable supplier approved by Avinor. If these requirements are not met, Avinor will appeal the municipality's building permit to the County Governor of Troms and Finnmark to protect flight safety and airport certification. The document references previous correspondences from Avinor regarding the need for a flow analysis, dated May 2, 2019, and June 6, 2019.\n\nAvinor is concerned about the potential impact of a new hotel near Troms\u00f8 Airport on air traffic due to the possibility of turbulence. They request a turbulence analysis be conducted as part of the building permit process. Avinor emphasizes the importance of ensuring the safety and regularity of flights at the airport. (Date: 02.05.2019)The document is an email communication regarding the requirement for a flow analysis for a new hotel construction in Troms\u00f8, dated June 17, 2020. Avinor emphasizes the need for a flow analysis due to potential turbulence issues near the Troms\u00f8 airport, based on European regulations. The sender, Torstein Piltingsrud, seeks clarification on the requirements outlined by Avinor in their previous communications.Avinor has filed a conditional complaint regarding the construction of a hotel building on property 118/1016 in Huldervegen 2, based on specific additional conditions to the building permit. The complaint includes requirements for a flow analysis/turbulence analysis, approval for crane use, and a lighting plan to be submitted and approved by Avinor. The responsible applicant acknowledges the conditions and is taking steps to fulfill the requirements to avoid the complaint being processed further."
        LABEL: NEWSWORTHY
        EXPLANATION: Complaint from Avinor (a big actor) regarding concerns surrounding the construction of a hotel interfering with flight safety.

        Now asses the following summary in the same style as given in the examples. Give one assessment to the entire summary. {summaries}
        """

        #newsworthiness_prompt = """Are there indications of newsvalue in this summary?"""
        
        #newsworthiness_query = self.make_api_request([{"role": "system", "content": f"Examples of newsworthy, not newsworthy, and partly newsworthy cases:  {few_shots}"},
        #                                              {"role": "user", "content": f"{newsworthiness_prompt}\n\n{summaries}"}], max_chunk_size)
        newsworthiness_query = self.make_api_request([{"role": "system", "content": "Work out your own solution to whether the summary you are given is newsworthy or not. Give a clear LABEL of your decision, as the examples show."},
                                                      {"role": "user", "content": few_shots}], max_chunk_size)
        #newsworthiness_query = self.get_response([{"role": "user", "content": few_shots}], max_chunk_size)

        return newsworthiness_query

if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY")
    folder_path = input('Enter the folder path for text documents:')
    news_detector = NewsDetector(api_key)
    cache_collect = CacheManager()
    nummer = 0
    newsworth_counter = ""
    folder = ['0news', '1news']
    # JSON prompting below :)
    cache_fetch = cache_collect.get_cached_response(folder_path)
    if cache_fetch is not None:
        categorize_json = news_detector.categorize(cache_fetch)
        print(categorize_json)
        assess_json = news_detector.assess_newsworthiness(categorize_json)
        print(assess_json)
    # ^^^GJØR FERDIG

    '''
    while nummer < 5:
        for j in folder:
            instructions_calculation = f"""The proper way of answering this is: "{j} - NOT NEWSWORTHY" OR "{j} - NEWSWORTHY". 
                    Some of the texts youre given might not be clear immediately, some might look similar to this:
                    "Based on the categories provided, the summary of the construction permit documents for the hotel project in Tromsø would likely be considered newsworthy due to its classification as a large project, public safety concerns, potential question of legality, and impact on locals." 
                    The above example is newsworthy, as it states: "would likely be considered newsworthy" """
            #for filename in os.listdir(folder_path):
            for filename in os.listdir(j):
                print("="*20, filename.upper(), "="*20)
                #check_cache = cache_collect.get_cached_response(folder_path+"/"+filename)
                check_cache = cache_collect.get_cached_response(j+"/"+filename)
                if check_cache is not None:
                    cache_categorize = news_detector.categorize(check_cache)
                    print(cache_categorize)
                    asses_cache = news_detector.assess_newsworthiness(cache_categorize)
                    time.sleep(2)
                    print("\nNewsworthiness assessment on cached file:\n", asses_cache, "\n\n")
                    time.sleep(2)
                    count_assessment = news_detector.make_api_request([{"role": "system", "content": f"{instructions_calculation}"},
                                                                       {"role": "user", "content": f"Was this assessed as newsworthy or not newsworthy? {asses_cache}. Count 'potentially newsworthy' as NEWSWORTHY."}])
                    newsworth_counter += count_assessment+'\n'
                    time.sleep(2)
                else:
                    #all_summaries = news_detector.summarise_individual_documents(folder_path+"/"+filename)
                    all_summaries = news_detector.summarise_individual_documents(j+"/"+filename)
                    # Først sende "all_summaries" til en egen funksjon
                    # Fjerne documentId.txt, andre unødvendige forekomster av ting
                    print("\nCompiled Summaries:\n", all_summaries, "\n")
                    time.sleep(2)
                    newsworthiness = news_detector.assess_newsworthiness(all_summaries)
                    print("\nNewsworthiness Assessment:\n", newsworthiness)
                    time.sleep(2)
                    count_assessment = news_detector.make_api_request([{"role": "system", "content": f"{instructions_calculation}"},
                                                                       {"role": "user", "content": f"Was this assessed as newsworthy or not newsworthy? {asses_cache}. Count 'potentially newsworthy' as NEWSWORTHY."}])
                    newsworth_counter += count_assessment+'\n'
                    time.sleep(2)
            nummer += 1
    print(newsworth_counter)
    calculate_assessments = news_detector.make_api_request([{"role": "user", "content": f"Calculate the accuracy in percentage. Where it says '0news' the correct prediction would be NOT NEWSWORTHY, where it says '1news' the correct prediction would be NEWSWORTHY. Calculate on this collection: {newsworth_counter}"}])
    print(calculate_assessments)'''

import os
import openai
import time
import requests
import fitz
import hashlib
import json
import ast
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
        
        with open('prompts/nyhets_prompts.json', 'r') as newsprompt_fil:
            self.news_prompts = json.load(newsprompt_fil)
    
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
        assessed = "SUBJECTS IDENTIFIED AND EXPLORED FROM THE SUMMARY:\n"
        #if len(definitions+summaries) > 13000:
        #    summaries = self.chunk_summary(summaries)
        #print(summaries)
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
        assessed += str(checking_prompt)
        print("-"*10, "Assessment complete!", "-"*10)
        assessed_summaries = 'THE FOLLOWING IS THE SUMMARY:\n' + summaries+ '\n' + assessed
        if len(assessed_summaries) > 20000:
            chunk_categories = self.chunk_summary(assessed_summaries)
            #return self.detailed_categories(chunk_categories)
            return chunk_categories
        else:
            return assessed_summaries
            #return self.detailed_categories(assessed_summaries)

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
    
    # Knytt de tre neste metodene sammen med categorize++
    # For det meste fikset, mangler å få current_prompt_key oppdatert
    def extract_subjects(self, subject_prompt, response):
        # Formatter riktig
        subject_response = self.make_api_request([{"role": "user", "content": f"{subject_prompt}, {response}"}])
        print(subject_response)
        try:
            subjects_list = ast.literal_eval(subject_response)
            if isinstance(subjects_list, list):
                return subjects_list
            else:
                print("The response is not in the expected list format.")
                return []
        except (ValueError, SyntaxError):
            print("Failed to parse the response into a list.")
            return []
        
    # ORDNE HER
    def get_next_prompt(self, file,  current_prompt_key, subjects):
        matched_prompts = []
        response_keys = file.get(current_prompt_key, {}).get("responses", {})

        for subject in subjects:
            subject_normalized = subject.lower()
            for response_key, next_prompt_key in response_keys.items():
                if subject_normalized == response_key.lower():
                    next_prompt_text = self.prompts.get(next_prompt_key, {}).get("prompt")
                    matched_prompts.append((next_prompt_key, next_prompt_text))
                    break

        return matched_prompts

    # ORDNE HER
    def handle_interaction(self, text):
        current_prompt_key = "identify_subjects"
        initial_prompt_text = self.prompts.get(current_prompt_key, {}).get("prompt", "")
        initial_response = self.make_api_request([{"role": "user", "content": f"{initial_prompt_text} {text}"}])
        
        subject_prompt = "Extract only the subjects identified in the text given, format the response into a Python list, all capital letters."
        subjects = self.extract_subjects(subject_prompt, initial_response)
        matched_prompts = self.get_next_prompt(self.prompts, current_prompt_key, subjects)
        assessed_text = ""
        if matched_prompts:
            for next_prompt_key, next_prompt_text in matched_prompts:
                # Handle each matched prompt. Here you could ask the user which one to explore or just explore each sequentially.
                print(f"Exploring subject {next_prompt_key.upper()}: {next_prompt_text}")
                further_response = self.make_api_request([{"role": "user", "content": f"{next_prompt_text}\n {text}"}])
                print(f"Response for {next_prompt_key.upper()}: {further_response}")
                # Add logic here if you want to do something with the responses, like asking for user input on which to explore further.
                #key_answer = next_prompt_key + further_response
                assessed_text += '\n'+next_prompt_key.upper()+'\n' + further_response
        else:
            print("No further details required based on the subjects identified.")
        return assessed_text


        '''
        while current_prompt_key:
            prompt_info = self.prompts.get(current_prompt_key, {})
            prompt_text = prompt_info.get("prompt", "")
            response = self.make_api_request([{"role": "user", "content": f"{prompt_text} {text}"}])
            print(response)

            subjects = self.extract_subjects(response)

            next_prompt_key = self.get_next_prompt(current_prompt_key, subjects)
            if next_prompt_key:
                current_prompt_key = next_prompt_key
                print(current_prompt_key)
            else:
                # Ingen flere prompts, eller ikke mulig å avgjøre neste steg
                break'''

    def assess_newsworthiness(self, summaries):
        max_chunk_size = 10000

        current_prompt_key = "identification"
        start_prompt = self.news_prompts.get(current_prompt_key, {}).get("prompt", "")
        print(start_prompt)
        initial_response = self.make_api_request([{"role": "user", "content": f"{start_prompt}, {summaries}"}])
        print(initial_response)
        subject_prompt = "This given text should contain either a positive response or a negative response. If it is positive, meaning it evaluated a text as newsworthy, return ['NEWSWORTHY']. If the text is negative, meaning it identified the text as not newsworthy, return a simple ['NOT NEWSWORTHY']."
        subjects = self.extract_subjects(subject_prompt, initial_response)
        matched_prompts = self.get_next_prompt(self.news_prompts, current_prompt_key, subjects)
        newsworthiness_text = ""
        if matched_prompts:
            for next_prompt_key, next_prompt_text in matched_prompts:
                explanation_prompt = self.make_api_request([{"role": "user", "content": f"{next_prompt_text} {summaries}"}])
                newsworthiness_text += str(subjects) + '\n' + explanation_prompt
        else:
            print("Fant ingenting, PROBLEM?")
        
        return newsworthiness_text

        #self.get_response(summaries)


if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY")
    #folder_path = input('Enter the folder path for text documents:')
    news_detector = NewsDetector(api_key)
    cache_collect = CacheManager()
    nummer = 0
    newsworth_counter = ""
    folder = ['0news', '1news']
    # JSON prompting below :)
    '''
    cache_fetch = cache_collect.get_cached_response(folder_path)
    if cache_fetch is not None:
        categorize_json = news_detector.categorize(cache_fetch)
        print(categorize_json)
        assess_json = news_detector.assess_newsworthiness(categorize_json)
        print(assess_json)
    '''


    while nummer < 1:
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
    print(calculate_assessments)

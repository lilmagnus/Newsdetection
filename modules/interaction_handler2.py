# interaction_handler.py
import ast
import json
from api_client import APIClient
import time

class InteractionHandler:
    def __init__(self, prompts_file):
        self.api_client = APIClient()
        self.combined_prompts = self._load_prompts(prompts_file)
        #self.tokenizer = AutoTokenizer.from_pretrained("bert-base-multilingual-cased")
        #self.model = AutoModelForSequenceClassification.from_pretrained("bert-base-multilingual-cased")
        #self.sentiment_pipeline = pipeline("sentiment-analysis", model=self.model, tokenizer=self.tokenizer)

    def _load_prompts(self, file_path):
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"Failed to load prompts from {file_path}: {e}")
            return {}
    
    
    def map_to_binary(self, text):
        positive_keywords = ['ja', 'yes', 'dette er et stort', 'det er bekymring for offentlig sikkerhet', 'absolutt', 'virker å være', 'kan dette potensielt være', 'there is some concern']
        negative_keywords = ['nei', 'no', 'dette er ikke et stort prosjekt', 'relativt', 'ikke bekymring for offentlig sikkerhet']
        
        response_text = text.lower()
        
        if any(keyword in response_text for keyword in positive_keywords):
            return "ja."
        elif any(keyword in response_text for keyword in negative_keywords):
            return "nei."
        else:
            return "nei."


    def process_section(self, section, text):
        ident_prompt = section["identifisering"]["prompt"]
        
        first_response = self.api_client.make_api_request([{"role": "user", "content": f"{ident_prompt} {text}"}])
        print(first_response, "FØRSTE")
        time.sleep(2)

        #f_resp = self.sentiment_analysis(first_response)
        '''
        eksempler = """EKSEMPLER PÅ SPØRSMÅL MED SVAR:
        TEKST: Dette kan anses som et stort prosjekt.
        Q: Svar med et enkelt 'Ja.' eller 'Nei.' basert på essensen i den gitte teksten.
        A: 'Ja.'
        
        TEKST: Dette er ikke et stort prosjekt.
        Q: Svar med et enkelt 'Ja.' eller 'Nei.' basert på essensen i den gitte teksten.
        A: 'Nei.'
        
        TEKST: Dette er et middels stort prosjekt.
        Q: Svar med et enkelt 'Ja.' eller 'Nei.' basert på essensen i den gitte teksten.
        A: 'Nei.'
        
        TEKST: IKKE RELEVANT.
        Q: Svar med et enkelt 'Ja.' eller 'Nei.' basert på essensen i den gitte teksten.
        A: 'Nei.'
        """
        f_resp = self.api_client.make_api_request([{"role": "system", "content": f"{eksempler}"},
                                                   {"role": "user", "content": f"Svar med et enkelt 'Ja.' eller 'Nei.' basert på essensen i den gitte teksten. {first_response}"}])
        '''
        f_resp = self.map_to_binary(first_response)
        #print(f_resp, "ANDRE")
        
        responses = [ident_prompt]

        if f_resp.strip().lower() in section["identifisering"]["responses"][f_resp.strip().lower()]:
            decision = section["identifisering"]["responses"][f_resp.strip().lower()]
            if "ja" in decision:
                for prompt_key in section["ja"]:
                    prompt = section["ja"][prompt_key]
                    response = self.api_client.make_api_request([{"role": "user", "content": f"{prompt} {text}"}])
                    responses.append(response)
            elif "nei" in decision:
                responses.append("IKKE RELEVANT.")
                #response = self.api_client.make_api_request([{"role": "user", "content": prompt}])
                #responses.append(response)
        return responses

    def handle_interaction(self, original_text):

        # Forhåndssjekk lengde for chunking
        print(len(original_text))
        if len(original_text) > 25000:
            original_text = self.reduce_text(original_text)
            print(len(original_text))
        
        # Step 1: Identifiser kategorier, og spør mer detaljer rundt
        details_large_project = self.process_section(self.combined_prompts["large_project"], original_text)
        print(str(details_large_project), 'ADGENHEFGHDSGETNDF')
        details_public_safety = self.process_section(self.combined_prompts["public_safety"], original_text)
        print(str(details_public_safety), 'ÅØÆÅØÆÅØÆÅØÆÅØÆÅØÆ')

        # Step 2: Kombiner kategoriene som er identifisert
        kategorier_funnet = details_large_project + details_public_safety
        hel_kontekst = original_text + str(kategorier_funnet)
        print(hel_kontekst)

        # Step 3: Send siste spørring for å hente ut nyhetsverdi
        # Begge stegene her må til assess_newsworth
        news_assessment = self.assess_newsworth(self.combined_prompts["assessment"], hel_kontekst)

        ny_kontekst = original_text + '   ' + news_assessment
        print('\n\n\n', ny_kontekst, '\n\n\n\n')

        #assessed_kontekst = hel_kontekst + str(news_assessment)
        #revised_assessment = self.assess_newsworth(self.combined_prompts["reassess"], news_assessment)
        revised_assessment = self.reassess_newsworth(self.combined_prompts["reassess"], ny_kontekst)
        return revised_assessment
    
    def assess_newsworth(self, section, text):
        first_prompt = section["identifisering"]["prompt"]
        response = self.api_client.make_api_request([{"role": "system", "content": "Du er en journalistassistent for den norske lokale avisen iTromsø, som rapporterer om nyhetsverdige byggesaker i Tromsø kommune."},
                                                     {"role": "user", "content": f"{first_prompt} {text}"}])
        print('FIRST RESPONSE ---------->   ',response)
        # Send til map_to_binary
        assess_response = self.map_to_binary(response)
        print(assess_response, 'HHHHHHHHHHHHOOOOOOOOOOOOOOOOLAAAAA')
        
        if assess_response.strip().lower() in section["identifisering"]["responses"][assess_response.strip().lower()]:
            decision = section["identifisering"]["responses"][assess_response.strip().lower()]
            if "ja" in decision:
                prompt = section["ja"]["prompt"]
                final_response = self.api_client.make_api_request([{"role": "system", "content": "Du er en journalistassistent for den norske lokale avisen iTromsø, som rapporterer om nyhetsverdige byggesaker i Tromsø kommune."},
                                                                   {"role": "user", "content": f"{prompt} {text}"}])
            elif "nei" in decision:
                prompt = section["nei"]["prompt"]
                final_response = self.api_client.make_api_request([{"role": "system", "content": "Du er en journalistassistent for den norske lokale avisen iTromsø, som rapporterer om nyhetsverdige byggesaker i Tromsø kommune."},
                                                                   {"role": "user", "content": f"{prompt} {text}"}])
        print('FINAL RESPONSE ----------->   ', final_response)
        return final_response
    
    def reassess_newsworth(self, section, text):
        first_prompt = section["identifisering"]["prompt"]
        response = self.api_client.make_api_request([{"role": "system", "content": "Du er en journalistassistent for den norske lokale avisen iTromsø, som rapporterer om nyhetsverdige byggesaker i Tromsø kommune."},
                                                     {"role": "user", "content": f"{first_prompt} {text}"}])
        # Send til map_to_binary
        #assess_response = self.map_to_binary(response)
        #print(assess_response, 'HHHHHHHHHHHHOOOOOOOOOOOOOOOOLAAAAA')
        '''
        if assess_response.strip().lower() in section["identifisering"]["responses"][assess_response.strip().lower()]:
            decision = section["identifisering"]["responses"][assess_response.strip().lower()]
            if "ja" in decision:
                prompt = section["ja"]["prompt"]
                final_response = self.api_client.make_api_request([{"role": "user", "content": f"{prompt} {text}"}])
            elif "nei" in decision:
                prompt = section["nei"]["prompt"]
                final_response = self.api_client.make_api_request([{"role": "user", "content": f"{prompt} {text}"}])
        '''
        return response
        
    
    def reduce_text(self, text):
        parts = self.split_text(text, 2)  # Splitting the text into 2 parts for this example, adjust as needed
        reduced_text_parts = []

        for part in parts:
            reduction_prompt = "Reduce the total number of tokens in this text by removing 'fluff'. Keep all key details. Return only the new, shorter text."
            reduced_part = self.api_client.make_api_request([{"role": "user", "content": f"{reduction_prompt} {part}"}])
            reduced_text_parts.append(reduced_part)
        
        return "".join(reduced_text_parts)

    def split_text(self, text, num_parts):
        if num_parts < 2:
            return [text]  # No need to split

        part_length = len(text) // num_parts
        parts = []
        last_index = 0

        for _ in range(num_parts - 1):  # Split into num_parts
            split_index = text.rfind(' ', last_index, last_index + part_length) + 1  # Find space to avoid splitting words
            parts.append(text[last_index:split_index])
            last_index = split_index

        parts.append(text[last_index:])  # Add the last part
        return parts
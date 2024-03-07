# interaction_handler.py
import ast
import json
from api_client import APIClient

class InteractionHandler:
    def __init__(self, prompts_file):
        self.api_client = APIClient()
        self.combined_prompts = self._load_prompts(prompts_file)

    def _load_prompts(self, file_path):
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"Failed to load prompts from {file_path}: {e}")
            return {}

    def extract_subjects(self, prompt):
        response = self.api_client.make_api_request([{"role": "system", "content": prompt}])
        try:
            subjects_list = ast.literal_eval(response)
            if isinstance(subjects_list, list):
                #print(subjects_list)
                return subjects_list
            else:
                print("The response is not in the expected list format.")
                return []
        except (ValueError, SyntaxError):
            print("Failed to parse the response into a list.")
            return []

    def handle_interaction(self, original_text):
        identified_subjects = []
        detailed_responses = []
        
        # Step 1: Identify subjects
        identification_prompt = self.combined_prompts['subject_identification']['identify_subjects']['prompt']
        subjects = self.extract_subjects(identification_prompt + " " + original_text)
        print(subjects)
        
        # Detailed analysis based on identified subjects
        combined_details = ""
        for subject in identified_subjects:
            response_key = self.combined_prompts['subject_identification']['identify_subjects']['responses'].get(subject, '')
            print(response_key)
            if response_key:
                prompt_details = self.combined_prompts['subject_identification'][response_key]['prompt']
                # Include the original text in the prompt for detailed analysis
                detailed_response = self.api_client.make_api_request([{"role": "system", "content": f"{prompt_details}\n\n{original_text}"}])
                combined_details += " " + detailed_response  # Concatenating all detailed responses
        
        # Ensure the original text is considered in the newsworthiness assessment
        if identified_subjects:
            newsworthiness_prompt = self.combined_prompts['newsworthiness_assessment']['identification']['prompt']
            # Combine both the detailed responses and the original text for a comprehensive context
            full_context = combined_details + " " + original_text
            newsworthiness_response = self.api_client.make_api_request([{"role": "system", "content": f"{newsworthiness_prompt}\n\n{full_context}"}])
            

            # Further detailing based on newsworthiness
            if ['NEWSWORTHY'] in newsworthiness_response:
                highlight_prompt = self.combined_prompts['newsworthiness_assessment']['newsworthy']['prompt']
                highlight_response = self.api_client.make_api_request([{"role": "system", "content": highlight_prompt + " " + combined_details}])
                return f"NEWSWORTHY: {highlight_response}"
            elif ['NOT NEWSWORTHY'] in newsworthiness_response:
                explanation_prompt = self.combined_prompts['newsworthiness_assessment']['not_newsworthy']['prompt']
                explanation_response = self.api_client.make_api_request([{"role": "system", "content": explanation_prompt + " " + combined_details}])
                return f"NOT NEWSWORTHY: {explanation_response}"
        
        #return "Unable to determine newsworthiness due to lack of identified subjects."


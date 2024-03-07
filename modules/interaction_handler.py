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
        definitions = """Definitions of the categories:
        PUBLIC SAFETY: Any dangers related to a project which could put citizens health and lives at risk. Routine communication regarding establishment of roadsigns, crosswalks, sidewalks or similar does not fall under this category, unless there is an ongoing dispute or disagreement mentioned.
        LARGE PROJECT: Projects which discuss the construction of buildings larger than a regular house. This category could be identified by detailed plans surrounding a project, where concerns surrounding multiple factors are mentioned. Multiple stakeholders, public feedback and strive for continuous improvement are also identifiers.
        IMPACT ON CITIZENS: Determine whether the construction project will impact citizens in a more significant way than just noise from construction. Such impacts would be: Construction requiring roads to be closed for an extended period of time, projects opening up for tourism or a general increase in visitors which would impact local businesses positively, a larger project in a very populated area such as a mall in the city centre, or changes to multiple properties impacting many citizens such as address change or demolition of building, mountain or other natural terrain which would force citizens to take extra precautions.
        CHILDREN: This category can only be true if there is direct involvement from children, meaning child labor.
        DRUG CARTEL: If a drug cartel is involved in the planning or construction of a project, this can be evaluated as true, else it is not to be considered."""
        response = self.api_client.make_api_request([{"role": "system", "content": f"{definitions} {prompt}"}])
        #print(response)
        try:
            subjects_list = ast.literal_eval(response)
            if isinstance(subjects_list, list) and all(isinstance(item, str) for item in subjects_list):
                #print(subjects_list)
                return subjects_list
            else:
                print("The response is not in the expected list format.")
                return []
        except (ValueError, SyntaxError):
            print("No subjects identified.")
            return ["No subjects identified."]

    def handle_interaction(self, original_text):
        #identified_subjects = []
        #detailed_responses = []
        
        # Step 1: Identify subjects
        identification_prompt = self.combined_prompts['subject_identification']['identify_subjects']['prompt']
        subjects = self.extract_subjects(identification_prompt + " " + original_text)

        # Detailed analysis based on identified subjects
        combined_details = ""
        for subject in subjects:
            response_key = self.combined_prompts['subject_identification']['identify_subjects']['responses'].get(subject, '')
            if response_key:
                prompt_details = self.combined_prompts['subject_identification'][response_key]['prompt']
                # Include the original text in the prompt for detailed analysis
                detailed_response = self.api_client.make_api_request([{"role": "system", "content": f"{prompt_details}\n\n{original_text}"}])
                combined_details += " " + detailed_response  # Concatenating all detailed responses
                print(combined_details)
        
        # Ensure the original text is considered in the newsworthiness assessment
        if subjects:
            newsworthiness_prompt = self.combined_prompts['newsworthiness_assessment']['identification']['prompt']
            # Combine both the detailed responses and the original text for a comprehensive context
            full_context = combined_details + " " + original_text
            newsworthiness_response = self.api_client.make_api_request([{"role": "system", "content": f"{newsworthiness_prompt}\n\n{full_context}"}])
            print(newsworthiness_response)
            

            # Further detailing based on newsworthiness
            if 'NEWSWORTHY' in newsworthiness_response:
                highlight_prompt = self.combined_prompts['newsworthiness_assessment']['newsworthy']['prompt']
                highlight_response = self.api_client.make_api_request([{"role": "system", "content": highlight_prompt + " " + combined_details}])
                return f"NEWSWORTHY: {highlight_response}"
            elif 'NOT NEWSWORTHY' in newsworthiness_response:
                explanation_prompt = self.combined_prompts['newsworthiness_assessment']['not_newsworthy']['prompt']
                explanation_response = self.api_client.make_api_request([{"role": "system", "content": explanation_prompt + " " + combined_details}])
                return f"NOT NEWSWORTHY: {explanation_response}"
            else:
                explanain_prompt2 = self.combined_prompts['assesser']['prompt']
                explanain_response2 = self.api_client.make_api_request([{"role": "system", "content": explanain_prompt2 + " " + original_text}])
                return f"GENERAL ASSESSMENT: {explanain_response2}"

        
        return "Unable to determine newsworthiness due to lack of identified subjects."


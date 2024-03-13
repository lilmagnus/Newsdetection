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
        response = self.api_client.make_api_request([{"role": "user", "content": f"{definitions} {prompt}"}])
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
        print(subjects)

        # Detailed analysis based on identified subjects
        # Gjør mer for å unngå å parse dokumenter med ingen subjects identified.

        # Få oversikt over om teksten har identifiserte subjects eller ikke
        combined_details = ""
        if "No subjects identified." in subjects:
            print("No subjects to analyze.")

        elif 'NO SUBJECTS PRESENT.' in subjects:
            print("No subjects present.")
        # Spør ut rundt hvert subject
        else:
            for subject in subjects:
                response_key = self.combined_prompts['subject_identification']['identify_subjects']['responses'].get(subject, '')
                if response_key:
                    prompt_details = self.combined_prompts['subject_identification'][response_key]['prompt']
                    # Include the original text in the prompt for detailed analysis
                    detailed_response = self.api_client.make_api_request([{"role": "user", "content": f"{prompt_details}\n\n{original_text}"}])
                    combined_details += '\n' + " " + subject.upper()+'\n' + detailed_response  # Concatenating all detailed responses
            print(combined_details)
        
        # Vurder alle subjects og forklar mer om hva de kan bety først
        all_text = combined_details + " " + original_text
        context_system = self.combined_prompts['assess_all']['question']['prompt1']
        context_prompt = self.combined_prompts['assess_all']['question']['prompt2']
        context_enrich = self.api_client.make_api_request([{"role": "system", "content": context_system},
                                                           {"role": "user", "content": f"{context_prompt} {all_text}"}])
        everything_text = "SUBJECTS:" + str(subjects) + context_enrich + " " + '\n' + original_text
        print(everything_text, '\n\nAAAAAAAAAAAAAAAAAAAAAAAAAAA\n\n\naa')


        # Ensure the original text is considered in the newsworthiness assessment
        if subjects and 'No subjects identified.' and 'NO SUBJECTS PRESENT.' not in subjects:
            newsworthiness_prompt = self.combined_prompts['newsworthiness_assessment']['identification']['prompt']
            # Combine both the detailed responses and the original text for a comprehensive context
            #full_context = combined_details + " " + original_text
            newsworthiness_response = self.api_client.make_api_request([{"role": "user", "content": f"{newsworthiness_prompt}\n\n{everything_text}"}])
            print(newsworthiness_response, '\n\nOOOOOOOOOOOOOOOOOOOOOOOOOO')
       

            # Further detailing based on newsworthiness
            
            if 'NEWSWORTHY' == newsworthiness_response.strip():
                highlight_prompt = self.combined_prompts['newsworthiness_assessment']['newsworthy']['prompt']
                highlight_response = self.api_client.make_api_request([{"role": "user", "content": highlight_prompt + " " + everything_text}]) # Bytt mellom combined_details og everything_text
                return f"NEWSWORTHY: {highlight_response}"
            else: # Alt annet er antatt dårlig nytt
                explanation_prompt = self.combined_prompts['newsworthiness_assessment']['not_newsworthy']['prompt']
                explanation_response = self.api_client.make_api_request([{"role": "user", "content": explanation_prompt + " " + everything_text}]) # Samme som over
                return f"NOT NEWSWORTHY: {explanation_response}"
        else:
            explanation_prompt2 = self.combined_prompts['newsworthiness_assessment']['no_subjects']['prompt']
            explanation_response2 = self.api_client.make_api_request([{"role": "user", "content": explanation_prompt2 + " " + everything_text}])
            return f"NO SUBJECTS IDENTIFIED, SUMMARY OF TEXT: {explanation_response2}"

        
        #return "Unable to determine newsworthiness due to lack of identified subjects."


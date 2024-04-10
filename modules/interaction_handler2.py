# interaction_handler.py
import ast
import json
from api_client import APIClient
import time

class InteractionHandler:
    def __init__(self, prompts_file):
        self.api_client = APIClient()
        self.combined_prompts = self._load_prompts(prompts_file)
        self.relevante_tema = """Dette er en oversikt over temaer som skal vurderes som nyhetsverdige, så lenge det er en allerede eksisterende vurdering om at dokumentet holder nyhetsverdi:
        - Flere naboklager
        - Ulovlig byggearbeid
        - Husly for flyktninger
        - Prosesser som virker å gå frem og tilbake med tillatelser og avslag over lengre tid
        - Avvik fra godkjente tegninger
        """
        self.ikke_relevant = """Følgende er en oversikt over temaer som ikke utgjør noe nyhetsverdi:
        - dispensasjonssøknader og søknader om dispensasjon for oppføring av enebolig
        - diskusjon om byggegrenser
        - forespørsel om ferdigattest
        - administrative dokumenter som mangler direkte relevans til de identifiserte temaene
        - søknad om byggetillatelse
        - søknad om godkjennelse for tilbygg
        - dokumenter som handler om inspeksjon av enebolig
        - økonomiske konsekvenser
        - avslag på søknad
        """
        self.nyhetsverdige_eksempler = """
        IKKE NYHETSVERDIGE TEMAER: søknader om dispensasjon for oppføring av eneboliger, ferdigstillelsesattest for eiendom/bygg, søknad om byggetillatelse, involveringen av lokale myndigheter, korte og enkle administrative dokumenter, dokumenter som handler om andre kommuner enn Tromsø kommune vil automatisk bli irrelevante, 
        IKKE NYHETSVERDIGE TEMAER: oppdeling av eiendommer, avslag og endringer i søknader, krav til korrekt dokumentasjon, omfattende godkjennelsesprosess, inspeksjoner, små/insignifikante overskridelser av byggegrenser på 2 meter eller mindre, saker som krever nøye inspeksjon på grunn av potensielle problemer med strukturell integritet
        IKKE NYHETSVERDIGE TEMAER: byggeprosjekt i andre kommuner enn Tromsø kommune er ikke nyhetsverdige
        IKKE NYHETSVERDIGE TEMAER: søknader om byggetillatelse, involveringen av lokale myndigheter, spørsmål om tillatelse
        
        NYHETSVERDIGE TEMAER: dokumenter med mye frem og tilbake korrespondanse over flere år, dokumenter som diskuterer ulovligheter som er gjort, dokumenter som omtaler livsfarlige eksisterende elementer, hvis oppsummeringen er på mer enn 30 000 ord burde det anses som svært sannsynlig nyhetsverdig
        """
        self.large_project_definition = """
        EKSEMPLER PÅ PROSJEKTER SOM IKKE ER STORE: generelle forespørsler, bygging av en eller to eneboliger, oppdeling av eiendom og tomt, søknader om dispensasjon, forespørsel om ferdigattest, to etasjes bygninger, landmåling, etablering av matrikkelenhet
        
        EKSEMPLER PÅ PROSJEKTER SOM KAN KLASSIFISERES SOM STORE: konstruksjon av industribygg, konstruksjon av hotell, konstruksjon av større leilighetskompleks, prosjekter som har pågått i over 5 år med korrespondanse frem og tilbake
        """
        self.public_safety_definition = """
        EKSEMPLER PÅ PROSJEKTER SOM IKKE BEKYMRER OFFENTLIG SIKKERHET: søknad om dispensasjon, generelle søknader, bygging av enebolig, oppdeling av eiendom, uten å vise til lovbrudd er bekymringer for bygningsforskifter og lignende ikke av bekymring for offentlig sikkerhet, etablering av gangoverfelt eller skilt og trafikklys
        
        EKSEMPLER PÅ PROSJEKTER SOM BEKYMRER SEG FOR OFFENTLIG SIKKERHET: umiddelbar fare for at liv går tapt, naturlige katastrofer som kan sette liv i fare
        """
        self.newsworth_definition = """NYHETSVERDI DEFINISJON: 
        I denne konteksten ser vi på nyhetsverdi i et dokument som noe en journalist vil kunne trygt bruke tiden sin på.
        Nyhetsverdi kan måles på en skala, fra 0 til 100: 
        
        0 er absolutt ingen nyhetsverdi, dokumenter som indikerer at de tilhører et annet geografisk område enn Tromsø kommune og de umiddelbare nabo-kommunene vil lande her, om det er en søknad om tillatelse eller dispensasjon, søknader eller dokumenter som omtaler konstruksjon av enebolig, landmåling, eller en form for kommunikasjon som for eksempel forespørsel om å sende dokumentasjon, avslag på søknad om å bygge noe smått eller enkelt, dokumenter som snakker om at noe "potensielt" kan være farlig, eller lignende vil ikke være av interesse fordi det ikke har noe håndfast å vise til.
        
        Etterhvert som vi stiger oppover skalaen burde vi vurdere noe som potensielt nyhetsverdig, altså at det foreløpig ikke finnes nyhetsverdi i dokumentet og den identifiserte konteksten, men det kan bli nyhetsverdig hvis noe drastisk oppdages, eller om det må sendes mer informasjon for å gjøre det nyhetsverdig. Dokumenter som faller under denne kategorien skal likevel vurderes som IKKE NYHETSVERDIG.
        
        Til sist har vi toppen av skalaen, der noe er absolutt nyhetsverdig, altså en journalist burde undersøke saken så fort som mulig. Dette kan være om det er en sak som har gått over veldig lang tid, altså 5+ år, om det er snakk om livsfarlige oppdagelser som faktisk er oppdaget, veldig store prosjekter i form av hotell, næringsbygg, eller konstruksjon av et helt nytt nabolag, lovbrudd eller ulovligheter bør anses som nyhetsverdig med mindre annen informasjon overskygger dette, oppdagelser som kan sette mange menneskelige liv i fare er alltid nyhetsverdig som å oppdage farlig gass veldig nært travle områder. Saker der det er snakk om å hjelpe flyktninger eller mennesker i nød vil automatisk være nyhetsverdige.
        
        Dokumenter som kan bli til en nyhetssak med mer informasjon, men som i dette øyeblikk ikke har den informasjonen skal vurderes som IKKE nyhetsverdig. Det kan heller bli revurdert senere med den nye informasjonen.
        
        Dokumentet har blitt analysert, og relevante temaer har blitt identifisert. Om et tema ikke er relevant blir det sagt. Se kritisk på temaene identifisert i forhold til teksten, kan de temaene virkelig bidra noe som helst til å informere om noe fornuftig og faktisk relevant for byggesaken?
        """
        
    def _load_prompts(self, file_path):
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"Failed to load prompts from {file_path}: {e}")
            return {}
    
    
    def map_to_binary(self, text):
        positive_keywords = ['ja', 'yes', 'dette er et stort', 'det er bekymring for offentlig sikkerhet', 'absolutt', 'virker å være', 'kan dette potensielt være', 'there is some concern', 'dette klassifiseres som', 'diskuterer bekymringer knyttet til offentlig sikkerhet', 'kan klassifiseres som stort']
        negative_keywords = ['nei', 'no', 'dette er ikke et stort prosjekt', 'relativt', 'ikke bekymring for offentlig sikkerhet', 'middels']
        
        response_text = text.lower()
        
        if any(keyword in response_text for keyword in positive_keywords):
            return "ja."
        elif any(keyword in response_text for keyword in negative_keywords):
            return "nei."
        else:
            return "nei."


    def process_section(self, section, text):
        ident_prompt = section["identifisering"]["prompt"]
        regler = """"""
        if ident_prompt == "Er dette et stort prosjekt?":
            regler += self.large_project_definition
        elif ident_prompt == "Nevnes det bekymring for offentlig sikkerhet?":
            regler += self.public_safety_definition
        #print(regler)
        
        first_response = self.api_client.make_api_request([{"role": "system", "content": f"Hold svaret ditt til maksimum 50 ord. Følg disse reglene når du vurderer dokumentet: {regler}"},
                                                           {"role": "user", "content": f"{ident_prompt} {text}"}], " ")
        print(first_response, "FØRSTE")
        time.sleep(2)

        f_resp = self.map_to_binary(first_response)
        #print(f_resp, "ANDRE")
        
        responses = [first_response, ident_prompt]

        if f_resp.strip().lower() in section["identifisering"]["responses"][f_resp.strip().lower()]:
            decision = section["identifisering"]["responses"][f_resp.strip().lower()]
            if "ja" in decision:
                for prompt_key in section["ja"]:
                    prompt = section["ja"][prompt_key]
                    response = self.api_client.make_api_request([{"role": "system", "content": "Hold svaret ditt til maksimum 50 ord."},
                                                                 {"role": "user", "content": f"{prompt} {text}"}]," ")
                    responses.append(response)
            elif "nei" in decision:
                print("IKKE RELEVANT, MOVING ON...")
                konkat_svar = str(ident_prompt) + " ...nei, ikke relevant..."
                responses = [konkat_svar]
                '''
                for prompt_key in section["nei"]:
                    prompt = section["nei"][prompt_key]
                    response = self.api_client.make_api_request([{"role": "system", "content": "Hold svaret ditt til maksimum 50 ord."},
                                                                 {"role": "user", "content": f"{prompt} {text}"}]," ")
                    responses.append(response)'''
                #responses.append("IKKE RELEVANT.")
                #response = self.api_client.make_api_request([{"role": "user", "content": prompt}])
                #responses.append(response)
        return responses
    
    def general_questioning(self, section, text):
        ident_prompt = section["identifisering"]["prompt"]
        first_response = self.api_client.make_api_request([{"role": "system", "content": f"Hold svaret ditt til maksimum 50 ord. Dette er en veiledning fra redaksjonen i lokalavisa iTromsø: {self.nyhetsverdige_eksempler}"},
                                                           {"role": "user", "content": f"{ident_prompt} {text}"}], " ")
        print(first_response, "FØRSTE")
        time.sleep(2)
        f_resp = self.map_to_binary(first_response)
        
        responses = []
        if f_resp.strip().lower() in section["identifisering"]["responses"][f_resp.strip().lower()]:
            decision = section["identifisering"]["responses"][f_resp.strip().lower()]
            if "ja" in decision:
                for prompt_key in section["ja"]:
                    prompt = section["ja"][prompt_key]
                    response = self.api_client.make_api_request([{"role": "system", "content": "Hold svaret ditt til maksimum 50 ord."},
                                                                 {"role": "user", "content": f"{prompt} {text}"}]," ")
                    responses.append(response)
            else:
                for prompt_key in section["ja"]:
                    prompt = section["ja"][prompt_key]
                    response = self.api_client.make_api_request([{"role": "system", "content": "Hold svaret ditt til maksimum 50 ord."},
                                                                 {"role": "user", "content": f"{prompt} {text}"}]," ")
                    responses.append(response)
        return responses

    def handle_interaction(self, original_text):

        # Forhåndssjekk lengde for chunking
        ogt = original_text
        print(len(original_text))
        if len(original_text) > 36000:
            original_text = self.reduce_text(original_text)
            print(len(original_text))
        
        # Step 1: Identifiser kategorier, og spør mer detaljer rundt
        details_large_project = self.process_section(self.combined_prompts["large_project"], original_text)
        print(str(details_large_project))
        time.sleep(5)
        details_public_safety = self.process_section(self.combined_prompts["public_safety"], original_text)
        print(str(details_public_safety))

        # Step 2: Kombiner kategoriene som er identifisert
        kategorier_funnet = details_large_project + details_public_safety
        hel_kontekst = original_text + '\nKATEGORIER IDENTIFISERT I TEKSTEN: ' + str(kategorier_funnet) + '\nLENGDE PÅ ORIGINAL OPPSUMMERING: ' + str(len(ogt))
        print(hel_kontekst)

        # Step 3: Generelle spørsmål som kan hjelpe med anrikelse av dokumentet
        general_questions = self.general_questioning(self.combined_prompts["general_questions"], hel_kontekst)
        #general_questions.pop(0)
        #general_questions.pop(0)
        print(str(general_questions))
        all_tekst = hel_kontekst + '\n' + 'SVAR PÅ GENERELLE SPØRSMÅL: ' + str(general_questions)
        
        # Step 4: Send siste spørring for å hente ut nyhetsverdi
        news_assessment = self.assess_newsworth(self.combined_prompts["assessment"], all_tekst)

        assessed_kontekst = all_tekst + '\nFØRSTE VURDERING FRA CHATGPT' + str(news_assessment)
        
        revised_assessment = self.reassess_newsworth(self.combined_prompts["reassess"], assessed_kontekst)
        
        return revised_assessment
    
    def assess_newsworth(self, section, text):
        few_shot_examples = '''EKSEMPLER PÅ HVORDAN UTPUTT SKAL FORMATTERES
        PROMPT: Denne teksten virker veldig relevant for lokalsamfunnet i Tromsø kommune. I tillegg har det blitt identifisert flere relevante temaer, som at det er et stort prosjekt, fordi det er snakk om et næringsdrivende bygg, som berører mange mennesker i nærområdet som ikke er direkte involvert i prosjektet. Det blir også nevnt risiko for stenras, som er en naturkatastrofe, fordi det bygges rett ved siden av et fjell, og den voldsomme konstruksjonen kan utløse et skred.
        UTPUTT: Denne byggesaken er absolutt verdt tiden til en journalist i lokalavisa iTromsø, fordi det er snakk om et prosjekt som påvirker innbyggere som ikke har noe med prosjektet å gjøre. Det er også svært interessant at det er så stor risiko for stenras, noe som befolkningen i Tromsø kommune kan være interesert i å vite om.
        
        PROMPT: Dokumentet snakker som etableringen av et nytt nabolag i Tromsø kommune, der det skal bygges 15 nye hus. Dette kan klassifiseres som et stort prosjekt, men siden det ikke har kommet lengre enn planleggingsfasen er det ikke identifisert flere temaer. Det faktum at det fortsatt er tidlig i planleggingen gjør at det ikke er identifisert andre temaer i teksten.
        UTPUTT: Dette dokumentet kan kanskje være verdt å følge med på, og rapportere på det ved en senere anledning når det har utviklet seg mer.
        
        PROMPT: Dette dokumentet handler om fordelingen av to eiendommer, og forslag til å bygge ett hus på hver av eiendommene. Dette kan vurderes som et middels stort prosjekt, fordi det handler om to eneboliger, istedet for bare en. Det blir ikke nevnt noe annet som kan indikere tilstedeværelse av andre kategorier.
        UTPUTT: Denne saken vil ikke være verdt tiden til en journalist i lokalavisa iTromsø, fordi det bare er snakk om standard prosedyrer for inndeling av eiendom og etablering av eneboliger.
        '''
        first_prompt = section["identifisering"]["prompt"]
        response = self.api_client.make_api_request([{"role": "system", "content": f"Redaksjonen i lokalavisa iTromsø er interessert i å vite om dokumentet er verdt å bruke tid på å utforske videre, og de har disse veiledningene: {self.nyhetsverdige_eksempler}. {self.newsworth_definition}. Hold svaret til maksimum 50 ord. {few_shot_examples}. Her er en oversikt over absolutt ikke relevante temaer: {self.ikke_relevant}"},
                                                     {"role": "user", "content": f"{first_prompt} {text}"}]," ")
        print('FIRST RESPONSE ---------->   ',response)
        # Send til map_to_binary
        #assess_response = self.map_to_binary(response)
        #print(assess_response, 'HHHHHHHHHHHHOOOOOOOOOOOOOOOOLAAAAA')
        '''
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
        '''
        return response
    
    def reassess_newsworth(self, section, text):
        first_prompt = section["identifisering"]["prompt"]
        response = self.api_client.make_api_request([{"role": "system", "content": f"{self.newsworth_definition}. Gi meg et svar på maksimum 50 ord. Lokalavisa iTromsø er nødt til å prioritere hvilke saker de vil utforske, og vil ikke kaste bort den dyrebare tiden de har på helt normale prosedyre-saker. Dette er en liten oversikt over noen temaer som ikke er relevante: {self.ikke_relevant}. Dette er en veiledning for hva de vil klassifisere som verdt å se videre på: {self.nyhetsverdige_eksempler}"},
                                                     {"role": "user", "content": f"{first_prompt} {text}"}], " ")

        # Send til map_to_binary
        assess_response = self.map_to_binary(response)
        print(assess_response, 'HHHHHHHHHHHHOOOOOOOOOOOOOOOOLAAAAA')
        
        if assess_response.strip().lower() in section["identifisering"]["responses"][assess_response.strip().lower()]:
            decision = section["identifisering"]["responses"][assess_response.strip().lower()]
            if "ja" in decision:
                prompt = section["ja"]["prompt"]
                final_response = self.api_client.make_api_request([{"role": "system", "content": f"{self.newsworth_definition}. {self.nyhetsverdige_eksempler}. {self.relevante_tema}. {self.ikke_relevant}"},
                                                                   {"role": "user", "content": f"{prompt} {text} \n {response}"}]," ")
                siste_utputt = response + '\n' + final_response
            elif "nei" in decision:
                prompt = section["nei"]["prompt"]
                final_response = self.api_client.make_api_request([{"role": "system", "content": f"{self.newsworth_definition}. {self.nyhetsverdige_eksempler}. {self.relevante_tema}. {self.ikke_relevant}"},
                                                                   {"role": "user", "content": f"{prompt} {text} \n {response}"}]," ")
                siste_utputt = response + '\n' + final_response
        
        return siste_utputt
        
    
    def reduce_text(self, text):
        parts = self.split_text(text, 2)  # Splitting the text into 2 parts for this example, adjust as needed
        reduced_text_parts = []

        for part in parts:
            reduction_prompt = "Remove any fluff, meaning any unnecessary spaces, or repetition of sentences which does not add any additional value to the total context."
            reduced_part = self.api_client.make_api_request([{"role": "user", "content": f"{reduction_prompt} {part}"}], " ")
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
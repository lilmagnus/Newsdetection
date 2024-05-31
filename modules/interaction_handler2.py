# interaction_handler.py
import ast
import json
from api_client import APIClient
import time

class InteractionHandler:
    def __init__(self, prompts_file):
        self.api_client = APIClient()
        self.combined_prompts = self._load_prompts(prompts_file)
        self.temaer = """VEILEDNING FOR HVA SOM GJØR NOE RELEVANT OG HVA SOM GJØR NOE IRRELEVANT
        
        Følgende er en oversikt over temaer som IKKE utgjør noe relevanse eller nyhetsverdi:
        - søknad om dispensasjon
        - flere søknader om dispensasjon
        - oppmålingsprosedyre eller oppmålingsoperasjon
        - nabovarsel
        - rutinemessig prosess
        - søknad om eiendomsutvikling
        - eiendomsutviklingsprosess
        - søknader sendt på grunn av minimal overskridelse av byggegrenser
        - diskusjon om byggegrenser
        - forespørsel om ferdigattest
        - behov for uavhengig inspeksjon
        - etablering av gangfelt
        - etablering av fotgjengerfelt
        - samarbeid mellom offentlige instanser
        - søknad om byggetillatelse
        - søknad om godkjennelse for tilbygg
        - dokumenter som handler om inspeksjon av enebolig
        - administrative dokumenter som peker til flere temaer på denne listen
        - avslag på søknad
        - fradeling og dispensasjon for 1-2 eiendommer
        - etablering av gangfelt eller ny fartsgrense eller nytt fortau
        - dispensasjon for gesimshøyde og byggegrense
        - behov for tillatelse
        - potensielle feil eller mangler
        - indikasjon på at det foregår andre steder enn Tromsø kommune og omegn
        - LOKALE MYNDIGHETER BETYR INGENTING
        
        Følgende er en oversikt over temaer som utgjør relevanse og nyhetsverdi:
        - Flere enn 5 naboklager
        - Ulovlig byggearbeid
        - Husly for flyktninger
        - Flomfare
        - Prosesser som virker å gå frem og tilbake med tillatelser og avslag over lengre tid
        - Avvik fra godkjente tegninger
        - Lovovertredelser
        - adresseendringer på en hel gate
        - Lang historie med søknader om tillatelser
        - Store prosjekt der det nevnes å gjøre justeringer og endringer basert på tilbakemeldinger
        - Endringer som vil påvirke flere husstander, addresser eller nabolag
        - Administrative dokumenter som etterlyser mangler i søknader og forlengelser kan være relevant
        - Store endringer i hvordan et bygg skal brukes
        - Administrative prosesser kan være relevant om tidligere vurderinger indikerer det
        """
        self.nyhetsverdige_eksempler = """Oversikt over temaer som ikke er nyhetsverdige, og temaer som er nyhetsverdige.
        IKKE NYHETSVERDIGE TEMAER: søknader om dispensasjon for oppføring av eneboliger, ferdigstillelsesattest for eiendom/bygg, søknad om byggetillatelse, involveringen av lokale myndigheter, korte og enkle administrative dokumenter, dokumenter som handler om andre kommuner enn Tromsø kommune vil automatisk bli irrelevante, 
        IKKE NYHETSVERDIGE TEMAER: oppdeling av eiendommer, avslag og endringer i søknader, krav til korrekt dokumentasjon, omfattende godkjennelsesprosess, inspeksjoner, små/insignifikante overskridelser av byggegrenser på 2 meter eller mindre, saker som krever nøye inspeksjon på grunn av potensielle problemer med strukturell integritet
        IKKE NYHETSVERDIGE TEMAER: byggeprosjekt i andre kommuner enn Tromsø kommune er ikke nyhetsverdige
        IKKE NYHETSVERDIGE TEMAER: søknader om byggetillatelse, involveringen av lokale myndigheter, spørsmål om tillatelse
        
        NYHETSVERDIGE TEMAER: dokumenter med mye frem og tilbake korrespondanse over flere år, dokumenter som diskuterer ulovligheter som er gjort, dokumenter som omtaler livsfarlige eksisterende elementer som farlig gass eller flomfare, hvis oppsummeringen er på mer enn 30 000 ord burde det anses som svært sannsynlig nyhetsverdig, dokumenter som omtaler justeringer og viktige endringer basert på tilbakemeldinger, militær involvering
        """
        self.large_project_definition = """
        EKSEMPLER PÅ PROSJEKTER SOM IKKE ER STORE: 
        - generelle forespørsler, 
        - bygging av en eller to eneboliger, 
        - oppdeling av eiendom, 
        - søknader om dispensasjon, 
        - forespørsel om ferdigattest, 
        - to etasjes bygninger, 
        - landmåling, 
        - landmålingsprosedyre, 
        - etablering av matrikkelenhet,
        - grenseavklaring, 
        - etablering av matrikkelenhet,
        - behov for byggetillatelse
        
        EKSEMPLER PÅ PROSJEKTER SOM KAN KLASSIFISERES SOM STORE: 
        - konstruksjon av industribygg, 
        - konstruksjon av hotell, 
        - konstruksjon av større leilighetskompleks, 
        - endringer i addresser for en hel gate eller mer, 
        - prosjekter som har pågått i over flere år med korrespondanse frem og tilbake, 
        - lengde på original oppsummering over 15000
        """
        self.admin_definition = """For at et dokument skal være hovedsakelig administrativt må det inneholde søknader eller krav om noen av kategoriene gitt under.
        ADMINISTRATIVE DOKUMENTER MED MINDRE BETYDNING: 
        - søknad om dispensasjon, 
        - korrespondanser om søknader, 
        - forespørsel om å ettersende dokumenter, 
        - innvilgede tillatelser
        
        ADMINISTRATIVE DOKUMENTER MED STØRRE BETYDNING: 
        - lovbrudd, 
        - avvik fra godkjente planer, 
        - varsling om funn av farlige gasser eller liknende som vil true sikkerheten til offentligheten
        """
        self.nutgraf_definisjon = """En 'nut graf', som står for nutshell paragraf, defineres som poenget i teksten 'i et nøtteskall'. Målet med en nut graf er å fortelle leseren hva teksten handler om. Den inneholder 'hvem', 'hva', 'hvor', 'når', 'hvorfor', og 'hvordan'. En nut graf er aldri mer enn 2 setninger lang. Til sammen er det aldri mer enn 50 ord."""
        
        
    def _load_prompts(self, file_path):
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"Failed to load prompts from {file_path}: {e}")
            return {}
    
    
    def map_to_binary(self, text):
        positive_keywords = ['ja', 'yes', 'dette er et stort', 'det er bekymring for offentlig sikkerhet', 'absolutt', 'virker å være', 'kan dette potensielt være', 'there is some concern', 'dette klassifiseres som', 'diskuterer bekymringer knyttet til offentlig sikkerhet', 'kan klassifiseres som stort', 'temaet virker å være relevant', 'temaet er relevant']
        negative_keywords = ['nei', 'no', 'dette er ikke et stort prosjekt', 'relativt', 'ikke bekymring for offentlig sikkerhet', 'middels', 'ikke en god nutgraf', 'er ikke en']
        
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
        if ident_prompt == "Tenk ut høyt steg for steg og resonner. Er dette et stort prosjekt?":
            regler += self.large_project_definition
        elif ident_prompt == "Tenk ut høyt steg for steg og resonner. Er det indikasjoner i denne teksten som sier at dette er et administrativt dokument?":
            regler += self.admin_definition
        
        first_response = self.api_client.make_api_request([{"role": "system", "content": f"Hold svaret ditt til maksimum 50 ord. Følg disse reglene når du vurderer dokumentet: {regler}"},
                                                           {"role": "user", "content": f"Maks 50 ord. {ident_prompt} {text}"}])

        summert_first = self.api_client.make_api_request([{"role": "user", "content": f"Gi et kort og klart svar. Sier teksten 'ja' eller 'nei' i bunn og grunn?"}])
        time.sleep(1)
        f_resp = self.map_to_binary(summert_first)
        #f_resp = self.map_to_binary(first_response)
        
        responses = [first_response]
        forrige_prompt = ""

        if f_resp.strip().lower() in section["identifisering"]["responses"][f_resp.strip().lower()]:
            decision = section["identifisering"]["responses"][f_resp.strip().lower()]
            if "ja" in decision:
                for prompt_key in section["ja"]:
                    prompt = section["ja"][prompt_key]
                    #response = self.api_client.make_api_request([{"role": "system", "content": "Hold svaret ditt til maksimum 50 ord."},
                    #                                             {"role": "user", "content": f"{prompt} {text}"}])
                    response = self.api_client.make_api_request([{"role": "user", "content": f"{prompt} {forrige_prompt} \n{text}"}])
                    
                    forrige_prompt += response
                    responses.append(response)
            elif "nei" in decision:
                for prompt_key in section["nei"]:
                    prompt = section["nei"][prompt_key]
                    #response = self.api_client.make_api_request([{"role": "system", "content": "Hold svaret ditt til maksimum 50 ord."},
                    #                                             {"role": "user", "content": f"{prompt} {text}"}])
                    response = self.api_client.make_api_request([{"role": "user", "content": f"{prompt} {text}"}])
                    
                    responses.append(response)
        
        # En siste gjennomgang og sjekk av temaer
        tema_oppsummering = self.api_client.make_api_request([{"role": "user", "content": f"Maks 50 ord. Oppsummer det som blir sagt her: {responses}"}]) #  \nTEKST: {text}
        return ident_prompt + '\n' + tema_oppsummering

    def handle_interaction(self, original_text):

        # Forhåndssjekk lengde for chunking
        ogt = original_text
        print(len(original_text))
        if len(original_text) > 36000:
            original_text = self.reduce_text(original_text)
            print(len(original_text))
        
        # Step 1: Identifiser kategorier, og spør mer detaljer rundt
        details_large_project = self.process_section(self.combined_prompts["large_project"], original_text)
        print(str(details_large_project),'\n')
        time.sleep(1)
        
        details_admin = self.process_section(self.combined_prompts["administrative"], original_text)
        print(str(details_admin),'\n')

        # Step 2: Kombiner kategoriene som er identifisert
        kategorier_funnet = str(details_large_project) + '\n' + '\n' + str(details_admin)
        hel_kontekst = original_text + '\nKATEGORIER IDENTIFISERT I TEKSTEN: ' + kategorier_funnet + '\nLENGDE PÅ ORIGINAL OPPSUMMERING: ' + str(len(ogt))
        print(hel_kontekst,'\n')
        
        # Step 3: Lag et nutshell paragraph
        nut_graf = self.nutgraf(self.combined_prompts["nutsgraf"], hel_kontekst)
        nutshell_graf = "NUTSHELL PARAGRAF: " + nut_graf
        
        time.sleep(1)
        
        # Step 4: Send siste spørring for å hente ut nyhetsverdi
        news_assessment = self.assess_newsworth(self.combined_prompts["assessment"], hel_kontekst)
        print('\n', news_assessment)
        
        assessed_kontekst = hel_kontekst + '\nINITIELL VURDERING: ' + str(news_assessment)
        
        # Til slutt kom med en helhetlig vurdering av nutgrafen og resten av teksten, med kritiske øyne.
        revised_assessment = self.reassess_newsworth(self.combined_prompts["reassess"], assessed_kontekst)

        return nutshell_graf + '\n' + revised_assessment
    
    def assess_newsworth(self, section, text):
        first_prompt = section["identifisering"]["prompt"]

        response = self.api_client.make_api_request([{"role": "system", "content": f"{self.temaer}. \n{self.nyhetsverdige_eksempler}"},
                                                     {"role": "user", "content": f"{first_prompt} {text}"}])
        
        return 'Initiell vurdering: ' + response
    
    def reassess_newsworth(self, section, text):
        first_prompt = section["identifisering"]["prompt"]
        response = self.api_client.make_api_request([{"role": "system", "content": f"Maksimum 50 ord. Alt som skjer utenfor Tromsø kommune eller nærtliggende områder er automatisk ikke relevant."},
                                                     {"role": "user", "content": f"{self.temaer} \n{first_prompt} \n{text}"}])
        time.sleep(1)
        
        # Send til map_to_binary
        assess_response = self.map_to_binary(response)
        print('\n\n')
        
        time.sleep(1)
        
        if assess_response.strip().lower() in section["identifisering"]["responses"][assess_response.strip().lower()]:
            decision = section["identifisering"]["responses"][assess_response.strip().lower()]
            if "ja" in decision:
                prompt = section["ja"]["prompt"]
                final_response = self.api_client.make_api_request([{"role": "system", "content": f"Alt utenfor Tromsø kommune eller nærtliggende områder er helt irrelevant og IKKE nyhetsverdig. Maks 50 ord."},
                                                                   {"role": "user", "content": f"RETNINGSLINJER: {self.temaer} \n{prompt} ###{response}### \n///{text}///"}])
                siste_utputt = response + '\n' + final_response
            elif "nei" in decision:
                prompt = section["nei"]["prompt"]
                final_response = self.api_client.make_api_request([{"role": "system", "content": f"Alt utenfor Tromsø kommune eller nærtliggende områder er helt irrelevant og IKKE nyhetsverdig. Maks 50 ord."},
                                                                   {"role": "user", "content": f"RETNINGSLINJER: {self.temaer} \n{prompt} ###{response}### \n///{text}///"}])
                siste_utputt = response + '\n' + final_response
        
        return siste_utputt
        
    def nutgraf(self, section, text):
        first_prompt = section["nutshell"]["prompt"]
        response = self.api_client.make_api_request([{"role": "system", "content": f"{self.nutgraf_definisjon}"},
                                                     {"role": "user", "content": f"Alt som ikke er fra Tromsø kommune eller omegn er ikke relevant. {first_prompt} {text}"}])
        return response
    
    def reduce_text(self, text):
        if len(text) < 50000:
            parts = self.split_text(text, 2)
        elif len(text) > 50000 and (len(text) < 80000):
            parts = self.split_text(text, 4)
        elif len(text) > 80000:
            parts = self.split_text(text, 6)
        reduced_text_parts = []

        for part in parts:
            reduction_prompt = "Remove any fluff, meaning any unnecessary spaces, or repetition of sentences which does not add any additional value to the total context."
            reduced_part = self.api_client.make_api_request([{"role": "user", "content": f"{reduction_prompt} {part}"}])
            reduced_text_parts.append(reduced_part)
        
        return "".join(reduced_text_parts)

    def split_text(self, text, num_parts):
        if num_parts < 2:
            return [text]  # Ingen behov for å splitte

        part_length = len(text) // num_parts
        parts = []
        last_index = 0

        for _ in range(num_parts - 1):  # Split til num_parts
            split_index = text.rfind(' ', last_index, last_index + part_length) + 1  # Find space to avoid splitting words
            parts.append(text[last_index:split_index])
            last_index = split_index

        parts.append(text[last_index:])  # Legg til siste del
        return parts
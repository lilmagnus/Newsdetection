# interaction_handler.py
import ast
import json
from api_client import APIClient
import time

class InteractionHandler:
    def __init__(self, prompts_file):
        self.api_client = APIClient()
        self.combined_prompts = self._load_prompts(prompts_file)
        self.relevante_tema = """Dette er en oversikt over temaer som skal vurderes som nyhetsverdige:
        - Flere enn 5 naboklager
        - Ulovlig byggearbeid
        - Husly for flyktninger
        - Flomfare
        - Prosesser som virker å gå frem og tilbake med tillatelser og avslag over lengre tid
        - Avvik fra godkjente tegninger
        - Lang historie med søknader om tillatelser
        - Endringer som vil påvirke flere husstander, addresser eller nabolag
        - Administrative dokumenter som etterlyser mangler i søknader og forlengelser kan være relevant
        - Store endringer i hvordan et bygg skal brukes
        - Administrative prosesser kan være relevant om tidligere vurderinger indikerer det
        """
        self.ikke_relevant = """Følgende er en oversikt over temaer som ikke utgjør noe nyhetsverdi:
        - søknad om dispensasjon
        - flere søknader om dispensasjon
        - oppmålingsprosedyre eller oppmålingsoperasjon
        - nabovarsel
        - rutinemessig prosess
        - søknad om eiendomsutvikling
        - søknader sendt på grunn av minimal overskridelse av byggegrenser
        - diskusjon om byggegrenser
        - forespørsel om ferdigattest
        - administrative dokumenter som mangler direkte relevans til de identifiserte temaene
        - søknad om byggetillatelse
        - søknad om godkjennelse for tilbygg
        - dokumenter som handler om inspeksjon av enebolig
        - avslag på søknad
        - etablering av gangfelt eller ny fartsgrense eller nytt fortau
        - dispensasjon for gesimshøyde og byggegrense
        - LOKALE MYNDIGHETER BETYR INGENTING
        """
        self.temaer = """VEILEDNING FOR HVA SOM GJØR NOE RELEVANT OG HVA SOM GJØR NOE IRRELEVANT
        
        Følgende er en oversikt over temaer som IKKE utgjør noe relevanse eller nyhetsverdi:
        - søknad om dispensasjon
        - flere søknader om dispensasjon
        - oppmålingsprosedyre eller oppmålingsoperasjon
        - nabovarsel
        - rutinemessig prosess
        - søknad om eiendomsutvikling
        - eiendomsutviklingsprosess
        - adresseendringer på en hel gate
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
        - Lang historie med søknader om tillatelser
        - Store prosjekt der det nevnes å gjøre justeringer og endringer basert på tilbakemeldinger
        - Endringer som vil påvirke flere husstander, addresser eller nabolag
        - Administrative dokumenter som etterlyser mangler i søknader og forlengelser kan være relevant
        - Store endringer i hvordan et bygg skal brukes
        - Administrative prosesser kan være relevant om tidligere vurderinger indikerer det
        """
        self.temaer2 = """**Veiledning for klassifisering av nyhetsverdighet i byggesaker**

**Ikke nyhetsverdige temaer:**

*   Rutinemessige søknader om dispensasjon, inkludert mindre overskridelser av byggegrenser.
*   Standard oppmålingsoperasjoner og nabovarsler.
*   Enkelte søknader om eiendomsutvikling uten større konflikter eller samfunnspåvirkning.
*   Administrative prosesser som adresseendringer, enkle byggetillatelser, og ferdigattester.
*   Søknader og dokumenter som håndterer fradeling av 1-2 eiendommer uten ytterligere komplikasjoner.
*   Etablering av standard infrastruktur som gangfelt og fotgjengerfelt.

**Nyhetsverdige temaer:**

*   Saker med signifikant antall naboklager (flere enn fem) som indikerer bredere samfunnskonflikt.
*   Ulovlig byggearbeid og andre klare lovovertredelser.
*   Tiltak for å skaffe husly til flyktninger, gitt den humanitære og samfunnsmessige betydningen.
*   Saker med flomfare som kan påvirke sikkerheten og livskvaliteten for innbyggere.
*   Langvarige saker med hyppige tillatelser og avslag som indikerer systemiske problemer eller signifikant offentlig interesse.
*   Prosesser som innebærer vesentlige avvik fra godkjente tegninger eller tidligere forventninger.
*   Store prosjekter som inkluderer flere tilbakemeldingsrunder og endringer, spesielt de som påvirker flere nabolag eller husstander.
*   Saker som indikerer alvorlige mangler i søknader eller behov for vesentlige forlengelser.
*   Signifikante endringer i bygningens bruk som kan ha store konsekvenser for lokalsamfunnet.

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
        self.public_safety_definition = """
        EKSEMPLER PÅ PROSJEKTER SOM IKKE BEKYMRER OFFENTLIG SIKKERHET: søknad om dispensasjon, generelle søknader, bygging av enebolig, oppdeling av eiendom, uten å vise til lovbrudd er bekymringer for bygningsforskifter og lignende ikke av bekymring for offentlig sikkerhet, etablering av gangoverfelt eller skilt og trafikklys
        
        EKSEMPLER PÅ PROSJEKTER SOM BEKYMRER SEG FOR OFFENTLIG SIKKERHET: umiddelbar fare for at liv går tapt, naturlige katastrofer som kan sette liv i fare
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
        self.newsworth_definition = """NYHETSVERDI DEFINISJON: 
        I denne konteksten ser vi på nyhetsverdi i et dokument som noe en journalist vil kunne trygt bruke tiden sin på.
        Nyhetsverdi kan måles på en skala, fra 0 til 100: 
        
        0 er absolutt ingen nyhetsverdi, dokumenter som indikerer at de tilhører et annet geografisk område enn Tromsø kommune og de umiddelbare nabo-kommunene vil lande her, om det er en søknad om tillatelse eller dispensasjon, søknader eller dokumenter som omtaler konstruksjon av enebolig, landmåling, eller en form for kommunikasjon som for eksempel forespørsel om å sende dokumentasjon, avslag på søknad om å bygge noe smått eller enkelt, dokumenter som snakker om at noe "potensielt" kan være farlig, eller lignende vil ikke være av interesse fordi det ikke har noe håndfast å vise til.
        
        Etterhvert som vi stiger oppover skalaen burde vi vurdere noe som potensielt nyhetsverdig, altså at det foreløpig ikke finnes nyhetsverdi i dokumentet og den identifiserte konteksten, men det kan bli nyhetsverdig hvis noe drastisk oppdages, eller om det må sendes mer informasjon for å gjøre det nyhetsverdig. Dokumenter som faller under denne kategorien skal likevel vurderes som IKKE NYHETSVERDIG.
        
        Til sist har vi toppen av skalaen, der noe er absolutt nyhetsverdig, altså en journalist burde undersøke saken så fort som mulig. Dette kan være om det er en sak som har gått over veldig lang tid, altså 5+ år, om det er snakk om livsfarlige oppdagelser som faktisk er oppdaget, veldig store prosjekter i form av hotell, næringsbygg, eller konstruksjon av et helt nytt nabolag, lovbrudd eller ulovligheter bør anses som nyhetsverdig med mindre annen informasjon overskygger dette, oppdagelser som kan sette mange menneskelige liv i fare er alltid nyhetsverdig som å oppdage farlig gass veldig nært travle områder. Saker der det er snakk om å hjelpe flyktninger eller mennesker i nød vil automatisk være nyhetsverdige.
        
        Dokumenter som kan bli til en nyhetssak med mer informasjon, men som i dette øyeblikk ikke har den informasjonen skal vurderes som IKKE nyhetsverdig. Det kan heller bli revurdert senere med den nye informasjonen.
        
        Dokumentet har blitt analysert, og relevante temaer har blitt identifisert. Om et tema ikke er relevant blir det sagt. Se kritisk på temaene identifisert i forhold til teksten, kan de temaene virkelig bidra noe som helst til å informere om noe fornuftig og faktisk relevant for byggesaken?
        """
        self.resonnering = """
        PROMPT: Kan den følgende teksten virkelig vurderes som relevant for en journalist i lokalavisa iTromsø? Gå steg for steg gjennom teksten, tenk ut høyt og forklar mens du leser gjennom.
        The document is a request for a pre-conference meeting regarding a new water treatment facility in Tromvik, Tromsø municipality, dated 2023-10-10. Norconsult, engaged by Tromsø municipality, recommends building a new facility at a higher location in the area due to technical reasons and the suitability of a former gravel pit. There is an urgent need for the new facility, and the stakeholders seek to discuss the further steps towards obtaining building permission during the pre-conference meeting.A pre-conference meeting was held on December 15, 2023 between Norconsult AS and Tromsø kommune regarding the Tromvik waterworks project, discussing the need for a new water treatment plant due to poor conditions of the existing facility. The project may require dispensation from the land-use plan and must adhere to regulations regarding proximity to waterways and roads. The municipality emphasized that the project's location may fall within a flood hazard area and that further approvals are needed from various authorities.On December 1, 2023, Marit Kure sent an email to Marianne Melbye and Trond Vestjord regarding a pre-conference meeting for the Tromvik vannverk project. The email included specific questions and requested possible meeting times for week 50. The message also emphasized confidentiality and disclaimer notice regarding the information shared.
        KATEGORIER IDENTIFISERT I TEKSTEN: Ja, det er tydelige indikasjoner i teksten på at dette dokumentet omhandler et stort prosjekt. Det nevnes at det er behov for en ny vannbehandlingsanlegg, tekniske årsaker for å plassere det høyere, dispensasjon fra reguleringsplanen og behov for godkjenninger fra ulike myndigheter.
        Det mest relevante temaet er at dokumentet omhandler bygging av en ny vannbehandlingsanlegg i Tromvik, Tromsø kommune, som krever godkjenninger og dispensasjon fra reguleringsplanen.
        ['Kan det finnes indikasjoner i denne teksten på at det er bekymring for offentlig sikkerhet i denne teksten? ...nei, ikke relevant...']
        Ja, tegn på at dette er et administrativt dokument inkluderer bruk av formelle språk, adresse til spesifikke organisasjoner og nevning av møter for å diskutere prosjektgodkjenning og tekniske spesifikasjoner. Disse elementene indikerer at dokumentet er en del av en organisatorisk prosess og ikke bare informasjon.
        Det mest relevante temaet i teksten er at dokumentet er en søknad om byggetillatelse for et nytt vannbehandlingsanlegg i Tromvik, Tromsø kommune.
        LENGDE PÅ ORIGINAL OPPSUMMERING: 1370 
        Initiell vurdering: Basert på de identifiserte kategoriene, spesielt behovet for et nytt vannbehandlingsanlegg i Tromvik, Tromsø kommune som krever godkjenninger og dispensasjon, er dokumentet verdt å vie tid til for lokalavisa iTromsø. Det adresserer viktige og relevante saker som berører lokalsamfunnet og har potensielle konsekvenser for offentlig sikkerhet.
        
        RESPONSE: Teksten handler om å bygge et nytt vannbehandlingsanlegg, fordi det nåværende anlegget kan være utsatt for flomfare. Det er identifisert at det er et stort prosjekt, og at det er en administrativ søknad om å bygge et nytt vannbehandlingsanlegg. 
        Siden det er snakk om at det nåværende vannbehandlingsanlegget er i dårlig stand, og kan være utsatt for flomfare. Det kommer også frem at det er en hastesak, noe som kan støtte under seriøsiteten i saken. 
        På bakgrunn av denne resonneringen vil jeg si at dette definitivt er relevant, og noe en journalist bør se nærmere på.
        
        PROMPT: Kan den følgende teksten virkelig vurderes som relevant for en journalist i lokalavisa iTromsø? Gå steg for steg gjennom teksten, tenk ut høyt og forklar mens du leser gjennom.
        Marianne Melbye from Tromsø kommune apologizes for the delay in processing Øyvind Emaus' application to move a fire barrier at Universitetssykehuset Nord-Norge. She requests an updated completion plan with dates for compliance statements from the designers and responsible contractors.Dokumentet er en tilbakemelding på en søknad om flytting av brannskille på eiendommen 124/86 Klokkargårdsbakken 13. Søknaden ble mottatt 19.05.2023 av NORCONSULT AS på vegne av UNIVERSITETSSYKEHUSET NORD-NORGE HF. Det ble funnet at søknaden mangler nødvendig informasjon, inkludert samtykke fra Arbeidstilsynet. Manglende informasjon må sendes innen 09.09.2023, ellers kan søknaden avvises. Hvis dokumentasjonen etterlyses, må tiltakshaver betale et mangelgebyr på kr. 2 700,-. Henvendelser kan rettes til saksbehandler Marianne Melbye.This is an application for a building permit for internal fire separation in a hospital building located in Tromsø, Norway. The project is called UNN C2-7 Fire Door and is being carried out by Universitetssykehuset Nord-Norge HF. The responsible applicant is Norconsult AS. The application includes details about the property, the nature of the project, and compliance with various regulations and requirements. It also includes information about access, water supply, drainage, and other relevant aspects of the project. The application includes signed declarations of responsibility and commitment to compliance with building regulations. Several attachments, including site maps and plans, are included with the application.Arbeidstilsynet gir samtykke til Universitetssykehuset Nord-Norge HF sin søknad om endring av bygningstekniske installasjoner i sykehusbygningen. Kommunen kan gi igangsettingstillatelse når samtykket foreligger. Det kan bli gjennomført etterkontroll og tilsyn for å sikre samsvar med kravene. Tiltakshaver må betale et gebyr for saksbehandlingen. Det er mulig å klage på vedtaket. Arbeidsgiver må informere arbeidsmiljøutvalget, verneombudet eller ansattes representant om brevet. Mer informasjon finnes på Arbeidstilsynet's nettside.Tromsø kommune gir tillatelse til flytting av brannskille i korridor C2-7 ved Universitetssykehuset Nord-Norge. Tillatelsen er basert på søknaden fra NORCONSULT AS og Universitetssykehuset. Klagefristen er tre uker. Kommunen vurderer at varsel til naboer kan unnlates. Tiltaket anses å være i tråd med plan- og bygningsloven og det gjeldende planverket. Gebyrer for saksbehandling vil bli fakturert til tiltakshaver.
        KATEGORIER IDENTIFISERT I TEKSTEN: Ja, teksten viser indikasjoner på at det dreier seg om et stort prosjekt knyttet til endring av bygningstekniske installasjoner, med involvering av ulike aktører som kommunen, Universitetssykehuset Nord-Norge HF og Norconsult AS. Det er også krav om dokumentasjon, samtykker og betaling av gebyrer knyttet til prosessen.
        Det mest relevante temaet i teksten er knyttet til et stort prosjekt med endring av bygningstekniske installasjoner og involvering av ulike aktører.
        ['Kan det finnes indikasjoner i denne teksten på at det er bekymring for offentlig sikkerhet i denne teksten? ...nei, ikke relevant...']
        Ja, det er indikasjoner i teksten som støtter at dette er et administrativt dokument. Det refereres til prosesser som søknader, tillatelser, gebyrer, samtykker, vedtak og klagefrister. Videre nevnes aktører som saksbehandlere, tiltakshavere, og organisasjoner som Universitetssykehuset og Norconsult. Typisk for administrativt språk og prosedyrer.
        Det mest relevante temaet er søknad om tillatelse for intern brannseparasjon på Universitetssykehuset Nord-Norge, som krever oppdatert plan og samtykke fra Arbeidstilsynet.
        LENGDE PÅ ORIGINAL OPPSUMMERING: 2498
        Initiell vurdering: Basert på de identifiserte kategoriene i teksten, spesielt med fokus på et stort prosjekt knyttet til endringer av bygningstekniske installasjoner med involvering av ulike aktører, er dette dokumentet av interesse for lokalavisa iTromsø. Det indikerer administrative prosesser, krav om samtykker, dokumentasjon og betalinger knyttet til et betydelig prosjekt ved Universitetssykehuset Nord-Norge HF.

        RESPONSE: Denne teksten handler om å flytte en brannbarriere ved Universitetssykehuset Nord-Norge. Det står skrevet at det er identifisert som et stort prosjekt, men jeg synes det egentlig viser mer indikasjon på en rutinemessig søknad, og påfølgende kommunikasjon virker også veldig uinteressant og normal.
        Den initielle vurderingen er veldig optimistisk, spesielt når det ikke er noe indikasjon på at noe faktisk har skjedd enda, det er fortsatt bare snakk om en søknad. 
        På bakgrunn av denne gjennomgangen, og faktum at hele dokumentet indikerer en normal søknad med normal kommunikasjon frem og tilbake vil dette ikke være av interesse for en journalist i lokalavisa iTromsø.
        
        PROMPT:
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
        if ident_prompt == "Er dette et stort prosjekt?":
            regler += self.large_project_definition
        #elif ident_prompt == "Nevnes det bekymring for offentlig sikkerhet?":
        #    regler += self.public_safety_definition
        elif ident_prompt == "Er det mer enn 15 administrative korrespondanser i den gitte teksten?":
            regler += self.admin_definition
        #print(regler)
        
        first_response = self.api_client.make_api_request([{"role": "system", "content": f"Hold svaret ditt til maksimum 50 ord. Følg disse reglene når du vurderer dokumentet: {regler}"},
                                                           {"role": "user", "content": f"Maks 50 ord. {ident_prompt} {text}"}])
        #print(first_response, "FØRSTE")
        time.sleep(2)

        f_resp = self.map_to_binary(first_response)
        #print(f_resp, "ANDRE")
        
        responses = [first_response]

        if f_resp.strip().lower() in section["identifisering"]["responses"][f_resp.strip().lower()]:
            decision = section["identifisering"]["responses"][f_resp.strip().lower()]
            if "ja" in decision:
                for prompt_key in section["ja"]:
                    prompt = section["ja"][prompt_key]
                    response = self.api_client.make_api_request([{"role": "system", "content": "Hold svaret ditt til maksimum 50 ord."},
                                                                 {"role": "user", "content": f"{prompt} {text}"}])
                    responses.append(response)
            elif "nei" in decision:
                print("IKKE RELEVANT, MOVING ON...")
                konkat_svar = str(ident_prompt) + " ...nei, ikke relevant..."
                responses = [konkat_svar]
                return responses
                '''
                for prompt_key in section["nei"]:
                    prompt = section["nei"][prompt_key]
                    response = self.api_client.make_api_request([{"role": "system", "content": "Hold svaret ditt til maksimum 50 ord."},
                                                                 {"role": "user", "content": f"{prompt} {text}"}])
                    responses.append(response)'''
                #responses.append("IKKE RELEVANT.")
                #response = self.api_client.make_api_request([{"role": "user", "content": prompt}])
                #responses.append(response)
        
        # En siste gjennomgang og sjekk av temaer
        mest_relevant_tema = self.api_client.make_api_request([{"role": "user", "content": f"Maks 20 ord. Av de identifiserte temaene, hvilket er det mest relevante i teksten? TEMAER: {responses} \nTEKST: {text}"}])
        return ident_prompt + '\n' + mest_relevant_tema
        # Siste sjekk med resonnering
        #final = self.combined_prompts["final_check"]
        #final_prompt = final["resonnering"]["prompt"]
        #parsed_response = self.api_client.make_api_request([{"role": "user", "content": f"###{regler}### {final_prompt} ///{text}\n{mest_relevant_tema}///"}])
        '''
        # Sjekk om det egentlig er relevant
        binary_last = self.map_to_binary(parsed_response)
        
        if "ja" in binary_last.strip().lower():
            return first_response + '\n' + mest_relevant_tema
            #responses.append(response)
            
        elif "nei" in binary_last.strip().lower():
            print("IKKE RELEVANT, MOVING ON...")
            konkat_svar2 = str(ident_prompt) + " ...nei, ikke relevant..."
            responses = [konkat_svar2]
            return responses'''
        #return ident_prompt + '\n' + parsed_response
    
    def general_questioning(self, section, text):
        ident_prompt = section["identifisering"]["prompt"]
        first_response = self.api_client.make_api_request([{"role": "system", "content": f"Hold svaret ditt til maksimum 50 ord. Dette er en veiledning fra redaksjonen i lokalavisa iTromsø: {self.nyhetsverdige_eksempler}"},
                                                           {"role": "user", "content": f"{ident_prompt} {text}"}])
        #print(first_response, "FØRSTE")
        time.sleep(2)
        f_resp = self.map_to_binary(first_response)
        
        responses = []
        if f_resp.strip().lower() in section["identifisering"]["responses"][f_resp.strip().lower()]:
            decision = section["identifisering"]["responses"][f_resp.strip().lower()]
            if "ja" in decision:
                for prompt_key in section["ja"]:
                    prompt = section["ja"][prompt_key]
                    response = self.api_client.make_api_request([{"role": "system", "content": "Hold svaret ditt til maksimum 50 ord."},
                                                                 {"role": "user", "content": f"{prompt} {text}"}])
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
        print(str(details_large_project),'\n')
        time.sleep(2)
        #details_public_safety = self.process_section(self.combined_prompts["public_safety"], original_text)
        #print(str(details_public_safety),'\n')
        #time.sleep(2)
        details_admin = self.process_section(self.combined_prompts["administrative"], original_text)
        print(str(details_admin),'\n')

        # Step 2: Kombiner kategoriene som er identifisert
        #kategorier_funnet = str(details_large_project) + '\n' + str(details_public_safety) + '\n' + str(details_admin)
        kategorier_funnet = str(details_large_project) + '\n' + '\n' + str(details_admin)
        hel_kontekst = original_text + '\nKATEGORIER IDENTIFISERT I TEKSTEN: ' + kategorier_funnet + '\nLENGDE PÅ ORIGINAL OPPSUMMERING: ' + str(len(ogt))
        print(hel_kontekst,'\n')

        # Step 3: Generelle spørsmål som kan hjelpe med anrikelse av dokumentet
        #general_questions = self.general_questioning(self.combined_prompts["general_questions"], hel_kontekst)
        #print(str(general_questions),'\n')
        #all_tekst = hel_kontekst + '\nSVAR PÅ GENERELLE SPØRSMÅL: ' + str(general_questions)
        #time.sleep(2)
        
        # Step 4: Lag et nutshell paragraph
        #nut_graf = self.nutgraf(self.combined_prompts["nutsgraf"], all_tekst)
        nut_graf = self.nutgraf(self.combined_prompts["nutsgraf"], hel_kontekst)
        nutshell_graf = "NUTSHELL PARAGRAF: " + nut_graf
        #print(all_tekst)
        time.sleep(1)
        
        # Step 5: Send siste spørring for å hente ut nyhetsverdi
        # Først se på nutgraf og original tekst
        #nut_og_ogt = original_text + '\n' + nutshell_graf
        #full_kontekst = all_tekst + '\n' + nutshell_graf
        #news_assessment = self.assess_newsworth(self.combined_prompts["assessment"], full_kontekst)
        #news_assessment = self.assess_newsworth(self.combined_prompts["assessment"], all_tekst)
        news_assessment = self.assess_newsworth(self.combined_prompts["assessment"], hel_kontekst)
        print('\n', news_assessment)
        #assessed_kontekst = all_tekst + '\nVURDERING AV NUTGRAF FRA CHATGPT : ' + str(news_assessment)
        #assessed_kontekst = all_tekst + '\nINITIELL VURDERING: ' + str(news_assessment)
        assessed_kontekst = hel_kontekst + '\nINITIELL VURDERING: ' + str(news_assessment)
        
        # Til slutt kom med en helhetlig vurdering av nutgrafen og resten av teksten, med kritiske øyne.
        revised_assessment = self.reassess_newsworth(self.combined_prompts["reassess"], assessed_kontekst)
        #return revised_assessment
        return nutshell_graf + '\n' + revised_assessment
    
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
        #response = self.api_client.make_api_request([{"role": "system", "content": f"Redaksjonen i lokalavisa iTromsø er interessert i å vite om dokumentet er verdt å bruke tid på å utforske videre, og de har disse veiledningene: {self.nyhetsverdige_eksempler}. {self.newsworth_definition}. Hold svaret til maksimum 50 ord. {few_shot_examples}. Her er en oversikt over absolutt ikke relevante temaer: {self.ikke_relevant}."},
        #                                             {"role": "user", "content": f"{first_prompt} {text}"}])
        #response = self.api_client.make_api_request([{"role": "system", "content": f"Definisjon å følge: {self.newsworth_definition}. Dette er en oversikt over temaer som ikke er relevante for en journalist å rapportere om: {self.ikke_relevant}. Dette er en oversikt over temaer som er relevante for en journalist å rapportere om: {self.relevante_tema}. Kan det virkelig finnes temaer i teksten som kan gjøre dette til relevant for en journalist? Hold svaret til maksimum 50 ord."},
        #                                             {"role": "user", "content": f"{first_prompt} {text}"}])
        response = self.api_client.make_api_request([{"role": "system", "content": f"{self.temaer}. \n{self.nyhetsverdige_eksempler}"},
                                                     {"role": "user", "content": f"{first_prompt} {text}"}])
        #time.sleep(1)
        #print('FIRST RESPONSE ---------->   ',response)
        # For å bare se på nutgraf trengs ikke dette under.
        # Kanskje verdt å se på om det kan inkluderes likevel.
        '''
        # Send til map_to_binary
        assess_response = self.map_to_binary(response)
        #print(assess_response, 'HHHHHHHHHHHHOOOOOOOOOOOOOOOOLAAAAA')

        if assess_response.strip().lower() in section["identifisering"]["responses"][assess_response.strip().lower()]:
            decision = section["identifisering"]["responses"][assess_response.strip().lower()]
            if "ja" in decision:
                prompt = section["ja"]["prompt"]
                #final_response = self.api_client.make_api_request([{"role": "system", "content": f"Du er en journalistassistent for den norske lokale avisen iTromsø, som rapporterer om nyhetsverdige byggesaker i Tromsø kommune. {self.newsworth_definition}"},
                #                                                   {"role": "user", "content": f"{prompt} {text}"}])
                final_response = self.api_client.make_api_request([{"role": "system", "content": f"Maks 50 ord. \n{self.newsworthy} \n{self.not_newsworthy} \n{self.temaer}"},
                                                                   {"role": "user", "content": f"{prompt} {text}"}])
            elif "nei" in decision:
                prompt = section["nei"]["prompt"]
                #final_response = self.api_client.make_api_request([{"role": "system", "content": "Du er en journalistassistent for den norske lokale avisen iTromsø, som rapporterer om nyhetsverdige byggesaker i Tromsø kommune."},
                #                                                   {"role": "user", "content": f"{prompt} {text}"}])
                final_response = self.api_client.make_api_request([{"role": "system", "content": f"Maks 50 ord. \n{self.newsworthy} \n{self.not_newsworthy} \n{self.temaer}"},
                                                                   {"role": "user", "content": f"{prompt} {text}"}])
        #print('FINAL RESPONSE ----------->   ', final_response)
        last_response = response + '\n' + final_response
        
        return last_response'''
        return 'Initiell vurdering: ' + response
    
    def reassess_newsworth(self, section, text):
        first_prompt = section["identifisering"]["prompt"]
        response = self.api_client.make_api_request([{"role": "system", "content": f"Maksimum 50 ord. Alt som skjer utenfor Tromsø kommune eller nærtliggende områder er automatisk ikke relevant."},
                                                     {"role": "user", "content": f"{self.temaer} \n{first_prompt} \n{text}"}])
        time.sleep(1)
        
        # Send til map_to_binary
        assess_response = self.map_to_binary(response)
        #print(assess_response, 'HHHHHHHHHHHHOOOOOOOOOOOOOOOOLAAAAA')
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
        
        #return response
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
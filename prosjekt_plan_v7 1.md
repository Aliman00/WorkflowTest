# Kompetanse- og HMS-portal
## Prosjektplan — Versjon 7

---

## Innholdsfortegnelse

1. Bakgrunn og målsetning
2. Kjernefunksjonalitet (Scope)
   - 2.1 Tilgangskontroll og roller (RBAC)
   - 2.2 Kurs, kompetansebevis og ansvarsområder
   - 2.3 HMS: «Lest og forstått»
   - 2.4 Stillingskrav med gjensidig bekreftelse
   - 2.5 Utstyrslogg (Uniform og PPE)
   - 2.6 Onboarding og offboarding
   - 2.7 Varslinger og rapportering
3. Teknisk arkitektur
4. Datamodell
5. API-endepunkter
6. Tidsplan
7. Risikovurdering
8. Fase 2 (etter MVP)

---

## 1. Bakgrunn og målsetning

Mange bedrifter sliter med å holde oversikt over lovpålagt HMS-opplæring, utløpsdatoer på kompetansebevis og utlevert verneutstyr. Tracking i Excel er upålitelig og mangler proaktive varslinger.

Dette prosjektet tar sikte på å bygge en webbasert portal — skreddersydd for én bedrift per installasjon — som automatiserer denne oppfølgingen. Løsningen vil sikre at bedriften overholder lovkrav gjennom dokumenterte signaturer, dynamisk kompetansestyring og automatiserte rutiner for nyansatte.

---

## 2. Kjernefunksjonalitet (Scope)

Prosjektet er strengt avgrenset til følgende syv hovedmoduler:

---

### 2.1 Tilgangskontroll og roller (RBAC)

Systemet settes opp for én bedrift (single-tenant), men har en avansert rollebasert tilgangskontroll (RBAC). Ulike brukere får tilgang til ulike moduler basert på sitt ansvarsområde.

**Eksempelroller:**

| Rolle | Beskrivelse |
|---|---|
| Admin | Full tilgang til hele systemet |
| Leder | Tilgang til sin avdelings ansatte, kompetanse og onboarding |
| Ansatt | Ser egen profil, egne oppgaver og HMS-dokumenter |
| Utstyrsansvarlig | Tilgang kun til utstyrsloggen (modul 2.5) |
| Personal Leder | Tilgang til brukeradmin, rapporter og onboarding-maler |

Roller er ikke hardkodet — de er samlinger av granulære tillatelser (f.eks. `competencies:read`, `equipment:write`). Bedriften kan selv definere egne roller med ønsket kombinasjon av tillatelser. Alle ruter i API-et sjekker tillatelser, ikke rollenavn.

Ansatte knyttes til én avdeling. Avdelinger er en enkel flat liste som bedriften definerer selv — for eksempel «Renholdsavdeling», «IKT-avdeling» eller «Lager». Det finnes ingen hierarkisk avdelingsstruktur; hvem som rapporterer til hvem styres av `manager_id`-kjeden på brukerobjektet. En ansatt tilhører én avdeling, men kan ha en leder fra en annen avdeling om nødvendig.

---

### 2.2 Kurs, kompetansebevis og ansvarsområder

Dette er «motoren» som definerer hva ansatte faktisk har lov til å gjøre.

Systemet håndterer en bred portefølje av kompetanse: interne kurs, formelle sertifikater og kompetansebevis (f.eks. varme arbeider, fallsikring, truckførerbevis). Bevisene knyttes opp mot ansvarsområder, slik at det er tydelig hvem som er godkjent for hvilke operasjoner i bedriften.

Bevisene er «levende» data. Systemet beregner automatisk status basert på dagens dato:

- **Gyldig** — utløpsdato er mer enn 60 dager frem i tid
- **Utløper snart** — utløpsdato er innen 60 dager
- **Utløpt** — utløpsdato er passert
- **Tilbakekalt** — beviset er manuelt satt som ugyldig, f.eks. fordi en ansatt har mistet en godkjenning midt i gyldighetsperioden

Statusen beregnes på nytt hver natt av en bakgrunnsjobb. Noen kompetansetyper har ingen utløpsdato (f.eks. et internt kurs som ikke fornyes) — disse forblir gyldige til de eventuelt fjernes manuelt. Et bevis kan settes til `REVOKED` manuelt av leder eller admin uavhengig av utløpsdato.

---

### 2.3 HMS: «Lest og forstått»

For å møte lovkrav om dokumentert opplæring.

Ledere kan laste opp eller lenke til viktige HMS-prosedyrer. Ansatte logger inn og bekrefter med en digital knapp («Lest og forstått»). Systemet loggfører hvem som har signert og nøyaktig når.

- **Versjonering:** Når et dokument oppdateres, økes versjonsnummeret og alle ansatte må signere på nytt. Tidligere signaturer bevares i loggen.
- **Kategorisering:** Dokumenter kan merkes med type — prosedyre, instruksjon, risikovurdering, policy, skjema eller annet — slik at de er lette å filtrere og finne igjen.
- **Obligatoriske dokumenter:** Noen dokumenter kan merkes som obligatoriske (`is_mandatory`). Systemet følger da aktivt opp at alle ansatte faktisk signerer, og inkluderer manglende signaturer i varslinger og rapporter.
- Signeringen lagres med tidsstempel og bruker-ID, slik at den er gyldig som dokumentasjon ved tilsyn (f.eks. fra Arbeidstilsynet).

---

### 2.4 Stillingskrav med gjensidig bekreftelse

For å sikre at riktig person har riktig kompetanse og ansvarsområde.

Systemet kan definere at en spesifikk stilling krever en gitt kombinasjon av kompetanse. Et krav kan enten være koblet til en definert kompetansetype eller formulert som fritekst — for eksempel «Gjennomført intern sikkerhetssamtale». Enten det ene eller det andre skal være utfylt.

Krav kan ha en tidsfrist angitt i antall dager fra tiltredelse. Hvis fristen passerer uten at kravet er bekreftet, settes status automatisk til `OVERDUE`.

For at et krav skal være oppfylt, må både den ansatte og lederen bekrefte at kompetansen er oppnådd.

**Bekreftelsesflyten:**
1. Ansatt logger inn og bekrefter at kravet er oppfylt (tidsstempel lagres)
2. Leder går inn og godkjenner samme krav (tidsstempel lagres)

**Statusverdier:**
- `Ikke bekreftet` — ingen av partene har signert
- `Bekreftet av ansatt` — ansatt har signert, venter på leder
- `Gjensidig bekreftet` — begge parter har signert
- `Forfalt` — fristen er passert uten at kravet er gjensidig bekreftet

Alle bekreftelsene inngår i revisjonsloggen.

---

### 2.5 Utstyrslogg (Uniform og PPE)

Hold oversikt over fysiske eiendeler som er utlevert til ansatte.

For hvert utlevert utstyr registreres:
- Utstyrsnavn og kategori (PPE / Uniform / Nøkkel / Annet)
- Utleveringsdato og forventet returdato
- Tilstandsbeskrivelse ved utlevering

**Offboarding-integrasjon:** Når en ansatt avsluttes, henter offboarding-modulen automatisk listen over ikke-returnert utstyr og inkluderer den i avslutningssjekklisten.

---

### 2.6 Onboarding og offboarding

Sikrer at ansatte får en trygg start og en ryddig avslutning.

**Onboarding:**
- Admin definerer gjenbrukbare maler (f.eks. «Standard onboarding», «Lagerarbeider onboarding»)
- Hver oppgave i malen har en ansvarlig part (ansatt eller leder) og en relativ tidsfrist (f.eks. «innen 3 dager etter startdato»)
- Malen tildeles en nyansatt, og systemet genererer en personlig sjekkliste med konkrete datoer

**Offboarding:**
- Når en ansatt avsluttes, genererer systemet en sjekkliste basert på offboarding-malen
- Listen henter automatisk data fra utstyrsloggen (modul 2.5), slik at man har full oversikt over hva som må leveres tilbake

---

### 2.7 Varslinger og rapportering

Systemet er proaktivt og støtter dokumentasjon ved tilsyn.

**E-postvarsler:**
- Sendes automatisk ved 60, 30 og 7 dager før utløp av et kompetansebevis
- Varselet går til den ansatte og nærmeste leder

**In-app-varsler:**
- En varslingsbjelke øverst i navigasjonen viser antall uleste varsler
- Varslene inkluderer utløpspåminnelser, ubekreftede stillingskrav og HMS-dokumenter som krever ny signering
- Hvert varsel kan ha en direktelenke til relevant side i appen (`action_url`)

**Rapporter:**
- Kompetansestatus per avdeling — filtrert på avdelingsdataene som er registrert i systemet
- Utstyrsoversikt per ansatt
- «Lest og forstått»-status for et gitt HMS-dokument

Alle rapporter kan eksporteres til PDF eller Excel/CSV for enkel dokumentasjon ved tilsyn.

---

## 3. Teknisk arkitektur

### Teknologistack

| Komponent | Teknologi | Hvorfor |
|---|---|---|
| Backend | Asp.Net Core Web Api | Håndterer forretningslogikk, utfører databaseoperasjoner og eksponerer REST-endepunkter. Bruker C# |
| Database | PostgreSQL | Åpen kildekode, enkel å sette opp lokalt med Docker, god integrasjon med Entity Framework Core via Npgsql. Støtter komplekse spørringer og transaksjoner |
| ORM | Entity Framework Core | Versjonskontroll for databaseskjema via migrasjoner, LINQ-spørringer og god integrasjon med ASP.NET Core |
| Frontend | Blazor Server | Komponentbasert server-side rammeverk med innebygd SignalR for sanntidsvarsler. Bruker C# |
| Stilsetting | MudBlazor | Godt dokumentert, mange komponenter og bygget for Blazor |
| Autentisering | Identity med JWT-autentisering | Enkel og sikker pålogging som er godt dokumentert og anbefalt av Microsoft |
| E-postvarsler | Twilio |  Pålitelig e-postlevering via REST API, enkel integrasjon med .NET og gratis tier for utvikling |
| SMS-varsler | Twilio | Enkelt REST API for utsending av SMS, godt dokumentert .NET SDK |
| Bakgrunnsjobber | Hangfire | Gratis og open-source med innebygd dashboard for overvåking av jobber. Enkel konfigurasjon mot PostgreSQL og automatisk retry ved feil |
| Fillagring | AWS S3 | Trygg og skalerbar lagring av HMS-dokumenter med innebygd versjonskontroll og sikker tilgang via pre-signerte URLs |
| Containerisering | Docker | Konsistent utviklingsmiljø lokalt via docker-compose. Forenkler deployment og sikrer at applikasjonen kjører likt på alle maskiner |
| Skytjenester | AWS (EC2, S3, RDS, ParameterStore) | Planlagt for produksjonsdeployment via CloudFormation (IaC). Gir skalerbar infrastruktur og sikker håndtering av secrets via Parameter Store |
| Testing | xUnit + Moq | Pålitelig og mye brukt testrammeverk for .NET. Moq brukes for mocking av avhengigheter i enhetstester, slik at service-logikk kan testes isolert fra database og infrastruktur |

> **Merk:** Teknologivalg er ikke endelig fastlagt og kan justeres underveis i prosjektet dersom det oppstår utfordringer med installasjon, konfigurasjon eller tidsbruk.

### Systemskisse (overordnet)

```
[ Nettleser ]
     │
     ▼
[ Blazor ]
     │  (HTTP / REST)
     ▼
[ Asp.Net Core Web Api ] ──────── [ PostgreSQL ]
     │
     ├── [ Hangfire ] ────── [ Twilio ] ────── (nattlig statusoppdatering, e-postvarsler) 
     │
     └── [ AWS S3 ] ────── (sky-lagring)
     │
     └── [ Twilio ] ────── (SMS/E-post innlogging)
```

### Viktige tekniske valg

- **Single-tenant:** All data tilhører én bedrift. Ingen `company_id` er nødvendig på hver tabell, noe som gir enklere spørringer og vedlikehold.
- **Soft delete:** Brukere deaktiveres, de slettes ikke. Historikk og revisjonslogg bevares (GDPR-hensyn).
- **JWT-autentisering:** Access token (15 min levetid) + Refresh token (7 dager).
- **Hangfire:** Kjører en nattlig jobb som sjekker utløpsdatoer og sender e-postvarsler/sms-varsler. Eget dashboard for å se fullførte jobber og egen retry-funksjonaltiet. Ingen ekstern køtjeneste nødvendig.
- **Tillatelsesbasert RBAC:** Roller er samlinger av tillatelser. API-ruter sjekker tillatelser (`competencies:write`), ikke rollenavn. Gjør det enkelt å lage nye roller uten kodeendringer.
- **AWS som skytejeneste:** Vi har tilgang til AWS Free Tier. Ved å benytte tjenester som EC2 for applikasjonshosting, S3 for fillagring og Parameter Store for sikker håndtering av secrets, får vi en produksjonsklar deployment med konsistent infrastruktur via CloudFormation (IaC).
- **Identity:** Identity gir oss ferdige User-modell vi kan tilpasse med egne egenskaper. Gir oss lockout-mekanisme og passord-hashing. Vi planlegger en passordløsinnlogging med access- og refresh-token.
- **Twilio:** Samme leverandør av tjenesten for SMS og epost. Sender sms eller epost ved innlogging og opprettelse av token par ved første innlogging eller innlogging etter utgåtte tokenpar.
- **Blazor Server:** Blazor Server gir enklere autentisering med tokens og enklere SignalR-oppsett. Ulempen igjen er skalering og at bruker alltid må ha tilkobling. Skalering løser vi med skytjenester.


### Prosjektstruktur
```
WorkOwl/
├── WC.Backend/                  ← ASP.NET Core Web API
│   ├── Common/                  ← BaseController og andre felles filer
│   │      
│   ├── Features/                ← Features med relevante modeller, DTO-er, kontrollere,
│   │   ├── Auth/                  services og repositories
│   │   ├── Competencies/
│   │   ├── Departments/
│   │   ├── Documents/
│   │   ├── Equipment/
│   │   ├── Notifications/
│   │   ├── Onboarding/
│   │   ├── Reports/
│   │   ├── Requirements/
│   │   ├── Roles/
│   │   └── Users/
│   │
│   └── Infrastructure/          ← AppDbContext, migrasjoner, Hangfire, Cache, Epost, SMS,
│                                  Security etc.
│
├── WC.Frontend/                 ← Blazor Server
│   ├── Pages/
│   ├── Components/
│   └── wwwroot/
├── WC.Shared/                   ← Delte klasser, f.eks. Result<T>, Result
│
├── WC.Tests/                    ← xUnit testprosjekt
│   ├── Unit/
│   ├── Integration/
│   └── Security/
│
└── docs/                        ← Prosjektdokumentasjon
    ├── kravspesifikasjon.docx
    ├── systemdesign.docx
    ├── testrapport.docx
    ├── api.md
    └── erd.png
```

---

## 4. Datamodell

Nedenfor beskrives de sentrale databasetabellene med kolonner og formål.

---

**Department** — Avdelinger i bedriften
- `id`, `name`, `description` (nullable)
- Enkel flat liste — bedriften definerer sine egne avdelinger (f.eks. «Renholdsavdeling», «IKT-avdeling»). Ingen hierarkisk struktur.

**User** — Brukere av systemet
- `id`, `email`, `password_hash`, `first_name`, `last_name`, `phone`
- `job_title`, `employment_type` (fast / vikariat / innleid)
- `is_active`, `deleted_at` (soft delete), `created_at`
- `manager_id` → User (FK til nærmeste leder)
- `department_id` → Department (FK, nullable)

**Role** — Roller definert for bedriften
- `id`, `name`, `description`, `created_at`

**Permission** — Granulære tillatelser
- `id`, `name` (f.eks. `equipment:read`), `description`

**RolePermission** — Kobling mellom rolle og tillatelse
- `role_id` → Role, `permission_id` → Permission

**UserRole** — Kobling mellom bruker og rolle
- `id`, `user_id` → User, `role_id` → Role, `assigned_by` → User, `assigned_at`

---

**CompetencyType** — Typer kompetansebevis (definert av admin)
- `id`, `name`, `description`
- `validity_months` (nullable — null betyr ingen utløpsdato)
- `is_internal` (bool — intern kurs vs. formelt bevis)

**Competency** — En ansatts faktiske kompetansebevis
- `id`, `user_id` → User, `type_id` → CompetencyType
- `issued_date`, `expiry_date` (nullable)
- `status` (ENUM: `VALID` / `EXPIRING_SOON` / `EXPIRED` / `REVOKED`)
- `document_url` (nullable), `notes`, `created_at`

**ResponsibilityArea** — Ansvarsområder (f.eks. «Truckoperatør sone A»)
- `id`, `name`, `description`

**UserResponsibility** — Hvilke ansvarsområder en bruker er godkjent for
- `id`, `user_id` → User, `area_id` → ResponsibilityArea
- `approved_by` → User, `approved_at`

---

**Document** — HMS-dokumenter for «Lest og forstått»
- `id`, `title`, `description`
- `file_url` (nullable), `external_url` (nullable)
- `version` (int, standard 1), `uploaded_by` → User, `created_at`
- `document_type` (ENUM: `PROSEDYRE` / `INSTRUKSJON` / `RISIKOVURDERING` / `POLICY` / `SKJEMA` / `ANNET`)
- `is_mandatory` (bool, standard false) — markerer om alle ansatte er pålagt å lese dette dokumentet

**DocumentAcknowledgement** — Signering av dokument
- `id`, `document_id` → Document, `user_id` → User
- `document_version` (int), `acknowledged_at`

---

**PositionRequirement** — Krav knyttet til en stilling
- `id`, `position_name`, `competency_type_id` → CompetencyType (nullable)
- `custom_requirement` (TEXT, nullable) — fritekst-krav som ikke passer en kompetansetype, f.eks. «Gjennomført intern sikkerhetssamtale». Enten `competency_type_id` eller `custom_requirement` skal være utfylt.
- `deadline_days` (INT, nullable) — antall dager fra tiltredelse til kravet må være bekreftet
- `description` (nullable), `created_by` → User, `created_at`

**RequirementConfirmation** — Gjensidig bekreftelse av stillingskrav
- `id`, `requirement_id` → PositionRequirement
- `employee_id` → User, `manager_id` → User
- `employee_confirmed_at` (nullable), `manager_confirmed_at` (nullable)
- `status` (ENUM: `PENDING` / `EMPLOYEE_CONFIRMED` / `MUTUALLY_CONFIRMED` / `OVERDUE`)

---

**Equipment** — Utlevert utstyr og PPE
- `id`, `user_id` → User, `item_name`
- `category` (ENUM: `PPE` / `Uniform` / `Nøkkel` / `Annet`)
- `issued_date`, `expected_return_date` (nullable), `returned_date` (nullable)
- `condition_notes`, `issued_by` → User

---

**OnboardingTemplate** — Mal for onboarding/offboarding
- `id`, `name`, `description`
- `type` (ENUM: `ONBOARDING` / `OFFBOARDING`), `is_active`

**OnboardingTask** — Oppgaver i en mal
- `id`, `template_id` → OnboardingTemplate, `title`, `description`
- `responsible_party` (ENUM: `EMPLOYEE` / `MANAGER`)
- `day_offset` (int — antall dager etter startdato)

**EmployeeOnboarding** — En ansatts aktive onboarding
- `id`, `user_id` → User, `template_id` → OnboardingTemplate
- `started_at`, `completed_at` (nullable)
- `status` (ENUM: `IN_PROGRESS` / `COMPLETED`)

**EmployeeTask** — Status på en konkret oppgave for en ansatt
- `id`, `onboarding_id` → EmployeeOnboarding, `task_id` → OnboardingTask
- `due_date`, `completed_at` (nullable), `notes`

---

**Notification** — In-app-varsler
- `id`, `user_id` → User, `title`, `message`
- `is_read` (bool), `created_at`
- `related_type` (nullable — f.eks. `competency`), `related_id` (nullable)
- `action_url` (VARCHAR, nullable) — direkte lenke til relevant side i appen
- `read_at` (TIMESTAMP, nullable) — tidsstempel for når varslet ble lest

**AuditLog** — Revisjonslogg
- `id`, `user_id` → User, `action`, `entity_type`, `entity_id`
- `details` (JSON), `created_at`

---

## 5. Arbeidsmetodikk og regler for samarbeid

Vi har valgt Agile Scrum som vår arbeidsmetodikk med sprinter på 2 uker. 
Vi har ukentlige møter med veileder og daglige stand-ups over Teams. Daglig stand-ups er enten via melding eller møte på maks 15 minutter med følgende tre punkter:
- Hva ble gjort siden sist?
- Hva skal gjøres i dag?
- Er det noen hindringer?

Vi bruker Jira som prosjektstyringsverktøy for oppgavefordeling, 
historikk og progresjon. Kommunikasjon skjer løpende via Teams-chat.

### Roller
| Rolle | Person |
|---|---|
| Prosjektleder | Majlinda Lajci |
| Utvikler | Almin Colakovic |
| Utvikler | Fredrik Magee |

### Sprintstruktur
Hver sprint starter med sprintplanlegging der oppgaver hentes fra 
backloggen og fordeles i Jira. Hver andre fredag avsluttes sprinten 
med en sprint-review og retrospekt der vi vurderer hva som fungerte 
og hva som kan forbedres. Ved sprint-avslutning merges `develop` inn i `main`.

### Definition of Done
En oppgave regnes som ferdig når:
- Koden er implementert og kompilerer uten feil
- Relevante tester er skrevet og passerer
- Koden er gjennomgått og godkjent via Pull Request
- Swagger-dokumentasjon er oppdatert ved nye endepunkter
- Koden er merget inn i `develop`

### Utviklingsflyt

Hver oppgave følger denne flyten fra start til ferdig:

1. **Opprett branch** — lag en ny branch fra `develop` med riktig prefiks (`feature/`, `bugfix/` osv.)
2. **Skriv kode** — implementer funksjonaliteten i henhold til kravspesifikasjonen
3. **Manuell test** — verifiser at funksjonaliteten fungerer som forventet via Swagger UI
4. **Skriv tester** — skriv enhets- og/eller integrasjonstester som dekker happy path og viktigste feilscenarier
5. **Verifiser tester** — kjør alle tester lokalt og sørg for at de passerer (`dotnet test`)
6. **Push og opprett PR** — push branchen og opprett en Pull Request mot `develop` i GitHub
7. **Kodegjennomgang** — minst ett annet teammedlem gjennomgår og godkjenner PR-en
8. **Merge** — PR merges inn i `develop` etter godkjenning

### Versjonskontroll og samarbeidsregler

Prosjektet bruker Git og GitHub for versjonskontroll. All utvikling skjer i feature-branches som merges inn i `develop` via Pull Requests.

### Grenstrategi

| Gren | Formål |
|---|---|
| `main` | Stabil produksjonskode — merges kun fra `develop` ved sprint-slutt |
| `develop` | Aktiv utviklingsgren — alle PRs går hit |
| `feature/...` | Ny funksjonalitet |
| `bugfix/...` | Feilretting |
| `chore/...` | Oppsett, avhengigheter, konfig |

### Branch-navngivning

Branches navngis etter konvensjonen `feature/kort-beskrivelse`, for eksempel `feature/add-auth-jwt` eller `bugfix/department-null-reference`. Kebab-case og engelsk brukes konsekvent.

### Pull Requests og kodegjennomgang

- Minimum én godkjenning fra et annet teammedlem før merge, så ingen self-merge
- Alle PRs merges til `develop`, aldri direkte til `main`
- `main` og `develop` er beskyttet med branch protection rules i GitHub

### Commit-konvensjon

Vi følger Conventional Commits med følgende format: `<type>: <beskrivelse>`, for eksempel:

- `feat: add JWT authentication endpoint`
- `fix: resolve null reference in DepartmentService`
- `chore: add docker-compose for local MySQL`





## 6. Tidsplan

**Totalt: ~400 timer fordelt på 3 personer over 8 uker (~133 timer per person)**

| Uke | Fokus | Leveranse |
|---|---|---|
| 1 | Prosjektoppsett | Repo, containerisering, database, autentisering (JWT), brukeradmin |
| 2 | RBAC + Kompetansebevis | Rolle/tillatelse-system, avdelinger, kompetansemodul med statusberegning |
| 3 | HMS-dokumenter + Stillingskrav | Oppsett av S3, opplastning av filer, «Lest og forstått», gjensidig bekreftelse |
| 4 | Utstyr + Onboarding/Offboarding | Utstyrslogg, onboarding-maler, offboarding-sjekkliste |
| 5 | Varslingssystem + Audit-logging | Hangfire, e-postvarsler, in-app-varsler, revisjonsspor, Twilio |
| 6 | Rapportering + Dashboard | PDF/CSV-eksport, rolle-tilpasset dashboard |
| 7 | Testing + Sikkerhet | Enhetstester, integrasjonstester, sikkerhetsjekk |
| 8 | Deploy + Ferdigstilling | Produksjonssett, dokumentasjon, feilretting |

---

## 7. Risikovurdering

| Risiko | Sannsynlighet | Konsekvens | Tiltak |
|---|---|---|---|
| RBAC-kompleksitet tar mer tid enn planlagt | Medium | Høy | Start uke 1, bygg iterativt og unngå å vente til alt er «perfekt» |
| Onboarding/offboarding-modulen er for stor i scope | Medium | Medium | Prioriter MVP: enkle sjekklister uten avansert mal-logikk |
| Frontend tar lengre tid enn backend | Høy | Medium | Bruk ferdige UI-komponenter — unngå å bygge fra scratch |
| JWT-sikkerhet implementeres feil | Lav | Høy | Bruk anerkjent bibliotek, skriv dedikerte sikkerhetstester |
| 400 timer er knapt for full feature-dekning | Høy | Høy | Strikt MVP-fokus; utsett alt som ikke er kjernefunksjonalitet til fase 2 |
| Twilio SendGrid/SMS er kostbart ved høy volum | Lav | Lav | Gratis tier dekker utviklings- og testformål. Varsler sendes kun ved faktiske utløpshendelser |
| Hangfire-oppsett tar mer tid enn planlagt | Medium | Høy | Les godt opp på dokumentasjon før implementering |
| Hangfire-dashboard er åpent uten autentisering by default | Medium | Høy | Beskytt dashboard med autorisasjonsfilter i Program.cs før deployment |
| Skytjeneste (AWS) er vanskelig å sette opp innen fristen | Medium | Medium | Start deployment tidlig. Docker-compose fungerer som fallback for lokal demonstrasjon ved innlevering |
| AWS-kostnader overstiger Free Tier | Lav | Lav | Bruk Free Tier-tjenester og sett opp billing alerts i AWS |

---

## 8. Fase 2 (etter MVP)

Følgende funksjoner er bevisst utelatt fra prosjektplanen og planlagt for en eventuell videre fase:

- **Mobil-app** (iOS/Android) med push-varsler
- **Gap-analyse** — automatisk beregning av kompetansemangler per avdeling
- **Compliance-score** — prosentandel av ansatte som oppfyller alle stillingskrav
- **SSO / Azure AD-integrasjon** for enterprise-pålogging
- **Delegering av godkjenningsansvar** — vikarfunksjon når leder er fraværende
- **API-integrasjon mot lønnssystem** for automatisk synkronisering av ansattdata

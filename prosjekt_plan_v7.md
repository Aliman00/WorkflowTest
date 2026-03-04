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
| HR | Tilgang til brukeradmin, rapporter og onboarding-maler |

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
| Backend | Backend API | Håndterer forretningslogikk og eksponerer REST-endepunkter |
| Database | Relasjonsdatabase | Robust, gratis alternativer tilgjengelig, støtter komplekse spørringer |
| ORM | ORM med migrasjoner | Versjonskontroll for databaseskjema og enkel spørringsbygging |
| Frontend | Frontend SPA | Komponentbasert, responsivt brukergrensesnitt |
| Stilsetting | CSS-rammeverk | Rask styling med ferdige komponenter |
| Autentisering | JWT-autentisering | Enkel og sikker pålogging |
| E-postvarsler | SMTP | Enkel integrasjon, ingen ekstern tjeneste nødvendig |
| Bakgrunnsjobber | Bakgrunnsplanlegger | Kjører nattlige jobber uten ekstra infrastruktur |
| Fillagring | Lokal disk / sky-lagring | For opplastede HMS-dokumenter |
| Containerisering | Containerisering | Konsistent miljø, enkel deployment |

> **Merk:** Teknologivalg er ikke endelig fastlagt og kan justeres underveis i prosjektet.

### Systemskisse (overordnet)

```
[ Nettleser ]
     │
     ▼
[ Frontend SPA ]
     │  (HTTP / REST)
     ▼
[ Backend API ] ──────── [ Relasjonsdatabase ]
     │
     ├── [ Bakgrunnsplanlegger ] ──── (e-postvarsler, nattlig statusoppdatering)
     │
     └── [ Fillagring ] ────── (lokal disk / sky-lagring)
```

### Viktige tekniske valg

- **Single-tenant:** All data tilhører én bedrift. Ingen `company_id` er nødvendig på hver tabell, noe som gir enklere spørringer og vedlikehold.
- **Soft delete:** Brukere deaktiveres, de slettes ikke. Historikk og revisjonslogg bevares (GDPR-hensyn).
- **JWT-autentisering:** Access token (15 min levetid) + Refresh token (7 dager).
- **Bakgrunnsplanlegger:** Kjører en nattlig jobb som sjekker utløpsdatoer og sender e-postvarsler. Ingen ekstern køtjeneste nødvendig.
- **Tillatelsesbasert RBAC:** Roller er samlinger av tillatelser. API-ruter sjekker tillatelser (`competencies:write`), ikke rollenavn. Gjør det enkelt å lage nye roller uten kodeendringer.

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

## 5. API-endepunkter

Alle endepunkter krever gyldig JWT, med unntak av `/auth/login`. Tillatelser angis som korte strenger.

### Autentisering

| Metode | Sti | Beskrivelse |
|---|---|---|
| POST | `/auth/login` | Logg inn, returner access + refresh token |
| POST | `/auth/refresh` | Forny access token |
| POST | `/auth/logout` | Ugyldiggjør refresh token |
| GET | `/auth/me` | Hent innlogget brukers profil og tillatelser |

### Brukere

| Metode | Sti | Beskrivelse | Tillatelse |
|---|---|---|---|
| GET | `/users` | List alle aktive brukere | `users:read` |
| POST | `/users` | Opprett ny bruker | `users:write` |
| GET | `/users/{id}` | Hent én bruker | `users:read` |
| PUT | `/users/{id}` | Oppdater bruker | `users:write` |
| DELETE | `/users/{id}` | Deaktiver bruker (soft delete) | `users:delete` |

### Avdelinger

| Metode | Sti | Beskrivelse | Tillatelse |
|---|---|---|---|
| GET | `/departments` | List alle avdelinger | `users:read` |
| POST | `/departments` | Opprett ny avdeling | `users:write` |
| PUT | `/departments/{id}` | Oppdater avdeling | `users:write` |
| DELETE | `/departments/{id}` | Slett avdeling | `users:delete` |

### Roller og tillatelser

| Metode | Sti | Beskrivelse | Tillatelse |
|---|---|---|---|
| GET | `/roles` | List alle roller | `roles:read` |
| POST | `/roles` | Opprett ny rolle | `roles:write` |
| PUT | `/roles/{id}` | Oppdater rolle | `roles:write` |
| POST | `/roles/{id}/permissions` | Tildel tillatelser til rolle | `roles:write` |
| POST | `/users/{id}/roles` | Tildel rolle til bruker | `roles:write` |

### Kompetansebevis

| Metode | Sti | Beskrivelse | Tillatelse |
|---|---|---|---|
| GET | `/competencies` | List kompetansebevis (filtrerbart på bruker/status) | `competencies:read` |
| POST | `/competencies` | Registrer nytt bevis | `competencies:write` |
| GET | `/competencies/{id}` | Hent ett bevis | `competencies:read` |
| PUT | `/competencies/{id}` | Oppdater bevis | `competencies:write` |
| DELETE | `/competencies/{id}` | Slett bevis | `competencies:delete` |
| GET | `/competencies/expiring` | List bevis som utløper innen 60 dager | `competencies:read` |

### Ansvarsområder

| Metode | Sti | Beskrivelse | Tillatelse |
|---|---|---|---|
| GET | `/responsibilities` | List alle ansvarsområder | `responsibilities:read` |
| POST | `/responsibilities` | Opprett nytt ansvarsområde | `responsibilities:write` |
| POST | `/users/{id}/responsibilities` | Knytt bruker til ansvarsområde | `responsibilities:write` |

### HMS-dokumenter

| Metode | Sti | Beskrivelse | Tillatelse |
|---|---|---|---|
| GET | `/documents` | List alle HMS-dokumenter | `documents:read` |
| POST | `/documents` | Last opp eller lenke til dokument | `documents:write` |
| PUT | `/documents/{id}` | Oppdater dokument (øker versjon) | `documents:write` |
| POST | `/documents/{id}/acknowledge` | Signer «Lest og forstått» | `documents:acknowledge` |
| GET | `/documents/{id}/acknowledgements` | Se hvem som har signert | `documents:read` |

### Stillingskrav

| Metode | Sti | Beskrivelse | Tillatelse |
|---|---|---|---|
| GET | `/requirements` | List alle stillingskrav | `requirements:read` |
| POST | `/requirements` | Opprett nytt krav | `requirements:write` |
| GET | `/requirements/user/{id}` | Hent krav for én bruker | `requirements:read` |
| POST | `/requirements/{id}/confirm/employee` | Ansatt bekrefter krav | `requirements:confirm` |
| POST | `/requirements/{id}/confirm/manager` | Leder godkjenner krav | `requirements:approve` |

### Utstyrslogg

| Metode | Sti | Beskrivelse | Tillatelse |
|---|---|---|---|
| GET | `/equipment` | List alt utlevert utstyr | `equipment:read` |
| POST | `/equipment` | Registrer utlevering | `equipment:write` |
| PUT | `/equipment/{id}` | Oppdater utstyrspost | `equipment:write` |
| POST | `/equipment/{id}/return` | Marker utstyr som returnert | `equipment:write` |
| GET | `/equipment/user/{id}` | Hent utstyr for én bruker | `equipment:read` |

### Onboarding og offboarding

| Metode | Sti | Beskrivelse | Tillatelse |
|---|---|---|---|
| GET | `/onboarding/templates` | List alle maler | `onboarding:read` |
| POST | `/onboarding/templates` | Opprett ny mal | `onboarding:write` |
| POST | `/onboarding/assign` | Tildel mal til ansatt | `onboarding:write` |
| GET | `/onboarding/user/{id}` | Hent aktiv onboarding for bruker | `onboarding:read` |
| PUT | `/onboarding/tasks/{id}/complete` | Marker oppgave som fullført | `onboarding:complete` |

### Varsler

| Metode | Sti | Beskrivelse | Tillatelse |
|---|---|---|---|
| GET | `/notifications` | Hent varsler for innlogget bruker | — |
| PUT | `/notifications/{id}/read` | Marker ett varsel som lest | — |
| PUT | `/notifications/read-all` | Marker alle varsler som lest | — |

### Rapporter

| Metode | Sti | Beskrivelse | Tillatelse |
|---|---|---|---|
| GET | `/reports/competence` | Kompetansestatus per avdeling (filtrerbart på `department_id`) | `reports:read` |
| GET | `/reports/equipment` | Utstyrsoversikt | `reports:read` |
| GET | `/reports/acknowledgements` | «Lest og forstått»-status | `reports:read` |

Alle rapportendepunkter støtter query-parameteren `?format=pdf` eller `?format=csv`.

### Revisjonslogg

| Metode | Sti | Beskrivelse | Tillatelse |
|---|---|---|---|
| GET | `/audit-log` | Hent revisjonslogg (filtrerbart) | `audit:read` |

---

## 6. Tidsplan

**Totalt: ~400 timer fordelt på 3 personer over 8 uker (~133 timer per person)**

| Uke | Fokus | Leveranse |
|---|---|---|
| 1 | Prosjektoppsett | Repo, containerisering, database, autentisering (JWT), brukeradmin |
| 2 | RBAC + Kompetansebevis | Rolle/tillatelse-system, avdelinger, kompetansemodul med statusberegning |
| 3 | HMS-dokumenter + Stillingskrav | Opplasting, «Lest og forstått», gjensidig bekreftelse |
| 4 | Utstyr + Onboarding/Offboarding | Utstyrslogg, onboarding-maler, offboarding-sjekkliste |
| 5 | Varslingssystem + Audit-logging | Bakgrunnsplanlegger, e-postvarsler, in-app-varsler, revisjonsspor |
| 6 | Rapportering + Dashboard | PDF/CSV-eksport, rolle-tilpasset dashboard |
| 7 | Testing + Sikkerhet | Enhetstester, integrasjonstester, sikkerhetsjekk |
| 8 | Deploy + Ferdigstilling | Produksjonssett, dokumentasjon, feilretting |

### Teamfordeling

- **Person 1 — Backend-arkitekt:** Auth, RBAC, database, infrastruktur, revisjonslogg
- **Person 2 — Backend-domene:** Kompetanse, stillingskrav, onboarding/offboarding, rapporter
- **Person 3 — Frontend + integrasjoner:** Frontend SPA, UI, varslingssystem, dokumenthåndtering, deployment

---

## 7. Risikovurdering

| Risiko | Sannsynlighet | Konsekvens | Tiltak |
|---|---|---|---|
| RBAC-kompleksitet tar mer tid enn planlagt | Medium | Høy | Start uke 1, bygg iterativt — unngå å vente til alt er «perfekt» |
| Fillagring og opplasting er vanskelig å sette opp | Lav | Medium | Start med lokal disk; bytt til sky-lagring ved behov |
| Onboarding/offboarding-modulen er for stor i scope | Medium | Medium | Prioriter MVP: enkle sjekklister uten avansert mal-logikk |
| Frontend tar lengre tid enn backend | Høy | Medium | Bruk ferdige UI-komponenter — unngå å bygge fra scratch |
| JWT-sikkerhet implementeres feil | Lav | Høy | Bruk anerkjent bibliotek, skriv dedikerte sikkerhetstester |
| 400 timer er knapt for full feature-dekning | Høy | Høy | Strikt MVP-fokus; utsett alt som ikke er kjernefunksjonalitet til fase 2 |

---

## 8. Fase 2 (etter MVP)

Følgende funksjoner er bevisst utelatt fra MVP og planlagt for en eventuell videre fase:

- **Mobil-app** (iOS/Android) med push-varsler
- **Gap-analyse** — automatisk beregning av kompetansemangler per avdeling
- **Compliance-score** — prosentandel av ansatte som oppfyller alle stillingskrav
- **SSO / Azure AD-integrasjon** for enterprise-pålogging
- **Delegering av godkjenningsansvar** — vikarfunksjon når leder er fraværende
- **API-integrasjon mot lønnssystem** for automatisk synkronisering av ansattdata

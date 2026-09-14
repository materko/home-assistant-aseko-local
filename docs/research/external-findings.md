# Aseko – zistenia z externých zdrojov

Stav k 2026-09-13. Súhrn všetkého, čo sa dá o dátach z jednotiek Aseko zistiť mimo nášho repozitára,
porovnaný s tým, čo dnes dekódujeme (vetva `claude/decoder-profiles`, `docs/support_matrix.md`).

Tento dokument **nie je commitnutý**. Neobsahuje sériové čísla ani kód prevzatý z aplikácie Aseko – len zistené fakty.

## Obsah

1. [Najdôležitejšie zistenia](#1-najdôležitejšie-zistenia)
2. [Zdroje](#2-zdroje)
3. [Rozdelenie zariadení Aseko](#3-rozdelenie-zariadení-aseko)
4. [Aké hodnoty má ktorý model](#4-aké-hodnoty-má-ktorý-model)
5. [Protokoly a prenos](#5-protokoly-a-prenos)
6. [v7 rámec – 120 bajtov](#6-v7-rámec--120-bajtov)
7. [v8 rámec – text](#7-v8-rámec--text)
8. [RS485 rámec – 27 bajtov (dokument výrobcu)](#8-rs485-rámec--27-bajtov-dokument-výrobcu)
9. [Čo máme v kóde určite zle](#9-čo-máme-v-kóde-určite-zle)
10. [Čo máme v kóde asi zle – pozrieť](#10-čo-máme-v-kóde-asi-zle--pozrieť)
11. [Hodnoty z appky a cloudu, ktoré nečítame](#11-hodnoty-z-appky-a-cloudu-ktoré-nečítame)
12. [Rozsahy hodnôt](#12-rozsahy-hodnôt)
13. [Čo overiť na jednotke](#13-čo-overiť-na-jednotke)
14. [Otázky pre Aseko](#14-otázky-pre-aseko)
15. [Návrhy na vylepšenie](#15-návrhy-na-vylepšenie)

---

## 1. Najdôležitejšie zistenia

| # | Zistenie | Istota |
|---|---|---|
| 1 | **Kontrolný súčet v7 je vyriešený:** `byte[39] = 0xAA XOR byte[0..38]`, rovnako `byte[79]` pre 40..78 a `byte[119]` pre 80..118. | overené na 95 z 96 segmentov (32 unikátnych rámcov z dumpov, docs a testov) |
| 2 | **byte[13] na HOME/SALT má inú tabuľku bitov**, než máme my (0x02 = chyba korekcie času, 0x08 = prázdna vyrovnávacia nádrž). | dokument výrobcu + 2 nezávislé implementácie |
| 3 | **Algicíd na HOME je byte[29] bit 0x10, nie 0x20** (0x20 = flokulant). | dokument výrobcu + JS-DE-Tech |
| 4 | **byte[27] = 0xFE = odpojený snímač hladiny** (0xFF = nad 200 cm). My ukážeme 254 cm. | dokument výrobcu |
| 5 | Cloud/appka pozná **13 typov nastavení, 35 alarmov, 5 režimov backwash, 60 metrík** – väčšinu nečítame. | APK Aseko Live 5.0.4 |
| 6 | **Rozsahy nastavení (min/max) nikde nie sú** – ani v appke, ani v API, manuály majú len odporúčania. Výnimka: PROFI. | manuály, APK, API |
| 7 | **Žiadny zdroj nevie posielať príkazy do jednotky.** Všetky implementácie iba čítajú. | všetky zdroje |
| 8 | Delenie **HOME firmvér A/B je len naše** – cloud pozná len HOME a HOME_PRO a číslo firmvéru. | APK |

---

## 2. Zdroje

| Zdroj | Čo obsahuje | Dôveryhodnosť |
|---|---|---|
| [HA fórum – vlákno 767914](https://community.home-assistant.io/t/aseko-asin-aqua-pool-tech-data-stream-local-tcp-api-update-12-october-2025/767914) (92 príspevkov) | pôvod celej integrácie, návrhy mapovaní bajtov, odkazy | zmiešaná, pri každom tvrdení treba overiť |
| [gist KIDNORswe – RS485 protokol](https://gist.github.com/KIDNORswe/cedbb9a3350f2221c7e3fd4be3dbdb40) | 27-bajtový RS485 rámec, tabuľky chýb a relé pre AQUA/NET, HOME, SALT | vysoká – text výrobcu |
| [Loxone knižnica – Asin Aqua Net](https://library.loxone.com/detail/asin-aqua-net-pool-chlorine-and-ph-584/overview) | šablóna RS485, prílohy: pôvodný český dokument výrobcu (2020) + anglický preklad | vysoká – vzorový rámec má platný kontrolný súčet |
| [gist Ataman – ImHex vzor NET](https://gist.github.com/Ataman/412f007eb6f5ea300a80993d2f45df04) | štruktúra NET 120 bajtov (3×40) | nízka – odhady |
| [cguedel/ChemDoserProxy](https://github.com/cguedel/ChemDoserProxy) | C# proxy, parser v7, testovacie rámce HOME a NET | stredná – malý rozsah, reálna prevádzka |
| [JS-DE-Tech/hacs-aseko-asin-aqua-home-clf](https://github.com/JS-DE-Tech/hacs-aseko-asin-aqua-home-clf) | HA integrácia pre HOME CLF, mapuje bajty 0–115, validácie | stredná až vysoká, niektoré polia sám označuje ako neisté |
| [forum.logicmachine.net 6040](https://forum.logicmachine.net/showthread.php?tid=6040) | Lua skript pre RS485 | nízka |
| [Aseko integrátorské API – dokumentácia](https://api.aseko.cloud/api/v1/docs) | OpenAPI 3.0, 3 GET endpointy, enumy | vysoká – oficiálne |
| [dkk54/ha-aseko-cloud](https://github.com/dkk54/ha-aseko-cloud) | oficiálna HA integrácia cez cloud (autor podľa dokumentácie pracuje v Aseku) | vysoká pre cloud |
| [milanmeu/aioaseko](https://github.com/milanmeu/aioaseko) + HA core `aseko_pool_live` | GraphQL klient (dnes cudzie klienty blokované) | vysoká pre cloud |
| Aplikácia **Aseko Live 5.0.4** (Android, `dk54.ipoollive`) | GraphQL schéma, enumy modelov/variantov, ukážkové jednotky pre každý model, preklady | vysoká pre cloud; neobsahuje rámce |
| Manuály | HOME VS 2021/2022, staršia HOME, NET, AQUA (starší), OXYGEN, SALT (4 vydania), SALT NET, PROFI (2 vydania), ASIN Pool, HOME PRO 2025 | vysoká pre menu a nastavenia; rozsahy takmer chýbajú |

Odkazy na manuály:
[NET](https://www.pool-fritid.se/wp-content/uploads/2022/04/aseko-net-manual.pdf) ·
[HOME VS 2022](https://heatpumps4pools.com/myfiles/file/Manual-ASIN-Aqua-HOME-EN.pdf) ·
[HOME VS 2021 DE](https://www.poolpowershop.de/media/96/b3/3a/1656958052/anleitung_mida-sin-pro-komprimiert.pdf) ·
[starší HOME DE](http://schwimmbeckenrs.com/wp-content/uploads/2016/12/asinmanual.pdf) ·
[AQUA / AQUA NET starší](https://heatpumps4pools.com/myfiles/file/ASIN-Aqua-User-Manual-EN.pdf) ·
[OXYGEN](https://heatpumps4pools.com/myfiles/file/ASIN-Aqua-Oxygen-User-Manual.pdf) ·
[SALT VS 2022](https://www.pooluppsala.se/wp-content/uploads/2023/09/Aseko-Asin-Aqua-Salt-VS-Manual-EN-2022-01.pdf) ·
[SALT (manualslib)](https://www.manualslib.com/manual/3465211/Aseko-Asin-Aqua-Salt.html) ·
[SALT NET](https://www.manualslib.com/manual/4199143/Pollet-Pool-Group-Welldana-Aseko-Asin-Aqua-Salt-Net.html) ·
[PROFI](https://www.heatpumps4pools.com/myfiles/file/Manual-ASIN-Aqua-PROFI-en.pdf) ·
[PROFI 2021](https://www.welldana.com/media/wysiwyg/attachments/Manualer/Vandbehandling/Manual_2021_ENG_Asin_Aqua_Profi_30-207000.pdf) ·
[ASIN Pool](https://heatpumps4pools.com/myfiles/file/ASIN-Pool-User-Manual.pdf) ·
[HOME PRO 2025](https://www.manualslib.com/manual/4379641/Aseko-Asin-Aqua-Home-Pro.html)

---

## 3. Rozdelenie zariadení Aseko

### 3.1 Ako ich delí cloud (appka Aseko Live)

Štyri úrovne: **typ → model → variant → firmvér**.

| Úroveň | Hodnoty |
|---|---|
| `UnitType` | `AQUA`, `COVREX`, `HYBRID`, `REMOTE` |
| `UnitModel` | `HOME`, `HOME_PRO`, `NET`, `NET_NEW`, `NET_PLUS`, `PRO`, `PROFI`, `SALT`, `SALT_NET`, `SALT_PRO`, `ASEKO_ASIN`, `COVREX_ASIN`, `COVREX_DOSING` |
| Obchodný názov (`UnitBrandName`) | ASIN AQUA Home, Home Pro, Net, Net Plus, **Oxygen**, Pro, Profi, Salt, Salt eOX, Salt Hybrid, Salt NET, Salt Pro, Salt Pro eOX, ASIN Pool, Covrex |
| Variant (`UnitModelVariant`) | pozri 3.2; každý má v databáze číselný `code` |
| Firmvér | `firmwareVersion` pre variant, pri jednotke pole `firmware` (v ukážkových dátach číslo, napr. 16) |

Pozn.: **OXY nie je samostatný model** – v cloude je to obchodný názov „Oxygen“ (a „Home Oxy“ v ukážkových dátach).

### 3.2 Varianty a čo znamenajú

| Prípona | Význam | Podklad |
|---|---|---|
| `_CL` | sonda voľného chlóru (CLF) | ukážková jednotka „Home Clf“, „Net Clf“, „Salt Clf“ |
| `_RX` | sonda redox | „Home Redox“, „Net Redox“, „Salt Redox“ |
| `_MLD` | bez sondy, dávkovanie v ml/m³ za deň | ukážková jednotka „Net Dose“/„Home Oxy“: `Dose 10 ml/m³ day` |
| `_MLH` | bez sondy, dávkovanie v ml/m³ za hodinu | manuál NET: DOSE v ml/m³/h |
| SALT `_GH1/_GH2` | bez sondy, výroba chlóru nastavená v **g/h** | ukážková „Salt Clf (dose)“: `Dose 5 g/h`; API `clFreeRequiredUnit` môže byť `g/h` |
| SALT `…1` / `…2` | **nevieme** (generácia elektródy? veľkosť? pH−/pH+?) | žiadny podklad |

Úplný zoznam variantov:

- **HOME:** `AQUA_HOME_CL`, `_RX`, `_MLD`, `_MLH`
- **HOME PRO:** `AQUA_HOME_PRO_CL`, `_RX`, `_MLD`, `_MLH`
- **NET:** `AQUA_NET_CL`, `_RX`, `_MLD`, `_MLH`; `AQUA_NET_NEW_*` (4); `AQUA_NET_PLUS_*` (4)
- **Dávkovač:** `AQUA_DOSING_CL`, `_RX`, `_MLD`, `_MLH`
- **SALT:** `AQUA_SALT_CL1`, `CL2`, `RX1`, `RX2`, `GH1`, `GH2`
- **SALT NET:** `AQUA_SALT_NET_CL`, `_RX`, `_DOSE`
- **SALT PRO:** `AQUA_SALT_PRO_CL`, `_RX`, `_DOSE`; `AQUA_SALT_PRO_EOX_CL`, `_RX`, `_DOSE`
- **PROFI:** `AQUA_PROFI`
- **HYBRID:** `HYBRID_PRO`, `HYBRID_PRO_RX`
- **REMOTE:** `REMOTE_ASEKO_ASIN`, `REMOTE_COVREX_ASIN`

### 3.3 Ako ich delíme my (v7 byte[4])

| byte[4] | Náš model | Sonda | Cloud variant (odvodené) |
|---|---|---|---|
| `0x02` | HOME | CLF | `AQUA_HOME_CL` |
| `0x03` | HOME | REDOX | `AQUA_HOME_RX` |
| `0x04` | HOME | DOSE | `AQUA_HOME_MLD`/`MLH` |
| `0x05` | OXY | – (OXY Pure) | HOME Oxy / Oxygen |
| `0x09` | NET | CLF | `AQUA_NET_CL` |
| `0x0A` | NET | REDOX | `AQUA_NET_RX` |
| `0x0B` | NET | DOSE | `AQUA_NET_MLD`/`MLH` |
| `0x0D` | SALT | CLF | `AQUA_SALT_CL1`/`CL2` |
| `0x0E` | SALT | REDOX | `AQUA_SALT_RX1`/`RX2` (**tvoja jednotka**, všetkých 35 rámcov) |
| `0x0F` | SALT | DOSE | `AQUA_SALT_GH1`/`GH2` |
| `0x10` | PROFI (nepotvrdené) | CLF + REDOX (+ celkový Cl) | `AQUA_PROFI` |

V dokumente výrobcu k RS485 je typ jednotky kódovaný **inak** (bitovo): dolný polbajt `0x01` Cl sonda, `0x02` Rx, `0x04` DOSE bez sondy, `0x08` Sanosil; horný polbajt `0x10` AQUA NET, `0x20` SALT, `0x40` HOME, `0x80` PROFI. Nie je to v rozpore s v7 – je to iné kódovanie v inom rámci.

### 3.4 HOME firmvér A a B

- **Je to naše delenie**, cloud ho nepozná. Odvodili sme ho z byte[37] bitu 0x40 (A ho má vždy nastavený, B nikdy).
- Rozdiely A/B u nás: `filtration_schedule` (kódovanie byte[37]), `filtration_running` (B: stav v byte[37] 0x04), `service_menu_open` (na A ho nevieme čítať).
- `HOME_PRO` **nie je** náš firmvér B – Home Pro 2025 je nová jednotka na `aseko.cloud`, pravdepodobne už bez v7 rámca.
- Cloud pozná číslo firmvéru každej jednotky, ale verejné API ho nevracia a appka ho síce načíta, ale nezobrazí.

### 3.5 Novšie jednotky mimo nášho rozsahu

ASIN Pool, PRO, HOME PRO, NET NEW, NET PLUS, SALT PRO, SALT eOX, SALT Hybrid, Covrex – majú režimy (AUTO/ECO/PARTY/WINTER), kryt bazéna, svetlá, VS čerpadlo s profilmi, tlak a prietok filtra.
Posielajú dáta na `aseko.cloud` (manuál HOME PRO). Či používajú v8 textový rámec, alebo niečo iné, nevieme. Hlavička v8 `105` = SALT, `804` = NET.

---

## 4. Aké hodnoty má ktorý model

### 4.1 Legenda

| Značka | Význam |
|---|---|
| **V** | **vždy** – je to súčasť hardvéru, každá jednotka modelu to má |
| **K** | **podľa konfigurácie / príslušenstva** – závisí od variantu (sonda), zapojeného čerpadla, snímača, ventilu alebo zapnutej funkcie |
| **N** | **nastavenie** – hodnota, ktorú používateľ nastavuje v menu |
| **—** | **nikdy** – model to nemá |
| **?** | nevieme |

Pri každej bunke je to, čo o tom hovorí **manuál (M)**, **ukážková jednotka v appke (A)**, **naše zachytené rámce (R)** alebo **cloud API (C)**. Stĺpec „U nás“ hovorí, či to dekódujeme.

Ako sa konfigurácia prejaví v rámci:

- **sonda** → byte[4] (spodné bity) → či existuje `free_chlorine`, `redox` alebo `required_*_dose`
- **čerpadlo zapojené/nezapojené** → prietok čerpadla (bajty 95–103) je `0xFF`, keď port nie je nakonfigurovaný
- **spoločný port algicíd/flokulant na SALT** → byte[37] bit 0x80
- **funkcia vypnutá** → bajty nastavenia sú `0xFF` alebo `0` (napr. backwash každých 0 dní)
- **snímač chýba** → `0xFF` / `0xFFFF` / špeciálne hodnoty (vzduch `0xFE70`, hladina `0xFE`)

### 4.2 Merané hodnoty

| Hodnota | HOME | SALT | OXY | NET | PROFI | U nás | Podklad |
|---|---|---|---|---|---|---|---|
| pH | V | V | V | V | V | `ph` | M, A, R |
| voľný chlór (mg/l) | K (CL) | K (CL) | — | K (CL) | V | `free_chlorine` | variant; A |
| chlór mV (surový signál sondy) | K (CL) | K (CL) | — | K (CL) | V | `free_chlorine_mv` | R |
| redox (mV) | K (RX) | K (RX) | — | K (RX) | V | `redox` | variant; A; PROFI M |
| viazaný / celkový chlór | — | — | — | — | K (CLT) | nečítame | M PROFI, A „Profi CLT“ |
| teplota vody | V | V | V | V | V | `water_temperature` | M, A |
| teplota vzduchu | K (snímač) | K (snímač) | K | — | K | `air_temperature` len SALT | A (všetky okrem NET), R SALT |
| soľ (kg/m³) | — | V | — | — | — | `salinity` | M, A |
| výkon elektrolýzy (g/h) | — | V | — | — | — | `chlorine_production` | M, A |
| polarita elektródy | — | V | — | — | — | `electrode_polarity` | M, A |
| prietok vody k sondám | V | V | V | V | V | `water_flow_to_probes` | M, A, R |
| hladina vody (cm) | K (hladinomer) | K | K | — | K | `water_level` | M, A |
| solárna teplota | — | — (relé Solar používa teplotu vody) | — | — | — | — | A len PRO/Pool |
| tlak / prietok filtra | — | — | — | — | — | — | A len PRO |

### 4.3 Výstupy (čerpadlá, relé)

| Výstup | HOME | SALT | OXY | NET | PROFI | U nás | Podklad |
|---|---|---|---|---|---|---|---|
| filtračné čerpadlo | V | V | V | — v7 / stav v v8 | V | `filtration_running` | M, R |
| pH− čerpadlo | V | V | V | V | K (pH− alebo pH+) | `ph_minus_pump_running` | M |
| pH+ čerpadlo | K? (port „algicíd (pH+)“) | ? | ? | — | K (voľba pH+) | nečítame | M PROFI, RS485 dok. |
| chlórové čerpadlo | K (CL/RX variant) | — (elektrolýza) | — | K (CL/RX) | K (tekutý Cl) | `chlorine_pump_running` | M, A |
| OXY Pure čerpadlo | K (HOME Oxy) | — | V | — | — | `oxygen_pump_running` len OXY | A „Home Oxy“, M |
| algicíd | K (samostatný port) | K (spoločný port s flokulantom) | K | — | ? | `algaecide_pump_running` | A, M |
| flokulant | K | K (spoločný port) | K | — | K | `flocculant_pump_running` | A, M |
| elektrolýza | — | V | — | — | K (metóda „elektrolýza“) | `electrolysis_running` | M |
| ohrev (relé) | K (zapnutá regulácia) | K | K | — | K | `heating_running` | M, A |
| backwash ventil | K | K | K | — | K (relé 25) | `backwash_running` | M, A |
| ventil dopúšťania vody | K (hladinomer) | K | K | — | K | `refilling` | M, A |
| VS čerpadlo | K | K | K? | — | ? | `variable_speed_pump_enabled` | M |
| programovateľné relé (Solar/Timer) | ? | K | ? | — | — | nečítame | M SALT |

### 4.4 Nastavenia

| Nastavenie | HOME | SALT | OXY | NET | PROFI | U nás | Podklad |
|---|---|---|---|---|---|---|---|
| požadované pH | N | N | N | N | N | `ph_target` | M |
| požadovaný voľný chlór | N (CL) | N (CL) | — | N (CL) | N | `free_chlorine_target` | M |
| požadovaný redox | N (RX) | N (RX) | — | N (RX) | — | `redox_target` | M |
| dávka bez sondy | N (ml/m³/deň) | N (g/h, GH) | N (OXY Pure ml/m³/deň) | N (ml/m³/h) | — | `chlorine_dose_target`, `oxygen_dose_target` | M, A |
| dávka algicídu | N | N (spoločný port) | N | — | ? | `algaecide_dose_target` | M |
| dávka flokulantu | N | N (spoločný port) | N | — | N | `flocculant_dose_target` | M |
| požadovaná teplota vody | N (pri ohreve) | N | N | — (A: „control: false“) | N | `water_temperature_target` | M, A |
| filtračné časy 1 a 2 / nonstop | N | N | N | — | N | `filtration_period_1_start…stop2`, `filtration_schedule` | M |
| backwash každých N dní / čas / trvanie | N | N | N | — | N | `backwash_*` | M |
| objem bazéna | N | N | N | N | ? | `pool_volume` | M, A |
| oneskorenie po štarte | N | N | N | N | N (wait time) | `startup_delay` | M |
| oneskorenie po dávke | N | N | N | N | N | `dosing_delay` | M |
| koncentrácia pH− | N | N | N | ? | N | `ph_minus_concentration` | M |
| koncentrácia pH+ | ? | ? | ? | ? | N | nečítame | cloud `PH_PLUS_CONCENTRATION` |
| koncentrácia chlóru | ? | — | — | ? | N | nečítame | M PROFI, kandidát byte[111] |
| max. počet dávok pH | N | N | N | odvodené z tvrdosti vody (10/15/25) | ? | `max_ph_doses` | M, R |
| max. počet dávok chlóru | N | ? | ? | N (30) | ? | nečítame | M, cloud `DOSE_MAX_CL_COUNT` |
| max. hodinová dávka dezinfekcie | N (výrobne 20 ml/m³/h) | ? | ? | N (1–11 ml/m³/h) | N | nečítame | M, cloud |
| max. čas dopúšťania | N | N | N | — | N | `max_refill_time` | M |
| prahy hladiny (4) | N | N | N | — | N | `water_level_*` | M |
| regulácia ohrevu zap/vyp | N | N | N | — | ? | `heating_control_enabled` len HOME | M |
| časové okno ohrevu, ohrev podľa vonkajšej teploty | N | N | N | — | ? | nečítame | M HOME |
| protizámrazová ochrana zap/vyp + teplota | N | N (zimný režim) | N | — | ? | `freeze_protection_enabled` len HOME | M |
| typ VS čerpadla, rýchlosti | N | N | ? | — | ? | nečítame | M |
| snímač prietoku / vodomer zap/vyp | N | N | N | N | N | nečítame | M, cloud `WATER_FLOW_METER_ENABLED` |
| hladinomer zap/vyp | N | N | N | — | ? | nečítame | M |
| automatický letný čas | N | N | ? | ? | ? | nečítame | M |
| interval prepínania polarity elektródy | — | N (1 h / 24 h / 7 dní / ručne) | — | — | — | nečítame | M, cloud `ELECTRODE_SWITCHING_FREQUENCY` |
| hysterézia soli | — | N | — | — | — | nečítame | cloud `SALT_HYSTERESIS` |
| max. dni elektrolýzy | — | N | — | — | — | nečítame | cloud `ELECTROLYSIS_ON_MAX_DAYS` |
| časová elektrolýza (min/h) | — | N (SALT NET) | — | — | — | nečítame | M SALT NET |
| zimný režim: teplota, časovač, dávka algicídu | — | N | — | — | — | nečítame | M SALT |
| programovateľné relé (Solar/Timer + časy) | ? | N | ? | — | — | nečítame | M SALT |
| typ bazéna, tvrdosť vody | — | — | — | N | — | nečítame | M NET |
| dávkovanie mimo filtračných časov | ? | ? | ? | ? | ? | nečítame | cloud `DOSING_OUTSIDE_TIME_FRAME` |
| metóda dezinfekcie, smer pH−/pH+, max. čas dávky, interval ukladania/odosielania | — | — | — | — | N | nečítame | M PROFI |

### 4.5 Čo určite nemá

| Model | Určite nemá |
|---|---|
| **HOME** | soľ, elektrolýzu, celkový chlór |
| **SALT** | chlórové čerpadlo (chlór vyrába elektrolýza), OXY Pure, celkový chlór; algicíd a flokulant **naraz** (jeden spoločný port) |
| **OXY** | sondu voľného chlóru, redox, chlórové čerpadlo, soľ, elektrolýzu |
| **NET** | filtračné časy, backwash, ohrev a požadovanú teplotu, hladinu a dopúšťanie, teplotu vzduchu, algicíd, flokulant, elektrolýzu; na v7 aj dátum a čas (bajty 6–11 = `0xFF`) |
| **PROFI** | soľ (ak nie je nastavená metóda elektrolýza), OXY Pure, požadovaný redox (reguluje podľa voľného chlóru) |

### 4.6 Alarmy podľa modelu

| Alarm (cloud `StatusMessageType`) | HOME | SALT | OXY | NET | PROFI | U nás |
|---|---|---|---|---|---|---|
| `NO_WATER_FLOW_TO_PROBES` | ✓ | ✓ | ✓ | ✓ | ✓ | `alarm_no_flow_to_probes` |
| `TOO_MANY_PH_DOSING_ATTEMPTS_WITHOUT_CHANGE` | ✓ | ✓ | ✓ | ✓ | ✓ | `alarm_ph_dosing_ineffective` |
| `MAXIMUM_DISINFECTION_DOSE_EXCEEDED` | ✓ | ? | ? | ✓ | ✓ | `alarm_max_disinfection_dose` |
| `MAXIMUM_HOURLY_DISINFECTION_DOSE_EXCEEDED` | ✓ | ? | ? | ✓ | ✓ | nečítame |
| `PH_VALUE_CHANGING_TOO_RAPIDLY` | ✓ (M HOME) | ? | ? | ✓ (RS485 AQUA) | ? | `alarm_rapid_ph_change` |
| `WATER_LEVEL_TOO_LOW` / `_TOO_HIGH` | ✓ | ✓ | ✓ | — | ✓ | nečítame |
| `WATER_REFILLING_TIME_EXCEEDED` | ✓ | ✓ | ✓ | — | ✓ | nečítame |
| `CLOCK_MEMORY_BATTERY_LOW` | ✓ | ✓ | ✓ | ? | ? | nečítame |
| `BACKWASH_RUNNING` / `BACKWASH_ERROR` | ✓ | ✓ | ✓ | — | ✓ | `backwash_running` (len beh) |
| `PH_TOO_LOW_FOR_ELECTROLYSIS` | — | ✓ | — | — | ? | nečítame |
| `TOO_LITTLE_SALT_PER_HOUR` / `TOO_MUCH_SALT_PER_HOUR` | — | ✓ | — | — | — | nečítame |
| `SALT_HIGH_TEMPERATURE` | — | ✓ (nad 65 °C v jednotke) | — | — | — | nečítame |
| `ELECTROLYSIS_ON_TOO_MANY_DAYS` | — | ✓ | — | — | — | nečítame |
| `NO_DOSING_OUTSIDE_TIME_FRAME` | ? | ? | ? | ? | ? | nečítame |
| `NO_FLOW_FROM_DOSING_UNIT` | ? | ? | ? | ? | ? | nečítame |
| `HEATER_COOLING_FILTRATION` | ✓ | ✓ | ✓ | — | ? | nečítame |
| `WINTER_MODE_ACTIVATED` | ? | ✓ | ? | — | — | nečítame |
| kryt, EMS, VS typ nenastavený, solár, časovač, MCU chyba | len novšie jednotky (ASIN Pool, PRO) | | | | | — |

---

## 5. Protokoly a prenos

| | v7 | v8 | RS485 |
|---|---|---|---|
| Firmvér | ≤ 7.x | 8.x | všetky (displej) |
| Formát | binárny, 120 bajtov (3 × 40) | text `{v1 … }` | binárny, 27 bajtov |
| Port / linka | TCP 47524 | TCP 51050 | RS485, 57600 Bd, 8N1 |
| Cieľ v cloude | `pool.aseko.com:47524`, `ipool.aseko.com:47524`; Pool Remote `iremote.aseko.com` | `aseko.cloud` | externý displej |
| Interval | ~10 s (manuál) + hneď pri zapnutí/vypnutí čerpadla (NET, fórum #79) | ~10 s | 10 s |
| Kontrolný súčet | `0xAA XOR` na každý 40-bajtový segment | `crc16:` sekcia (nevalidujeme) | `0xAA XOR` bajtov 1..26 |

Ďalšie fakty:

- **Staršie jednotky** (OXYGEN, AQUA) posielajú na IP `217.11.244.139`, port `10004` (manuál).
- Modul v jednotke sa hlási ako **USR-K5/K6** (prevodník RS232 → IP), web na porte 80, výrobné prihlásenie admin/admin. Má aj HTTP režim (`1.php?`, `config.cgi`).
- NET občas pošle rámec rozdelený do viacerých TCP paketov (106 + 14, 112 + 128) alebo dva rámce naraz (240) – fórum #17, #62. Kontrolný súčet by pomohol takéto rámce overiť.
- Niektoré jednotky posielajú popri 120-bajtovom rámci aj **27-bajtový RS485 rámec** cez TCP (fórum #4, #12); iní to nevideli.
- **Do jednotky sa nedá nič poslať** – nikto nenašiel príkazový kanál. Verejné API je len GET. Jediný známy spôsob ovládania je externý dotykový displej cez RS485.
- Cloudové API:
  - **v1 REST** `pool.aseko.com` (stará web appka), `/api/V2/*` stará mobilná appka
  - **GraphQL** `graphql.acs.prod.aseko.cloud` – dnes odmieta cudzie klienty („use official integrator API“)
  - **integrátorské REST** `api.aseko.cloud/api/v1` – API kľúč, 3 GET endpointy, predplatné

---

## 6. v7 rámec – 120 bajtov

### 6.1 Štruktúra

```
segment 1: bajty   0– 39   hlavička 0–11, dáta 12–38, kontrolný súčet 39
segment 2: bajty  40– 79   hlavička 40–51, dáta 52–78, kontrolný súčet 79
segment 3: bajty  80–119   hlavička 80–91, dáta 92–118, kontrolný súčet 119

hlavička (na začiatku každého segmentu):
  +0..+3  sériové číslo (u32 big-endian)
  +4      typ jednotky + sonda
  +5      číslo segmentu / značka
  +6..+11 YY MM DD hh mm ss   (NET: 0xFF)

kontrolný súčet segmentu:
  sum = 0xAA
  for b in segment[0:39]: sum ^= b
  segment[39] == sum
```

Čísla (word) sú big-endian. `0xFF` / `0xFFFF` = nenastavené / nie je.

### 6.2 Mapa bajtov

Stĺpec **Stav**: ✅ potvrdené, 👁 videné, ❓ neoverené, ⚠️ podozrenie na chybu, 🆕 nové z externých zdrojov.

| Bajt | Význam | Škála / kódovanie | Modely | Stav | Poznámka / externý zdroj |
|---|---|---|---|---|---|
| 0–3 | sériové číslo | u32 | všetky | ✅ | |
| 4 | typ jednotky + sonda | pozri 3.3 | všetky | ✅ | |
| 5 | číslo segmentu | | všetky | 👁 | Ataman: „page“ |
| 6–11 | dátum a čas | YY MM DD hh mm ss | okrem NET | ✅ | opakuje sa v 46–51 a 86–91 |
| 12 | varovania dávkovania | 0x20 dezinfekcia, 0x40 pH | HOME | ✅ | 🆕 kandidát pre SALT error_2 (soľ, pH pod 6,7) |
| 13 | chyby | bitová maska | všetky | ⚠️ | pozri 9 a 10 – tabuľka výrobcu sa líši |
| 14–15 | pH | ÷100 | všetky | ✅ | displej ukazuje „<4“, „>10“ |
| 16–17 | voľný chlór ÷100, alebo redox mV | | podľa sondy | ✅ | |
| 18–19 | redox pri dvoch sondách | mV | PROFI | ❓ | |
| 20 | soľ | ÷10 kg/m³ | SALT | ✅ | |
| 20–21 | chlór mV | u16 | CLF sonda | ✅ | |
| 21 | výkon elektrolýzy | g/h | SALT | ✅ | manuál ukazuje 1 desatinné miesto – overiť mierku |
| 22 | bit 0x08 VS čerpadlo beží | | HOME, SALT | ✅ | marvin78 tipol elektrolýzu – nepravdepodobné |
| 23–24 | teplota vzduchu | i16 ÷10 °C; `0xFE70`/`0xFDC4` = bez snímača | SALT | ✅ | 🆕 JS-DE-Tech číta aj na HOME |
| 25–26 | teplota vody | ÷10 °C | všetky | ✅ | |
| 27 | hladina vody | cm; `0xFF` nad 200 cm; **`0xFE` odpojený snímač** | s hladinomerom | ✅ / ⚠️ | 🆕 0xFE neošetrujeme; JS-DE-Tech pripočítava offset 33 |
| 28 | prietok k sondám | `0xAA` áno, `0x00` nie | všetky | ✅ | |
| 29 | relé | pozri 6.3 | všetky | ✅ / ⚠️ | |
| 30–31 | 🆕 odpočet oneskorenia (s) | u16 | HOME, NET, SALT | ❓ | ChemDoserProxy `DelaySeconds`; u nás „mení sa“ |
| 32–36 | ? | | | ❓ | |
| 37 | príznaky | pozri 6.4 | HOME, SALT, OXY | ✅ | |
| 38 | ? | | | ❓ | |
| **39** | **🆕 kontrolný súčet segmentu 1** | `0xAA XOR 0..38` | všetky | ✅ | u nás „unknown checksum“ |
| 40–51 | hlavička segmentu 2 | | | ✅ | |
| 52 | požadované pH | ÷10 | všetky | ✅ | |
| 53 | požadovaný Cl ÷10 / redox ×10 / dávka | podľa sondy | všetky | ✅ | |
| 54 | požadovaný flokulant / algicíd | ml | HOME, SALT, OXY | ✅ | |
| 55 | požadovaná teplota vody | °C | okrem NET | ✅ | |
| 56–63 | filtračné časy 1 a 2 | hh mm | okrem NET | ✅ | |
| 64–67 | ? (NET 66–67 = teplota vody znova) | | | ❓ | |
| 68 | backwash každých N dní | 0 = vypnuté | okrem NET | ✅ | |
| 69–70 | čas backwash | hh mm | okrem NET | ✅ | |
| 71 | trvanie backwash | ×10 s | okrem NET | ✅ SALT | ⚠️ manuál HOME uvádza minúty |
| 72 | požadovaný algicíd (routovaný) | | SALT | ✅ | |
| 73 | ? | | | ❓ | LuckyG3000 tipol objem bazéna – neplatí |
| 74–75 | oneskorenie po štarte | s | všetky | ✅ / ⚠️ NET | 🆕 na NET rámci z ChemDoserProxy je `0xFFFF` |
| 76–77 | max. čas dopúšťania | s | s hladinomerom | ✅ SALT | |
| 78 | ? | | HOME | ❓ | 🆕 JS-DE-Tech: stavový bajt (34 filtrácia, 162 filtrácia + ohrev, 40 menu…) |
| **79** | **🆕 kontrolný súčet segmentu 2** | `0xAA XOR 40..78` | všetky | ✅ | Ataman tipol odpočet – nesprávne |
| 80–91 | hlavička segmentu 3 | | | ✅ | |
| 92–93 | objem bazéna | m³ | všetky | ✅ | |
| 95 | prietok pH− čerpadla | ml/min; `0xFF` nezapojené | všetky | ✅ | ChemDoserProxy: 95 = ChlorPure (slabý podklad) |
| 97 | ? (pH+?) | | | ❓ | ChemDoserProxy: pH− |
| 99 | prietok chlórového / OXY čerpadla | ml/min | HOME, NET, OXY | ✅ | |
| 101 | prietok flokulantu / algicídu (spoločný port) | ml/min | HOME, SALT, OXY | ✅ | |
| 102 | prah hladiny: nízky alarm | cm | s hladinomerom | ✅ | |
| 103 | prah hladiny: dopúšťanie ZAP **alebo** prietok algicídu | | | ⚠️ | na HOME a OXY čítame oboje – nemôže platiť oboje |
| 104 | prah hladiny: dopúšťanie VYP | cm | | ✅ | |
| 105 | prah hladiny: vysoký alarm | cm | | ✅ | |
| 106–107 | oneskorenie po dávke | s | všetky | ✅ | |
| 108 | 🆕 kandidát: max. hodinová dávka dezinfekcie | ml/m³/h | | ❓ | HOME 20, SALT 10; výrobne 20 |
| 109–110 | ? | | | ❓ | HOME 600, SALT 3000; JS-DE-Tech: oneskorenie po štarte – nesedí s 74–75 |
| 111 | 🆕 kandidát: koncentrácia chlóru % | | | ❓ | 15 na HOME aj SALT; JS-DE-Tech „concentration“ |
| 112 | koncentrácia pH− | % | HOME, SALT | ✅ | |
| 113 | 🆕 kandidát: max. dávok chlóru | | | ❓ | HOME 15 |
| 114 | 🆕 kandidát: max. dávok chlóru | | | ❓ | HOME 30; JS-DE-Tech tvrdí 114, ale na SALT sa mení |
| 115 | max. počet dávok pH | počet | okrem NET | ✅ SALT | overené zmenou 20 → 17 |
| 116–118 | ? | | | ❓ | |
| **119** | **🆕 kontrolný súčet segmentu 3** | `0xAA XOR 80..118` | všetky | ✅ | |

### 6.3 byte[29] – relé

| Bit | Dnes u nás | Dokument výrobcu RS485 | Poznámka |
|---|---|---|---|
| 0x01 | backwash (HOME/SALT…), **pH− na NET** | HOME: backwash; AQUA: pH− | súhlasí |
| 0x02 | dopúšťanie vody, **chlór na NET** | HOME: dopúšťanie; AQUA: Cl | súhlasí |
| 0x04 | ohrev | HOME: ohrev | súhlasí |
| 0x08 | filtrácia | HOME: filtrácia | súhlasí |
| 0x10 | elektrolýza (SALT), algicíd (OXY) | HOME: **algicíd (pH+)**; SALT: štart elektrolýzy | ⚠️ HOME algicíd máme 0x20 |
| 0x20 | algicíd/flokulant (SALT), flokulant (OXY), algicíd (HOME) | HOME: flokulant; SALT: algicíd | ⚠️ HOME |
| 0x40 | chlór (HOME, PROFI), ľavá polarita (SALT) | HOME: Cl; SALT: smer elektrolýzy | súhlasí |
| 0x80 | pH− | HOME: pH− | súhlasí |

ChemDoserProxy: `0x48` = ChlorPure, `0x88` = pH−, `0x28` = Floc+C (vrátane filtrácie 0x08). Pumpy podľa neho nebežia naraz – na NET potvrdil aj kidnor, na OXY u nás bežia naraz.

### 6.4 byte[37] – príznaky

| Bit | Význam | Modely |
|---|---|---|
| 0x01, 0x02 | filtračný rozvrh / prechodný stav editácie | HOME A, HOME B, SALT |
| 0x04 | menu otvorené / manuálne vypnutie | HOME B, SALT |
| 0x08 | regulácia ohrevu zapnutá | HOME A |
| 0x10, 0x20 | filtračná perióda 1, 2 zapnutá | HOME B, SALT |
| 0x40 | vždy nastavený na firmvéri A (a na SALT) | HOME A |
| 0x80 | protizámrazová ochrana (HOME A) / spoločný port = algicíd (SALT) | |

Kandidáti na ďalšie zapínače z menu (zatiaľ nenájdené): backwash zap/vyp, snímač prietoku, hladinomer, VS čerpadlo, letný čas, zimný režim na SALT.

---

## 7. v8 rámec – text

```
{v1 <serial> <typ> <?> <?> ins: … ains: … outs: … areqs: … reqs: … fncs: … mods: … flags: … crc16: <hex>}
```

- Hlavička: sériové číslo, typ (`804` = NET, `105` = SALT), `0`, `27` (význam neznámy).
- `-500` = sonda chýba.

| Sekcia | Index | Význam | Stav |
|---|---|---|---|
| `ins` | 0 | teplota vody ÷10 | ✅ |
| `ins` | 1–3 | `-500` = bez sondy | ✅ |
| `ins` | 8 | prietok k sondám | ✅ |
| `ins` | 12 | bit 0x80 = max. dávka dezinfekcie (Issue #151) | ✅ |
| `ins` | 13–15 | ? (dátum?) | ❓ |
| `ins` | 16, 17 | hodina, minúta | ✅ |
| `ains` | 0 (1 kópia) | pH ÷100 | ✅ |
| `ains` | 2 | ? (o ~5 menej ako redox) | ❓ |
| `ains` | 3 | redox ×10 | 👁 |
| `ains` | 6 (7 kópia) | redox mV | ✅ |
| `outs` | 2 | filtračné čerpadlo | ✅ |
| `outs` | 0, 1 alebo 8, 9 | pH− a chlórové čerpadlo | ⚠️ pozri 10 |
| `areqs` | 0 | požadované pH ÷10 | ✅ |
| `areqs` | 1 | požadovaný redox ×10 | ✅ |
| `areqs` | 2, 3, 5, 6, 10, 12, 19, 21 | ? | ❓ |
| `areqs` | 14 | objem bazéna | ✅ |
| `areqs` | 17 | oneskorenie po štarte (min) | ✅ |
| `areqs` | 18 | oneskorenie po dávke (min) | ✅ |
| `reqs` | 7 | požadovaný čas filtrácie (h) – pravdepodobne | 👁 |
| `fncs`, `mods`, `flags` | | ? (mods[0] = režim?) | ❓ |
| `crc16` | | kontrolný súčet – nevalidujeme | ❓ |

Pozn.: v7 dáva oneskorenia v **sekundách**, v8 v **minútach**. SALT na v8 máme len podľa hlavičky – rozloženie je prevzaté z NET a neoverené.

---

## 8. RS485 rámec – 27 bajtov (dokument výrobcu)

Nie je to náš rámec, ale **význam bitov je rovnaký** – preto je to najlepší podklad pre byte[13] a byte[29].

| Bajt | Význam |
|---|---|
| 0 | štart `0x0A` |
| 1 | typ jednotky (horný polbajt model, dolný sonda – pozri 3.3) |
| 2–3 | pH ÷100 (`0xFF` = chyba merania) |
| 4–7 | chlór / redox |
| 8–9 | teplota ÷10 |
| 10 | **error_1** |
| 11 | **error_2** (SALT) |
| 12–15 | sériové číslo |
| 16 | hladina (`0xFF` nad 200 cm, `0xFE` odpojený snímač) |
| 17–19 | požadované hodnoty (pH ÷10, Cl ÷10, Rx ×10) |
| 20 | hodiny bez filtrácie |
| 21 | hodinová dávka ml/m³/h |
| 22 | relé |
| 24 | obrazovka displeja |
| 26 | kontrolný súčet `0xAA XOR 1..25` |

**error_1:**

| Bit | HOME, SALT | AQUA / NET |
|---|---|---|
| 0x01 | prekročená hodinová dávka | 10/15/25 dávok pH bez zmeny |
| 0x02 | chyba korekcie času | 30 dávok Cl bez zmeny |
| 0x04 | žiadny prietok | žiadny prietok k sondám |
| 0x08 | prázdna vyrovnávacia nádrž | rýchla zmena pH, bez dávky pH |
| 0x10 | pretečenie vyrovnávacej nádrže | |
| 0x20 | nízka rýchlosť dopúšťania | |
| 0x40 | 20 dávok pH bez zmeny | |
| 0x80 | 30 dávok Cl bez zmeny | |

**error_2 (SALT):**

| Bit | Význam |
|---|---|
| 0x01 | prúd na elektródach nad 22 A |
| 0x02 | soľ pod 4 g/l |
| 0x04 | soľ pod 4,5 g/l |
| 0x08 | pH pod 7,3 |
| 0x10 | pH pod 6,7 – elektrolýza vypnutá |

**Relé SALT:** bit 4 štart elektrolýzy, bit 5 algicíd, bit 6 smer elektrolýzy.

---

## 9. Čo máme v kóde určite zle

Overené čítaním kódu alebo dát.

| # | Problém | Kde | Dôsledok | Oprava |
|---|---|---|---|---|
| 1 | **Nekontrolujeme kontrolný súčet v7** a bajty 39/79/119 vedieme ako neznáme. | `decoding/frame.py` `parse_v7`, `salt_device_analysis.md` | poškodený alebo zle poskladaný rámec sa dekóduje a vytvorí nezmyselné hodnoty | validovať `0xAA XOR` na každý segment; pri chybe rámec zahodiť a zapísať do diagnostiky |
| 2 | **`startup_delay` nemá kontrolu `0xFFFF`** (`frame.word(74)` bez `NOT_PRESENT`). | `decoders/startup_delay.py` | ak jednotka pošle `0xFFFF` (NET rámec z ChemDoserProxy), ukážeme 65535 s | pridať `0xFFFF → NOT_PRESENT` ako pri `max_refill_time` |
| 3 | **byte[27] = `0xFE` sa ukáže ako 254 cm.** | `decoders/water_level.py` (`byte_or_absent` rieši len `0xFF`) | pri odpojenom snímači falošná hladina | `0xFE → None` (neznáme) alebo samostatný stav „snímač odpojený“ |
| 4 | **`docs/doc_hex.md` je zastaraný** – desiatky známych bajtov ako „unknown“, `max_refill_time` na 94:95 (správne 76–77), poradie prietokov 95/97/99 opačne ako dekodér. | `docs/doc_hex.md` | zavádza každého, kto začína | nahradiť odkazom na support matrix, alebo generovať z profilov |
| 5 | **`support_matrix.md` obsahuje sériové čísla jednotiek z issues.** | evidence stringy v `decoding/profiles/v7.py` → generovaný `docs/support_matrix.md` | v rozpore s pravidlom „žiadne sériové čísla v docs“ | nahradiť popisom („HOME REDOX z Issue #151“) |
| 6 | **v8 čerpadlá: dekodér číta `outs[8]`/`outs[9]`, analýza uvádza kandidátov `outs[0]`/`outs[1]`.** | `decoders/ph_minus_pump_running.py`, `chlorine_pump_running.py` vs. `net_v8_device_analysis.md` | aspoň jedno z toho je zlé | zosúladiť a označiť ❓, kým nie je rámec s bežiacim čerpadlom |
| 7 | **byte[103] čítame na HOME aj ako prah hladiny, aj ako prietok algicídu.** | `water_level_refill_start`, `algaecide_flow_rate` na HOME/OXY | jedna z hodnôt je nezmysel (už to hovorí aj support matrix) | na HOME rozhodnúť podľa usporiadania prahov (low < on < off < high); manuál HOME ukazuje 60 ml/min pre čerpadlá, 33 nie je štandardný prietok |

---

## 10. Čo máme v kóde asi zle – pozrieť

| # | Podozrenie | Dnes u nás | Externý podklad | Ako overiť |
|---|---|---|---|---|
| 1 | **byte[13] 0x02 a 0x08 na HOME/SALT** | 0x02 = pH dávky (odvodené symetriou), 0x08 = rýchla zmena pH | dokument výrobcu, ChemDoserProxy, JS-DE-Tech: 0x02 = chyba korekcie času, 0x08 = prázdna nádrž, 0x40 = pH dávky, 0x80 = Cl dávky. Náš HOME rámec s `0x28` pri hladine pod alarmom sedí na „prázdna nádrž + pomalé dopúšťanie“. | dump pri alarme „príliš veľa dávok pH“ a pri nízkej hladine |
| 2 | **byte[13] 0x01 a 0x02 na NET** | 0x01 dezinfekcia, 0x02 pH | RS485 AQUA: 0x01 pH, 0x02 Cl. kidnor videl 2 pri zlyhaní chlórových dávok. | NET dump pri alarme |
| 3 | **byte[13] – bitová maska alebo posledná chyba?** | maska | kidnor (NET): pri druhej chybe sa 2 zmenilo na 1, nie na 3 | dve súčasné chyby |
| 4 | **Algicíd na HOME = byte[29] 0x10** | 0x20 (neisté) | dokument výrobcu + JS-DE-Tech: 0x10 algicíd (pH+), 0x20 flokulant | HOME dump pri bežiacom algicíde |
| 5 | **`startup_delay` na NET** | bajty 74–75 (👁) | NET rámec: 74–75 = `0xFFFF`, 109–110 = 600, 106–107 = 300 | porovnať NET dump s menu |
| 6 | **`backwash_duration` mierka na HOME** | ×10 s (potvrdené na SALT) | manuál HOME: „Backwash period 05“ v minútach | HOME dump + displej |
| 7 | **byte[78] na HOME** | poznámka o značke VS čerpadla | JS-DE-Tech: stavový bajt (34 filtrácia, 162 filtrácia + ohrev, 226 vypnuté, 64 standby, 40 menu) | HOME dumpy v rôznych stavoch |
| 8 | **`ph_minus_concentration` na HOME** – v `home_device_analysis.md` je hex `0f` (15) pri hodnote „5 %“ | | manuál: príklady 30 % (HOME/OXY) a 15 % (SALT) | skontrolovať riadok v analýze – pravdepodobne preklep |
| 9 | **`chlorine_production` mierka** | surový byte[21] = g/h | manuál: displej „14.9 g/h“ – môže byť ×10 | dump počas elektrolýzy + displej |
| 10 | **Poradie prietokov 95/97/99/101** | 95 pH−, 99 chlór | ChemDoserProxy: 95 ChlorPure, 97 pH−, 99 pH+, 101 Floc+C – ale všetky jeho testovacie hodnoty sú 60, takže nedokazuje nič | ponechať, u nás je potvrdenie z appky |
| 11 | **Súbežné čerpadlá na NET** | `net_device_analysis.md` pripúšťa 0x03 | kidnor + ChemDoserProxy: na NET nikdy naraz | len dokumentácia |
| 12 | **Teplota vzduchu na HOME** | na HOME `—` | JS-DE-Tech číta 23–24 aj na HOME; appka ukazuje teplotu vzduchu pri všetkých modeloch okrem NET | HOME dump so snímačom vzduchu |
| 13 | **`alarm_max_disinfection_dose` – dva rôzne alarmy v jednom** | byte[13] 0x01 alebo byte[12] 0x20 | cloud rozlišuje `MAXIMUM_DISINFECTION_DOSE_EXCEEDED` a `MAXIMUM_HOURLY_DISINFECTION_DOSE_EXCEEDED`; RS485 0x01 = hodinová dávka, 0x80 = 30 dávok Cl | alarmy rozdeliť, keď budú dumpy |
| 14 | **`max_ph_doses` na NET = `—`** | NET neprofilované | manuál AQUA/NET: 10/15/25 podľa tvrdosti vody – nastavuje sa nepriamo | NET dump pri zmene tvrdosti |

---

## 11. Hodnoty z appky a cloudu, ktoré nečítame

### 11.1 Nastavenia (`ConfigurationValueType`)

| Cloud | U nás | Kandidát v rámci |
|---|---|---|
| `POOL_VOLUME` | ✅ `pool_volume` | 92–93 |
| `DELAY_TIME_AT_STARTUP` | ✅ `startup_delay` | 74–75 |
| `DELAY_TIME_AT_DOSE` | ✅ `dosing_delay` | 106–107 |
| `PH_MINUS_CONCENTRATION` | ✅ `ph_minus_concentration` | 112 |
| `DOSE_MAX_PH_COUNT` | ✅ `max_ph_doses` | 115 |
| `DOSE_MAX_CL_COUNT` | ❌ | 113 alebo 114 |
| `DOSE_MAX_DISINFECTION_CONCENTRATION_PER_HOUR` | ❌ | 108 |
| `PH_PLUS_CONCENTRATION` | ❌ | ? |
| `DOSING_OUTSIDE_TIME_FRAME` | ❌ | bit v 37? |
| `ELECTRODE_SWITCHING_FREQUENCY` | ❌ (SALT) | ? |
| `ELECTROLYSIS_ON_MAX_DAYS` | ❌ (SALT) | ? |
| `SALT_HYSTERESIS` | ❌ (SALT) | ? |
| `WATER_FLOW_METER_ENABLED` | ❌ | bit v 37? |

### 11.2 Stavové hodnoty (`StatusValueType`)

| Cloud | U nás | Pozn. |
|---|---|---|
| `PH`, `CL_FREE`, `REDOX`, `SALINITY`, `ELECTROLYZER`, `WATER_TEMPERATURE`, `AIR_TEMPERATURE`, `WATER_FLOW_TO_PROBES`, `WATER_LEVEL`, `HEATING` | ✅ | |
| `DOSE` | ✅ (požadovaná dávka) | |
| `UPCOMING_FILTRATION_PERIOD` | čiastočne (`filtration_schedule` + časy) | cloud počíta najbližšiu periódu |
| `POOL_FLOW` (OVERFLOW / BOTTOM) | ❌ | trojcestný ventil BESGO – aj naša otvorená položka „Pool flow OVERFLOW“ na SALT |
| `SOLAR`, `SOLAR_TIMER`, `SOLAR_TEMPERATURE` | ❌ | programovateľné relé na SALT |
| `FILTRATION_PUMP_SPEED`, `PUMP_SPEED` (BOOST/HIGH/MEDIUM/LOW/OFF) | ❌ (máme len beží/nebeží) | VS čerpadlo |
| `MODE` (AUTO/ECO/OFF/ON/PARTY/WINTER) | — | len novšie jednotky |
| `FILTER_FLOW`, `FILTER_PRESSURE` | — | len PRO |
| `REDOX_PRO`, `CL_BOUNDED`, `CL_TOTAL_MV` | — | PRO/PROFI CLT |
| `COVER_STATE`, `LIGHTS_STATE` | — | ASIN Pool |

### 11.3 Filtrácia (`FiltrationConfiguration`)

- `nonstop` – máme
- `intervals[]` s `start`, `end`, `period` – máme (2 periódy)
- `intervals[].speed` (rýchlosť VS čerpadla v perióde) – ❌
- `intervals[].poolFlow` (OVERFLOW / BOTTOM v perióde) – ❌
- `speedBetweenFiltrationIntervals` (LOW / OFF) – ❌
- `requiredTime` (požadovaný čas filtrácie) – ❌ (v8 `reqs[7]`?)
- `limitedByWaterTemp` (čas filtrácie podľa teploty vody) – ❌

### 11.4 Backwash – 5 režimov

| Režim | Polia | U nás |
|---|---|---|
| raz za X dní | `oncePerXDays`, `start`, `takes` | ✅ |
| vybrané dni v týždni | `days{mon…sun}`, `start`, `takes` | ❌ |
| X-krát denne | `timesPerDay`, `delay`, `start`, `takes` | ❌ |
| podľa prietoku | `flowThreshold`, `takes` | ❌ |
| podľa tlaku | `pressureThreshold`, `oncePerXDays`, `start`, `takes` | ❌ |

Naše modely (HOME, SALT, OXY) majú podľa manuálov len „raz za X dní“. Ostatné sú pre PRO/ASIN Pool.

### 11.5 Dopúšťanie vody

- `levelMin`, `levelLow`, `levelHigh`, `levelMax`, `maxFillingTime`, `enabled` – máme (okrem `enabled`)
- `levelMeterType` (FLOAT / HYDROSTATIC) – ❌
- `litersPerMinute`, `totalLiters`, `totalTime` – počíta cloud (vodomer)

### 11.6 Spotrebný materiál (počíta cloud)

- kanister: `remaining` %, `volume`, `warningLevel`, `weekConsumption`
- hadička: `remaining` %, `remainingDays`
- elektróda: `remaining` %, `weekChlorineProduction`
- ohrev: `power`, `totalEnergy`, `totalTime`

Z rámca sa to dá odvodiť (prietok × čas behu čerpadla) – ChemDoserProxy to tak robí: `spotreba = prietok / 60 × sekundy behu`.

---

## 12. Rozsahy hodnôt

Manuály takmer nikde neuvádzajú min/max/krok. **[M]** = prečítané v manuáli, **[O]** = odporúčanie, nie limit, **[I]** = odvodené.

### 12.1 Merané hodnoty

| Hodnota | Rozsah / hranice | Zdroj |
|---|---|---|
| pH | displej „<4“ a „>10“ (NET „>9“); mimo = mimo rozsahu sondy | [M] HOME, SALT, NET |
| kalibrácia pH | 6,2–7,8; blokovaná pri rozdiele >1 | [M] HOME |
| voľný chlór | kalibrácia 0,3–5,0 mg/l; blokovaná pod 20 mV | [M] HOME |
| redox | test sondy: 475 mV pufor, musí ukázať ≥420 mV | [M] HOME |
| soľ | alarm pod 1,5 kg/m³; optimum 4; max 4 (TE-25) / 4,5 (Ti20) | [M] SALT |
| výkon elektrolýzy | max 20 g/h (TE-25 pri 4 g/l); displej 1 desatinné miesto | [M] SALT |
| teplota v jednotke SALT | nad 65 °C elektrolýza stop | [M] SALT |
| čerpadlá | 60 ml/min (OXY aj 10 ml/min) | [M] |
| validácia JS-DE-Tech | pH 0–14, Cl 0–20 mg/l, voda −5…45 °C, vzduch −30…50 °C | implementácia |

### 12.2 Nastavenia

| Nastavenie | HOME / SALT / OXY | NET | PROFI (jediné pevné rozsahy) |
|---|---|---|---|
| požadované pH | [O] 6,8–7,5 (starší HOME 6,5–7,6; SALT 7,3–7,6; OXY 6,4–7,6); výrobne 7,0 | [O] 6,8–7,5 | **6,4–7,2** |
| požadovaný voľný chlór | [O] 0,3–1,0 podľa teploty, nikdy pod 0,3; krok 0,1 | | **0–1,5 mg/l** |
| požadovaný redox | príklad 650 (SALT 700) | príklad 650 | — |
| požadovaná teplota | krok 0,5 (príklad 28,5), výrobne 25 | — | **0–45 °C**, presnosť 0,1 |
| flokulant | [O] HOME 10–40 ml/h, OXY 5–20 ml/h | — | **0,0–99,9** |
| algicíd | príklad 10 ml/m³/deň (starší HOME 0–1 ml/m³) | — | (spoločne s flokulantom 0–99,9) |
| OXY Pure | príklad 10 ml/m³/deň; cieľ vo vode 50–100 mg/l | — | — |
| dávka NET | — | príklad 5 ml/m³/h | — |
| max. hodinová dávka dezinfekcie | výrobne 20 ml/m³/h | [M] 1–11 ml/m³/h (25 v extrémnych podmienkach) | ? |
| max. dávok pH | príklady 10/15/30, výrobne 15 | 10/15/25 podľa tvrdosti | ? |
| max. dávok Cl | 15/30/60 v textoch chýb | 30 | ? |
| oneskorenie po dávke | [O] 4–10 min bazén, 1–10 min vírivka; krok 1 min | | [O] wait time 4–6 min |
| oneskorenie po štarte | krok 1 min, príklad 10 | | |
| max. čas dopúšťania | príklad 60 min; 0 = vypnuté (HOME PRO) | — | |
| prahy hladiny | príklad 30/20/10/5 cm; krok 1; musí platiť low < on < off < high [I] | — | |
| dopúšťanie začne po | 10 s pod prahom (HOME), 1 min (ASIN Pool) | — | |
| backwash každých | príklad 30 dní | — | |
| trvanie backwash | HOME „05“ min, SALT potvrdené ×10 s | — | |
| protizámrazová ochrana | HOME filtrácia pri 4 °C; SALT zimný režim 2 °C, časovač 12:00–12:15, algicíd 2 ml | — | |
| ohrev podľa vonkajšej teploty | príklad 18,0 °C, krok 0,1 [I] | — | |
| časové okno ohrevu | príklad 08:00–20:00 | — | |
| solárne relé (SALT) | zap pri teplote vody +5 °C, vyp pri +2 °C | — | |
| polarita elektródy (SALT) | 1 h / 24 h / 7 dní / ručne, výrobne 1 h | — | |
| objem bazéna | príklad 29–30 m³; HOME max bazén 250 m³ (dimenzovanie, nie limit menu) | príklad 45 m³ | |
| tvrdosť vody (NET) | — | 0–9 mäkká, 9–21 tvrdá, 21+ veľmi tvrdá °dH | |
| sériové číslo | 7 alebo 9 znakov | | |

### 12.3 Použitie pre našu validáciu

| Pole | Kontrola |
|---|---|
| `ph` | mimo 4–10 → mimo rozsahu sondy (nie reálna hodnota) |
| `dosing_delay`, `startup_delay`, `max_refill_time` | násobky 60 s (menu je v celých minútach); na SALT sedí (240, 480, 1140 s) |
| `water_level_*` | low < filling_on < filling_off < high |
| `salinity` | 0–~6 kg/m³ (alarm pod 1,5) |
| `chlorine_production` | 0–25 g/h |
| `ph_target` / `free_chlorine_target` / `water_temperature_target` | pevné limity **len na PROFI** |
| `max_ph_doses` | voľné celé číslo – neobmedzovať |

---

## 13. Čo overiť na jednotke

Postup ako pri 20 → 17: zmeniť **jednu** hodnotu na číslo, ktoré sa v rámci inde nevyskytuje, stiahnuť diagnostiku a porovnať.

### 13.1 Na tvojom SALT (REDOX, pH−)

| Poradie | Čo zmeniť | Na aké číslo | Kde hľadať |
|---|---|---|---|
| 1 | Max. hodinová dávka dezinfekcie (ak je v menu) | 20 → 13 | byte[108] |
| 2 | Interval prepínania polarity elektródy | 1 h → 7 dní | nový bajt / enum |
| 3 | Max. počet dávok chlóru / dezinfekcie (ak je v menu) | → 23 | 113, 114 |
| 4 | Zimný režim: teplota | 2 → 7 °C | 7 alebo 70 |
| 5 | Zimný režim: časovač | 12:00–12:15 → 11:13–11:47 | `0B 0D` / `0B 2F` |
| 6 | Programovateľné relé Solar/Timer + časy | nepárne časy | dvojice hh mm |
| 7 | Zapínače po jednom: backwash, snímač prietoku, hladinomer, VS čerpadlo, letný čas, zimný režim | zap ↔ vyp | byte[37], 73, 113, 116–118 |
| 8 | Displej „Power xx.x g/h“ počas elektrolýzy | – | byte[21] (je ×10?) |
| 9 | Dump hneď po zapnutí filtrácie, potom o minútu | – | byte[30–31] (odpočet?) |
| 10 | Dump pri alarme nízka soľ / pH pod 6,7 / prehriatie | – | byte[12], byte[13] |
| 11 | Hysteréza soli, max. dni elektrolýzy (ak sú v menu) | → nepárne číslo | ? |
| 12 | Pool flow OVERFLOW / BOTTOM (ak máš ventil) | prepnúť | ? |

### 13.2 Od iných používateľov

| Model | Čo potrebujeme |
|---|---|
| HOME | dump pri bežiacom algicíde (bit 0x10 alebo 0x20?); pri alarme pH dávok; so snímačom vzduchu; backwash trvanie vs. displej; byte[78] v rôznych stavoch; byte[103] vs. menu hladiny |
| HOME A a B | číslo firmvéru z displeja – aby sme vedeli, čo A/B naozaj je |
| NET | oneskorenie po štarte vs. menu; alarm chlórových dávok (byte[13]); zmena tvrdosti vody |
| NET v8 | rámec s bežiacim pH− a chlórovým čerpadlom (`outs`) |
| SALT v8 | akýkoľvek rámec |
| OXY | alarmy, hladina |
| PROFI | akýkoľvek reálny rámec (dnes nemáme ani jeden) |
| SALT DOSE (GH) | rámec s byte[4] = `0x0F` |

---

## 14. Otázky pre Aseko

Najlepší kontakt: autor [dkk54/ha-aseko-cloud](https://github.com/dkk54/ha-aseko-cloud) (podľa dokumentácie repozitára pracuje v Aseku).

1. Zodpovedá číselný `code` variantu (`UnitModelVariant`) bajtu byte[4] v 120-bajtovom rámci? Ak áno, dá sa zverejniť tabuľka?
2. Čo znamenajú prípony `1`, `2` a `GH` pri variantoch SALT?
3. Ako z v7 rámca zistiť verziu firmvéru? Ktoré verzie HOME menia rozloženie byte[37] a byte[29]?
4. Je tabuľka bitov error_1 / error_2 z RS485 dokumentu platná aj pre byte[12] a byte[13] v 120-bajtovom rámci?
5. Existuje verejný popis 120-bajtového a v8 rámca?
6. Plánuje sa zápis (príkazy) do jednotky cez lokálnu sieť alebo integrátorské API?

---

## 15. Návrhy na vylepšenie

| # | Návrh | Prínos | Náročnosť |
|---|---|---|---|
| 1 | Validácia kontrolného súčtu v7 (`0xAA XOR`) a uloženie výsledku do diagnostiky | zahodenie poškodených rámcov, detekcia zle poskladaných TCP paketov | malá |
| 2 | `0xFFFF` → `NOT_PRESENT` pre `startup_delay` (a skontrolovať všetky ďalšie `word()` čítania) | žiadne 65535 s | malá |
| 3 | `0xFE` na byte[27] → „snímač odpojený“ | žiadnych 254 cm | malá |
| 4 | Zjednotiť názvy s cloudom (`DOSE_MAX_PH_COUNT` → `max_ph_doses` už sedí; ďalšie polia pomenovať podľa `ConfigurationValueType`) | používatelia spoznajú hodnoty z appky | malá |
| 5 | Kontroly rozsahov z kapitoly 12.3 ako varovania v diagnostike, nie orezanie hodnôt | skoré odhalenie zlého mapovania | stredná |
| 6 | Rozdeliť `alarm_max_disinfection_dose` na „max. dávka“ a „max. hodinová dávka“, keď budú dumpy | presnejšie alarmy | stredná |
| 7 | Nahradiť `docs/doc_hex.md` generovanou mapou bajtov z profilov | jedna pravda | stredná |
| 8 | Odstrániť sériové čísla z evidence stringov v profiloch | súkromie používateľov | malá |
| 9 | Spotreba chemikálií z rámca (prietok × čas behu) ako voliteľná entita | rovnaké čísla ako appka | stredná |
| 10 | Validácia `crc16` v8 – najprv zistiť algoritmus (skúsiť CRC-16/MODBUS, CCITT, XMODEM na reálnych rámcoch) | integrita v8 | malá až stredná |

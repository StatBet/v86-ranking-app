# UNDERSKATTAD HÄST V1

Datum: 2026-06-07

## Kriterier

- model_rank 6-8
- spread <= 51
- spike_score >= 170
- total_score 99-139

## Resultat

Kandidater: 56
Vinnare: 10
Träff%: 17.9%

## Jämförelse

Rank 6-8 totalt:
70 / 1512
4.6%

Underskattad V1:
10 / 56
17.9%

≈ 3.9x bättre träffprocent

## Viktiga fynd

1. Låg spread (<=51) är den starkaste triggern.
2. Loppets totala styrka spelar nästan ingen roll.
3. Spike slog Place%, 4-av-5 och övriga filter.
4. Score 99-139 tog bort 9 förlorare utan att tappa en enda vinnare.

## Att undersöka nästa gång

- Speed-gruppen
- Form-gruppen
- Volt-gruppen
- Spår-gruppen
- Skräll-gruppen

Mål:
Hitta ytterligare typer av rank 6-8-vinnare utanför Underskattad V1.

# ==========================================================
# UNDERSKATTAD HÄST V1
#
# model_rank 6-8
# spread <= 51
# spike_score >= 170
# total_score 99-139
#
# Historik:
# 56 kandidater
# 10 vinnare
# 17.9%
# ==========================================================

# Anti-spik kandidater

Favoriter från tillägg:
22.2% träff

Favoriter utan tillägg:
37.0% träff

Score och gap är identiska.

Tillägget verkar i sig vara en stor riskfaktor.

Att undersöka:
- Gap >= 10
- Gap >= 15
- Gap >= 20
- Gap >= 25


# NÄSTA SESSION

## Färdigt

- Underskattad Häst V1 dokumenterad

## Att undersöka

- Speed-gruppen
- Form-gruppen
- Volt-gruppen
- Spår-gruppen
- Skräll-gruppen

Mål:
Identifiera vilka typer av rank 6-8-vinnare som INTE fångas av Underskattad V1.


# NÄSTA ANALYSSPÅR

## Förloraranalys

Mål:
Identifiera förlorare som kan filtreras bort utan att tappa vinnare.

### Underskattad V1
Analysera de 46 förlorarna.

### Spike
Analysera Spike-vinnare vs Spike-förlorare.
Kan vissa spikförslag filtreras bort?

### Top5
Analysera de 135 loppen där Top5 missade.
Finns gemensamma kännetecken?

Princip:
Det kan vara lättare att identifiera och ta bort förlorare än att hitta fler vinnare.



  PS C:\Users\Grinvald\Desktop\Ranking v85> python analyze_all_rank68_winners.py
================================================================================
ALLA RANK 6-8 VINNARE
================================================================================

Antal: 70

================================================================================
SNITT
================================================================================
avg_odds                         14.01
avg_odds_score                    0.00
avg_time                         15.28
class_change_score                1.53
date                       20257185.63
distance                       2207.40
distance_addition_score           0.00
driver_change_score               0.00
driver_score                      5.07
field_size                       12.26
form_score                       21.57
gallop_score                      0.00
gender_score                     -0.57
inactivity_score                 -7.43
is_model_rank_1                   0.00
latest_start_score                4.51
model_rank                        6.84
number                            5.41
percent                           0.00
place_percent                    47.97
place_score                       9.77
post                              5.31
post_score                        0.00
prize_money                  508591.21
prize_money_score                 0.00
race_no                           4.93
recent_prize_score                1.53
record_score                     14.90
score_gap_to_top                 39.17
seconds                           3.33
shoe_score                        0.00
speed_score                      14.90
spel_score                       25.00
stallform_score                   0.00
starts                           23.66
starts_score                      9.21
thirds                            2.10
total_score                     115.89
wagon_score                       0.00
win_percent                      25.08
win_score                        15.89
wins                              5.24
won                               1.00

================================================================================
ALLA VINNARE
================================================================================


================================================================================
KOLUMNER
================================================================================
date
race_id
race_no
track
distance
start_type
field_size
horse
winner
won
model_rank
is_model_rank_1
score_gap_to_top
total_score
speed_score
record_score
form_score
stallform_score
latest_start_score
post_score
driver_score
driver_change_score
starts_score
win_score
place_score
spel_score
prize_money_score
recent_prize_score
class_change_score
avg_odds_score
wagon_score
shoe_score
inactivity_score
distance_addition_score
gender_score
gallop_score
avg_time
avg_odds
starts
wins
seconds
thirds
win_percent
place_percent
percent
prize_money
post
number
raw
PS C:\Users\Grinvald\Desktop\Ranking v85>


AVG_ODDS FIXAD 2026-06

Tidigare oddsanalys byggde på felaktig extraktion.

Efter fix:

- Median vinnare: 7.22
- 75% av vinnarna: under 14.43
- 93.1% av vinnarna: under 30

Extrema historiska skrällhästar (>30 i avg_odds) utgör endast ca 7% av alla vinnare.


2026-06-08

AVG_ODDS-BUG FIXAD

Problem:
- build_ml_dataset.py missade odds och gav avg_odds=0 för 70 hästar.

Lösning:
- Odds extraheras nu korrekt från historikrader.

Resultat:
- avg_odds=0 försvann helt.
- Median avg_odds vinnare: 7.22
- 75-percentil: 14.43
- 93.1% av alla vinnare har avg_odds <= 30

SPÅRPOÄNGER UPPDATERADE

Resultat:
- Top5: 73.9%
- Spike170 + låg spread + score 99-139:
  60 kandidater
  10 vinnare
  16.7%


  Tilläggsfavorit

Gap < 20
= risk

Gap >= 25
= stark kandidat


hur många vinnare totalt hade avg odds under 8?


Badge V1
60 kandidater
10 vinnare
16.7%

Badge V2
196 kandidater
20 vinnare
10.2%

Gemensamma: 7
Endast V1: 3
Endast V2: 13

Totalt unika rank 6-8-vinnare:
23 av 71
= 32.4%



Badge V2 Strong
Rank 6-8
Spike >= 120
Spread <= 50
Total score >= 105
Avg odds <= 15
+
(post <= 4 OR latest_start_score >= 10 OR form_score >= 35)



# Badge V2 Strong B (sparad 2026-06-08)

Syfte:
Identifiera spelbara rank 6-8-vinnare med högre träffprocent.

## Badge V1

Rank 6-8

Spike >= 170
Spread <= 51
Total Score 99-139

Resultat:
60 kandidater
10 vinnare
16.7%

## Badge V2 Strong B

Rank 6-8

Spike >= 120
Spread <= 50
Total Score >= 105
Avg Odds <= 15

PLUS

(
Post <= 5
OR
Latest Start Score >= 7
OR
Form Score >= 35
)

Resultat:
138 kandidater
18 vinnare
13.0%

## Kombinerat V1 + V2 Strong B

162 kandidater
22 vinnare

Träff:
13.6%

Rank 6-8-vinnare fångade:
22 av 71
(31.0%)

Jämförelse mot V1 + V2 Bas:

Bas:
205 kandidater
23 vinnare
11.2%

Strong B:
162 kandidater
22 vinnare
13.6%

Förbättring:
-43 kandidater
-1 vinnare



# Nästa analyser

1. Favoriter från tillägg
   - Gap >= 10
   - Gap >= 15
   - Gap >= 20
   - Gap >= 25

2. Förlorare i spikförslag
   - Identifiera gemensamma drag
   - Kan några tas bort utan att tappa spikträffar?

3. Topp 5-förlorare
   - Identifiera gemensamma drag
   - Kan några tas bort utan att tappa topp 5-träff?

4. Rank 6-8 missade vinnare
   - Fortsatt jakt på Badge V3
   - Fokus på de återstående 49 vinnarna


   Top5 = stabil
Badge V2 Variant B = sparas
Skrällflagga = sparas
Favoriter från tillägg = nästa stora analys
Rank 6-8 missade vinnare = största guldgruvan


Badge V3 Candidate
Rank 6-8

Latest 7-10
Form 19-40
Driver >= 8
Avg_odds <= 15
Win% >= 10

73 kandidater
9 vinnare
12.3%




V1 + V2 Strong B + Combo C

217 kandidater
37 vinnare av 77 rank 6-8-vinnare
48.1% fångade
12.4% träff



# Loser Filter B

Syfte:
Identifiera svaga rank 6-8-hästar som kan prioriteras ned / endast tas med vid bred gardering.

Regel:

Rank 6-8

(
Spike <= 120
AND Driver Score = 0
AND Latest Start Score <= 3
AND Form Score <= 20
AND Avg Odds > 15
)

OR

Spike <= 50

Resultat:
328 kandidater
6 vinnare
1.8%

Kommentar:
Filtret tappar främst extrema kaosvinnare med låg spike, svag form, svag latest och ingen kusksignal.


Bästa rena filter hittills
Loser C:
Rank 6-8
Spel% <= 4
Spike <= 100

590 kandidater
6 vinnare
1.0%

markera med mörkgrön, ljusgrön, gul vilket ger (ungefär) 80%, 85% och 90% chans till att få med vinnaren.



# Implementerade regler 2026-06-09

## Loppbadges

### 3-hästarslopp
spread_1_8 >= 80  
Rank 1-3: 81.0%

### 4-hästarslopp
spread_1_8 >= 75  
Rank 1-4: 82.6%

### 5-hästarslopp
gap_1_4 >= 30  
Rank 1-5: 80.4%

Alternativ trigger:
gap_1_3 >= 30  
Rank 1-5: 80.2%

## Hästbadges

- Underskattad V1
- Underskattad V2 Strong B
- Form/Kusk V3
- Skrällvarning

## Loserflags

### Röd loserflagga
Loser B + speed <= 14  
Historik: 68 kandidater, 0 vinnare

### Gul loserflagga
Loser B  
Historik: 328 kandidater, 6 vinnare

### Loser C
Rank 6-8, spel% <= 4, spike <= 100  
Historik: 590 kandidater, 6 vinnare
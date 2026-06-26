cd "C:\Users\Grinvald\Desktop\Ranking v85"

streamlit run app.py




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



# Loppbadges

## Mörkgrön (80%)

3-hästarslopp
spread_1_8 >= 80

63 lopp
Rank 1-3 = 81.0%

## Ljusgrön (85%)

4-hästarslopp
spread_1_8 >= 75

92 lopp
Rank 1-4 = 82.6%

## Gul (90%)

5-hästarslopp

gap_1_4 >= 30
eller
gap_1_3 >= 30

≈80% inom rank 1-5



Alla profiler hittade:

1 åtta
1 sjua

på 69 spelbara omgångar.

Bästa profil just nu:

balanced_512

eftersom den ger samma 8/7 men något bättre snitträff:

avg_hits 3.28
Viktig observation

Det här säger att själva “radfördelningen” inte är problemet just nu. Alla profiler hittar samma toppomgångar:

20260103 = 8 rätt
20260218 = 7 rätt

Problemet är snarare att vinnarna ofta saknas i våra valda hästar per lopp.

Nästa steg bör vara att analysera:

Vilka missade lopp återkommer mest?
Vilken rank hade vinnarna i missade lopp?
Fanns Rank 6-8-badge där?
Var vinnaren rank 9+?


🔴 Loser Badge
(
    Spike < 60
    AND Total < 90
)
OR
(
    Spike < 80
    AND Total < 100
    AND WinScore < 12
)

Historik:

690 hästar
685 förlorare
5 vinnare

0.725%
Men jag hade även sparat komponenterna
🔴 Loser A
Spike <60
Total <90

461 hästar
2 vinnare
0.434%
🔴 Loser C+
Spike <80
Total <100
WinScore <12

471 hästar
5 vinnare
1.062%

För de är användbara att analysera separat framöver.



UTDELNING VS SUMMA VINNAR-%
====================================================================================================
payout_bucket  rounds  avg_winner_percent_sum  median_winner_percent_sum  min_winner_percent_sum  max_winner_percent_sum  avg_payout  median_payout
      0-4 999      17                   233.5                      272.0                      70                     350        1082            518
     100 000+      30                   182.6                      184.0                     107                     228     1534551         533748
11 000-49 999      10                   226.9                      219.5                     179                     284       28125          26651
 5 000-10 000       4                   261.8                      270.5                     225                     281        7660           7890
50 000-99 999       4                   212.5                      216.0                     181                     237       63271          61705

====================================================================================================
OMGÅNGAR
====================================================================================================
    date  winner_percent_sum  payout_8_value payout_bucket
20260425                 204         7519371      100 000+
20260117                 171         6458451      100 000+
20260221                 202         6434734      100 000+
20251217                 142         5660893      100 000+
20251101                 143         4450653      100 000+
20260131                 158         3092569      100 000+
20251108                 188         1752017      100 000+
20251015                 107         1459267      100 000+
20260328                 165         1152562      100 000+
20260207                 175          860245      100 000+
20260211                 213          846657      100 000+
20260523                 178          719237      100 000+
20260110                 161          670483      100 000+
20251105                 191          611043      100 000+
20260228                 228          544494      100 000+
20260513                 204          523001      100 000+
20260325                 149          489940      100 000+
20260121                 203          405967      100 000+
20260401                 187          378862      100 000+
20251220                 210          321633      100 000+
20251230                 226          293366      100 000+
20251129                 199          292703      100 000+
20260527                 189          269134      100 000+
20251025                 155          174601      100 000+
20260404                 181          167354      100 000+
20260506                 178          134493      100 000+
20251227                 174          127386      100 000+
20251112                 177          110974      100 000+
20260314                 221          103885      100 000+
20260124                 217           78265 50 000-99 999
20260114                 181           65228 50 000-99 999
20251126                 215           58182 50 000-99 999
20260429                 237           51408 50 000-99 999
20251001                 216           47917 11 000-49 999
20251119                 179           40201 11 000-49 999
20251022                 218           38551 11 000-49 999
20260502                 221           32497 11 000-49 999
20260107                 284           28578 11 000-49 999
20260411                 256           24724 11 000-49 999
20251122                 256           21524 11 000-49 999
20251210                 201           20446 11 000-49 999
20260214                 214           15746 11 000-49 999
20251029                 224           11068 11 000-49 999
20260311                 199           10547      100 000+
20260307                 281            8957  5 000-10 000
20260603                 225            8252  5 000-10 000
20260318                 268            7529  5 000-10 000
20260225                 273            5900  5 000-10 000
20251008                 222            4781       0-4 999
20251206                 315            3840       0-4 999
20260408                 271            2790       0-4 999
20260304                 286            1970       0-4 999
20260103                 310            1470       0-4 999
20260218                 272            1083       0-4 999
20260128                 321             844       0-4 999
20260204                 297             595       0-4 999
20260422                 331             518       0-4 999
20251203                 305             255       0-4 999
20251115                 350             217       0-4 999
20260321                 106              12       0-4 999
20260415                 126               7       0-4 999
20260418                 119               3       0-4 999
20260516                 134               3       0-4 999
20251213                 135               2       0-4 999
20251231                  70               1       0-4 999


180–280% = bred/balanserad, rimlig chans på 7/8
130–230% = mer offensiv, söker högre utdelning


NYA LOPPBADGE-FILTER
====================================================================================================
                                  filter  races  avg_winner_rank  rank1_pct  rank1_3_pct  rank1_5_pct  rank6_8_pct  rank9plus_pct  avg_total_sum  avg_spike_sum  avg_spread
🟢 Kompakt lopp: Total<=555 OR Spike<=810    169             3.37       32.0         62.1         79 .9         13.6            6.5          552.8          828.5        30.2
  🔥 Skrällopp: Total>=750 OR Spike>=1200    193             5.48       13.0         40.9         54.9         25.4           19.7          742.9         1222.3        23.8
                             Övriga lopp    194             4.10       24.7         55.7         69.1         18.6           12.4          643.5          998.3        25.6



   >> python analyze_high_payout_misses.py
>>
>> python simulate_high_payout_wild_profiles_550.py
====================================================================================================
MISSAR I 100 000+ OMGÅNGAR
====================================================================================================
 winner_rank  misses  avg_percent  avg_spike  avg_total
           3      21    23.190476 148.890476 136.857143
           4      28    17.178571 165.446429 131.464286
           5      16    13.875000 131.131250 127.187500
           6      15    11.600000 121.126667 120.800000
           7      15     9.933333 138.493333 116.600000
           8       8    22.125000 141.075000 108.500000
           9       8     3.625000 101.975000 103.750000
          10       8     8.625000  98.325000  94.125000
          11       8     5.375000  90.075000  82.500000
          12       3     3.666667 107.333333  93.333333
          13       1     7.000000 118.200000  85.000000
          14       1     2.000000  65.100000 106.000000
          15       1     4.000000  91.900000  64.000000

====================================================================================================
DETALJER
====================================================================================================
    date  race_no  payout_8_value  winner_percent_sum                winner  winner_rank  winner_percent  total_score  spike_score  spread  core_top3  all_top3
20251015        2       1459267.0               107.0       5 Molly Jo Poof            7               2          105        130.0    52.0          0         2
20251015        3       1459267.0               107.0     1 Gangster Vendil           11               7           81         73.2    56.0          0         2
20251015        5       1459267.0               107.0             9 Walmann            7               9          121        106.2    52.0          0         1
20251015        6       1459267.0               107.0          6 Tintarella            5               6          145        119.7    58.0          2         5
20251015        7       1459267.0               107.0   4 Screen Time Limit            4              22          151        188.8    68.0          1         4
20251025        1        174601.0               155.0          1 A Fair Day            5               9          150        211.6    50.0          2         4
20251025        2        174601.0               155.0 10 M.T.Tomorrows Hope            4              20          129         69.0    20.0          2         5
20251025        4        174601.0               155.0    2 Googoo Sensation            4              19          114        186.4    21.0          1         4
20251025        7        174601.0               155.0        1 Lucifer Boko            7              11          112         79.1    39.0          1         4
20251101        1       4450653.0               143.0             10 Fangio            3              14          115        123.5    60.0          2         6
20251101        2       4450653.0               143.0        5 Bonus Credit            7              14          119        176.5    48.0          2         4
20251101        3       4450653.0               143.0              1 Kruson           11               1           91         88.2    44.0          1         3
20251101        4       4450653.0               143.0        4 Cashman J.R.            3              19          136        140.6    63.0          3         6
20251101        8       4450653.0               143.0              4 Jikken            5              17          143        147.9    21.0          1         3
20251105        1        611043.0               191.0        7 Mister Aloha            4              11          131        112.0    43.0          1         4
20251105        6        611043.0               191.0         4 Wiener Blut            8               2           96        104.5    47.0          0         2
20251105        7        611043.0               191.0         9 Magic Jewel            4               4          112         87.7    46.0          0         2
20251108        2       1752017.0               188.0              5 Zaxton            7               1          113        127.0    56.0          0         2
20251108        5       1752017.0               188.0          1 Bilbao Ace            5              15          118        174.4    74.0          3         5
20251108        6       1752017.0               188.0   3 Monsieur Chocolat            9              10          123        140.3    32.0          0         2
20251108        8       1752017.0               188.0         10 Don E.Star            4              12          128        119.4    46.0          2         3
20251112        5        110974.0               177.0         9 Nash Keeper            4              12          126        128.4    68.0          4         8
20251112        6        110974.0               177.0     4 Ray Of Sunshine            4               8          114        178.8    23.0          2         5
20251112        7        110974.0               177.0       7 Googoo Casino            6               8          123        116.7    59.0          0         3
20251112        8        110974.0               177.0            3 Quick Bo           10              21          110        100.9    26.0          2         4
20251129        2        292703.0               199.0     7 Supernova Lyjam           15               4           64         91.9    48.0          0         1
20251129        3        292703.0               199.0            11 Barkley            8              36          130         80.3    21.0          1         4
20251129        4        292703.0               199.0       4 Idle Seabrook            3              30          125        187.2    46.0          3         5
20251129        5        292703.0               199.0            7 Clarissa            3              28          174        208.1    67.0          5         8
20251129        6        292703.0               199.0         1 Jay Jay Zet            3              34          144        120.6    58.0          0         2
20251129        7        292703.0               199.0             6 Parveny            7               3          135        126.0    47.0          0         3
20251129        8        292703.0               199.0         11 Pure Atlas            7              20          137        143.7    35.0          1         4
20251217        4       5660893.0               142.0            7 Navy Zon            9               1           83         68.0    59.0          0         3
20251217        5       5660893.0               142.0        3 Kul Stilling           10               9           95         83.9    51.0          0         3
20251217        6       5660893.0               142.0          7 Love Bites            5              14          144        151.0    62.0          1         3
20251217        7       5660893.0               142.0    1 Cool Hand Energy            5               7          123        210.5    39.0          3         6
20251220        1        321633.0               210.0         5 Ken's Queen           10               3           90        114.7    38.0          1         3
20251220        2        321633.0               210.0             5 Starman            7               7          103        200.9    67.0          2         4
20251220        3        321633.0               210.0            5 Free Day           10              11           94        131.4    52.0          0         1
20251220        5        321633.0               210.0        12 Gudrid Face            6              19          130        104.6    41.0          2         4
20251220        7        321633.0               210.0         1 Funny Money           13               7           85        118.2    37.0          0         2
20251227        5        127386.0               174.0      4 Xanthis Joojoo            8              23          106        113.9    35.0          3         6
20251227        6        127386.0               174.0      1 Kringelandisak            8              15          117        172.2    47.0          1         2
20251227        7        127386.0               174.0      2 Northman Maxus            6              17          126        140.8    41.0          2         4
20251227        8        127386.0               174.0     3 Steady Countess            6              10          132        139.7    30.0          2         4
20251230        1        293366.0               226.0             7 Alunita           11               0           68         91.2    44.0          2         4
20251230        5        293366.0               226.0   10 Memorial Fashion            3              48          122        103.6    46.0          3         6
20251230        6        293366.0               226.0        4 Nytomt Amira            4              30          125        170.2    52.0          4         7
20260110        1        670483.0               161.0        2 Nytomt Amira            8              10          125        175.0    40.0          4         5
20260110        5        670483.0               161.0  1 Timotejs Messenger            7               6          107         78.1    33.0          0         3
20260110        8        670483.0               161.0           2 Galadriel            4              14          130        160.6    62.0          2         5
20260117        1       6458451.0               171.0            1 Karin B.           11               7           96         90.8    41.0          0         2
20260117        2       6458451.0               171.0        5 Arnie Silvio            3              18          128        112.5    24.0          2         5
20260117        4       6458451.0               171.0          2 J.H.Oliver            6              20           90        133.0    44.0          2         4
20260117        7       6458451.0               171.0   9 Phantom le Soleil            7               0          120         97.9    51.0          2         4
20260121        1        405967.0               203.0   6 Lindendale's Iris            9               1           73         19.3    44.0          1         5
20260121        7        405967.0               203.0        3 Grand Safari            6              12           95         98.7    78.0          1         4
20260121        8        405967.0               203.0      3 Ready Creation            4              19          125        160.6    49.0          3         5
20260131        1       3092569.0               158.0     1 Colombe Blanche           11               4           73         63.2    37.0          0         1
20260131        2       3092569.0               158.0          5 Ogden Boko            4              15          123        225.4    83.0          2         5
20260131        3       3092569.0               158.0        15 Åsvinn S.K.            4               9          129        178.6    88.0          2         4
20260131        6       3092569.0               158.0            4 Maui Sun            4               8          119        140.5    45.0          3         6
20260131        7       3092569.0               158.0        8 Ellen Ripley            4               3          131        116.7    40.0          1         3
20260207        1        860245.0               175.0        5 Staro Steven            4               5          128        258.5    54.0          1         3
20260207        3        860245.0               175.0    5 Mister Smartface            4              21          127        157.2    58.0          2         5
20260207        4        860245.0               175.0      2 Eminent Kronos            4              59          149        180.7    45.0          3         5
20260207        5        860245.0               175.0       7 Louis Vuitton            3               4          148        191.4    53.0          4         7
20260207        6        860245.0               175.0    4 Urbina Southwind            3              13          176        143.4    41.0          2         5
20260207        7        860245.0               175.0       4 Mago Launcher           12               5           96        114.0    45.0          1         3
20260211        1        846657.0               213.0       10 Dalens Elvis            4              14          130        129.3    68.0          3         5
20260211        2        846657.0               213.0          10 Home Safe            3              24          130        195.0    50.0          4         8
20260211        4        846657.0               213.0            6 Indy Boy            6              20          105         94.7    77.0          1         4
20260211        5        846657.0               213.0      2 Skilling Banco            5               1          107         61.3    54.0          1         5
20260211        6        846657.0               213.0       6 Solo Traveler           10               8           78         37.2    64.0          0         3
20260221        5       6434734.0               202.0         3 Kapten Nemo            6               8          130        107.7    78.0          1         3
20260221        6       6434734.0               202.0         9 B.G.Svedjan           10               8          100         78.6    36.0          1         4
20260221        7       6434734.0               202.0      8 Västerbo Tramp            9               0          132        114.6    45.0          1         3
20260228        2        544494.0               228.0       12 Mr Carnation            7              23           94        154.2    42.0          2         4
20260228        4        544494.0               228.0           12 Flotilla            6               6          118         72.8    43.0          0         1
20260228        5        544494.0               228.0      1 Twelve O'Clock           11               3           94         99.6    45.0          0         2
20260228        6        544494.0               228.0           8 Nyharajah           10               4           99         96.7    23.0          1         2
20260228        7        544494.0               228.0             8 Joelynn            9               2          111         81.7    62.0          0         1
20260311        3         10547.0               199.0       5 DiMaggio Face            3              35          150        104.8    59.0          5         9
20260311        4         10547.0               199.0         3 Micke Sting            4               8          145        155.1   109.0          3         6
20260314        1        103885.0               221.0  1 Sven the Forestman            6              20          128        140.6    40.0          3         4
20260314        4        103885.0               221.0           8 Voje Dino            9               7          111        161.9    51.0          1         3
20260314        5        103885.0               221.0      6 Excalibur Gene            5              22          136        215.5    29.0          2         5
20260314        7        103885.0               221.0    2 Humanity Pellini            5               7          131        136.6    75.0          0         3
20260314        8        103885.0               221.0            14 Joelynn            9               7          111        100.9    46.0          1         2
20260325        2        489940.0               149.0       7 German Kaiser            3               8          117        180.0    39.0          4         6
20260325        4        489940.0               149.0     6 Currency Artist            5               2          127         66.3    85.0          1         3
20260325        5        489940.0               149.0     12 Landmark River            3              24          134         97.9    58.0          1         5
20260325        6        489940.0               149.0           5 Marseille            5              16          118        105.3    60.0          3         6
20260325        7        489940.0               149.0           7 Kalle May            3              35          134        161.5    49.0          5         9
20260328        1       1152562.0               165.0  7 Jula Redmile Champ           10               5           87        143.2    80.0          0         2
20260328        4       1152562.0               165.0         9 Halina S.H.            4               8          133        193.4    68.0          3         5
20260328        5       1152562.0               165.0  8 Ready for Cash N.O            3              11          140        206.2    55.0          1         3
20260328        6       1152562.0               165.0            8 Indy Boy            7              30          108        123.6    55.0          1         3
20260328        7       1152562.0               165.0            11 Diva Ek            4               8          170        209.9    46.0          3         6
20260328        8       1152562.0               165.0          3 Ogden Boko            6              12          134        208.1    76.0          2         4
20260401        1        378862.0               187.0              10 Flame            5              23          104         36.1    29.0          1         5
20260401        3        378862.0               187.0          2 Sefyr Lane            3              26          139        173.8    68.0          4         7
20260401        4        378862.0               187.0         2 Large Level           11               6           63        114.9    61.0          1         2
20260401        6        378862.0               187.0                9 J.C.            9               1           86        129.1    64.0          2         4
20260404        1        167354.0               181.0          6 Chantecler            3              24          124        124.2    50.0          2         5
20260404        3        167354.0               181.0                 4 Tix            4              18          130        160.8     0.0          4         8
20260404        6        167354.0               181.0        4 Gigant Tider            7               5          135        268.3    40.0          2         5
20260404        7        167354.0               181.0             4 Charron            5              38          127        160.0    66.0          1         3
20260425        1       7519371.0               204.0               5 Qulör           14               2          106         65.1    53.0          0         1
20260425        2       7519371.0               204.0         5 Kapten Nemo           12               0           95        102.0    75.0          0         2
20260425        3       7519371.0               204.0    3 Tiberius Victory            4              17          127        148.5    48.0          2         5
20260425        5       7519371.0               204.0    12 Maker's Wall Ås            8              11           91        169.9    65.0          2         3
20260425        7       7519371.0               204.0       6 Brilliant Kid            7               9          128        139.7    47.0          1         2
20260425        8       7519371.0               204.0        3 Speed Change            4              36          166        235.0    62.0          4         7
20260506        1        134493.0               178.0    4 A View to a Kill            4              46          121        206.7    30.0          3         6
20260506        2        134493.0               178.0           1 Likeaboss            3              30          147        227.5    49.0          4         6
20260506        3        134493.0               178.0      4 Briskeby Pilen           12               6           89        106.0    44.0          1         3
20260506        4        134493.0               178.0        6 Fusion Blaze            5              19          112        114.9    21.0          2         6
20260506        6        134493.0               178.0       3 Mister Navajo            4              34          140        248.1    56.0          2         5
20260506        7        134493.0               178.0           1 Euro S.L.            5               3          120         72.5    51.0          2         6
20260513        1        523001.0               204.0  12 Mr Explosive H.H.            6               3          114         99.6    51.0          1         2
20260513        2        523001.0               204.0             8 Hybrida            3              18          126        119.5    34.0          2         6
20260513        4        523001.0               204.0          7 Illuminato            8              63          100        230.1    31.0          2         5
20260513        5        523001.0               204.0              5 Remina            8              17          103         82.7    25.0          1         4
20260513        7        523001.0               204.0         12 Black Fire            4               1          128        126.2    76.0          2         5
20260513        8        523001.0               204.0            2 Mud Hill            7               9          112        126.2    44.0          3         5
20260523        1        719237.0               178.0           8 Ditte Gel            6              13          138        124.0    42.0          3         6
20260523        3        719237.0               178.0          6 R.K.Pascal            3              27          130        116.0    44.0          1         5
20260527        2        269134.0               189.0          5 Hulte Alva            6               3          128        133.4    79.0          2         5
20260527        3        269134.0               189.0    9 Oliver Transs R.            5              23          130        114.5    53.0          3         5
20260527        5        269134.0               189.0  9 M.T.Tomorrows Hope            3              17          135         89.4    76.0          2         6
20260527        7        269134.0               189.0        2 Rosso Rubino           11              15           94         99.5    58.0          1         3
20260527        8        269134.0               189.0        6 Charlys Mine            6               3          121        102.5    57.0          1         4

Sparat:
high_payout_misses_details.csv
high_payout_misses_summary.csv
25/243
50/243
75/243
100/243
125/243
150/243
175/243
200/243
225/243
====================================================================================================
HIGH PAYOUT WILD PROFILES - 100 000+
====================================================================================================
              profile  high_rounds  avg_rows  eight_right  seven_right  six_right  five_right  avg_hits
hp_o5_w6_r10_p10_s100           30     384.0            0            0          2           5      3.57
hp_o5_w6_r10_p10_s120           30     384.0            0            0          2           5      3.57
hp_o5_w6_r10_p10_s140           30     384.0            0            0          2           5      3.57
hp_o5_w6_r10_p15_s100           30     384.0            0            0          2           5      3.57
hp_o5_w6_r10_p15_s120           30     384.0            0            0          2           5      3.57
hp_o5_w6_r10_p15_s140           30     384.0            0            0          2           5      3.57
hp_o5_w6_r10_p20_s100           30     384.0            0            0          2           5      3.57
hp_o5_w6_r10_p20_s120           30     384.0            0            0          2           5      3.57
hp_o5_w6_r10_p20_s140           30     384.0            0            0          2           5      3.57
hp_o5_w6_r12_p10_s100           30     384.0            0            0          2           5      3.57
hp_o5_w6_r12_p10_s120           30     384.0            0            0          2           5      3.57
hp_o5_w6_r12_p10_s140           30     384.0            0            0          2           5      3.57
hp_o5_w6_r12_p15_s100           30     384.0            0            0          2           5      3.57
hp_o5_w6_r12_p15_s120           30     384.0            0            0          2           5      3.57
hp_o5_w6_r12_p15_s140           30     384.0            0            0          2           5      3.57
hp_o5_w6_r12_p20_s100           30     384.0            0            0          2           5      3.57
hp_o5_w6_r12_p20_s120           30     384.0            0            0          2           5      3.57
hp_o5_w6_r12_p20_s140           30     384.0            0            0          2           5      3.57
 hp_o5_w6_r8_p10_s100           30     384.0            0            0          2           5      3.57
 hp_o5_w6_r8_p10_s120           30     384.0            0            0          2           5      3.57
 hp_o5_w6_r8_p10_s140           30     384.0            0            0          2           5      3.57
 hp_o5_w6_r8_p15_s100           30     384.0            0            0          2           5      3.57
 hp_o5_w6_r8_p15_s120           30     384.0            0            0          2           5      3.57
 hp_o5_w6_r8_p15_s140           30     384.0            0            0          2           5      3.57
 hp_o5_w6_r8_p20_s100           30     384.0            0            0          2           5      3.57
 hp_o5_w6_r8_p20_s120           30     384.0            0            0          2           5      3.57
 hp_o5_w6_r8_p20_s140           30     384.0            0            0          2           5      3.57
hp_o5_w7_r10_p10_s100           30     384.0            0            0          2           5      3.57
hp_o5_w7_r10_p10_s120           30     384.0            0            0          2           5      3.57
hp_o5_w7_r10_p10_s140           30     384.0            0            0          2           5      3.57

Sparat:
high_payout_wild_profiles_summary.csv
high_payout_wild_profiles_all.csv
high_payout_wild_profiles_best_details.csv
PS C:\Users\Grinvald\Desktop\Ranking v85>



Value-kandidat
+
spread < 70

gav:

183 lopp
91 st 100k+
49.7%
33 value-vinnare



Nivå 1 – Värdejaktslopp

Value-kandidat + spread < 70
183 lopp
91 st 100k+ omgångar (49,7%)

Nivå 2 – Skrällrisk

Öppet lopp + value-kandidat
122 lopp
42 vinnare ≤10%
57 vinnare ≤15%

Nivå 3 – Extrem skrällrisk

Öppet lopp + value-kandidat + Top3Sum 65–74
38 lopp
17 vinnare ≤10%
23 vinnare ≤15%
# Dataset Audit Report - Video Game Sales (vgsales.csv)

Source file: `vgsales.csv` (downloaded via KaggleHub, copied from KaggleHub cache into `data/raw/`)

## 1. Structure
- Rows: **16598**
- Columns: **11** -> `Rank, Name, Platform, Year, Genre, Publisher, NA_Sales, EU_Sales, JP_Sales, Other_Sales, Global_Sales`
- Types: `Rank`: int64, `Name`: str, `Platform`: str, `Year`: float64, `Genre`: str, `Publisher`: str, `NA_Sales`: float64, `EU_Sales`: float64, `JP_Sales`: float64, `Other_Sales`: float64, `Global_Sales`: float64

## 2. Missing values (count, percent)
| Column | Missing | Percent |
|---|---|---|
| Rank | 0 | 0% |
| Name | 0 | 0% |
| Platform | 0 | 0% |
| Year | 271 | 1.63% |
| Genre | 0 | 0% |
| Publisher | 58 | 0.35% |
| NA_Sales | 0 | 0% |
| EU_Sales | 0 | 0% |
| JP_Sales | 0 | 0% |
| Other_Sales | 0 | 0% |
| Global_Sales | 0 | 0% |

## 3. Duplicates
- Exact duplicate rows (all 11 columns equal): **0** (rows involved: 0)
- Duplicate **Name + Platform** combinations: **5** (rows involved: 10)
- Note: the same Name on *different* platforms is legitimate and is not counted here.

**Example duplicate Name+Platform rows (first 10):**
```
 Rank                        Name Platform   Year    Genre  Global_Sales
  604               Madden NFL 13      PS3 2012.0   Sports          2.56
16130               Madden NFL 13      PS3 2012.0   Sports          0.01
 5902 Need for Speed: Most Wanted       PC 2005.0   Racing          0.30
11678 Need for Speed: Most Wanted       PC 2012.0   Racing          0.08
 1175 Need for Speed: Most Wanted     X360 2012.0   Racing          1.58
 1532 Need for Speed: Most Wanted     X360 2005.0   Racing          1.29
 1717          Sonic the Hedgehog      PS3 2006.0 Platform          1.18
 4147          Sonic the Hedgehog      PS3    NaN Platform          0.48
15000 Wii de Asobu: Metroid Prime      Wii    NaN  Shooter          0.02
15002 Wii de Asobu: Metroid Prime      Wii    NaN  Shooter          0.02
```

## 4. Categorical columns
- Genre (12 unique): `['Action', 'Adventure', 'Fighting', 'Misc', 'Platform', 'Puzzle', 'Racing', 'Role-Playing', 'Shooter', 'Simulation', 'Sports', 'Strategy']`
- Platform (31 unique): `['2600', '3DO', '3DS', 'DC', 'DS', 'GB', 'GBA', 'GC', 'GEN', 'GG', 'N64', 'NES', 'NG', 'PC', 'PCFX', 'PS', 'PS2', 'PS3', 'PS4', 'PSP', 'PSV', 'SAT', 'SCD', 'SNES', 'TG16', 'WS', 'Wii', 'WiiU', 'X360', 'XB', 'XOne']`
- Publisher: 578 unique values

## 5. Sales column validity
| Column | Negative | Non-numeric text | Min | Max |
|---|---|---|---|---|
| NA_Sales | 0 | 0 | 0.0 | 41.49 |
| EU_Sales | 0 | 0 | 0.0 | 29.02 |
| JP_Sales | 0 | 0 | 0.0 | 10.22 |
| Other_Sales | 0 | 0 | 0.0 | 10.57 |
| Global_Sales | 0 | 0 | 0.01 | 82.74 |

Zero values (genuine zero sales, NOT missing data): {'NA_Sales': 4499, 'EU_Sales': 5730, 'JP_Sales': 10455, 'Other_Sales': 6477, 'Global_Sales': 0}
Missing values inside sales columns (count, NOT zeros): {'NA_Sales': 0, 'EU_Sales': 0, 'JP_Sales': 0, 'Other_Sales': 0, 'Global_Sales': 0}

## 6. Year column
- Missing: **271**
- Range: 1980.0 to 2020.0
- Non-integer values: 0
- Values after 2016 (suspicious / impossible for this snapshot): 4
```
 Rank                                             Name Platform   Year        Genre    Publisher
 5959                           Imagine: Makeup Artist       DS 2020.0   Simulation      Ubisoft
14393 Phantasy Star Online 2 Episode 4: Deluxe Package      PS4 2017.0 Role-Playing         Sega
16244 Phantasy Star Online 2 Episode 4: Deluxe Package      PSV 2017.0 Role-Playing         Sega
16441                 Brothers Conflict: Precious Baby      PSV 2017.0       Action Idea Factory
```

## 7. Global_Sales vs sum of regions
- Agree within 0.01: 13973 of 16598 (84.185%)
- Disagree by more than 0.01: **2625**
- Largest discrepancy: 0.020000000000000462
Worst rows:
```
 Rank                      Name Platform  NA_Sales  EU_Sales  JP_Sales  Other_Sales  Global_Sales
  106                  Tekken 3       PS      3.27      2.22      1.40         0.29          7.16
 4593 Yu-Gi-Oh! GX: Tag Force 2      PSP      0.03      0.20      0.10         0.11          0.42
 3234                       Wet      PS3      0.22      0.27      0.01         0.11          0.63
 1550      Kid Icarus: Uprising      3DS      0.48      0.35      0.36         0.07          1.28
 1413   Need for Speed: The Run     X360      0.63      0.58      0.00         0.15          1.38
```

## 8. Extra observations
- Unique game titles: 11493
- Rows whose title appears on more than one platform (legitimate): 5105

Rows with a missing Publisher:
```
 Rank                                                                Name Platform   Year        Genre  Global_Sales
  471                                          wwe Smackdown vs. Raw 2006      PS2    NaN     Fighting          3.00
 1305                                                      Triple Play 99       PS    NaN       Sports          1.46
 1664                        Shrek / Shrek 2 2-in-1 Gameboy Advance Video      GBA 2007.0         Misc          1.21
 2224                                                  Bentley's Hackpack      GBA 2005.0         Misc          0.93
 3161               Nicktoons Collection: Game Boy Advance Video Volume 1      GBA 2004.0         Misc          0.64
 3168              SpongeBob SquarePants: Game Boy Advance Video Volume 1      GBA 2004.0         Misc          0.64
 3768              SpongeBob SquarePants: Game Boy Advance Video Volume 2      GBA 2004.0         Misc          0.53
 4147                                                  Sonic the Hedgehog      PS3    NaN     Platform          0.48
 4528             The Fairly Odd Parents: Game Boy Advance Video Volume 1      GBA 2004.0         Misc          0.43
 4637             The Fairly Odd Parents: Game Boy Advance Video Volume 2      GBA 2004.0         Misc          0.42
 5304                       Dragon Ball Z: Budokai Tenkaichi 2 (JP sales)      Wii    NaN       Action          0.35
 5649 Cartoon Network Collection: Game Boy Advance Video Platinum Edition      GBA 2005.0         Misc          0.32
 6274                The Legend of Zelda: The Minish Cap(weekly JP sales)      GBA    NaN       Action          0.27
 6439                            Sonic X: Game Boy Advance Video Volume 1      GBA 2004.0         Misc          0.27
 6564                  Dora the Explorer: Game Boy Advance Video Volume 1      GBA 2004.0         Misc          0.26
 6650         Cartoon Network Collection: Game Boy Advance Video Volume 1      GBA 2004.0         Misc          0.25
 6851                      All Grown Up!: Game Boy Advance Video Volume 1      GBA 2004.0         Misc          0.24
 7210               Nicktoons Collection: Game Boy Advance Video Volume 2      GBA 2004.0         Misc          0.22
 7353                                      Yu Yu Hakusho: Dark Tournament      PS2    NaN     Fighting          0.21
 7472              SpongeBob SquarePants: Game Boy Advance Video Volume 3      GBA 2004.0         Misc          0.21
 7955                                    Thomas the Tank Engine & Friends      GBA 2004.0    Adventure          0.19
 8332                     Dragon Ball GT: Game Boy Advance Video Volume 1      GBA 2004.0         Misc          0.17
 8343           Codename: Kids Next Door: Game Boy Advance Video Volume 1      GBA 2004.0         Misc          0.17
 8370       Teenage Mutant Ninja Turtles: Game Boy Advance Video Volume 1      GBA 2004.0         Misc          0.17
 8505                                                        Stronghold 3       PC 2011.0     Strategy          0.16
 8772  Cartoon Network Collection: Game Boy Advance Video Special Edition      GBA 2005.0         Misc          0.15
 8850                 Pokémon: Johto Photo Finish: Game Boy Advance Video      GBA 2004.0         Misc          0.15
 8898               Strawberry Shortcake: Game Boy Advance Video Volume 1      GBA 2004.0         Misc          0.15
 9519                                              Farming Simulator 2011       PC 2010.0   Simulation          0.13
 9751  Super Robot Wars OG Saga: Masou Kishin II - Revelation of Evil God      PSP    NaN     Strategy          0.12
10384                                    Disney Channel Collection Vol. 1      GBA 2004.0         Misc          0.11
10496                              Atsumare! Power Pro Kun no DS Koushien       DS    NaN       Sports          0.10
11078                                        Action Man-Operation Extreme       PS    NaN       Action          0.09
11528         Cartoon Network Collection: Game Boy Advance Video Volume 2      GBA 2004.0         Misc          0.08
12489                                                Chou Soujuu Mecha MG       DS    NaN   Simulation          0.06
12519                        Prinny: Can I Really Be The Hero? (US sales)      PSP    NaN       Action          0.06
13280                                      Monster Hunter Frontier Online      PS3    NaN Role-Playing          0.05
13674                                           B.L.U.E.: Legend of Water       PS    NaN    Adventure          0.04
13964                                                      World of Tanks     X360    NaN      Shooter          0.04
14089                                                        Housekeeping       DS    NaN       Action          0.04
14299                                                 Bikkuriman Daijiten       DS    NaN         Misc          0.03
14314                                                       Silverlicious       DS 2012.0       Action          0.03
14701                                                  UK Truck Simulator       PC 2010.0   Simulation          0.03
14945      Umineko no Naku Koro ni San: Shinjitsu to Gensou no Yasoukyoku      PS3    NaN    Adventure          0.02
15059                                                             Xia-Xia       DS 2012.0     Platform          0.02
15264                                                        Mario Tennis      3DS    NaN       Sports          0.02
15328               Nicktoons Collection: Game Boy Advance Video Volume 3      GBA 2005.0         Misc          0.02
15356                                    Demolition Company: Gold Edition       PC 2011.0   Simulation          0.02
15791               Moshi, Kono Sekai ni Kami-sama ga Iru to suru Naraba.      PSV 2016.0    Adventure          0.02
15918                                                        Dream Dancer       DS    NaN         Misc          0.02
16194                                     Homeworld Remastered Collection       PC    NaN     Strategy          0.01
16201                              AKB1/48: Idol to Guam de Koishitara...     X360    NaN         Misc          0.01
16211            Super Robot Monkey Team: Game Boy Advance Video Volume 1      GBA 2005.0         Misc          0.01
16232                                         Brothers in Arms: Furious 4     X360    NaN      Shooter          0.01
16370                                                   Dance with Devils      PSV 2016.0       Action          0.01
16497                                     Legends of Oz: Dorothy's Return      3DS 2014.0       Puzzle          0.01
16546                                              Driving Simulator 2011       PC 2011.0       Racing          0.01
16556                                                      Bound By Flame     X360 2014.0 Role-Playing          0.01
```

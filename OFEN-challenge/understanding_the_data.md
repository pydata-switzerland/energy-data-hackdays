# Electricity production data

Prototyping to understand the data for the challenge
owned by the Swiss Federal Office of Energy (SFOE).

See also : [https://www.energydatahackdays.ch/challenges/estimating-hourly-energy-production-for-switzerland](https://www.energydatahackdays.ch/challenges/estimating-hourly-energy-production-for-switzerland)


## Challenge description

*The Swiss Federal Office of Energy currently publishes electricity production
data on a daily level across multiple technologies such as hydro, nuclear,
thermal, wind and PV. However, with the increasing share of renewable and
variable energy sources, hourly resolution becomes crucial to better understand
system dynamics. While hourly production data is available from the ENTSO-E
Transparency Platform, it is not directly aligned with the official daily
totals published by the SFOE.*

*The goal of this challenge is to ***combine these
data sources and develop a method to estimate hourly electricity production per
technology in a consistent way***. Participants will explore how ENTSO-E hourly
profiles can be scaled or adjusted to match SFOE's daily totals. The challenge
is to ensure that the resulting time series is both physically plausible and
methodologically transparent.*

## Data description

## SFOE

Source : https://www.energiedashboard.admin.ch/strom/produktion

The _power production_ figures available through SFOE's (Swiss Federal Office of Energy) energy dashboard (across multiple technologies such as hydro, nuclear, thermal, wind and PV) are reportedly aggregated **daily** data.[^0]  The data are publicly accessible via (opendata.swiss)[opendata.swiss] [^1][^2] in the form of comma-separated-values[^3].  The _provider_ of the data, however, is Swissgrid.[^4]  

### Swissgrid

Description from
[www.swissgrid.ch/en/home/operation/grid-data/generation.html#downloads](https://www.swissgrid.ch/en/home/operation/grid-data/generation.html#downloads)

> The total of the produced energy in the control block Switzerland.
> The aggregations of the feed-in sequences for the balancing groups
> are sent from the distribution network operators to Swissgrid.
> The sum contains all the energy produced and fed in the network.
> (Only productions plants equipped with load profile meters)

Looking closer at the data provided by Swissgrid
in form of Excel spreadsheets [^5]
their _original_ temporal resolution is **every 15'**[^6].

Some example statistics from the 2026 data (downloaded on April 21)
after manually extracting the energy production time series
from the _Zeitreihen0h15_ sheet
(starting from `01.01.2026 00:00` up to `31.03.2026 23:45`,
here saved as : `total_energy_production_swissgrid.csv`) :

``` bash
mlr --c2p --ofmt '%.2f' \
put '$MWh = $kWh / 1000' \
then stats1 -a sum,median,mean,stddev,mad -f MWh \
total_energy_production_swissgrid.csv

MWh_sum     MWh_median MWh_mean MWh_stddev MWh_mad
13100359.20 1375.90    1516.95  573.90     471.09
```

## Get the data

First, let's retrieve small samples of the data.

### Download data manually

The data :

[energiedashboard.ch: Stromproduktion Swissgrid-CSV](https://opendata.swiss/en/dataset/energiedashboard-ch-stromproduktion-swissgrid/resource/0879ba1b-40ea-4e26-bba0-9cbb339f577e)

and a quick-look on the downloaded data

``` bash
mlr --csv head -n 3 ogd104_stromproduktion_swissgrid.csv
```

returns

``` csv
Datum,Energietraeger,Produktion_GWh
2015-01-01,Flusskraft,22.6
2015-01-01,Kernkraft,79.6
2015-01-01,Photovoltaik,1.2
```

### Get data via the Web API

---
Input : `https://energiedashboard.ch/api/v1/datasets/stromproduktion-swissgrid/data?from=2026-01-01&offset=0&limit=1000'`  
Output `stromproduktion.csv`

---

### Daily electricity production 

Following, let's retrieve daily electricity production totals for 2026

``` bash
curl -s -X 'GET'   'https://energiedashboard.ch/api/v1/datasets/stromproduktion-swissgrid/data?from=2026-01-01&offset=0&limit=1000'   -H 'accept: application/json'   > stromproduktion.json
```

and peak

``` bash
mlr --ijson head stromproduktion.json
```

_This will return a large one-liner_ :

`data.1.datum=2026-03-13,data.1.energietraeger=Thermische,data.1.produktion_gwh=8.6,...`

Now, convert to CSV : 

``` bash
mlr --ijson put '
  for (k,v in $data) {
    @row = v;
    emit @row
  }
' then cut -f datum,energietraeger,produktion_gwh \
then rename 'produktion_gwh,Produktion_GWh' \
--ocsv \
then skip-trivial-records \
stromproduktion.json \
> stromproduktion.csv
```

and _compare_ with the manually downloaded sample data,
to ensure we have the same numbers,
i.e. no errors during the JSON

### Convert data to CSV

---
Input : `stromproduktion_2026_01.csv`  
Output : `stromproduktion_2026_01_GWh.csv`

---

``` bash
mlr --csv \
stats1 -a sum -f Produktion_GWh  -g energietraeger \
then sort -f energietraeger \
stromproduktion.csv
```

returns

``` csv
energietraeger,Produktion_GWh_sum
Flusskraft,3268.4999999999995
Kernkraft,5864.4
Photovoltaik,2332.6999999999994
Speicherkraft,5773.400000000004
Thermische,1152.100000000001
Wind,57.30000000000002
```

and

``` bash
mlr --csv \
filter '$Datum =~ "2026"' \
then stats1 -a sum -f Produktion_GWh -g Energietraeger \
then sort -f Energietraeger \
ogd104_stromproduktion_swissgrid.csv
```

returns

```
Energietraeger,Produktion_GWh_sum
Flusskraft,3268.5000000000005
Kernkraft,5864.400000000002
Photovoltaik,2332.7
Speicherkraft,5773.399999999997
Thermische,1152.1000000000004
Wind,57.300000000000004
```

Actually save output to a new file

``` bash
mlr --csv \
stats1 -a sum -f Produktion_GWh  -g energietraeger \
then sort -f energietraeger \
then label Type,Production_GWh \
stromproduktion_2026_01.csv \
> stromproduktion_2026_01_GWh.csv
```

### Focus on Switzerland

---
Input : `2026_01_AggregatedGenerationPerType_16.1.B_C_r3_AreaMapCode_CH.csv`  
Intermediate : `2026_01_AggregatedGenerationPerType_16.1.B_C_r3_AreaMapCode_CH_GWh.csv`  
Output : `entsoe_GWh.csv`

---

Extract all about Switzerland

``` bash
mlr --csv \
stats1 -a sum -f ActualGenerationOutput[MW] -g ProductionType \
then put '$Production_GWh = ${ActualGenerationOutput[MW]_sum} / 1000'  \
then cut -f ProductionType,Production_GWh 2026_01_AggregatedGenerationPerType_16.1.B_C_r3_AreaMapCode_CH.csv \
> 2026_01_AggregatedGenerationPerType_16.1.B_C_r3_AreaMapCode_CH_GWh.csv
```

Map SFOE to ENTSOE _Production Type_

It is required to understand
the correspondence between SFOE and ENTSOE energy production types.

| SFOE          | ENTSOE                          |
|---------------|---------------------------------|
| Speicherkraft | Hydro Pumped Storage            |
| Flusskraft    | Hydro Run-of-river and poundage |
| Speicherkraft | Hydro Water Reservoir           |
| Kernkraft     | Nuclear                         |
| Photovoltaik  | Solar                           |
| Wind          | Wind Onshore                    |


``` bash
mlr --csv put '
  begin {
    @map["Hydro Pumped Storage"] = "Speicherkraft";
    @map["Hydro Run-of-river and poundage"] = "Flusskraft";
    @map["Hydro Water Reservoir"] = "Speicherkraft";
    @map["Nuclear"] = "Kernkraft";
    @map["Solar"] = "Photovoltaik";
    @map["Wind Onshore"] = "Wind"
  }
  $MatchType = @map[$ProductionType]
' \
then rename ProductionType,Type \
2026_01_AggregatedGenerationPerType_16.1.B_C_r3_AreaMapCode_CH_GWh.csv \
> entsoe_GWh.csv
```

Print to verify output

``` bash
mlr --c2p --ofmt '%.2f' cat entsoe_GWh.csv
```

```
Type                            Production_GWh MatchType
Hydro Pumped Storage            750.07         Speicherkraft
Hydro Run-of-river and poundage 661.77         Flusskraft
Hydro Water Reservoir           992.96         Speicherkraft
Nuclear                         1458.41        Kernkraft
Solar                           78.36          Photovoltaik
Wind Onshore                    17.99          Wind
```


## Compare SFOE vs ENTSOE data

Now we can compare the two "sources" (daily and hourly)
and verify they refer to the same quantities.

Let's generate a file for all production types (?)

``` bash
mlr --csv \
join --lp Daily_ --rp Hourly_ -j Type -r MatchType -f stromproduktion_2026_01_GWh.csv entsoe_GWh.csv \
|mlr --csv reorder -f Type,Hourly_Type,Daily_Production_GWh,Hourly_Production_GWh \
then rename Type,SFOE_Type,Hourly_Type,ENTSOE_Type \
then put '
  $Difference = $Daily_Production_GWh - $Hourly_Production_GWh;
  $Percentage = ($Daily_Production_GWh == 0 ? 0 : 100 * $Difference / $Daily_Production_GWh)
' \
> type_and_production.csv
```

Now print

``` bash
mlr --csv cat type_and_production.csv
```

```
SFOE_Type,ENTSOE_Type,DailyProduction_GWh,HourlyProduction_GWh,Absolute_difference,Relative_difference
Speicherkraft,Hydro Pumped Storage,2177.1000000000004,750.0662699999997,1427.0337300000006,65.54745900509853
Flusskraft,Hydro Run-of-river and poundage,706.0999999999999,661.7663986239978,44.33360137600209,6.278657608837573
Speicherkraft,Hydro Water Reservoir,2177.1000000000004,992.9575699999995,1184.1424300000008,54.390814845436616
Kernkraft,Nuclear,1454.1000000000001,1458.4139899999996,-4.313989999999421,-0.2966776700364088
Photovoltaik,Solar,205.89999999999998,78.35501765500003,127.54498234499995,61.945110415250106
Wind,Wind Onshore,17.999999999999996,17.98906078800001,0.010939211999986043,0.06077339999992247
```

or prettier print via `--c2p`

``` bash
mlr --c2p cat type_and_production.csv
```

returns

```
SFOE_Type     ENTSOE_Type                     Daily_Production_GWh Hourly_Production_GWh Difference           Percentage
Speicherkraft Hydro Pumped Storage            2177.1000000000004   750.0662699999997     1427.0337300000006   65.54745900509853
Flusskraft    Hydro Run-of-river and poundage 706.0999999999999    661.7663986239978     44.33360137600209    6.278657608837573
Speicherkraft Hydro Water Reservoir           2177.1000000000004   992.9575699999995     1184.1424300000008   54.390814845436616
Kernkraft     Nuclear                         1454.1000000000001   1458.4139899999996    -4.313989999999421   -0.2966776700364088
Photovoltaik  Solar                           205.89999999999998   78.35501765500003     127.54498234499995   61.945110415250106
Wind          Wind Onshore                    17.999999999999996   17.98906078800001     0.010939211999986043 0.06077339999992247
```

or in Markdown

``` bash
mlr --csv --omd --ofmt '%.2f' cat type_and_production.csv
```

| SFOE_Type | ENTSOE_Type | Daily_Production_GWh | Hourly_Production_GWh | Difference | Percentage |
| --- | --- | --- | --- | --- | --- |
| Speicherkraft | Hydro Pumped Storage | 2177.10 | 750.07 | 1427.03 | 65.55 |
| Flusskraft | Hydro Run-of-river and poundage | 706.10 | 661.77 | 44.33 | 6.28 |
| Speicherkraft | Hydro Water Reservoir | 2177.10 | 992.96 | 1184.14 | 54.39 |
| Kernkraft | Nuclear | 1454.10 | 1458.41 | -4.31 | -0.30 |
| Photovoltaik | Solar | 205.90 | 78.36 | 127.54 | 61.95 |
| Wind | Wind Onshore | 18.00 | 17.99 | 0.01 | 0.06 |



### Further _cleaning_

Two of the _Hydro_ types among the ENTSOE classification _belong_ to SFOE's
_Speicherkraft_ !  Let's try to combine them.

### Production of "Speicherkraft" only

---
Input : `type_and_production.csv`  
Output : `type_and_production_Speicherkraft_Hourly_Production.csv`

---

Genrate the data

``` bash
mlr --csv filter '$SFOE_Type == "Speicherkraft"' \
then stats1 -a sum -f Hourly_Production_GWh -g SFOE_Type \
then put '$ENTSOE_Type = "Hydro: Pumped Storage + Water Reservoir"' \
then reorder -f SFOE_Type,ENTSOE_Type \
type_and_production.csv \
> type_and_production_Speicherkraft_Hourly_Production.csv

```

and print

``` bash
mlr --c2p --ofmt '%.2f' cat type_and_production_Speicherkraft_Hourly_Production.csv
```

returns

```
SFOE_Type     ENTSOE_Type                             Hourly_Production_GWh_sum
Speicherkraft Hydro: Pumped Storage + Water Reservoir 1743.02
```


### Production without "Speicherkraft"

---
Input : `type_and_production.csv`  
Output : `type_and_production_without_Speicherkraft`

---

Generate the wanted CSV file

``` bash
mlr --csv filter '$SFOE_Type != "Speicherkraft"' \
type_and_production.csv \
> type_and_production_without_Speicherkraft.csv
```

and print via

``` bash
mlr --c2p --ofmt '%.2f' cat type_and_production_without_Speicherkraft.csv
```

returns

```
SFOE_Type    ENTSOE_Type                     Daily_Production_GWh Hourly_Production_GWh Difference Percentage
Flusskraft   Hydro Run-of-river and poundage 706.10               661.77                44.33      6.28
Kernkraft    Nuclear                         1454.10              1458.41               -4.31      -0.30
Photovoltaik Solar                           205.90               78.36                 127.54     61.95
Wind         Wind Onshore                    18.00                17.99                 0.01       0.06
```


### Bring back the `DailyProduction_GWh`

---
Input :  `type_and_production.csv`, `type_and_production_Speicherkraft_Hourly_Production.csv`  
Output : `type_and_production_only_Speicherkraft.csv`

---

After the `stats1 -a sum` command, not all _fields_ are preserved.
Hence, we need to get the `DailyProduction_GWh` column back in manually !

Genrate a "join"ed CSV file

``` bash
mlr --csv then join --lk "Daily_Production_GWh" -j SFOE_Type -f type_and_production.csv type_and_production_Speicherkraft_Hourly_Production.csv \
| mlr --csv head -n 1   then put '
  $Difference = $Daily_Production_GWh - $Hourly_Production_GWh_sum;
  $Percentage = ($Daily_Production_GWh == 0 ? 0 : 100 * $Difference / $Daily_Production_GWh)
'
then rename Hourly_Production_GWh_sum,Hourly_Production_GWh
then reorder -f SFOE_Type,ENTSOE_Type > type_and_production_only_Speicherkraft.csv
```

and print

``` bash
mlr --c2p --ofmt '%.2f' cat type_and_production_only_Speicherkraft.csv
```

```
SFOE_Type     ENTSOE_Type                             Daily_Production_GWh Hourly_Production_GWh Difference Percentage
Speicherkraft Hydro: Pumped Storage + Water Reservoir 2177.10              1743.02               434.08     19.94
```


### Combine in one data file

---
Input :  `type_and_production_without_Speicherkraft.csv`, `type_and_production_only_Speicherkraft.csv`  
Output : `type_and_production_harmonised.csv`

---

Generate the "final" CSV file `type_and_production_harmonised.csv`

``` bash
mlr --csv cat \
then sort -f SFOE_Type \
type_and_production_without_Speicherkraft.csv \
type_and_production_only_Speicherkraft.csv \
> type_and_production_harmonised.csv
```

and print it

``` bash
mlr --c2p --ofmt '%.2f' --omd cat type_and_production_harmonised.csv
```


| SFOE_Type | ENTSOE_Type | Daily_Production_GWh | Hourly_Production_GWh | Difference | Percentage |
| --- | --- | --- | --- | --- | --- |
| Flusskraft | Hydro Run-of-river and poundage | 706.10 | 661.77 | 44.33 | 6.28 |
| Kernkraft | Nuclear | 1454.10 | 1458.41 | -4.31 | -0.30 |
| Photovoltaik | Solar | 205.90 | 78.36 | 127.54 | 61.95 |
| Speicherkraft | Hydro: Pumped Storage + Water Reservoir | 2177.10 | 1743.02 | 434.08 | 19.94 |
| Wind | Wind Onshore | 18.00 | 17.99 | 0.01 | 0.06 |


## Convert time series to wide CSV

*SFOE*

```
mlr --csv   sort -f datum,energietraeger   then nest --implode --values --across-fields -f energietraeger   stromproduktion.csv | mlr --csv rename datum,Date then reshape -s energietraeger,Produktion_GWh > stromproduktion_wide.csv
```

*ENTSO-E*
```
mlr --csv   cut -x -f UpdateTime then sort -f DateTime,Type   then nest --implode --values --across-fields -f Type   data/entsoe_generation_per_type_2026_01.csv   | mlr --csv reshape -s Type,Generation_MW > data/entsoe_generation_per_type_wide_2026_01.csv
```

## Compare hourly to daily

The daily time series from SFOE is the "truth" reference.
Let's aggregate the ENTSO-E data from hourly to daily and compare the sums for
each type.


```
mlr --c2p cat entsoe_generation_per_type_2026_01_daily.csv
```

```
Date       Hydro Pumped Storage Hydro Run-of-river and poundage Hydro Water Reservoir Nuclear            Solar              Wind Onshore
2026-01-01 3364.59              17817.699941999996              7708.32               47089.79           4334.332181        809.929896
2026-01-02 5767.000000000001    16765.60009                     9181.329999999998     47057.68           2157.0237300000003 835.6943990000001
2026-01-03 4405.989999999999    16534.200003                    8222.769999999999     47116.420000000006 1448.9675039999997 336.28556
2026-01-04 6638.249999999999    16698.60009                     17522.770000000004    47140.840000000004 2172.514831        86.41189899999998
2026-01-05 60718.909999999996   22843.999988999993              53405.200000000004    47120.87           1870.561648        120.863572
2026-01-06 56087.40999999999    27350.799919                    50029.22000000001     47094.479999999996 1616.3419540000002 213.361304
2026-01-07 30120.04             23420.299855999994              46964.119999999995    47110.25           2102.470898        359.892285
2026-01-08 44120.80000000001    23280.199937999994              48335.56              47055.890000000014 422.90077800000006 1089.8525180000001
2026-01-09 22028.450000000004   23210.400134999996              42649.78              46973.30000000001  1826.078797        1485.296912
2026-01-10 7016.81              19438.700062                    29296.450000000004    47132.109999999986 683.1590229999999  1265.784486
2026-01-11 3783.9500000000003   16124.299976000002              14172.650000000001    47131.86           898.9946060000001  261.491615
2026-01-12 41023.02             23222.799917                    50930.47000000001     47096.33999999999  1182.845463        1033.4175199999997
2026-01-13 38940.530000000006   26009.400015                    47424.22              47081.29           2445.7513239999994 1258.316618
2026-01-14 28744.740000000005   24210.799981999993              38730.85              47084.67000000001  3670.4754300000004 971.398285
2026-01-15 23051.979999999996   23645.100026999997              43010.15              47040.020000000004 4091.0804479999997 953.1150900000001
2026-01-16 26073.37             23545.899831                    40248.17              47131.549999999996 3504.919617        686.065091
2026-01-17 7527.529999999999    18103.600087999996              15556.849999999999    47121.77           2863.6410240000005 652.54321
2026-01-18 4674.650000000001    17066.500052000003              10247.560000000001    45454.64000000001  2187.598179        558.7421949999999
2026-01-19 22622.56             19553.599904                    31411.799999999996    47113.81999999999  3057.303321        384.55628800000005
2026-01-20 27648.12             22053.39994999999               37478.469999999994    47122.75000000001  3933.6287360000006 500.9403669999999
2026-01-21 38882.98             22667.000113                    46655.63              47121.369999999995 4301.053486000001  264.875465
2026-01-22 40052.51999999999    25291.299432                    47194.689999999995    47110.170000000006 3322.544314        150.868214
2026-01-23 40169.95999999999    24525.200125000003              45463.319999999985    47121.01           2927.958388000001  408.9926619999999
2026-01-24 9192.789999999999    18983.699879999993              21237.210000000006    47117.61           2265.4737580000005 238.26938700000002
2026-01-25 2838.13              16474.000051                    11243.26              47122.990000000005 3195.3008729999997 146.67754599999998
2026-01-26 31901.600000000006   21702.500055000004              35646.97              47069.67           3405.375681000001  354.60200900000007
2026-01-27 27252.77             22463.799855999998              30939.2               47121.939999999995 3181.651645        1445.3218990000005
2026-01-28 29844.860000000004   23880.299913999992              35546.340000000004    47094.270000000004 1120.210531        192.409131
2026-01-29 38854.850000000006   24773.099598000004              36540.729999999996    47056.31999999999  3151.939854        176.44766099999998
2026-01-30 21895.329999999998   21747.49980399999               28706.78              47095.340000000004 1982.8857410000003 654.174176
2026-01-31 4821.78              18362.100029999998              11256.730000000001    47112.96           3030.033892000001  92.463528
```


## References

[^0]: https://www.energiedashboard.admin.ch/strom/produktion
[^1]: https://opendata.swiss/en/dataset/energiedashboard-ch-stromproduktion-swissgrid
[^2]: https://opendata.swiss/en/dataset/energiedashboard-ch-stromproduktion-swissgrid/resource/0879ba1b-40ea-4e26-bba0-9cbb339f577e
[^3]: https://www.bfe-ogd.ch/ogd104_stromproduktion_swissgrid.csv
[^4]: https://www.swissgrid.ch/en/home/operation/grid-data/generation.html
[^5]: https://www.swissgrid.ch/en/home/operation/grid-data/generation.html#downloads
[^6]: Example Excel file [www.swissgrid.ch/dam/jcr:805e525c-44fe-4701-a227-6144193257ac/EnergieUebersichtCH_2026.xlsx](https://www.swissgrid.ch/dam/jcr:805e525c-44fe-4701-a227-6144193257ac/EnergieUebersichtCH_2026.xlsx)

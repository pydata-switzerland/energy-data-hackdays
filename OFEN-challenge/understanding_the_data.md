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

## Get the data

First, let's retrieve small samples of the data.

### Download data manually

The data :

[energiedashboard.ch: Stromproduktion Swissgrid-CSV](https://opendata.swiss/en/dataset/energiedashboard-ch-stromproduktion-swissgrid/resource/0879ba1b-40ea-4e26-bba0-9cbb339f577e)

and a quick-look on the downloaded data

```
mlr --csv head -n 3 ogd104_stromproduktion_swissgrid.csv
```

returns

```
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

```
curl -s -X 'GET'   'https://energiedashboard.ch/api/v1/datasets/stromproduktion-swissgrid/data?from=2026-01-01&offset=0&limit=1000'   -H 'accept: application/json'   > stromproduktion.json
```

and peak

```
mlr --ijson head stromproduktion.json
```

_This will return a large one-liner_ :

`data.1.datum=2026-03-13,data.1.energietraeger=Thermische,data.1.produktion_gwh=8.6,...`

Now, convert to CSV : 

```
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

```
mlr --csv \
stats1 -a sum -f Produktion_GWh  -g energietraeger \
then sort -f energietraeger \
stromproduktion.csv
```

returns

```
energietraeger,Produktion_GWh_sum
Flusskraft,3268.4999999999995
Kernkraft,5864.4
Photovoltaik,2332.6999999999994
Speicherkraft,5773.400000000004
Thermische,1152.100000000001
Wind,57.30000000000002
```

and

```
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

```
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

```
mlr --csv \
stats1 -a sum -f ActualGenerationOutput[MW] -g ProductionType \
then put '$Production_GWh = ${ActualGenerationOutput[MW]_sum} / 1000'  \
then cut -f ProductionType,Production_GWh 2026_01_AggregatedGenerationPerType_16.1.B_C_r3_AreaMapCode_CH.csv \
> 2026_01_AggregatedGenerationPerType_16.1.B_C_r3_AreaMapCode_CH_GWh.csv
```

Map SFOE to ENTSOE _Production Type_

```
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

```
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

```
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

```
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

```
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

```
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

```
mlr --csv filter '$SFOE_Type == "Speicherkraft"' \
then stats1 -a sum -f Hourly_Production_GWh -g SFOE_Type \
then put '$ENTSOE_Type = "Hydro: Pumped Storage + Water Reservoir"' \
then reorder -f SFOE_Type,ENTSOE_Type \
type_and_production.csv \
> type_and_production_Speicherkraft_Hourly_Production.csv

```

and print

```
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

```
mlr --csv filter '$SFOE_Type != "Speicherkraft"' \
type_and_production.csv \
> type_and_production_without_Speicherkraft.csv
```

and print via
```

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

```
mlr --csv then join --lk "Daily_Production_GWh" -j SFOE_Type -f type_and_production.csv type_and_production_Speicherkraft_Hourly_Production.csv \
| mlr --csv head -n 1   then put '
  $Difference = $Daily_Production_GWh - $Hourly_Production_GWh_sum;
  $Percentage = ($Daily_Production_GWh == 0 ? 0 : 100 * $Difference / $Daily_Production_GWh)
'
then rename Hourly_Production_GWh_sum,Hourly_Production_GWh
then reorder -f SFOE_Type,ENTSOE_Type > type_and_production_only_Speicherkraft.csv
```

and print

```
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

```
mlr --csv cat \
then sort -f SFOE_Type \
type_and_production_without_Speicherkraft.csv \
type_and_production_only_Speicherkraft.csv \
> type_and_production_harmonised.csv
```

and print it

```
mlr --c2p --ofmt '%.2f' --omd cat type_and_production_harmonised.csv
```


| SFOE_Type | ENTSOE_Type | Daily_Production_GWh | Hourly_Production_GWh | Difference | Percentage |
| --- | --- | --- | --- | --- | --- |
| Flusskraft | Hydro Run-of-river and poundage | 706.10 | 661.77 | 44.33 | 6.28 |
| Kernkraft | Nuclear | 1454.10 | 1458.41 | -4.31 | -0.30 |
| Photovoltaik | Solar | 205.90 | 78.36 | 127.54 | 61.95 |
| Speicherkraft | Hydro: Pumped Storage + Water Reservoir | 2177.10 | 1743.02 | 434.08 | 19.94 |
| Wind | Wind Onshore | 18.00 | 17.99 | 0.01 | 0.06 |

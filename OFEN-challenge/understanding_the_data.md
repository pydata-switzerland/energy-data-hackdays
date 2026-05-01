# Electricity production data

<!-- vim-markdown-toc Marked -->

* [The challenge](#the-challenge)
* [The Data](#the-data)
    * [SFOE](#sfoe)
        * [Swissgrid time series](#swissgrid-time-series)
            * [Sample statistics](#sample-statistics)
    * [ENTSO-E](#entso-e)
* [Get the data](#get-the-data)
    * [SFOE](#sfoe)
        * [Download CSV data](#download-csv-data)
        * [Get JSON data via the Web API](#get-json-data-via-the-web-api)
            * [Get JSON data](#get-json-data)
            * [Convert JSON to CSV](#convert-json-to-csv)
        * [Verify integrity ?](#verify-integrity-?)
        * [Work with a sample ?](#work-with-a-sample-?)
        * [Convert to wide table](#convert-to-wide-table)
    * [ENTSO-E](#entso-e)
        * [Manual download](#manual-download)
        * [Extract data for Switzerland](#extract-data-for-switzerland)
        * [Convert MWh to GWh](#convert-mwh-to-gwh)
        * [Convert to wide table](#convert-to-wide-table)
            * [Diagnose the data structure](#diagnose-the-data-structure)
            * [Unsparsify the data](#unsparsify-the-data)
            * [Reshape to wide table](#reshape-to-wide-table)
* [SFOE vs ENTSOE](#sfoe-vs-entsoe)
    * [Link SFOE and ENTSO-E data](#link-sfoe-and-entso-e-data)
        * [Electricity generation types](#electricity-generation-types)
        * [Mapping ENTSO-E to SFOE types](#mapping-entso-e-to-sfoe-types)
    * [Further _cleaning_](#further-_cleaning_)
        * ["Speicherkraft" production](#"speicherkraft"-production)
        * [Production without "Speicherkraft"](#production-without-"speicherkraft")
        * [Restore lost field `DailyProduction_GWh`](#restore-lost-field-`dailyproduction_gwh`)
    * [Combine in one data file](#combine-in-one-data-file)
* [Compare hourly to daily](#compare-hourly-to-daily)
* [Unsorted...](#unsorted...)
* [References](#references)

<!-- vim-markdown-toc -->

> **Under heavy development !**

---

Prototyping to understand the data for the challenge
owned by the Swiss Federal Office of Energy (SFOE).


## The challenge

> From [https://www.energydatahackdays.ch/challenges/estimating-hourly-energy-production-for-switzerland](https://www.energydatahackdays.ch/challenges/estimating-hourly-energy-production-for-switzerland)
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

## The Data

### SFOE

> Source : https://www.energiedashboard.admin.ch/strom/produktion

The _power production_ figures available through SFOE's
(Swiss Federal Office of Energy) energy dashboard 
(across multiple technologies such as hydro, nuclear, thermal, wind and PV)
are reportedly aggregated **daily** data.[^0]
The data are publicly accessible via (opendata.swiss)[opendata.swiss] [^1][^2]
in the form of comma-separated-values[^3].
The _provider_ of the data, however, is Swissgrid.[^4]  Read on the next
subsection about the _raw_ time series.

#### Swissgrid time series

The _raw_ time series for the daily aggregated data come from Swissgrid :

> Description from
[www.swissgrid.ch/en/home/operation/grid-data/generation.html#downloads](https://www.swissgrid.ch/en/home/operation/grid-data/generation.html#downloads)

> The total of the produced energy in the control block Switzerland.
> The aggregations of the feed-in sequences for the balancing groups
> are sent from the distribution network operators to Swissgrid.
> The sum contains all the energy produced and fed in the network.
> (Only productions plants equipped with load profile meters)

Looking closer at the _raw_ time series provided by Swissgrid
in form of Excel spreadsheets [^5]
their _original_ temporal resolution is **every 15'**[^6].

##### Sample statistics

Example statistics from the 2026 Swissgrid data (downloaded on April 21)
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

### ENTSO-E

[...]

## Get the data

### SFOE

#### Download CSV data

We download the daily _SFOE_ time series :

[energiedashboard.ch: Stromproduktion Swissgrid-CSV](https://opendata.swiss/en/dataset/energiedashboard-ch-stromproduktion-swissgrid/resource/0879ba1b-40ea-4e26-bba0-9cbb339f577e)

and have a quick-look on the downloaded data

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

#### Get JSON data via the Web API

---
Input : `https://energiedashboard.ch/api/v1/datasets/stromproduktion-swissgrid/data?from=2026-01-01&offset=0&limit=1000'`  
Output `stromproduktion.csv`

---

##### Get JSON data 

Following, let's retrieve **daily electricity production** totals for 2026

``` bash
curl -s -X 'GET'   'https://energiedashboard.ch/api/v1/datasets/stromproduktion-swissgrid/data?from=2026-01-01&offset=0&limit=1000'   -H 'accept: application/json'   > stromproduktion.json
```

and take a look at

``` bash
mlr --ijson head stromproduktion.json
```

_This will return a large one-liner_ :

`data.1.datum=2026-03-13,data.1.energietraeger=Thermische,data.1.produktion_gwh=8.6,...`

##### Convert JSON to CSV

Now, convert `stromproduktion.json` to CSV (new file named `stromproduktion.csv`) : 

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


#### Verify integrity ?

---
Input : `stromproduktion.csv`, `ogd104_stromproduktion_swissgrid.csv`  
Output : -

---

We _compare_ the Web-API retrieved data
`stromproduktion.csv`
to the manually downloaded sample data
`ogd104_stromproduktion_swissgrid.csv`,
to ensure we have the same numbers,
i.e. no errors during the JSON

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

#### Work with a sample ?

> ___Skip this section if working with a small sample is not of concern.___

---
Input : `stromproduktion.csv`  
Intermediate : `stromproduktion_2026_01.csv`  
Output : `stromproduktion_2026_01_GWh.csv`

---

For practical reasons, we can work with a smaller sample,
i.e. the January 2026 data.

``` bash
mlr --csv \
sort -f datum \
then filter '$datum =~ "2026-01"' \
stromproduktion.csv \
> stromproduktion_2026_01.csv
```

Actually save output to a new file

``` bash
mlr --csv \
stats1 -a sum -f Produktion_GWh  -g energietraeger \
then sort -f energietraeger \
then label Type,Production_GWh \
stromproduktion_2026_01.csv  
> stromproduktion_2026_01_GWh.csv
```

#### Convert to wide table

``` bash
mlr --csv \
sort -f datum,energietraeger \
then nest --implode --values --across-fields -f energietraeger \
stromproduktion.csv \
| mlr --csv rename datum,Date \
then reshape -s energietraeger,Produktion_GWh \
> stromproduktion_wide.csv
```


### ENTSO-E

#### Manual download

The full directory of the ENTSO-E data
can be downloaded manually
from the **File Library** of the Transparency Platform :

**File Browser Mode** > **TP_export** > `AggregatedGenerationPerType_16.1.B_C_r3`

These files are (TSV and not CSV, yet they are)
consistent in terms of their header,
i.e. the data-columns are :

``` bash
DateTime(UTC)
ResolutionCode
AreaCode
AreaDisplayNameAreaTypeCode
AreaMapCode
ProductionType
ActualGenerationOutput[MW]
ActualConsumption[MW]
UpdateTime(UTC)
```

In addition, the timestamps are all in UTC.
While the downloaded `.zip` file
(which is the complete folder with monthly time series per file)
is larg (~690MB) and needs some filtering to extract data for Switzerland.

> * This dataset is perhaps cleaner than files downloaded via the interactive map
@ [https://transparency.entsoe.eu/generation/actual/perType/generation?appState=%7B%22sa%22%3A%5B%22BZN%7C10YGR-HTSO-----Y%22%5D%2C%22st%22%3A%22BZN%22%2C%22mm%22%3Atrue%2C%22ma%22%3Afalse%2C%22sp%22%3A%22HALF%22%2C%22dt%22%3A%22CHART%22%2C%22df%22%3A%5B%222026-04-30%22%2C%222026-04-30%22%5D%2C%22tz%22%3A%22UTC%22%7D](https://transparency.entsoe.eu/generation/actual/perType/generation?appState=%7B%22sa%22%3A%5B%22BZN%7C10YGR-HTSO-----Y%22%5D%2C%22st%22%3A%22BZN%22%2C%22mm%22%3Atrue%2C%22ma%22%3Afalse%2C%22sp%22%3A%22HALF%22%2C%22dt%22%3A%22CHART%22%2C%22df%22%3A%5B%222026-04-30%22%2C%222026-04-30%22%5D%2C%22tz%22%3A%22UTC%22%7D).

Some metadata for `AggregatedGenerationPerType_16.1.B_C_r3` are available at

[Transparency Platform > Specifications > File Library extracts > AggregatedGenerationPerType-16-1-B-C-r3](https://transparencyplatform.zendesk.com/hc/en-us/articles/36493702227729-AggregatedGenerationPerType-16-1-B-C-r3)

---
Input : `2026_01_AggregatedGenerationPerType_16.1.B_C_r3_AreaMapCode.csv`  
Intermediate : `2026_01_AggregatedGenerationPerType_16.1.B_C_r3_AreaMapCode_CH_GWh.csv`  
Output : `entsoe_GWh.csv`

---

#### Extract data for Switzerland

```
mlr --t2c \
filter '$AreaMapCode == "CH"' \
then sort -f "DateTime(UTC)" \
*_AggregatedGenerationPerType_16.1.B_C_r3.csv \
> AggregatedGenerationPerType_16.1.B_C_r3_CH.csv
```

#### Convert MWh to GWh

and convert units to GWh while keeping only the columns : 
`DateTime(UTC)`, `ProductionType` and `Generation_GWh`

``` bash
mlr --csv \
put '$Generation_GWh = ${ActualGenerationOutput[MW]} / 1000'  \
then cut -f "DateTime(UTC)",ProductionType,Generation_GWh \
then rename "DateTime(UTC),DateTime,ProductionType,Type"  \
AggregatedGenerationPerType_16.1.B_C_r3_CH.csv \
> entsoe_aggregated_generation_per_type_GWh.csv
```


#### Convert to wide table

##### Diagnose the data structure

First we take a look at the uniue _types_ and their _counts_

``` bash
mlr --csv uniq -c -f Type entsoe_aggregated_generation_per_type_GWh.csv
```
```
Type,count
Solar,99286
Wind Onshore,99262
Fossil Gas,6215
Nuclear,95013
Hydro Pumped Storage,94941
Hydro Water Reservoir,94941
Hydro Run-of-river and poundage,92206
```

The *problem* is that the ENTSO-E time series are sparse.
The counts show that not every `DateTime` has data for every `Type`
(e.g., Solar appears 99k times vs. Fossil Gas only 6k).
In other words, the *problem* is that the ENTSO-E time series are sparse.
What is required, however, is a standard CSV with all types as columns,
even where data is absent.

##### Unsparsify the data

A `nest` operation will create varying field sets per row
(e.g. `DateTime,Solar` vs `DateTime,Fossil Gas,Solar`),
breaking the CSV's schema consistency.
The solution is to `unsparsify` the data after `nest` (or after `reshape`)
to fill missing fields with empty strings,
creating a consistent schema across all rows.

##### Reshape to wide table

``` bash
mlr --csv \
sort -f DateTime,Type \
then nest --implode --values --across-fields -f Type entsoe_aggregated_generation_per_type_GWh.csv \
| mlr --csv \
reshape -s Type,Generation_GWh \
then unsparsify \
> entsoe_hourly_generation_per_type.csv
```

> **How it works**
>
> Miller streams data record after record.
> Hence, we can `nest`, then `reshape` and finally `unsparsify`
> which will process each row to ensure internal consistency.
>
> - `nest --implode --values --across-fields -f Type` : pivots types into columns per DateTime, but sparsely.
> - `unsparsify` : adds missing type columns so every row has identical `Type` fields (`Solar`, `Wind Onshore`, etc.).
> - `reshape -s Type,Generation_GWh` sees stable input headers and outputs pivoted DateTime rows with Solar_Generation_GWh, Wind Onshore_Generation_GWh, etc..

Finally, our reshaped time series look as follows
(showing 3 lines from the `head` and `tail` of the data) : 

``` bash
mlr --c2m head -n 3 entsoe_hourly_generation_per_type.csv
```
| DateTime            | Solar                   | Wind Onshore | Fossil Gas | Nuclear | Hydro Pumped Storage | Hydro Water Reservoir | Hydro Run-of-river and poundage |
| ---                 | ---                     | ---          | ---        | ---     | ---                  | ---                   | ---                             |
| 2014-12-30 23:00:00 | 0.000029999999999999997 |              |            |         |                      |                       |                                 |
| 2014-12-31 00:00:00 | 0.00005                 |              |            |         |                      |                       |                                 |
| 2014-12-31 01:00:00 | 0.00007000000000000001  |              |            |         |                      |                       |                                 |



``` bash
mlr --c2m tail -n 3 entsoe_hourly_generation_per_type.csv
```
| DateTime | Solar | Wind Onshore | Fossil Gas | Nuclear | Hydro Pumped Storage | Hydro Water Reservoir | Hydro Run-of-river and poundage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-04-29 17:00:00 | 0.379468231 | 0.027049998999999998 |  | 2.5298000000000003 | 3.2977 | 2.31515 | 1.7917299800000002 |
| 2026-04-29 18:00:00 | 0.032936542000000006 | 0.0287 |  | 2.5335199999999998 | 3.54215 | 2.37668 | 1.794550048 |
| 2026-04-29 19:00:00 | 0 | 0.030600000000000002 |  |  |  |  | 1.7973499750000002 |


## SFOE vs ENTSOE

### Link SFOE and ENTSO-E data

Part of the preparative steps
is to understand the correspondence between definitions of energy generation types
in the SFOE and ENTSO-E time series.


#### Electricity generation types

The electricity generation types in 

- the _daily_ SFOE time series are :

    ```bash
    mlr --csv uniq -f Energietraeger ogd104_stromproduktion_swissgrid.csv
    ```
    ```
    Energietraeger
    Flusskraft
    Kernkraft
    Photovoltaik
    Speicherkraft
    Thermische
    Wind
    ```

- the _hourly_ ENTSO-E time series are :

    ``` bash
    mlr --csv sort -f Type then uniq -f Type entsoe_aggregated_generation_per_type_GWh.csv
    ```
    ```
    Type
    Fossil Gas
    Hydro Pumped Storage
    Hydro Run-of-river and poundage
    Hydro Water Reservoir
    Nuclear
    Solar
    Wind Onshore
    ```

#### Mapping ENTSO-E to SFOE types

Mapping the ENTSO-E _types_ to the SFOE ones in one table :

<!-- layed out in the column `Produktion_GWh` by SFOE to ENTSO-E _Production Type_ -->


| ENTSO-E                         | SFOE          |
|---------------------------------|---------------|
| Fossil Gas                      | Thermische    |
| Hydro Pumped Storage            | Speicherkraft |
| Hydro Run-of-river and poundage | Flusskraft    |
| Hydro Water Reservoir           | Speicherkraft |
| Nuclear                         | Kernkraft     |
| Solar                           | Photovoltaik  |
| Wind Onshore                    | Wind          |


and applying this mapping with Miller's help

``` bash
mlr --csv put '
  begin {
    @map["Fossil Gas"] = "Thermische";
    @map["Hydro Pumped Storage"] = "Speicherkraft";
    @map["Hydro Run-of-river and poundage"] = "Flusskraft";
    @map["Hydro Water Reservoir"] = "Speicherkraft";
    @map["Nuclear"] = "Kernkraft";
    @map["Solar"] = "Photovoltaik";
    @map["Wind Onshore"] = "Wind"
  }
  $MatchType = @map[$Type]
' \
entsoe_aggregated_generation_per_type_GWh.csv \
> entsoe_aggregated_generation_per_type_mapping_to_sfoe_GWh.csv`
```

``` bash
mlr --csv \
filter 'strptime($DateTime, "%Y-%m-%d %H:%M:%S") >= strptime("2015-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")' \
entsoe_aggregated_generation_per_type_mapping_to_SFOE_GWh.csv \
> entsoe_hourly_generation_per_type_mapping_to_SFOE_GWh.csv
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

Now we can compare the _daily_ (SFOE) and _hourly_ (ENTSO-E) time series
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

Now pretty-print via `--c2p`

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

or in Markdown and figures limited to two decimal digits

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

#### "Speicherkraft" production

---
Input : `type_and_production.csv`  
Output : `type_and_production_Speicherkraft_Hourly_Production.csv`

---

Generate the data

``` bash
mlr --csv filter '$SFOE_Type == "Speicherkraft"' \
then stats1 -a sum -f Hourly_Production_GWh -g SFOE_Type \
then put '$ENTSOE_Type = "Hydro: Pumped Storage + Water Reservoir"' \
then reorder -f SFOE_Type,ENTSOE_Type \
type_and_production.csv \
> type_and_production_Speicherkraft_Hourly_Production.csv

```

and print via

``` bash
mlr --c2p --ofmt '%.2f' cat type_and_production_Speicherkraft_Hourly_Production.csv
```

which returns

```
SFOE_Type     ENTSOE_Type                             Hourly_Production_GWh_sum
Speicherkraft Hydro: Pumped Storage + Water Reservoir 1743.02
```


#### Production without "Speicherkraft"

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


#### Restore lost field `DailyProduction_GWh`

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

## Unsorted...

_Stuff to clean-up_


```
❯ mlr --csv --ofmt '%.2f' label Date,"ENTSOE Pumped","ENTSOE Run-of-river","ENTSOE Reservoir","ENTSOE Nuclear","ENTSOE Solar","ENTSOE Wind","SFOE Flusskraft","SFOE Kernkraft","SFOE Photovoltaik","SFOE Speicherkraft","SFOE Thermische","SFOE Wind" then reorder -f Date,"SFOE Kernkraft","ENTSOE Nuclear","SFOE Photovoltaik","ENTSOE Solar","SFOE Wind","ENTSOE Wind","SFOE Flusskraft","ENTSOE Run-of-river","SFOE Speicherkraft","ENTSOE Reservoir","SFOE Thermische"   then put '$Kernkraft = ${SFOE Kernkraft} - ${ENTSOE Nuclear}; $Photovoltaik = ${SFOE Photovoltaik} - ${ENTSOE_Solar}; $Wind = ${ENTSOE Wind} - ${SFOE Wind}; $Flusskraft = ${SFOE Flusskraft} - ${ENTSOE Run-of-river}; $Speicherkraft = ${SFOE Speicherkraft} - ${ENTSOE Reservoir};'   then reorder -f Date,"SFOE Kernkraft","ENTSOE Nuclear",Kernkraft,"SFOE Photovoltaik","ENTSOE Solar",Photovoltaik,"SFOE Wind","ENTSOE Wind",Wind,"SFOE Flusskraft","ENTSOE Run-of-river",Flusskraft,"SFOE Speicherkraft","ENTSOE Reservoir",Speicherkraft  generation_per_type_2026_01.csv |mlr --c2m cat
```

| Date | SFOE Kernkraft | ENTSOE Nuclear | Kernkraft | SFOE Photovoltaik | ENTSOE Solar | Photovoltaik | SFOE Wind | ENTSOE Wind | Wind | SFOE Flusskraft | ENTSOE Run-of-river | Flusskraft | SFOE Speicherkraft | ENTSOE Reservoir | Speicherkraft | SFOE Thermische | ENTSOE Pumped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-01-01 | 47 | 47.09 | -0.09 | 11.40 | 4.33 | 11.40 | 0.80 | 0.81 | 0.01 | 18 | 17.82 | 0.18 | 25.50 | 7.71 | 17.79 | 11.30 | 3.36 |
| 2026-01-02 | 46.90 | 47.06 | -0.16 | 5.70 | 2.16 | 5.70 | 0.90 | 0.84 | -0.06 | 17.30 | 16.77 | 0.53 | 27.20 | 9.18 | 18.02 | 11.30 | 5.77 |
| 2026-01-03 | 47 | 47.12 | -0.12 | 3.80 | 1.45 | 3.80 | 0.30 | 0.34 | 0.04 | 16.90 | 16.53 | 0.37 | 24.30 | 8.22 | 16.08 | 11.30 | 4.41 |
| 2026-01-04 | 47 | 47.14 | -0.14 | 5.70 | 2.17 | 5.70 | 0.10 | 0.09 | -0.01 | 17.70 | 16.70 | 1.00 | 27.90 | 17.52 | 10.38 | 11.30 | 6.64 |
| 2026-01-05 | 47 | 47.12 | -0.12 | 4.90 | 1.87 | 4.90 | 0.10 | 0.12 | 0.02 | 25.30 | 22.84 | 2.46 | 140.30 | 53.41 | 86.89 | 11.30 | 60.72 |
| 2026-01-06 | 47 | 47.09 | -0.09 | 4.20 | 1.62 | 4.20 | 0.20 | 0.21 | 0.01 | 28.90 | 27.35 | 1.55 | 130.50 | 50.03 | 80.47 | 11.30 | 56.09 |
| 2026-01-07 | 47 | 47.11 | -0.11 | 5.50 | 2.10 | 5.50 | 0.30 | 0.36 | 0.06 | 25.50 | 23.42 | 2.08 | 95.70 | 46.96 | 48.74 | 11.30 | 30.12 |
| 2026-01-08 | 46.90 | 47.06 | -0.16 | 1.10 | 0.42 | 1.10 | 1 | 1.09 | 0.09 | 25.70 | 23.28 | 2.42 | 116.70 | 48.34 | 68.36 | 11.30 | 44.12 |
| 2026-01-09 | 46.80 | 46.97 | -0.17 | 4.80 | 1.83 | 4.80 | 1.50 | 1.49 | -0.01 | 25 | 23.21 | 1.79 | 79.70 | 42.65 | 37.05 | 11.30 | 22.03 |
| 2026-01-10 | 47 | 47.13 | -0.13 | 1.80 | 0.68 | 1.80 | 1.30 | 1.27 | -0.03 | 20.40 | 19.44 | 0.96 | 47.10 | 29.30 | 17.80 | 11.30 | 7.02 |
| 2026-01-11 | 47 | 47.13 | -0.13 | 2.40 | 0.90 | 2.40 | 0.30 | 0.26 | -0.04 | 17.30 | 16.12 | 1.18 | 24.90 | 14.17 | 10.73 | 11.30 | 3.78 |
| 2026-01-12 | 47 | 47.10 | -0.10 | 3.10 | 1.18 | 3.10 | 1 | 1.03 | 0.03 | 25.60 | 23.22 | 2.38 | 111.30 | 50.93 | 60.37 | 11.30 | 41.02 |
| 2026-01-13 | 46.90 | 47.08 | -0.18 | 6.40 | 2.45 | 6.40 | 1.20 | 1.26 | 0.06 | 29.40 | 26.01 | 3.39 | 101.80 | 47.42 | 54.38 | 11.30 | 38.94 |
| 2026-01-14 | 46.90 | 47.08 | -0.18 | 9.60 | 3.67 | 9.60 | 1 | 0.97 | -0.03 | 26.80 | 24.21 | 2.59 | 84.90 | 38.73 | 46.17 | 11.30 | 28.74 |
| 2026-01-15 | 46.90 | 47.04 | -0.14 | 10.80 | 4.09 | 10.80 | 0.90 | 0.95 | 0.05 | 26.10 | 23.65 | 2.45 | 79.30 | 43.01 | 36.29 | 11.30 | 23.05 |
| 2026-01-16 | 46.80 | 47.13 | -0.33 | 9.20 | 3.50 | 9.20 | 0.70 | 0.69 | -0.01 | 25.20 | 23.55 | 1.65 | 84.10 | 40.25 | 43.85 | 11.30 | 26.07 |
| 2026-01-17 | 46.90 | 47.12 | -0.22 | 7.50 | 2.86 | 7.50 | 0.60 | 0.65 | 0.05 | 19.40 | 18.10 | 1.30 | 29.70 | 15.56 | 14.14 | 11.30 | 7.53 |
| 2026-01-18 | 45.50 | 45.45 | 0.05 | 5.80 | 2.19 | 5.80 | 0.60 | 0.56 | -0.04 | 17.50 | 17.07 | 0.43 | 21 | 10.25 | 10.75 | 11.30 | 4.67 |
| 2026-01-19 | 47 | 47.11 | -0.11 | 8 | 3.06 | 8 | 0.40 | 0.38 | -0.02 | 20.10 | 19.55 | 0.55 | 65.80 | 31.41 | 34.39 | 11.30 | 22.62 |
| 2026-01-20 | 47 | 47.12 | -0.12 | 10.30 | 3.93 | 10.30 | 0.50 | 0.50 | 0.00 | 23.20 | 22.05 | 1.15 | 80 | 37.48 | 42.52 | 11.30 | 27.65 |
| 2026-01-21 | 47 | 47.12 | -0.12 | 11.30 | 4.30 | 11.30 | 0.30 | 0.26 | -0.04 | 25.10 | 22.67 | 2.43 | 102.40 | 46.66 | 55.74 | 11.30 | 38.88 |
| 2026-01-22 | 47 | 47.11 | -0.11 | 8.70 | 3.32 | 8.70 | 0.20 | 0.15 | -0.05 | 27 | 25.29 | 1.71 | 106.40 | 47.19 | 59.21 | 11.30 | 40.05 |
| 2026-01-23 | 47 | 47.12 | -0.12 | 7.70 | 2.93 | 7.70 | 0.40 | 0.41 | 0.01 | 26.20 | 24.53 | 1.67 | 105.90 | 45.46 | 60.44 | 11.30 | 40.17 |
| 2026-01-24 | 47 | 47.12 | -0.12 | 6 | 2.27 | 6 | 0.20 | 0.24 | 0.04 | 19.90 | 18.98 | 0.92 | 37 | 21.24 | 15.76 | 11.30 | 9.19 |
| 2026-01-25 | 47 | 47.12 | -0.12 | 8.40 | 3.20 | 8.40 | 0.20 | 0.15 | -0.05 | 17.10 | 16.47 | 0.63 | 19.10 | 11.24 | 7.86 | 11.30 | 2.84 |
| 2026-01-26 | 46.90 | 47.07 | -0.17 | 9 | 3.41 | 9 | 0.30 | 0.35 | 0.05 | 22.80 | 21.70 | 1.10 | 82.80 | 35.65 | 47.15 | 11.30 | 31.90 |
| 2026-01-27 | 47 | 47.12 | -0.12 | 8.40 | 3.18 | 8.40 | 1.50 | 1.45 | -0.05 | 23.80 | 22.46 | 1.34 | 69.90 | 30.94 | 38.96 | 11.30 | 27.25 |
| 2026-01-28 | 47 | 47.09 | -0.09 | 2.90 | 1.12 | 2.90 | 0.20 | 0.19 | -0.01 | 25 | 23.88 | 1.12 | 80.40 | 35.55 | 44.85 | 11.30 | 29.84 |
| 2026-01-29 | 46.90 | 47.06 | -0.16 | 8.30 | 3.15 | 8.30 | 0.20 | 0.18 | -0.02 | 25.80 | 24.77 | 1.03 | 92 | 36.54 | 55.46 | 11.30 | 38.85 |
| 2026-01-30 | 46.90 | 47.10 | -0.20 | 5.20 | 1.98 | 5.20 | 0.70 | 0.65 | -0.05 | 23 | 21.75 | 1.25 | 61 | 28.71 | 32.29 | 11.30 | 21.90 |
| 2026-01-31 | 46.90 | 47.11 | -0.21 | 8 | 3.03 | 8 | 0.10 | 0.09 | -0.01 | 19.10 | 18.36 | 0.74 | 22.50 | 11.26 | 11.24 | 11.30 | 4.82 |


```
mlr --c2m cat scaling_factors.csv
```

| Date | SFOE Kernkraft | ENTSOE Nuclear | SFOE Photovoltaik | ENTSOE Solar | SFOE Wind | ENTSOE Wind | SFOE Flusskraft | ENTSOE Run-of-river | SFOE Speicherkraft | ENTSOE Reservoir | SFOE Thermische | ENTSOE Pumped | Flusskraft_Scale | Speicherkraft_Scale | Total_ENTSOE | Total_SFOE | Total_Scale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-01-01 | 47 | 47.09 | 11.40 | 4.33 | 0.80 | 0.81 | 18 | 17.82 | 25.50 | 7.71 | 11.30 | 3.36 | 1.0101010101010102 | 3.307392996108949 | 77.76 | 102.7 | 1.320730452674897 |
| 2026-01-02 | 46.90 | 47.06 | 5.70 | 2.16 | 0.90 | 0.84 | 17.30 | 16.77 | 27.20 | 9.18 | 11.30 | 5.77 | 1.0316040548598688 | 2.962962962962963 | 76.01 | 98.00000000000001 | 1.2893040389422445 |
| 2026-01-03 | 47 | 47.12 | 3.80 | 1.45 | 0.30 | 0.34 | 16.90 | 16.53 | 24.30 | 8.22 | 11.30 | 4.41 | 1.0223835450695704 | 2.9562043795620436 | 73.66000000000001 | 92.3 | 1.253054575074667 |
| 2026-01-04 | 47 | 47.14 | 5.70 | 2.17 | 0.10 | 0.09 | 17.70 | 16.70 | 27.90 | 17.52 | 11.30 | 6.64 | 1.0598802395209581 | 1.5924657534246576 | 83.62 | 98.39999999999999 | 1.17675197321215 |
| 2026-01-05 | 47 | 47.12 | 4.90 | 1.87 | 0.10 | 0.12 | 25.30 | 22.84 | 140.30 | 53.41 | 11.30 | 60.72 | 1.1077057793345009 | 2.6268489046994947 | 125.36000000000001 | 217.60000000000002 | 1.7358008934269304 |
| 2026-01-06 | 47 | 47.09 | 4.20 | 1.62 | 0.20 | 0.21 | 28.90 | 27.35 | 130.50 | 50.03 | 11.30 | 56.09 | 1.0566727605118829 | 2.608434939036578 | 126.3 | 210.79999999999998 | 1.6690419635787805 |
| 2026-01-07 | 47 | 47.11 | 5.50 | 2.10 | 0.30 | 0.36 | 25.50 | 23.42 | 95.70 | 46.96 | 11.30 | 30.12 | 1.0888129803586677 | 2.0379045996592846 | 119.94999999999999 | 174 | 1.4506044185077116 |
| 2026-01-08 | 46.90 | 47.06 | 1.10 | 0.42 | 1 | 1.09 | 25.70 | 23.28 | 116.70 | 48.34 | 11.30 | 44.12 | 1.1039518900343641 | 2.41414977244518 | 120.19000000000001 | 191.4 | 1.5924785755886512 |
| 2026-01-09 | 46.80 | 46.97 | 4.80 | 1.83 | 1.50 | 1.49 | 25 | 23.21 | 79.70 | 42.65 | 11.30 | 22.03 | 1.0771219302024988 | 1.8686987104337633 | 116.14999999999999 | 157.8 | 1.3585880327163153 |
| 2026-01-10 | 47 | 47.13 | 1.80 | 0.68 | 1.30 | 1.27 | 20.40 | 19.44 | 47.10 | 29.30 | 11.30 | 7.02 | 1.0493827160493825 | 1.6075085324232081 | 97.82000000000001 | 117.6 | 1.2022081373952156 |
| 2026-01-11 | 47 | 47.13 | 2.40 | 0.90 | 0.30 | 0.26 | 17.30 | 16.12 | 24.90 | 14.17 | 11.30 | 3.78 | 1.0732009925558312 | 1.7572335920959774 | 78.58000000000001 | 91.9 | 1.1695087808602698 |
| 2026-01-12 | 47 | 47.10 | 3.10 | 1.18 | 1 | 1.03 | 25.60 | 23.22 | 111.30 | 50.93 | 11.30 | 41.02 | 1.1024978466838933 | 2.18535244453171 | 123.46000000000001 | 188 | 1.522760408229386 |
| 2026-01-13 | 46.90 | 47.08 | 6.40 | 2.45 | 1.20 | 1.26 | 29.40 | 26.01 | 101.80 | 47.42 | 11.30 | 38.94 | 1.1303344867358707 | 2.1467735132855332 | 124.22000000000001 | 185.7 | 1.4949283529222346 |
| 2026-01-14 | 46.90 | 47.08 | 9.60 | 3.67 | 1 | 0.97 | 26.80 | 24.21 | 84.90 | 38.73 | 11.30 | 28.74 | 1.10698058653449 | 2.192099147947328 | 114.66 | 169.2 | 1.4756671899529041 |
| 2026-01-15 | 46.90 | 47.04 | 10.80 | 4.09 | 0.90 | 0.95 | 26.10 | 23.65 | 79.30 | 43.01 | 11.30 | 23.05 | 1.1035940803382664 | 1.8437572657521506 | 118.74 | 164.00000000000003 | 1.3811689405423617 |
| 2026-01-16 | 46.80 | 47.13 | 9.20 | 3.50 | 0.70 | 0.69 | 25.20 | 23.55 | 84.10 | 40.25 | 11.30 | 26.07 | 1.070063694267516 | 2.08944099378882 | 115.12 | 165.99999999999997 | 1.4419735927727586 |
| 2026-01-17 | 46.90 | 47.12 | 7.50 | 2.86 | 0.60 | 0.65 | 19.40 | 18.10 | 29.70 | 15.56 | 11.30 | 7.53 | 1.0718232044198894 | 1.9087403598971722 | 84.29 | 104.1 | 1.2350219480365403 |
| 2026-01-18 | 45.50 | 45.45 | 5.80 | 2.19 | 0.60 | 0.56 | 17.50 | 17.07 | 21 | 10.25 | 11.30 | 4.67 | 1.0251903925014645 | 2.048780487804878 | 75.52000000000001 | 90.39999999999999 | 1.1970338983050846 |
| 2026-01-19 | 47 | 47.11 | 8 | 3.06 | 0.40 | 0.38 | 20.10 | 19.55 | 65.80 | 31.41 | 11.30 | 22.62 | 1.0281329923273657 | 2.0948742438713785 | 101.50999999999999 | 141.3 | 1.3919810856073296 |
| 2026-01-20 | 47 | 47.12 | 10.30 | 3.93 | 0.50 | 0.50 | 23.20 | 22.05 | 80 | 37.48 | 11.30 | 27.65 | 1.0521541950113378 | 2.1344717182497335 | 111.08000000000001 | 161 | 1.4494058336334172 |
| 2026-01-21 | 47 | 47.12 | 11.30 | 4.30 | 0.30 | 0.26 | 25.10 | 22.67 | 102.40 | 46.66 | 11.30 | 38.88 | 1.1071901191001323 | 2.194599228461209 | 121.00999999999999 | 186.10000000000002 | 1.5378894306255684 |
| 2026-01-22 | 47 | 47.11 | 8.70 | 3.32 | 0.20 | 0.15 | 27 | 25.29 | 106.40 | 47.19 | 11.30 | 40.05 | 1.0676156583629894 | 2.2547149819877097 | 123.05999999999999 | 189.29999999999998 | 1.5382740126767431 |
| 2026-01-23 | 47 | 47.12 | 7.70 | 2.93 | 0.40 | 0.41 | 26.20 | 24.53 | 105.90 | 45.46 | 11.30 | 40.17 | 1.0680799021606195 | 2.3295204575450947 | 120.45000000000002 | 187.2 | 1.5541718555417183 |
| 2026-01-24 | 47 | 47.12 | 6 | 2.27 | 0.20 | 0.24 | 19.90 | 18.98 | 37 | 21.24 | 11.30 | 9.19 | 1.048472075869336 | 1.7419962335216574 | 89.85 | 110.10000000000001 | 1.2253756260434059 |
| 2026-01-25 | 47 | 47.12 | 8.40 | 3.20 | 0.20 | 0.15 | 17.10 | 16.47 | 19.10 | 11.24 | 11.30 | 2.84 | 1.0382513661202188 | 1.699288256227758 | 78.18 | 91.80000000000001 | 1.1742133537989257 |
| 2026-01-26 | 46.90 | 47.07 | 9 | 3.41 | 0.30 | 0.35 | 22.80 | 21.70 | 82.80 | 35.65 | 11.30 | 31.90 | 1.0506912442396314 | 2.3225806451612905 | 108.17999999999998 | 161.8 | 1.4956553891662048 |
| 2026-01-27 | 47 | 47.12 | 8.40 | 3.18 | 1.50 | 1.45 | 23.80 | 22.46 | 69.90 | 30.94 | 11.30 | 27.25 | 1.0596616206589493 | 2.2592113768584356 | 105.15000000000002 | 150.6 | 1.432239657631954 |
| 2026-01-28 | 47 | 47.09 | 2.90 | 1.12 | 0.20 | 0.19 | 25 | 23.88 | 80.40 | 35.55 | 11.30 | 29.84 | 1.0469011725293134 | 2.2616033755274265 | 107.83 | 155.5 | 1.4420847630529539 |
| 2026-01-29 | 46.90 | 47.06 | 8.30 | 3.15 | 0.20 | 0.18 | 25.80 | 24.77 | 92 | 36.54 | 11.30 | 38.85 | 1.04158255954784 | 2.5177887246852766 | 111.70000000000002 | 173.2 | 1.5505819158460157 |
| 2026-01-30 | 46.90 | 47.10 | 5.20 | 1.98 | 0.70 | 0.65 | 23 | 21.75 | 61 | 28.71 | 11.30 | 21.90 | 1.0574712643678161 | 2.124695228143504 | 100.19000000000001 | 136.79999999999998 | 1.3654057291146817 |
| 2026-01-31 | 46.90 | 47.11 | 8 | 3.03 | 0.10 | 0.09 | 19.10 | 18.36 | 22.50 | 11.26 | 11.30 | 4.82 | 1.0403050108932463 | 1.9982238010657194 | 79.85 | 96.6 | 1.2097683155917345 |



```
./derive_scaling_factor_statistics.sh |mlr --c2m cat
```

| Flusskraft_Scale_mean | Flusskraft_Scale_stddev | Flusskraft_Scale_min | Flusskraft_Scale_p50 | Flusskraft_Scale_max | Total_Scale_mean | Total_Scale_stddev | Total_Scale_min | Total_Scale_p50 | Total_Scale_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.064 | 0.030 | 1.010 | 1.060 | 1.130 | 1.398 | 0.156 | 1.170 | 1.432 | 1.736 |



```
mlr --c2m cat entsoe_generation_per_type_2026_01_daily_scaled.csv
```

| Date | Hydro Pumped Storage | Hydro Run-of-river and poundage | Hydro Water Reservoir | Nuclear | Solar | Wind Onshore | SFOE Kernkraft | ENTSOE Nuclear | SFOE Photovoltaik | ENTSOE Solar | SFOE Wind | ENTSOE Wind | SFOE Flusskraft | ENTSOE Run-of-river | SFOE Speicherkraft | ENTSOE Reservoir | SFOE Thermische | ENTSOE Pumped | Flusskraft_Scale | Speicherkraft_Scale | Total_ENTSOE | Total_SFOE | Total_Scale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-01-01 | 3.36 | 18 | 25.5 | 47.09 | 4.33 | 0.81 | 47 | 47.09 | 11.40 | 4.33 | 0.80 | 0.81 | 18 | 17.82 | 25.50 | 7.71 | 11.30 | 3.36 | 1.0101010101010102 | 3.307392996108949 | 77.76 | 102.7 | 1.320730452674897 |
| 2026-01-02 | 5.77 | 17.3 | 27.2 | 47.06 | 2.16 | 0.84 | 46.90 | 47.06 | 5.70 | 2.16 | 0.90 | 0.84 | 17.30 | 16.77 | 27.20 | 9.18 | 11.30 | 5.77 | 1.0316040548598688 | 2.962962962962963 | 76.01 | 98.00000000000001 | 1.2893040389422445 |
| 2026-01-03 | 4.41 | 16.9 | 24.3 | 47.12 | 1.45 | 0.34 | 47 | 47.12 | 3.80 | 1.45 | 0.30 | 0.34 | 16.90 | 16.53 | 24.30 | 8.22 | 11.30 | 4.41 | 1.0223835450695704 | 2.9562043795620436 | 73.66000000000001 | 92.3 | 1.253054575074667 |
| 2026-01-04 | 6.64 | 17.7 | 27.9 | 47.14 | 2.17 | 0.09 | 47 | 47.14 | 5.70 | 2.17 | 0.10 | 0.09 | 17.70 | 16.70 | 27.90 | 17.52 | 11.30 | 6.64 | 1.0598802395209581 | 1.5924657534246576 | 83.62 | 98.39999999999999 | 1.17675197321215 |
| 2026-01-05 | 60.72 | 25.3 | 140.3 | 47.12 | 1.87 | 0.12 | 47 | 47.12 | 4.90 | 1.87 | 0.10 | 0.12 | 25.30 | 22.84 | 140.30 | 53.41 | 11.30 | 60.72 | 1.1077057793345009 | 2.6268489046994947 | 125.36000000000001 | 217.60000000000002 | 1.7358008934269304 |
| 2026-01-06 | 56.09 | 28.9 | 130.5 | 47.09 | 1.62 | 0.21 | 47 | 47.09 | 4.20 | 1.62 | 0.20 | 0.21 | 28.90 | 27.35 | 130.50 | 50.03 | 11.30 | 56.09 | 1.0566727605118829 | 2.608434939036578 | 126.3 | 210.79999999999998 | 1.6690419635787805 |
| 2026-01-07 | 30.12 | 25.5 | 95.7 | 47.11 | 2.10 | 0.36 | 47 | 47.11 | 5.50 | 2.10 | 0.30 | 0.36 | 25.50 | 23.42 | 95.70 | 46.96 | 11.30 | 30.12 | 1.0888129803586677 | 2.0379045996592846 | 119.94999999999999 | 174 | 1.4506044185077116 |
| 2026-01-08 | 44.12 | 25.7 | 116.7 | 47.06 | 0.42 | 1.09 | 46.90 | 47.06 | 1.10 | 0.42 | 1 | 1.09 | 25.70 | 23.28 | 116.70 | 48.34 | 11.30 | 44.12 | 1.1039518900343641 | 2.41414977244518 | 120.19000000000001 | 191.4 | 1.5924785755886512 |
| 2026-01-09 | 22.03 | 24.999999999999996 | 79.7 | 46.97 | 1.83 | 1.49 | 46.80 | 46.97 | 4.80 | 1.83 | 1.50 | 1.49 | 25 | 23.21 | 79.70 | 42.65 | 11.30 | 22.03 | 1.0771219302024988 | 1.8686987104337633 | 116.14999999999999 | 157.8 | 1.3585880327163153 |
| 2026-01-10 | 7.02 | 20.4 | 47.1 | 47.13 | 0.68 | 1.27 | 47 | 47.13 | 1.80 | 0.68 | 1.30 | 1.27 | 20.40 | 19.44 | 47.10 | 29.30 | 11.30 | 7.02 | 1.0493827160493825 | 1.6075085324232081 | 97.82000000000001 | 117.6 | 1.2022081373952156 |
| 2026-01-11 | 3.78 | 17.3 | 24.9 | 47.13 | 0.90 | 0.26 | 47 | 47.13 | 2.40 | 0.90 | 0.30 | 0.26 | 17.30 | 16.12 | 24.90 | 14.17 | 11.30 | 3.78 | 1.0732009925558312 | 1.7572335920959774 | 78.58000000000001 | 91.9 | 1.1695087808602698 |
| 2026-01-12 | 41.02 | 25.6 | 111.3 | 47.10 | 1.18 | 1.03 | 47 | 47.10 | 3.10 | 1.18 | 1 | 1.03 | 25.60 | 23.22 | 111.30 | 50.93 | 11.30 | 41.02 | 1.1024978466838933 | 2.18535244453171 | 123.46000000000001 | 188 | 1.522760408229386 |
| 2026-01-13 | 38.94 | 29.4 | 101.79999999999998 | 47.08 | 2.45 | 1.26 | 46.90 | 47.08 | 6.40 | 2.45 | 1.20 | 1.26 | 29.40 | 26.01 | 101.80 | 47.42 | 11.30 | 38.94 | 1.1303344867358707 | 2.1467735132855332 | 124.22000000000001 | 185.7 | 1.4949283529222346 |
| 2026-01-14 | 28.74 | 26.8 | 84.9 | 47.08 | 3.67 | 0.97 | 46.90 | 47.08 | 9.60 | 3.67 | 1 | 0.97 | 26.80 | 24.21 | 84.90 | 38.73 | 11.30 | 28.74 | 1.10698058653449 | 2.192099147947328 | 114.66 | 169.2 | 1.4756671899529041 |
| 2026-01-15 | 23.05 | 26.1 | 79.3 | 47.04 | 4.09 | 0.95 | 46.90 | 47.04 | 10.80 | 4.09 | 0.90 | 0.95 | 26.10 | 23.65 | 79.30 | 43.01 | 11.30 | 23.05 | 1.1035940803382664 | 1.8437572657521506 | 118.74 | 164.00000000000003 | 1.3811689405423617 |
| 2026-01-16 | 26.07 | 25.2 | 84.1 | 47.13 | 3.50 | 0.69 | 46.80 | 47.13 | 9.20 | 3.50 | 0.70 | 0.69 | 25.20 | 23.55 | 84.10 | 40.25 | 11.30 | 26.07 | 1.070063694267516 | 2.08944099378882 | 115.12 | 165.99999999999997 | 1.4419735927727586 |
| 2026-01-17 | 7.53 | 19.4 | 29.7 | 47.12 | 2.86 | 0.65 | 46.90 | 47.12 | 7.50 | 2.86 | 0.60 | 0.65 | 19.40 | 18.10 | 29.70 | 15.56 | 11.30 | 7.53 | 1.0718232044198894 | 1.9087403598971722 | 84.29 | 104.1 | 1.2350219480365403 |
| 2026-01-18 | 4.67 | 17.5 | 21 | 45.45 | 2.19 | 0.56 | 45.50 | 45.45 | 5.80 | 2.19 | 0.60 | 0.56 | 17.50 | 17.07 | 21 | 10.25 | 11.30 | 4.67 | 1.0251903925014645 | 2.048780487804878 | 75.52000000000001 | 90.39999999999999 | 1.1970338983050846 |
| 2026-01-19 | 22.62 | 20.099999999999998 | 65.8 | 47.11 | 3.06 | 0.38 | 47 | 47.11 | 8 | 3.06 | 0.40 | 0.38 | 20.10 | 19.55 | 65.80 | 31.41 | 11.30 | 22.62 | 1.0281329923273657 | 2.0948742438713785 | 101.50999999999999 | 141.3 | 1.3919810856073296 |
| 2026-01-20 | 27.65 | 23.2 | 80 | 47.12 | 3.93 | 0.50 | 47 | 47.12 | 10.30 | 3.93 | 0.50 | 0.50 | 23.20 | 22.05 | 80 | 37.48 | 11.30 | 27.65 | 1.0521541950113378 | 2.1344717182497335 | 111.08000000000001 | 161 | 1.4494058336334172 |
| 2026-01-21 | 38.88 | 25.1 | 102.39999999999999 | 47.12 | 4.30 | 0.26 | 47 | 47.12 | 11.30 | 4.30 | 0.30 | 0.26 | 25.10 | 22.67 | 102.40 | 46.66 | 11.30 | 38.88 | 1.1071901191001323 | 2.194599228461209 | 121.00999999999999 | 186.10000000000002 | 1.5378894306255684 |
| 2026-01-22 | 40.05 | 27.000000000000004 | 106.40000000000002 | 47.11 | 3.32 | 0.15 | 47 | 47.11 | 8.70 | 3.32 | 0.20 | 0.15 | 27 | 25.29 | 106.40 | 47.19 | 11.30 | 40.05 | 1.0676156583629894 | 2.2547149819877097 | 123.05999999999999 | 189.29999999999998 | 1.5382740126767431 |
| 2026-01-23 | 40.17 | 26.2 | 105.9 | 47.12 | 2.93 | 0.41 | 47 | 47.12 | 7.70 | 2.93 | 0.40 | 0.41 | 26.20 | 24.53 | 105.90 | 45.46 | 11.30 | 40.17 | 1.0680799021606195 | 2.3295204575450947 | 120.45000000000002 | 187.2 | 1.5541718555417183 |
| 2026-01-24 | 9.19 | 19.9 | 37 | 47.12 | 2.27 | 0.24 | 47 | 47.12 | 6 | 2.27 | 0.20 | 0.24 | 19.90 | 18.98 | 37 | 21.24 | 11.30 | 9.19 | 1.048472075869336 | 1.7419962335216574 | 89.85 | 110.10000000000001 | 1.2253756260434059 |
| 2026-01-25 | 2.84 | 17.1 | 19.1 | 47.12 | 3.20 | 0.15 | 47 | 47.12 | 8.40 | 3.20 | 0.20 | 0.15 | 17.10 | 16.47 | 19.10 | 11.24 | 11.30 | 2.84 | 1.0382513661202188 | 1.699288256227758 | 78.18 | 91.80000000000001 | 1.1742133537989257 |
| 2026-01-26 | 31.90 | 22.8 | 82.8 | 47.07 | 3.41 | 0.35 | 46.90 | 47.07 | 9 | 3.41 | 0.30 | 0.35 | 22.80 | 21.70 | 82.80 | 35.65 | 11.30 | 31.90 | 1.0506912442396314 | 2.3225806451612905 | 108.17999999999998 | 161.8 | 1.4956553891662048 |
| 2026-01-27 | 27.25 | 23.8 | 69.9 | 47.12 | 3.18 | 1.45 | 47 | 47.12 | 8.40 | 3.18 | 1.50 | 1.45 | 23.80 | 22.46 | 69.90 | 30.94 | 11.30 | 27.25 | 1.0596616206589493 | 2.2592113768584356 | 105.15000000000002 | 150.6 | 1.432239657631954 |
| 2026-01-28 | 29.84 | 25.000000000000004 | 80.4 | 47.09 | 1.12 | 0.19 | 47 | 47.09 | 2.90 | 1.12 | 0.20 | 0.19 | 25 | 23.88 | 80.40 | 35.55 | 11.30 | 29.84 | 1.0469011725293134 | 2.2616033755274265 | 107.83 | 155.5 | 1.4420847630529539 |
| 2026-01-29 | 38.85 | 25.799999999999997 | 92 | 47.06 | 3.15 | 0.18 | 46.90 | 47.06 | 8.30 | 3.15 | 0.20 | 0.18 | 25.80 | 24.77 | 92 | 36.54 | 11.30 | 38.85 | 1.04158255954784 | 2.5177887246852766 | 111.70000000000002 | 173.2 | 1.5505819158460157 |
| 2026-01-30 | 21.90 | 23 | 61.00000000000001 | 47.10 | 1.98 | 0.65 | 46.90 | 47.10 | 5.20 | 1.98 | 0.70 | 0.65 | 23 | 21.75 | 61 | 28.71 | 11.30 | 21.90 | 1.0574712643678161 | 2.124695228143504 | 100.19000000000001 | 136.79999999999998 | 1.3654057291146817 |
| 2026-01-31 | 4.82 | 19.1 | 22.5 | 47.11 | 3.03 | 0.09 | 46.90 | 47.11 | 8 | 3.03 | 0.10 | 0.09 | 19.10 | 18.36 | 22.50 | 11.26 | 11.30 | 4.82 | 1.0403050108932463 | 1.9982238010657194 | 79.85 | 96.6 | 1.2097683155917345 |



```
mlr --csv put '@dt = strptime($DateTime, "%Y-%m-%d %H:%M:%S"); $Date = strftime(@dt, "%Y-%m-%d")' entsoe_generation_per_type_2026_01_daily_scaled.csv |mlr --csv stats1 -a sum --grfx "Date$" | mlr --c2x --ofmt '%.2f' cat
```

```
Date                                (error)
Hydro Pumped Storage_sum            750.04
Hydro Run-of-river and poundage_sum 706.10
Hydro Water Reservoir_sum           2177.10
Nuclear_sum                         1458.39
Solar_sum                           78.35
Wind Onshore_sum                    17.99
SFOE Kernkraft_sum                  1454.10
ENTSOE Nuclear_sum                  1458.39
SFOE Photovoltaik_sum               205.90
ENTSOE Solar_sum                    78.35
SFOE Wind_sum                       18.00
ENTSOE Wind_sum                     17.99
SFOE Flusskraft_sum                 706.10
ENTSOE Run-of-river_sum             661.75
SFOE Speicherkraft_sum              2177.10
ENTSOE Reservoir_sum                992.97
SFOE Thermische_sum                 350.30
ENTSOE Pumped_sum                   750.04
Flusskraft_Scale_sum                33.00
Speicherkraft_Scale_sum             68.09
Total_ENTSOE_sum                    3209.45
Total_SFOE_sum                      4561.20
Total_Scale_sum                     43.33
```

## References

[^0]: https://www.energiedashboard.admin.ch/strom/produktion
[^1]: https://opendata.swiss/en/dataset/energiedashboard-ch-stromproduktion-swissgrid
[^2]: https://opendata.swiss/en/dataset/energiedashboard-ch-stromproduktion-swissgrid/resource/0879ba1b-40ea-4e26-bba0-9cbb339f577e
[^3]: https://www.bfe-ogd.ch/ogd104_stromproduktion_swissgrid.csv
[^4]: https://www.swissgrid.ch/en/home/operation/grid-data/generation.html
[^5]: https://www.swissgrid.ch/en/home/operation/grid-data/generation.html#downloads
[^6]: Example Excel file [www.swissgrid.ch/dam/jcr:805e525c-44fe-4701-a227-6144193257ac/EnergieUebersichtCH_2026.xlsx](https://www.swissgrid.ch/dam/jcr:805e525c-44fe-4701-a227-6144193257ac/EnergieUebersichtCH_2026.xlsx)

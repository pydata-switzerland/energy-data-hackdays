# Estimating Hourly Energy Production for Switzerland

challenge description: https://www.energydatahackdays.ch/challenges/estimating-hourly-energy-production-for-switzerland

## [datasets](./datasets/)

datasets currently present under [./datasets/entsoe](./datasets/entsoe)  were fetched manually :point_down: 

### ENTSO-E

#### manual download 

 from https://transparency.entsoe.eu/generation/actual/perType/generation:

hidden button: select the country -> select table (not graph) -> click on 3 dots (next to date picker) -> "export" -> "csv (year)" 

#### API

* [how to get an API key](https://www.amsleser.no/blog/post/21-obtaining-api-token-from-entso-e#:~:text=Now%20you%20need%20to%20send,it%20to%20generate%20API%20token.)

* [entsoe-py](https://github.com/EnergieID/entsoe-py) can be also useful !


### SFOE (OFEN)

https://opendata.swiss/en/dataset/energiedashboard-ch-stromproduktion-swissgrid/resource/0879ba1b-40ea-4e26-bba0-9cbb339f577e

### Energy-charts.info

a very useful project , by Fraunhofer ISE, is https://energy-charts.info/
and in particular [power generation for CH](https://energy-charts.info/charts/power/chart.htm?l=en&c=CH&interval=year&source=entsoe_bfe) , where you can select the source of data (ENTSO or SFOE) and compare them.

In particular, see https://energy-charts.info/explanations.html?l=en&c=CH for some notes on the discrepancies between the two datasets.

## Questions on data

* how are ENTSO data created? 
* how are SFOE data created?
* check the map between production types in ENTSO and SFOE datasets
* meaning of 'thermal' in SFOE dataset
* meaning of 'other' in ENTSO dataset
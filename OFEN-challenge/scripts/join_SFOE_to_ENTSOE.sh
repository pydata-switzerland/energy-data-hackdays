#!/bin/bash
mlr --csv \
join --lp ENTSOE_ \
--rp SFOE_ \
-j Date \
-f entsoe_generation_per_type_2026_01_daily.csv stromproduktion_wide.csv

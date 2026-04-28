#!/bin/bash
mlr --csv --ofmt '%.3f' \
stats1 -a mean,stddev,min,p50,max \
-f Kernkraft_Scale,Photovoltaik_Scale,Wind_Scale,Flusskraft_Scale,Total_Scale \
scaling_factors.csv
# |mlr --c2x --ofmt '%.3f' cat

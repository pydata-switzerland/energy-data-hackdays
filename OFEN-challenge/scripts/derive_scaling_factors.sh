#!/bin/bash
mlr --csv \
put '
    $Flusskraft_Scale = ${SFOE Flusskraft} / ${ENTSOE Run-of-river};
    $Speicherkraft_Scale = ${SFOE Speicherkraft} / ${ENTSOE Reservoir};
    $Kernkraft_Scale = $SFOE_Kernkraft / $ENTSOE_Nuclear;
    $Photovoltaik_Scale = $SFOE_Photovoltaik / $ENTSOE_Solar;
    $Wind_Scale = $SFOE_Wind / $ENTSOE_Wind;
    $Total_ENTSOE = ${ENTSOE Run-of-river} + ${ENTSOE Reservoir} + ${ENTSOE Nuclear} + ${ENTSOE Solar} + ${ENTSOE Wind};
    $Total_SFOE = ${SFOE Flusskraft} + ${SFOE Speicherkraft} + ${SFOE Kernkraft} + ${SFOE Photovoltaik} + ${SFOE Wind};
    $Total_Scale = $Total_SFOE / $Total_ENTSOE
' generation_per_type_labeled_2026_01.csv

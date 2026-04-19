"""utils functions for loading and cleaning the data"""

import pandas as pd
from pathlib import Path


def load_and_clean_entsoe_data(
    data_path: Path = Path("./OFEN-challenge/datasets/entsoe"),
) -> pd.DataFrame:
    """Merge datasets from different years,
    Load and clean the ENTSOE data from the csv files in the entsoe folder.
    Args:
        data_path (Path): path to the folder containing the csv files
    Returns:
        pd.DataFrame: cleaned ENTSOE data
    """
    entsoe = [
        pd.read_csv(file)
        for file in data_path.iterdir()
        if file.suffix == ".csv"
    ]

    # concatenate all datasets into one dataframe
    entsoe_df = pd.concat(entsoe, ignore_index=True)

    # make sure we are considering only CH
    assert all(entsoe_df["Area"].unique() == "BZN|CH"), (
        "Data contains areas other than CH"
    )

    # drop area since we are only looking at CH
    entsoe_df.drop(columns=["Area"], inplace=True)

    # convert generation to numeric
    entsoe_df["Generation (MW)"] = pd.to_numeric(
        entsoe_df["Generation (MW)"], errors="coerce"
    )

    # ## clean the UTC datetime column and convert to local time
    # split the string and take the interval end in UTC
    entsoe_df["MTU (UTC)"] = (
        entsoe_df["MTU (UTC)"].dropna().apply(lambda x: x.split(" - ")[1])
    )

    # parse UTC and convert to Swiss local time (CET/CEST with DST)
    entsoe_df["MTU (UTC)"] = pd.to_datetime(
        entsoe_df["MTU (UTC)"], format="%d/%m/%Y %H:%M:%S", utc=True
    )

    # ## clean the CET/CEST datetime column and convert to local time
    # split the string and take the interval end in CET/CEST
    entsoe_df["MTU (CET/CEST)"] = (
        entsoe_df["MTU (CET/CEST)"].dropna().apply(lambda x: x.split(" - ")[1])
    )
    # replace the ' (CET/CEST)' suffix with an empty string
    entsoe_df["MTU (CET/CEST)"] = entsoe_df["MTU (CET/CEST)"].str.replace(
        " (CET)", "", regex=False
    )
    entsoe_df["MTU (CET/CEST)"] = entsoe_df["MTU (CET/CEST)"].str.replace(
        " (CEST)", "", regex=False
    )

    # convert to datetime without timezone (local time)
    entsoe_df["MTU (CET/CEST)"] = pd.to_datetime(
        entsoe_df["MTU (CET/CEST)"], format="%d/%m/%Y %H:%M:%S", errors="coerce"
    )

    # set only the missing CET/CEST datetimes
    # to the converted datetimes from UTC to local time
    dt_filter = entsoe_df["MTU (CET/CEST)"].isna()

    entsoe_df.loc[dt_filter, "MTU (CET/CEST)"] = (
        entsoe_df.loc[dt_filter, "MTU (UTC)"]
        .dt.tz_convert("Europe/Zurich")
        .dt.tz_localize(None)
    )

    # use local Swiss time as index
    entsoe_df.set_index("MTU (CET/CEST)", inplace=True)

    return entsoe_df


def import_ofen_data(
    data_path: Path = Path(
        "./OFEN-challenge/datasets/ogd104_stromproduktion_swissgrid.csv"
    ),
) -> pd.DataFrame:
    """Load and clean the OFEN data from the csv file.
    Args:
        data_path (Path): path to the csv file

    Returns:
        pd.DataFrame: cleaned OFEN data
    """

    ofen_df = pd.read_csv(data_path)
    # set datum to datetime and set as index
    ofen_df["Datum"] = pd.to_datetime(ofen_df["Datum"])
    ofen_df.set_index("Datum", inplace=True)

    # map OFEN / german names to entsoe / english names for easier comparison and analysis
    ofen_df["Energietraeger"] = ofen_df["Energietraeger"].map(
        {
            "Flusskraft": "Hydro Water Reservoir",
            "Kernkraft": "Nuclear",
            "Speicherkraft": "Storage",  #  only Hydro Pumped Storage ???
            "Photovoltaik": "Solar",
            "Wind": "Wind Onshore",
            "Thermische": "Thermal",  # only fossil fuel ???
        }
    )
    ofen_df["Energietraeger"].value_counts()

    return ofen_df

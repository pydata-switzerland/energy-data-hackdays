# %% [markdown]
# # Explore generation datasets

# %% [markdown]
# ## import libraries
import pandas as pd
from pathlib import Path
from IPython.display import display

# import seaborn as sns
import plotly.express as px

# %% [markdown]
#  ## data import,  cleaning and preprocessing


# import all csv files in the entsoe folder
def load_and_clean_entsoe_data(
    data_path: Path = Path("./OFEN-challenge/datasets/entsoe"),
):

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


# %%
# %debug
entsoe_df = load_and_clean_entsoe_data()

# %%

display(entsoe_df.head())

display(entsoe_df.describe())

entsoe_df.info()


# show N nulls
entsoe_df.isnull().sum()


# %%
# ## Exploratory data analysis


# %%
# quick check of values counts for production type
entsoe_df["Production Type"].value_counts()

# %%
# distribution of generation by production type

fig = px.histogram(
    entsoe_df.dropna(),
    x="Generation (MW)",
    color="Production Type",
    # marginal="box",
    nbins=100,
    opacity=0.7,
    histnorm="density",
)
fig.update_layout(barmode="overlay")
fig.show()

# %%
# quick time series plot of generation by production type
fig = px.scatter(
    entsoe_df.dropna(subset=["Generation (MW)"]),
    x=entsoe_df.dropna(subset=["Generation (MW)"]).index,
    y="Generation (MW)",
    color="Production Type",
)
fig.update_traces(opacity=0.3)
fig.update_traces(marker=dict(size=4))
fig.show()

# %%

# %% [markdown]
# # Explore generation datasets

# %% [markdown]
# ## import libraries
from pathlib import Path
from IPython.display import display

# import seaborn as sns
import plotly.express as px

import sys

sys.path.append(str((Path.cwd() / "OFEN-challenge").resolve()))

# %load_ext autoreload
# %autoreload 1
# %aimport utils


from utils import (
    load_and_clean_entsoe_data,
    import_ofen_data,
    prepare_entsoe_for_comparison,
)

# %% [markdown]
#  ## ENTSOE data import,  cleaning and preprocessing

entsoe_df = load_and_clean_entsoe_data()

display(entsoe_df.head())

display(entsoe_df.describe())

entsoe_df.info()


# show N nulls
entsoe_df.isnull().sum()
print(entsoe_df.index.isnull().sum())  # check for nulls in index


entsoe_df["Production Type"].value_counts()

# %% [markdown]
# ### prepare data for comparison

entsoe_daily_pivot = prepare_entsoe_for_comparison(entsoe_df)

display(entsoe_daily_pivot.head())
display(entsoe_daily_pivot.describe())
entsoe_daily_pivot.info()

# %% [markdown]
# ## OFEN data import, cleaning and preprocessing

ofen_df = import_ofen_data()

display(ofen_df.head())
display(ofen_df.describe())
ofen_df.info()

# %%
# check overlap of production types between the two datasets

overlap_types = list(
    set(entsoe_df["Production Type"].unique())
    & set(ofen_df["Energietraeger"].unique())
)

overlap_types

# %%
# pivot the OFEN dataset to have energy carrier as columns
# and date as index
ofen_df_pivot = ofen_df.pivot(
    columns="Energietraeger",
    values="Produktion_GWh",
)

display(ofen_df_pivot.head())

# %%
# ## Exploratory data analysis


# %% [markdown]
# ### ENTSOE data exploration
# %%
# quick check of values counts for production type
entsoe_df["Production Type"].value_counts()

# %%
# distribution of generation by production type

fig = px.histogram(
    entsoe_df.dropna(),
    x="Generation (MW)",
    color="Production Type",
    marginal="box",
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

# %% [markdown]
# ### OFEN data exploration


# %%
# plot time series of generation by energy carrier
fig = px.scatter(
    data_frame=ofen_df,
    x=ofen_df.index,
    y="Produktion_GWh",
    color="Energietraeger",
)
fig.update_traces(opacity=0.6)
fig.update_traces(marker=dict(size=4))
fig.show()

# %% [markdown]
# ###  plot diff time-series for shared common production types


# %%

diff_df = entsoe_daily_pivot[overlap_types] - ofen_df_pivot[overlap_types]

# melt for easier plotting with plotly
diff_melted = diff_df.reset_index().melt(
    id_vars="MTU (CET/CEST)",
    var_name="Production Type",
    value_name="Difference (GWh)",
)

diff_melted.head()

# %%
px.scatter(
    diff_melted,
    x="MTU (CET/CEST)",
    y="Difference (GWh)",
    color="Production Type",
    title="Difference in generation between ENTSOE and OFEN datasets (GWh)",
).update_traces(opacity=0.6, marker=dict(size=4)).show()
# %%

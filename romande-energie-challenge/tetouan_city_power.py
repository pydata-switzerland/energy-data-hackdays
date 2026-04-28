# %% [markdown]
# # Power Consumption of Tetouan City

# %% [markdown]
## imports
from ucimlrepo import fetch_ucirepo

# %% [markdown]
# fetch and prepare dataset
tetouan_power = fetch_ucirepo(id=849)

# data (as pandas dataframes)
X = tetouan_power.data.features
y = tetouan_power.data.targets

# metadata
print(tetouan_power.metadata)

# variable information
print(tetouan_power.variables)


# %% [markdown]
# ## quick  data exploration


# %%

# %%

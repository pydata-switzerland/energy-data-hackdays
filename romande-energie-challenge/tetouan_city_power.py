# %% [markdown]
# # Power Consumption of Tetouan City

# %% [markdown]
## imports
from pathlib import Path
import sys

sys.path.append(str((Path.cwd() / "romande-energie-challenge").resolve()))


from ucimlrepo import fetch_ucirepo
import pandas as pd
import plotly.io as pio
from xgboost import XGBRegressor

from sklearn.model_selection import TimeSeriesSplit, GridSearchCV

# %%

from forecasting_utils import train_test_split, test_model, run_CV


# %load_ext autoreload
# %autoreload 1
# %aimport forecasting_utils

# %% [markdown]
# ## fetch and explore dataset
tetouan_power = fetch_ucirepo(id=849)


# overview of the raw dataset
print(type(tetouan_power))
for k in tetouan_power.keys():
    print(f"{k}: {type(tetouan_power[k])}")
    print(f"{k}: {tetouan_power[k].keys()}")

# %% [markdown]
# ### data features exploration

print(type(tetouan_power.data.features))
print(tetouan_power.data.features.info())
display(tetouan_power.data.features.describe())
display(tetouan_power.data.features.head())

# %% [markdown]
#  ### data targets exploration
print(type(tetouan_power.data.targets))
print(tetouan_power.data.targets.info())
display(tetouan_power.data.targets.describe())
display(tetouan_power.data.targets.head())


# %%
# set datetime index


tetouan_power.data.features.index = pd.DatetimeIndex(
    tetouan_power.data.features["DateTime"]
)
# we can drop the DateTime column as it is now the index
tetouan_power.data.features.drop(columns=["DateTime"], inplace=True)

tetouan_power.data.targets.set_index(
    tetouan_power.data.features.index, inplace=True
)
# %% [markdown]
# ## quick  data exploration

# %% [markdown]
# ### features scatter_matrix

pd.options.plotting.backend = "matplotlib"

pd.plotting.scatter_matrix(tetouan_power.data.features, figsize=(10, 10), s=3)

# %% [markdown]
# #### notes

# is there some issues with wind speed ? the distribution is  basically bimodal

# %% [markdown]
# ### line plots

INTERACTIVE = False
if INTERACTIVE:
    pd.options.plotting.backend = "plotly"

    fig = tetouan_power.data.features.plot.line(title="features line plot")
    pio.show(fig)

    fig = tetouan_power.data.targets.plot.line(title="targets line plot")
    pio.show(fig)
else:
    pd.options.plotting.backend = "matplotlib"
    tetouan_power.data.features.plot.line(
        figsize=(10, 5), alpha=0.3, title="features line plot"
    )
    tetouan_power.data.targets.plot.line(
        figsize=(10, 5), alpha=0.3, title="targets line plot"
    )

# %% [markdown]
# ## Forecasting task

# %% [markdown]
# ### feature preparation

# %%
# add temporal features: hour of day, day of week, month
tetouan_power.data.features["hour"] = tetouan_power.data.features.index.hour
tetouan_power.data.features["dayofweek"] = (
    tetouan_power.data.features.index.dayofweek
)
tetouan_power.data.features["month"] = tetouan_power.data.features.index.month

# %% [markdown]
# ### Split the data

# we try keeping only the most important features, but it makes the performance worse,
# so we keep all features for now

X_train, y_train, X_test, y_test = train_test_split(
    tetouan_power.data.features, tetouan_power.data.targets, plot=True
)


# %% [markdown]
# ### Assess a XGBoost regressor (multioutput)
# relevants docs:
# https://xgboost.readthedocs.io/en/stable/treemethod.html
# https://xgboost.readthedocs.io/en/stable/tutorials/multioutput.html
# https://xgboost.readthedocs.io/en/latest/python/python_api.html#module-xgboost.sklearn
model = XGBRegressor(
    tree_method="hist",
    random_state=42,
    multi_strategy="multi_output_tree",
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
)
model.fit(X_train, y_train)
# %% [markdown]
# ### feature importance

feature_importances = model.feature_importances_
feature_names = X_train.columns
feature_importance_df = pd.DataFrame({
    "feature": feature_names,
    "importance": feature_importances,
}).sort_values(by="importance", ascending=False)
print(feature_importance_df)

# %% [markdown]
# ### Cross validation evaluation

tscv = TimeSeriesSplit(n_splits=5, test_size=int(len(X_train) * 0.2), gap=0)

cv_results = run_CV(model, X_train, y_train, tscv=tscv)
display(cv_results)

# %% [markdown]
# ### Hyperparameter tuning with CV

param_grid = {
    "n_estimators": [50, 70, 100],
    "max_depth": [6, 8],
    "learning_rate": [0.1],  # from prev. exp.
    # "learning_rate": [0.01, 0.1, 0.2]
}
grid_search = GridSearchCV(
    estimator=XGBRegressor(
        tree_method="hist", random_state=42, multi_strategy="multi_output_tree"
    ),
    param_grid=param_grid,
    cv=tscv,
    scoring="neg_mean_squared_error",
    n_jobs=-1,
    verbose=1,
)
grid_search.fit(X_train, y_train)

# best hyperparameters
print("Best Hyperparameters:", grid_search.best_params_)

# %% [markdown]
# ### retrain and test best model

best_model = grid_search.best_estimator_
best_model.fit(X_train, y_train)

# test the best model on the test set
test_model(best_model, X_test, y_test, plot=True)

# %%
# performance is still quite bad...room for improvement!
# %%

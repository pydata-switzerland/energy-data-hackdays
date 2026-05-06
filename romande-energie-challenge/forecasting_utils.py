"""basic module for forecasting basic functions"""

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import (
    root_mean_squared_error,
    mean_absolute_percentage_error,
)
import numpy as np

from sklearn.base import clone


def train_test_split(
    features: pd.DataFrame,
    targets: pd.DataFrame,
    train_fraction: float = 0.7,
    plot=False,
):
    """split the data into train and test sets,
    according to the given fractions. optionally plot the split.

    Args:
        features (pd.DataFrame): feature data
        targets (pd.DataFrame): target data
        train_fraction (float, optional): fraction of data to use for training. Defaults to 0.7.
        plot (bool, optional): whether to plot the split. Defaults to False.
    Returns:
        tuple: train and test sets for features and targets
    """
    X = features
    y = targets
    assert len(X) == len(y), (
        "Features and targets must have the same number of samples"
    )

    train_size = int(train_fraction * len(X))

    X_train = X.iloc[:train_size]
    X_test = X.iloc[train_size:]

    y_train = y.iloc[:train_size]
    y_test = y.iloc[train_size:]

    if plot:
        # plot with different colors the targets
        # in train and test sets to check the split

        fig = plt.figure(figsize=(12, 6))
        for i, target in enumerate(y_train.columns):
            plt.plot(
                X_train.index,
                y_train[target],
                label=f"Train - {target}",
                alpha=0.5,
            )
            plt.plot(
                X_test.index,
                y_test[target],
                label=f"Test - {target}",
                alpha=0.5,
            )
            break  # only plot the first target for clarity
        plt.xlabel("Time")
        plt.ylabel("targets")
        plt.title("Train and Test Split")
        plt.legend()
        fig.show()

    return X_train, y_train, X_test, y_test


def run_CV(
    model, X_train: pd.DataFrame, y_train: pd.DataFrame, tscv, verbose=True
):
    """run cross-validation

    Args:
        model: usual sklearn-like model with fit and predict methods
        X_train (pd.DataFrame): training feature data
        y_train (pd.DataFrame): training target data
        tscv (generator): time series cross-validation splitter
        verbose (bool, optional): whether to print details of the splits. Defaults to True.

    Returns:
        pd.DataFrame: DataFrame containing cross-validation metrics for each fold
    """
    assert hasattr(model, "fit"), "Model must have a fit method"
    assert hasattr(model, "predict"), "Model must have a predict method"

    cv_results = []

    for fold, (train_idx, val_idx) in enumerate(tscv.split(X_train), start=1):
        # show details of the splits
        if verbose:
            print(f"Fold {fold}:")
            print(
                f"  Train indices: {train_idx[0]} to {train_idx[-1]} (size: {len(train_idx)})"
            )
            print(
                f"  Validation indices: {val_idx[0]} to {val_idx[-1]} (size: {len(val_idx)})"
            )

        X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
        y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]

        model = clone(model)  # to ensure a fresh model for each fold
        model.fit(X_tr, y_tr)
        y_val_pred = model.predict(X_val)

        rmse = root_mean_squared_error(y_val, y_val_pred)
        mape = mean_absolute_percentage_error(y_val, y_val_pred)
        cv_results.append({"fold": fold, "rmse": rmse, "mape": mape})

    cv_results_df = pd.DataFrame(cv_results)

    print(
        "CV mean metrics -> "
        f"RMSE: {cv_results_df['rmse'].mean():.4f}, "
        f"MAPE: {cv_results_df['mape'].mean():.4f}"
    )

    return cv_results_df


def plot_test_pred(y_test: pd.DataFrame, y_pred_test: np.ndarray):

    for i, target in enumerate(y_test.columns):
        plt.figure(figsize=(10, 5))
        plt.plot(y_test.index, y_test[target], label="True")
        plt.plot(y_test.index, y_pred_test[:, i], label="Predicted")
        plt.xlabel("Time")
        plt.ylabel(target)
        plt.title(f"{target} -- Test Set")
        plt.legend()
        plt.show()


def test_model(
    model, X_test: pd.DataFrame, y_test: pd.DataFrame, plot: bool = False
):
    """Test a model on the given test set and optionally plot the predictions.

    Args:
        model: the model to test, must have a predict method
        X_test (pd.DataFrame): feature data for testing
        y_test (pd.DataFrame): target data for testing
        plot (bool, optional): whether to plot the predictions. Defaults to False.

    """

    assert hasattr(model, "predict"), "Model must have a predict method"
    y_pred_test = model.predict(X_test)

    # show metrics per target
    for i, target in enumerate(y_test.columns):
        target_rmse = root_mean_squared_error(y_test[target], y_pred_test[:, i])
        target_mape = mean_absolute_percentage_error(
            y_test[target], y_pred_test[:, i]
        )
        print(f"{target} -- Test RMSE: {target_rmse:.3f}")
        print(f"{target} -- Test MAPE: {target_mape:.3f}")

    if plot:
        plot_test_pred(y_test, y_pred_test)

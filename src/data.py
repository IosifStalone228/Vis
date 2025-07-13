from datetime import datetime

import numpy as np
import pandas as pd

# Load preprocessed dataset
data: pd.DataFrame = pd.read_parquet("datasets/processed_data.parquet")

# Extract unique incident types and state codes for filtering
incident_types: list[str] = sorted(data["type_of_incident"].unique())
state_codes: list[str] = sorted(data["state_code"].unique())


def compute_agg_incident_rate(df: pd.DataFrame, column: str = None) -> pd.DataFrame:
    """
    Compute the aggregated incident rate per state or specified column.

    Args:
        df (pd.DataFrame): Input dataset.
        column (str, optional): Additional column to group by. Defaults to None.

    Returns:
        pd.DataFrame: Aggregated incident rate data.
    """
    # Deduplicate for company-level fields
    deduplicated = df.drop_duplicates(subset=["state_code", "company_name"])
    agg_cols = ["state_code", column] if column is not None else ["state_code"]

    # Sum case numbers directly from injury-level data
    injury_data = df.groupby(agg_cols, observed=False).agg(case_number=("case_number", "count")).reset_index()

    # Aggregate deduplicated company-level data
    company_data = (
        deduplicated.groupby(agg_cols, observed=False)
        .agg(total_hours_worked=("total_hours_worked", "sum"))
        .reset_index()
    )

    # Merge and calculate incident rate
    temp = injury_data.merge(company_data, on=agg_cols, how="left")
    temp["incident_rate"] = np.where(
        temp["total_hours_worked"] > 0,
        temp["case_number"] / temp["total_hours_worked"] * 1e5,
        0,
    )
    return temp[agg_cols + ["incident_rate"]]


def compute_agg_fatality_rate(df: pd.DataFrame, column: str = None) -> pd.DataFrame:
    """
    Compute the aggregated fatality rate per state or specified column.

    Args:
        df (pd.DataFrame): Input dataset.
        column (str, optional): Additional column to group by. Defaults to None.

    Returns:
        pd.DataFrame: Aggregated fatality rate data.
    """
    agg_cols = ["state_code", column] if column is not None else ["state_code"]

    # Sum fatalities directly from injury-level data
    temp = (
        df.groupby(agg_cols, observed=False)
        .agg(death=("death", "sum"), case_number=("case_number", "count"))
        .reset_index()
    )

    # Calculate fatality rate
    temp["fatality_rate"] = np.where(
        temp["case_number"] > 0,
        temp["death"] / temp["case_number"] * 1e4,
        0,
    )
    return temp[agg_cols + ["fatality_rate"]]


def compute_agg_lost_workday_rate(df: pd.DataFrame, column: str = None) -> pd.DataFrame:
    """
    Compute the aggregated lost workday rate per state or specified column.

    Args:
        df (pd.DataFrame): Input dataset.
        column (str, optional): Additional column to group by. Defaults to None.

    Returns:
        pd.DataFrame: Aggregated lost workday rate data.
    """
    agg_cols = ["state_code", column] if column is not None else ["state_code"]

    # Sum injury-level data
    injury_data = (
        df.groupby(agg_cols, observed=False)
        .agg(
            dafw_num_away=("dafw_num_away", "sum"),
            djtr_num_tr=("djtr_num_tr", "sum"),
            case_number=("case_number", "count"),
        )
        .reset_index()
    )

    # Calculate lost workdays and rate
    injury_data["total_lost_days"] = injury_data["dafw_num_away"] + injury_data["djtr_num_tr"]
    injury_data["lost_workday_rate"] = np.where(
        injury_data["case_number"] > 0,
        injury_data["total_lost_days"] / injury_data["case_number"],
        0,
    )
    return injury_data[agg_cols + ["lost_workday_rate"]]


def compute_workforce_exposure(df: pd.DataFrame, column: str = None) -> pd.DataFrame:
    """
    Compute the workforce exposure per state or specified column.

    Args:
        df (pd.DataFrame): Input dataset.
        column (str, optional): Additional column to group by. Defaults to None.

    Returns:
        pd.DataFrame: Aggregated workforce exposure data.
    """
    # Deduplicate for company-level fields
    deduplicated = df.drop_duplicates(subset=["state_code", "company_name"])
    agg_cols = ["state_code", column] if column is not None else ["state_code"]

    # Sum injury-level data
    injury_data = df.groupby(agg_cols, observed=False).agg(case_number=("case_number", "count")).reset_index()

    # Aggregate deduplicated company-level data
    company_data = (
        deduplicated.groupby(agg_cols, observed=False)
        .agg(annual_average_employees=("annual_average_employees", "sum"))
        .reset_index()
    )

    # Merge and calculate workforce exposure
    temp = injury_data.merge(company_data, on=agg_cols, how="left")
    temp["workforce_exposure"] = np.where(
        temp["case_number"] > 0,
        temp["case_number"] / temp["annual_average_employees"] * 1e2,
        0,
    )
    return temp[agg_cols + ["workforce_exposure"]]


def compute_agg_safety_score(df: pd.DataFrame, column: str = None) -> pd.DataFrame:
    """
    Compute an aggregated safety score based on multiple metrics.

    Args:
        df (pd.DataFrame): Input dataset.
        column (str, optional): Additional column to group by. Defaults to None.

    Returns:
        pd.DataFrame: Aggregated safety score data.
    """
    stats = compute_agg_incident_rate(df, column)
    stats = stats.merge(
        compute_agg_fatality_rate(df, column),
        on=["state_code"] + ([column] if column else []),
        how="left",
    )
    stats = stats.merge(
        compute_agg_lost_workday_rate(df, column),
        on=["state_code"] + ([column] if column else []),
        how="left",
    )
    stats = stats.merge(
        compute_workforce_exposure(df, column),
        on=["state_code"] + ([column] if column else []),
        how="left",
    )
    stats["danger_score"] = (
        2.38 * stats["incident_rate"]
        + 3.33 * stats["fatality_rate"]
        + 0.37 * stats["lost_workday_rate"]
        + 1.4 * stats["workforce_exposure"]
    )
    return stats


kpi_name_function_mapping: dict[str, callable] = {
    "incident_rate": compute_agg_incident_rate,
    "fatality_rate": compute_agg_fatality_rate,
    "lost_workday_rate": compute_agg_lost_workday_rate,
    "workforce_exposure": compute_workforce_exposure,
    # "death_to_incident": compute_death_to_incident_ratio,  # Optional metric for future use
    "danger_score": compute_agg_safety_score,
}

# Compute aggregated safety score for all regions
region_safety_score: pd.DataFrame = compute_agg_safety_score(data)

# Initialize dictionaries to store min, max, and mean values for each metric
min_metric_values: dict[str, float] = {}
max_metric_values: dict[str, float] = {}
mean_metric_values: dict[str, float] = {}

# Calculate statistics (min, max, mean) for each metric in a single loop
for metric in kpi_name_function_mapping:
    column_data = region_safety_score[metric]
    min_metric_values[metric] = column_data.min()
    max_metric_values[metric] = column_data.max()
    mean_metric_values[metric] = column_data.mean()


def filter_data(
    df: pd.DataFrame,
    start_date: str,
    end_date: str,
    filter_incident_types: list[str],
) -> pd.DataFrame:
    """
    Filter the dataset based on date range and incident types.

    Args:
        df (pd.DataFrame): Input dataset.
        start_date (str): Start date for filtering (ISO format).
        end_date (str): End date for filtering (ISO format).
        filter_incident_types (list[str]): List of incident types to include.

    Returns:
        pd.DataFrame: Filtered dataset.
    """
    start_date = datetime.fromisoformat(start_date)
    end_date = datetime.fromisoformat(end_date)

    # Check if precomputed data can be used
    use_precomputed = start_date == df["date_of_incident"].min() and end_date == df["date_of_incident"].max()

    if use_precomputed and not filter_incident_types:
        return df  # Return unfiltered dataset if precomputed is valid

    # Apply date and incident type filters
    filtered_data = df[(df["date_of_incident"] >= start_date) & (df["date_of_incident"] <= end_date)]
    if filter_incident_types:
        filtered_data = filtered_data[filtered_data["type_of_incident"].isin(filter_incident_types)]

    return filtered_data


def prepare_mean_radar_data(radar_region_safety_score: pd.DataFrame) -> pd.DataFrame:
    """
    Add mean values for each metric to the radar dataset.

    Args:
        radar_region_safety_score (pd.DataFrame): Input radar safety score data.

    Returns:
        pd.DataFrame: Radar data with mean values added.
    """
    mean_values = radar_region_safety_score.iloc[:, 1:].mean()

    # Add mean values as new columns
    for col in mean_values.index:
        radar_region_safety_score[f"mean_{col}"] = mean_values[col]

    return radar_region_safety_score


def calculate_mean_values(
    min_metric_values: dict[str, float],
    max_metric_values: dict[str, float],
    metrics: list[str],
    mean_values: list[float],
) -> list[float]:
    """
    Normalize mean values to a 0-1 scale based on min and max values.

    Args:
        min_metric_values (dict[str, float]): Minimum values for each metric.
        max_metric_values (dict[str, float]): Maximum values for each metric.
        metrics (list[str]): List of metric names.
        mean_values (list[float]): List of mean values for the metrics.

    Returns:
        list[float]: Normalized mean values.
    """
    return [
        (
            (mean_value - min_metric_values[metric]) / (max_metric_values[metric] - min_metric_values[metric])
            if max_metric_values[metric] > min_metric_values[metric]
            else 0
        )
        for metric, mean_value in zip(metrics, mean_values)
    ]


def prepare_radar_data(df: pd.DataFrame, state_code: str) -> pd.DataFrame:
    """
    Prepare radar chart data for a specific state.

    Args:
        df (pd.DataFrame): Input dataset.
        state_code (str): State code to filter by.

    Returns:
        pd.DataFrame: Prepared radar chart data.
    """
    # Use precomputed or filtered data
    radar_region_safety_score = region_safety_score if df is data else compute_agg_safety_score(df)

    radar_region_safety_score = prepare_mean_radar_data(radar_region_safety_score)

    # Extract relevant metrics
    metrics = [
        "incident_rate",
        "fatality_rate",
        "lost_workday_rate",
        "workforce_exposure",
        "danger_score",
    ]
    metric_values = radar_region_safety_score.loc[
        radar_region_safety_score["state_code"] == state_code, metrics
    ].squeeze()

    # Scale metrics to a 0-1 range
    scaled_values = [
        (
            (metric_values[metric] - min_metric_values[metric])
            / (max_metric_values[metric] - min_metric_values[metric])
            if max_metric_values[metric] > min_metric_values[metric]
            else 0
        )
        for metric in metrics
    ]
    mean_values = [radar_region_safety_score[f"mean_{metric}"].iloc[0] for metric in metrics]

    scaled_mean_values = calculate_mean_values(min_metric_values, max_metric_values, metrics, mean_values)

    # Construct radar data
    radar_data = {
        "kpi": metrics,
        "value": metric_values.tolist(),
        "scaled_value": scaled_values,
        "mean_value": mean_values,
        "scaled_mean_value": scaled_mean_values,
    }
    return pd.DataFrame(radar_data)


def prepare_state_data(df: pd.DataFrame, kpi: str = "incident_rate") -> pd.DataFrame:
    """
    Prepare aggregated state-level data.

    Args:
        df (pd.DataFrame): Input dataset.
        kpi (str, optional): Key performance indicator to include. Defaults to "incident_rate".

    Returns:
        pd.DataFrame: Aggregated state-level data.
    """
    # Deduplicate company-level fields
    deduplicated = df.drop_duplicates(subset=["state_code", "company_name"])

    # Aggregate company-level data
    company_data = (
        deduplicated.groupby("state_code", observed=False)
        .agg(
            annual_average_employees_median=("annual_average_employees", "mean"),
            annual_average_employees_sum=("annual_average_employees", "sum"),
            total_hours_worked=("total_hours_worked", "mean"),
        )
        .reset_index()
    )

    # Aggregate injury-level data
    injury_data = (
        df.groupby("state_code", observed=False)
        .agg(
            dafw_num_away=("dafw_num_away", "mean"),
            djtr_num_tr=("djtr_num_tr", "mean"),
            death=("death", "mean"),
            case_number=("case_number", "count"),
        )
        .reset_index()
    )

    # Merge aggregated data
    aggregated_data = pd.merge(company_data, injury_data, on="state_code", how="inner")

    # Calculate injury density
    aggregated_data["injury_density"] = np.where(
        aggregated_data["annual_average_employees_median"] > 0,
        aggregated_data["case_number"] / aggregated_data["annual_average_employees_sum"],
        0,
    )

    # Merge with KPI-specific output
    return pd.merge(
        aggregated_data,
        kpi_name_function_mapping[kpi](df),
        on="state_code",
        how="inner",
    )


def prepare_treemap_data(df, state_code, kpi):
    temp = df[df["state_code"] == state_code]

    # Select the metric function
    metric_function = kpi_name_function_mapping[kpi]
    return (
        temp.query("soc_description_1 != 'Insufficient info' & soc_description_1 != 'Not assigned'")
        .groupby(["soc_description_1", "soc_description_2"], observed=True)
        .agg(
            count=(
                "soc_description_1",
                "size",
            ),  # Count the number of rows in each group
            metric=(
                "soc_description_1",
                lambda group: metric_function(temp.loc[group.index])
                .query(f"state_code == '{state_code}'")
                .iloc[0, -1],
            ),
        )
        .reset_index()
    )


def prepare_scatter_plot(df: pd.DataFrame, state: str) -> pd.DataFrame:
    """
    Prepare scatter plot data for a specific state.

    Args:
        df (pd.DataFrame): Input dataset.
        state (str): State code to filter by.

    Returns:
        pd.DataFrame: Aggregated data for the scatter plot.
    """
    # Filter data for the specified state
    aggregated_data = (
        df[df["state_code"] == state]
        .groupby("naics_description_5", observed=True)
        .agg(
            {
                "case_number": "count",
                "time_started_work": "mean",
                "time_of_incident": "mean",
                "establishment_type": lambda x: x.mode().iloc[0],  # Most frequent establishment type
            }
        )
        .reset_index()
    )

    # Format time columns for hover information
    aggregated_data["time_started_work_str"] = aggregated_data["time_started_work"].dt.strftime("%H:%M")
    aggregated_data["time_of_incident_str"] = aggregated_data["time_of_incident"].dt.strftime("%H:%M")

    return aggregated_data


def prepare_stacked_bar_chart(df: pd.DataFrame, state: str) -> pd.DataFrame:
    """
    Prepare stacked bar chart data for a specific state.

    Args:
        df (pd.DataFrame): Input dataset.
        state (str): State code to filter by.

    Returns:
        pd.DataFrame: Aggregated data for the stacked bar chart.
    """
    # Filter data for the specified state and exclude invalid entries
    filtered_data = df.query(
        "state_code == @state & establishment_type != 'Not Stated' & establishment_type != 'Invalid Entry'"
    )

    # Aggregate data: count incidents by outcome and establishment type
    aggregated_data = (
        filtered_data.groupby(["incident_outcome", "establishment_type"], observed=True)
        .size()
        .reset_index(name="count")
    )

    # Pivot the data for a stacked bar chart structure
    pivot_data = aggregated_data.pivot(index="incident_outcome", columns="establishment_type", values="count").fillna(
        0
    )

    # Normalize counts to proportions within each incident outcome
    return pivot_data.div(pivot_data.sum(axis=1), axis=0).reset_index()

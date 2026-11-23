import pandas as pd
import numpy as np


def load_data(filepath: str) -> pd.DataFrame:
    """Load and validate HR cost dataset."""
    df = pd.read_csv(filepath)
    cost_cols = [
        "Base_Salary",
        "Benefits_Cost",
        "Performance_Bonus",
        "Overtime_Cost",
        "Training_Cost",
        "Recruitment_Cost",
        "Turnover_Cost",
    ]
    df["Total_HR_Cost"] = df[cost_cols].sum(axis=1)
    df["Overhead_Cost"] = (
        df["Benefits_Cost"]
        + df["Overtime_Cost"]
        + df["Training_Cost"]
        + df["Recruitment_Cost"]
        + df["Turnover_Cost"]
    )
    df["Overhead_Ratio_Pct"] = np.where(
        df["Total_HR_Cost"] > 0,
        (df["Overhead_Cost"] / df["Total_HR_Cost"]) * 100,
        0.0,
    )
    return df


def compute_kpis(df: pd.DataFrame) -> dict:
    """Compute top-level executive HR cost KPIs."""
    total_cost = float(df["Total_HR_Cost"].sum())
    headcount = int(len(df))
    active_headcount = int((df["Attrition_Status"] == "Active").sum())
    left_headcount = int((df["Attrition_Status"] == "Left").sum())
    cost_per_employee = total_cost / headcount if headcount > 0 else 0.0
    total_salary = float(df["Base_Salary"].sum())
    total_benefits = float(df["Benefits_Cost"].sum())
    total_turnover = float(df["Turnover_Cost"].sum())
    total_overtime = float(df["Overtime_Cost"].sum())
    attrition_rate = (left_headcount / headcount * 100) if headcount > 0 else 0.0
    overhead_pct = (
        ((total_cost - total_salary - float(df["Performance_Bonus"].sum())) / total_cost * 100)
        if total_cost > 0
        else 0.0
    )

    return {
        "total_cost": total_cost,
        "headcount": headcount,
        "active_headcount": active_headcount,
        "cost_per_employee": cost_per_employee,
        "total_salary": total_salary,
        "total_benefits": total_benefits,
        "total_turnover": total_turnover,
        "total_overtime": total_overtime,
        "attrition_rate": attrition_rate,
        "overhead_pct": overhead_pct,
    }


def get_department_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate HR costs by department."""
    summary = (
        df.groupby("Department", as_index=False)
        .agg(
            Headcount=("Employee_ID", "count"),
            Base_Salary=("Base_Salary", "sum"),
            Benefits_Cost=("Benefits_Cost", "sum"),
            Performance_Bonus=("Performance_Bonus", "sum"),
            Overtime_Cost=("Overtime_Cost", "sum"),
            Training_Cost=("Training_Cost", "sum"),
            Recruitment_Cost=("Recruitment_Cost", "sum"),
            Turnover_Cost=("Turnover_Cost", "sum"),
            Total_HR_Cost=("Total_HR_Cost", "sum"),
            Avg_Cost_Per_Employee=("Total_HR_Cost", "mean"),
        )
        .sort_values(by="Total_HR_Cost", ascending=False)
    )
    summary["Cost_Share_Pct"] = (
        summary["Total_HR_Cost"] / summary["Total_HR_Cost"].sum() * 100
    ).round(2)
    return summary


def get_cost_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Return total spend across each HR cost category."""
    categories = [
        ("Base Salary", df["Base_Salary"].sum()),
        ("Benefits", df["Benefits_Cost"].sum()),
        ("Performance Bonus", df["Performance_Bonus"].sum()),
        ("Turnover & Attrition", df["Turnover_Cost"].sum()),
        ("Overtime", df["Overtime_Cost"].sum()),
        ("Training & Upskilling", df["Training_Cost"].sum()),
        ("Recruitment", df["Recruitment_Cost"].sum()),
    ]
    breakdown_df = pd.DataFrame(categories, columns=["Cost_Category", "Amount"])
    breakdown_df["Share_Pct"] = (
        breakdown_df["Amount"] / breakdown_df["Amount"].sum() * 100
    ).round(2)
    return breakdown_df.sort_values(by="Amount", ascending=False)


def simulate_budget_scenario(
    df: pd.DataFrame,
    salary_hike_pct: float = 0.0,
    attrition_reduction_pct: float = 0.0,
    overtime_reduction_pct: float = 0.0,
    training_boost_pct: float = 0.0,
) -> dict:
    """Simulate financial impact of HR policy adjustments."""
    baseline_total = float(df["Total_HR_Cost"].sum())

    sim_salary = df["Base_Salary"] * (1 + salary_hike_pct / 100.0)
    # Benefits scale proportionally with base salary for full-time staff
    sim_benefits = df["Benefits_Cost"] * (1 + salary_hike_pct / 100.0)
    sim_bonus = df["Performance_Bonus"] * (1 + salary_hike_pct / 100.0)
    sim_turnover = df["Turnover_Cost"] * (1 - attrition_reduction_pct / 100.0)
    sim_overtime = df["Overtime_Cost"] * (1 - overtime_reduction_pct / 100.0)
    sim_training = df["Training_Cost"] * (1 + training_boost_pct / 100.0)
    sim_recruitment = df["Recruitment_Cost"] * (1 - attrition_reduction_pct / 100.0)

    projected_total = float(
        (
            sim_salary
            + sim_benefits
            + sim_bonus
            + sim_turnover
            + sim_overtime
            + sim_training
            + sim_recruitment
        ).sum()
    )

    net_delta = projected_total - baseline_total
    delta_pct = (net_delta / baseline_total * 100) if baseline_total > 0 else 0.0

    return {
        "baseline_total": baseline_total,
        "projected_total": projected_total,
        "net_delta": net_delta,
        "delta_pct": delta_pct,
    }

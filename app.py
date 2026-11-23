import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure repository root and nested project folder are on sys.path
ROOT_DIR = Path(__file__).resolve().parent
for candidate in (ROOT_DIR, ROOT_DIR / "hr_cost_analysis"):
    if candidate.exists() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

try:
    from src.analytics import (
        compute_kpis,
        get_cost_breakdown,
        get_department_summary,
        load_data,
        simulate_budget_scenario,
    )
except ModuleNotFoundError:
    def _prepare_df(df: pd.DataFrame) -> pd.DataFrame:
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

    def load_data(filepath: str) -> pd.DataFrame:
        return _prepare_df(pd.read_csv(filepath))

    def compute_kpis(df: pd.DataFrame) -> dict:
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
        baseline_total = float(df["Total_HR_Cost"].sum())
        sim_salary = df["Base_Salary"] * (1 + salary_hike_pct / 100.0)
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


st.set_page_config(
    page_title="HR Cost Analysis & Workforce Budgeting",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom subtle CSS for KPI cards
st.markdown(
    """
    <style>
    div[data-testid="stMetric"] {
        background-color: #f8f9fb;
        border: 1px solid #e6e9ef;
        padding: 14px 18px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_inr(value: float) -> str:
    """Format currency cleanly in Lakhs/Crores."""
    if abs(value) >= 1e7:
        return f"₹{value / 1e7:.2f} Cr"
    if abs(value) >= 1e5:
        return f"₹{value / 1e5:.2f} L"
    return f"₹{value:,.0f}"


def generate_default_dataset(n_employees: int = 250, seed: int = 42) -> pd.DataFrame:
    """Fallback synthetic dataset generator if data/hr_cost_data.csv is not on disk."""
    rng = np.random.default_rng(seed)
    departments = [
        "Engineering",
        "Data & AI",
        "Sales",
        "Marketing",
        "Human Resources",
        "Operations",
        "Finance",
    ]
    dept_weights = [0.30, 0.15, 0.20, 0.10, 0.05, 0.12, 0.08]
    levels = ["Junior", "Mid-Level", "Senior", "Lead", "Manager"]
    level_weights = [0.25, 0.35, 0.22, 0.10, 0.08]
    locations = ["Bengaluru", "Noida", "Hyderabad", "Pune", "Remote"]
    loc_weights = [0.35, 0.25, 0.15, 0.15, 0.10]
    emp_types = ["Full-Time", "Contract"]
    emp_type_weights = [0.85, 0.15]

    base_salary_map = {
        ("Engineering", "Junior"): 750000,
        ("Engineering", "Mid-Level"): 1400000,
        ("Engineering", "Senior"): 2400000,
        ("Engineering", "Lead"): 3200000,
        ("Engineering", "Manager"): 3800000,
        ("Data & AI", "Junior"): 850000,
        ("Data & AI", "Mid-Level"): 1600000,
        ("Data & AI", "Senior"): 2700000,
        ("Data & AI", "Lead"): 3500000,
        ("Data & AI", "Manager"): 4200000,
        ("Sales", "Junior"): 550000,
        ("Sales", "Mid-Level"): 1050000,
        ("Sales", "Senior"): 1800000,
        ("Sales", "Lead"): 2500000,
        ("Sales", "Manager"): 3100000,
        ("Marketing", "Junior"): 500000,
        ("Marketing", "Mid-Level"): 950000,
        ("Marketing", "Senior"): 1600000,
        ("Marketing", "Lead"): 2200000,
        ("Marketing", "Manager"): 2800000,
        ("Human Resources", "Junior"): 480000,
        ("Human Resources", "Mid-Level"): 880000,
        ("Human Resources", "Senior"): 1500000,
        ("Human Resources", "Lead"): 2000000,
        ("Human Resources", "Manager"): 2500000,
        ("Operations", "Junior"): 450000,
        ("Operations", "Mid-Level"): 850000,
        ("Operations", "Senior"): 1450000,
        ("Operations", "Lead"): 1950000,
        ("Operations", "Manager"): 2450000,
        ("Finance", "Junior"): 600000,
        ("Finance", "Mid-Level"): 1100000,
        ("Finance", "Senior"): 1850000,
        ("Finance", "Lead"): 2450000,
        ("Finance", "Manager"): 3000000,
    }

    dept_list = rng.choice(departments, n_employees, p=dept_weights)
    level_list = rng.choice(levels, n_employees, p=level_weights)
    loc_list = rng.choice(locations, n_employees, p=loc_weights)
    type_list = rng.choice(emp_types, n_employees, p=emp_type_weights)

    records = []
    for i in range(n_employees):
        dept, lvl, loc, etype = dept_list[i], level_list[i], loc_list[i], type_list[i]
        base = round(base_salary_map[(dept, lvl)] * rng.uniform(0.90, 1.15), -3)
        benefits = round(base * (rng.uniform(0.12, 0.16) if etype == "Full-Time" else 0.03), -2)
        bonus = round(
            base * (rng.uniform(0.05, 0.18) if etype == "Full-Time" else rng.uniform(0.0, 0.05)),
            -2,
        )
        overtime = round(
            rng.uniform(15000, 85000)
            if lvl in ["Junior", "Mid-Level"] and rng.random() < 0.45
            else 0,
            -2,
        )
        training = round(
            rng.uniform(15000, 65000)
            if dept in ["Data & AI", "Engineering"]
            else rng.uniform(8000, 35000),
            -2,
        )
        tenure_years = round(float(rng.uniform(0.2, 6.5)), 1)
        recruitment_cost = round(base * rng.uniform(0.08, 0.14) if tenure_years <= 1.0 else 0, -2)
        attrition_status = "Left" if rng.random() < 0.14 else "Active"
        turnover_cost = round(base * 0.35, -2) if attrition_status == "Left" else 0

        records.append(
            {
                "Employee_ID": f"EMP-{1001 + i}",
                "Department": dept,
                "Role_Level": lvl,
                "Location": loc,
                "Employment_Type": etype,
                "Tenure_Years": tenure_years,
                "Attrition_Status": attrition_status,
                "Base_Salary": base,
                "Benefits_Cost": benefits,
                "Performance_Bonus": bonus,
                "Overtime_Cost": overtime,
                "Training_Cost": training,
                "Recruitment_Cost": recruitment_cost,
                "Turnover_Cost": turnover_cost,
            }
        )

    df = pd.DataFrame(records)
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


def resolve_data_path():
    """Locate hr_cost_data.csv if present on disk, otherwise return None."""
    candidates = [
        ROOT_DIR / "data" / "hr_cost_data.csv",
        ROOT_DIR / "hr_cost_analysis" / "data" / "hr_cost_data.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


@st.cache_data
def get_cached_data(path_str: str) -> pd.DataFrame:
    if path_str:
        return load_data(path_str)
    return generate_default_dataset()


# Sidebar - Data Upload & Filters
st.sidebar.title("HR Cost Controls")
uploaded_file = st.sidebar.file_uploader(
    "Upload Custom HR CSV (Optional)", type=["csv"]
)

if uploaded_file is not None:
    raw_df = pd.read_csv(uploaded_file)
    cost_cols = [
        "Base_Salary",
        "Benefits_Cost",
        "Performance_Bonus",
        "Overtime_Cost",
        "Training_Cost",
        "Recruitment_Cost",
        "Turnover_Cost",
    ]
    raw_df["Total_HR_Cost"] = raw_df[cost_cols].sum(axis=1)
    df = raw_df
else:
    data_path = resolve_data_path()
    df = get_cached_data(str(data_path) if data_path else "")

st.sidebar.subheader("Workforce Filters")
selected_depts = st.sidebar.multiselect(
    "Department",
    options=sorted(df["Department"].unique()),
    default=sorted(df["Department"].unique()),
)
selected_levels = st.sidebar.multiselect(
    "Role Level",
    options=sorted(df["Role_Level"].unique()),
    default=sorted(df["Role_Level"].unique()),
)
selected_locations = st.sidebar.multiselect(
    "Location",
    options=sorted(df["Location"].unique()),
    default=sorted(df["Location"].unique()),
)
selected_types = st.sidebar.multiselect(
    "Employment Type",
    options=sorted(df["Employment_Type"].unique()),
    default=sorted(df["Employment_Type"].unique()),
)

filtered_df = df[
    (df["Department"].isin(selected_depts))
    & (df["Role_Level"].isin(selected_levels))
    & (df["Location"].isin(selected_locations))
    & (df["Employment_Type"].isin(selected_types))
]

# Header
st.title("📊 HR Cost Analysis & Workforce Budgeting Dashboard")
st.caption(
    "End-to-end workforce spend intelligence across compensation, benefits, overtime, training, recruitment, and attrition."
)

if filtered_df.empty:
    st.warning("No employee records match your current filter selection. Adjust sidebar filters.")
    st.stop()

# Top KPI Row
kpis = compute_kpis(filtered_df)
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total HR Spend", format_inr(kpis["total_cost"]), f"{kpis['headcount']} Employees")
col2.metric("Avg Cost / Employee", format_inr(kpis["cost_per_employee"]))
col3.metric("Base Payroll", format_inr(kpis["total_salary"]))
col4.metric("Turnover & Attrition Cost", format_inr(kpis["total_turnover"]), f"{kpis['attrition_rate']:.1f}% Attrition")
col5.metric("Non-Salary Overhead", f"{kpis['overhead_pct']:.1f}%", f"Overtime: {format_inr(kpis['total_overtime'])}")

st.divider()

# Tabs for structured exploration
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📈 Cost Breakdown & Departments",
        "📍 Location & Role Matrix",
        "🎛️ Budget What-If Simulator",
        "🗂️ Employee Cost Explorer",
    ]
)

with tab1:
    c1, c2 = st.columns([1.15, 0.85])

    with c1:
        st.subheader("Departmental HR Cost Breakdown")
        dept_summary = get_department_summary(filtered_df)
        cost_components = [
            "Base_Salary",
            "Benefits_Cost",
            "Performance_Bonus",
            "Overtime_Cost",
            "Training_Cost",
            "Recruitment_Cost",
            "Turnover_Cost",
        ]
        fig_dept = px.bar(
            dept_summary,
            x="Department",
            y=cost_components,
            title="Stacked Cost Components by Department (INR)",
            labels={"value": "Cost (INR)", "variable": "Component"},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_dept.update_layout(barmode="stack", legend_title_text="Cost Component", height=430)
        st.plotly_chart(fig_dept, use_container_width=True)

    with c2:
        st.subheader("Overall Cost Structure")
        breakdown_df = get_cost_breakdown(filtered_df)
        fig_donut = px.pie(
            breakdown_df,
            names="Cost_Category",
            values="Amount",
            hole=0.48,
            title="Share of Total HR Expenditure",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_donut.update_traces(textposition="inside", textinfo="percent+label")
        fig_donut.update_layout(showlegend=False, height=430)
        st.plotly_chart(fig_donut, use_container_width=True)

    st.subheader("Departmental Cost & Headcount Summary")
    display_dept = dept_summary.copy()
    currency_cols = [
        "Base_Salary",
        "Benefits_Cost",
        "Performance_Bonus",
        "Overtime_Cost",
        "Training_Cost",
        "Recruitment_Cost",
        "Turnover_Cost",
        "Total_HR_Cost",
        "Avg_Cost_Per_Employee",
    ]
    for col in currency_cols:
        display_dept[col] = display_dept[col].apply(format_inr)
    st.dataframe(display_dept, use_container_width=True, hide_index=True)

with tab2:
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Average Cost per Employee: Department vs. Role Level")
        pivot_df = filtered_df.pivot_table(
            index="Department",
            columns="Role_Level",
            values="Total_HR_Cost",
            aggfunc="mean",
        ).fillna(0)
        fig_heat = px.imshow(
            pivot_df,
            text_auto=".2s",
            aspect="auto",
            color_continuous_scale="Blues",
            title="Avg Annual HR Cost Heatmap (INR)",
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    with c4:
        st.subheader("Total HR Spend by Office Location")
        loc_df = (
            filtered_df.groupby("Location", as_index=False)
            .agg(Total_Cost=("Total_HR_Cost", "sum"), Headcount=("Employee_ID", "count"))
            .sort_values("Total_Cost", ascending=True)
        )
        fig_loc = px.bar(
            loc_df,
            x="Total_Cost",
            y="Location",
            orientation="h",
            text="Headcount",
            title="Total Spend & Headcount by Location",
            color="Total_Cost",
            color_continuous_scale="Teal",
        )
        fig_loc.update_traces(texttemplate="%{text} staff", textposition="outside")
        st.plotly_chart(fig_loc, use_container_width=True)

with tab3:
    st.subheader("Workforce Budget Optimization & Scenario Simulator")
    st.write(
        "Model annual financial impact by adjusting salary increments, attrition reduction targets, overtime controls, and L&D investments."
    )

    s1, s2, s3, s4 = st.columns(4)
    hike_pct = s1.slider("Annual Salary Hike (%)", -5.0, 20.0, 8.0, 0.5)
    attrition_red = s2.slider("Attrition Reduction (%)", 0.0, 60.0, 20.0, 5.0)
    overtime_red = s3.slider("Overtime Reduction (%)", 0.0, 50.0, 15.0, 5.0)
    training_boost = s4.slider("Training Budget Change (%)", -20.0, 50.0, 10.0, 5.0)

    sim = simulate_budget_scenario(
        filtered_df,
        salary_hike_pct=hike_pct,
        attrition_reduction_pct=attrition_red,
        overtime_reduction_pct=overtime_red,
        training_boost_pct=training_boost,
    )

    m1, m2, m3 = st.columns(3)
    m1.metric("Current Baseline Budget", format_inr(sim["baseline_total"]))
    m2.metric(
        "Projected Annual Budget",
        format_inr(sim["projected_total"]),
        f"{sim['delta_pct']:+.2f}%",
        delta_color="inverse",
    )
    m3.metric(
        "Net Cost Variance",
        format_inr(sim["net_delta"]),
        "Savings" if sim["net_delta"] < 0 else "Additional Spend",
        delta_color="inverse",
    )

    fig_waterfall = go.Figure(
        go.Waterfall(
            name="Budget Impact",
            orientation="v",
            measure=["absolute", "relative", "total"],
            x=["Baseline Budget", "Policy Adjustments", "Projected Budget"],
            y=[sim["baseline_total"], sim["net_delta"], sim["projected_total"]],
            text=[
                format_inr(sim["baseline_total"]),
                f"{sim['net_delta']:+,.0f}",
                format_inr(sim["projected_total"]),
            ],
            textposition="outside",
            decreasing={"marker": {"color": "#2ca02c"}},
            increasing={"marker": {"color": "#d62728"}},
            totals={"marker": {"color": "#1f77b4"}},
        )
    )
    fig_waterfall.update_layout(title="Baseline vs. Simulated HR Budget Bridge", height=400)
    st.plotly_chart(fig_waterfall, use_container_width=True)

with tab4:
    st.subheader("Granular Employee Cost Records")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    csv_export = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Filtered HR Cost Report (CSV)",
        data=csv_export,
        file_name="filtered_hr_cost_report.csv",
        mime="text/csv",
    )

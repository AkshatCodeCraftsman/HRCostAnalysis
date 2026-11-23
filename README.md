# HR Cost Analysis & Workforce Budgeting Dashboard

An interactive data analytics and workforce budgeting application built with **Python**, **Pandas**, **Plotly**, and **Streamlit**. It enables HR leaders and finance teams to track total workforce expenditure, uncover hidden cost drivers (overtime, attrition turnover, recruitment), and simulate annual budget scenarios.

## Features
- **Executive KPI Overview:** Tracks total HR spend, average cost per employee, base payroll, attrition replacement costs, and non-salary overhead percentage.
- **Departmental & Category Breakdown:** Visualizes stacked cost components (Base Salary, Benefits, Performance Bonus, Overtime, Training, Recruitment, Turnover) across departments.
- **Location & Role Level Matrix:** Interactive heatmap and regional spend comparison across offices and seniority levels.
- **Budget What-If Simulator:** Models the net financial impact of annual salary increments, attrition reduction initiatives, overtime caps, and training investments.
- **Custom CSV Support & Export:** Upload your own HR cost dataset or export filtered workforce reports directly to CSV.

## Project Structure
```text
hr_cost_analysis/
├── .streamlit/
│   └── config.toml         # Streamlit UI theme configuration
├── data/
│   └── hr_cost_data.csv    # Sample workforce cost dataset (250 employees)
├── src/
│   ├── __init__.py
│   └── analytics.py        # Core data processing, KPI, and simulation logic
├── app.py                  # Main Streamlit dashboard application
├── requirements.txt        # Python dependencies
├── .gitignore              # Git ignore rules
└── README.md               # Project documentation
```

## Quickstart (Local Setup)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/hr_cost_analysis.git
   cd hr_cost_analysis
   ```

2. **Create a virtual environment & install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate      # On Windows Git Bash: source venv/Scripts/activate
   pip install -r requirements.txt
   ```

3. **Run the Streamlit app:**
   ```bash
   streamlit run app.py
   ```

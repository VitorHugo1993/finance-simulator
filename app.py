import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Budget Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Data file path
DATA_FILE = "budget_data.json"

def load_data():
    """Load financial data from JSON file"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        "net_worth": {
            "current": 0,
            "savings_accounts": [],
            "investment_account": 0,
            "other_assets": 0
        },
        "income": {
            "user_salary": 0,
            "partner_salary": 0,
            "salary_months": 14
        },
        "fixed_expenses": [],
        "variable_expenses": [],
        "savings_contributions": [],
        "investment_contributions": [],
        "transactions": []
    }

def save_data(data):
    """Save financial data to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def calculate_total_expenses(data):
    """Calculate total monthly expenses"""
    fixed_total = sum(exp.get("amount", 0) for exp in data["fixed_expenses"])
    variable_total = sum(exp.get("amount", 0) for exp in data["variable_expenses"])
    return fixed_total + variable_total

def calculate_total_income(data):
    """Calculate total net monthly income"""
    return data["income"]["user_salary"] + data["income"]["partner_salary"]

def calculate_yearly_income(data):
    """Calculate net yearly income based on salary months (12 or 14)"""
    monthly_income = calculate_total_income(data)
    salary_months = data["income"].get("salary_months", 14)
    return monthly_income * salary_months

def calculate_total_savings(data):
    """Calculate total savings across all accounts"""
    savings_accounts = data["net_worth"].get("savings_accounts", [])
    if isinstance(savings_accounts, list):
        return sum(acc.get("balance", 0) for acc in savings_accounts)
    # Backward compatibility: if it's still a single value
    return data["net_worth"].get("savings_account", 0)

def calculate_current_net_worth(data):
    """Calculate current net worth"""
    total_savings = calculate_total_savings(data)
    return (
        total_savings +
        data["net_worth"]["investment_account"] +
        data["net_worth"]["other_assets"]
    )

def simulate_year_end_networth(data, years=1):
    """Simulate net worth at end of year(s)"""
    monthly_income = calculate_total_income(data)
    monthly_expenses = calculate_total_expenses(data)
    monthly_savings_contribution = sum(
        contrib.get("amount", 0) for contrib in data["savings_contributions"]
    )
    monthly_investment_contribution = sum(
        contrib.get("amount", 0) for contrib in data["investment_contributions"]
    )
    
    monthly_surplus = monthly_income - monthly_expenses - monthly_savings_contribution - monthly_investment_contribution
    
    current_networth = calculate_current_net_worth(data)
    current_savings = calculate_total_savings(data)
    current_investments = data["net_worth"]["investment_account"]
    
    # Monthly contributions are considered as consistent 12-month contributions
    # regardless of salary months (12 or 14)
    CONTRIBUTION_MONTHS = 12
    
    # Simple simulation (assuming no interest/growth for now)
    # User can add investment returns later
    projected_savings = current_savings + (monthly_savings_contribution * CONTRIBUTION_MONTHS * years)
    projected_investments = current_investments + (monthly_investment_contribution * CONTRIBUTION_MONTHS * years)
    projected_networth = (
        current_networth +
        (monthly_surplus * CONTRIBUTION_MONTHS * years) +
        (monthly_savings_contribution * CONTRIBUTION_MONTHS * years) +
        (monthly_investment_contribution * CONTRIBUTION_MONTHS * years)
    )
    
    return {
        "years": years,
        "current_networth": current_networth,
        "projected_networth": projected_networth,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "monthly_surplus": monthly_surplus,
        "projected_savings": projected_savings,
        "projected_investments": projected_investments
    }

# Load data
if 'data' not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data

# Sidebar navigation
st.sidebar.title("💰 Budget Tracker")
page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "💵 Income & Expenses", "💰 Savings & Investments", "🔮 Simulator", "⚙️ Settings"]
)

# Dashboard Page
if page == "📊 Dashboard":
    st.title("📊 Financial Dashboard")
    
    # Net Worth Card
    current_networth = calculate_current_net_worth(data)
    total_income = calculate_total_income(data)
    total_expenses = calculate_total_expenses(data)
    monthly_surplus = total_income - total_expenses
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Net Worth", f"€{current_networth:,.2f}")
    
    with col2:
        st.metric("Net Monthly Income", f"€{total_income:,.2f}")
    
    with col3:
        st.metric("Monthly Expenses", f"€{total_expenses:,.2f}")
    
    with col4:
        st.metric("Monthly Surplus", f"€{monthly_surplus:,.2f}", 
                 delta=f"{monthly_surplus/total_income*100:.1f}%" if total_income > 0 else "0%")
    
    st.divider()
    
    # Net Worth Breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Net Worth Breakdown")
        total_savings = calculate_total_savings(data)
        networth_data = {
            "Savings Accounts": total_savings,
            "Investment Account": data["net_worth"]["investment_account"],
            "Other Assets": data["net_worth"]["other_assets"]
        }
        st.bar_chart(networth_data)
    
    with col2:
        st.subheader("Net Monthly Cash Flow")
        cashflow_data = {
            "Net Income": total_income,
            "Expenses": total_expenses,
            "Surplus": max(0, monthly_surplus)
        }
        st.bar_chart(cashflow_data)
    
    # Recent Transactions
    if data.get("transactions"):
        st.subheader("Recent Transactions")
        transactions_df = pd.DataFrame(data["transactions"][-10:])
        st.dataframe(transactions_df, use_container_width=True, hide_index=True)

# Income & Expenses Page
elif page == "💵 Income & Expenses":
    st.title("💵 Income & Expenses")
    
    tab1, tab2, tab3 = st.tabs(["💰 Income", "📋 Fixed Expenses", "🛒 Variable Expenses"])
    
    with tab1:
        st.subheader("Net Monthly Income")
        
        # Salary months selection
        salary_months = st.radio(
            "Salary Months per Year",
            options=[12, 14],
            index=0 if data["income"].get("salary_months", 14) == 12 else 1,
            horizontal=True,
            help="Select 12 months (standard) or 14 months (Portugal - includes holiday and Christmas bonuses)"
        )
        data["income"]["salary_months"] = salary_months
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            user_salary = st.number_input("Your Net Monthly Salary", min_value=0.0, value=float(data["income"]["user_salary"]), step=100.0)
            data["income"]["user_salary"] = user_salary
        
        with col2:
            partner_salary = st.number_input("Partner's Net Monthly Salary", min_value=0.0, value=float(data["income"]["partner_salary"]), step=100.0)
            data["income"]["partner_salary"] = partner_salary
        
        total_income = user_salary + partner_salary
        yearly_income = calculate_yearly_income(data)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Net Monthly Income", f"€{total_income:,.2f}")
        with col2:
            st.metric(f"Net Yearly Income ({salary_months} months)", f"€{yearly_income:,.2f}")
    
    with tab2:
        st.subheader("Fixed Monthly Expenses")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("➕ Add Fixed Expense"):
                st.session_state.new_fixed_expense = True
        
        if st.session_state.get("new_fixed_expense", False):
            with st.form("add_fixed_expense", clear_on_submit=True):
                name = st.text_input("Expense Name")
                amount = st.number_input("Amount", min_value=0.0, step=10.0)
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("✅ Add Expense", use_container_width=True)
                with col2:
                    cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
                
                if submitted and name:
                    data["fixed_expenses"].append({"name": name, "amount": amount})
                    st.session_state.new_fixed_expense = False
                    st.rerun()
                elif cancelled:
                    st.session_state.new_fixed_expense = False
                    st.rerun()
        
        if data["fixed_expenses"]:
            # Display expenses with edit/delete options
            for idx, expense in enumerate(data["fixed_expenses"]):
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                with col1:
                    st.write(f"**{expense.get('name', 'Unnamed')}**")
                with col2:
                    st.write(f"€{expense.get('amount', 0):,.2f}")
                with col3:
                    if st.button("✏️", key=f"edit_fixed_{idx}"):
                        st.session_state[f"editing_fixed_{idx}"] = True
                with col4:
                    if st.button("🗑️", key=f"delete_fixed_{idx}"):
                        data["fixed_expenses"].pop(idx)
                        st.rerun()
                
                # Edit form
                if st.session_state.get(f"editing_fixed_{idx}", False):
                    with st.form(f"edit_fixed_expense_{idx}"):
                        new_name = st.text_input("Expense Name", value=expense.get('name', ''), key=f"edit_name_{idx}")
                        new_amount = st.number_input("Amount", min_value=0.0, value=float(expense.get('amount', 0)), step=10.0, key=f"edit_amount_{idx}")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Save", use_container_width=True):
                                data["fixed_expenses"][idx]["name"] = new_name
                                data["fixed_expenses"][idx]["amount"] = new_amount
                                st.session_state[f"editing_fixed_{idx}"] = False
                                st.rerun()
                        with col2:
                            if st.form_submit_button("❌ Cancel", use_container_width=True):
                                st.session_state[f"editing_fixed_{idx}"] = False
                                st.rerun()
            
            st.divider()
            
            # Summary
            total_fixed = sum(exp.get("amount", 0) for exp in data["fixed_expenses"])
            st.metric("Total Fixed Expenses", f"€{total_fixed:,.2f}")
            
            # Delete all option
            if st.button("🗑️ Delete All Fixed Expenses"):
                data["fixed_expenses"] = []
                st.rerun()
        else:
            st.info("No fixed expenses added yet.")
    
    with tab3:
        st.subheader("Variable Expenses")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("➕ Add Variable Expense"):
                st.session_state.new_variable_expense = True
        
        if st.session_state.get("new_variable_expense", False):
            with st.form("add_variable_expense", clear_on_submit=True):
                name = st.text_input("Expense Name")
                amount = st.number_input("Amount", min_value=0.0, step=10.0)
                date = st.date_input("Date", value=datetime.now())
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("✅ Add Expense", use_container_width=True)
                with col2:
                    cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
                
                if submitted and name:
                    data["variable_expenses"].append({
                        "name": name,
                        "amount": amount,
                        "date": date.strftime("%Y-%m-%d")
                    })
                    data["transactions"].append({
                        "type": "expense",
                        "category": "variable",
                        "name": name,
                        "amount": -amount,
                        "date": date.strftime("%Y-%m-%d")
                    })
                    st.session_state.new_variable_expense = False
                    st.rerun()
                elif cancelled:
                    st.session_state.new_variable_expense = False
                    st.rerun()
        
        if data["variable_expenses"]:
            # Display expenses with edit/delete options
            for idx, expense in enumerate(data["variable_expenses"]):
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
                with col1:
                    st.write(f"**{expense.get('name', 'Unnamed')}**")
                with col2:
                    st.write(f"€{expense.get('amount', 0):,.2f}")
                with col3:
                    st.write(f"📅 {expense.get('date', 'N/A')}")
                with col4:
                    if st.button("✏️", key=f"edit_variable_{idx}"):
                        st.session_state[f"editing_variable_{idx}"] = True
                with col5:
                    if st.button("🗑️", key=f"delete_variable_{idx}"):
                        # Remove from variable expenses
                        deleted_expense = data["variable_expenses"].pop(idx)
                        # Remove corresponding transaction
                        for trans_idx, trans in enumerate(data["transactions"]):
                            if (trans.get("type") == "expense" and 
                                trans.get("category") == "variable" and
                                trans.get("name") == deleted_expense.get("name") and
                                trans.get("date") == deleted_expense.get("date")):
                                data["transactions"].pop(trans_idx)
                                break
                        st.rerun()
                
                # Edit form
                if st.session_state.get(f"editing_variable_{idx}", False):
                    with st.form(f"edit_variable_expense_{idx}"):
                        new_name = st.text_input("Expense Name", value=expense.get('name', ''), key=f"var_edit_name_{idx}")
                        new_amount = st.number_input("Amount", min_value=0.0, value=float(expense.get('amount', 0)), step=10.0, key=f"var_edit_amount_{idx}")
                        expense_date = datetime.strptime(expense.get('date', datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d").date()
                        new_date = st.date_input("Date", value=expense_date, key=f"var_edit_date_{idx}")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Save", use_container_width=True):
                                old_expense = data["variable_expenses"][idx].copy()
                                data["variable_expenses"][idx]["name"] = new_name
                                data["variable_expenses"][idx]["amount"] = new_amount
                                data["variable_expenses"][idx]["date"] = new_date.strftime("%Y-%m-%d")
                                
                                # Update corresponding transaction
                                for trans in data["transactions"]:
                                    if (trans.get("type") == "expense" and 
                                        trans.get("category") == "variable" and
                                        trans.get("name") == old_expense.get("name") and
                                        trans.get("date") == old_expense.get("date")):
                                        trans["name"] = new_name
                                        trans["amount"] = -new_amount
                                        trans["date"] = new_date.strftime("%Y-%m-%d")
                                        break
                                
                                st.session_state[f"editing_variable_{idx}"] = False
                                st.rerun()
                        with col2:
                            if st.form_submit_button("❌ Cancel", use_container_width=True):
                                st.session_state[f"editing_variable_{idx}"] = False
                                st.rerun()
            
            st.divider()
            
            # Summary
            total_variable = sum(exp.get("amount", 0) for exp in data["variable_expenses"])
            st.metric("Total Variable Expenses", f"€{total_variable:,.2f}")
            
            # Delete all option
            if st.button("🗑️ Delete All Variable Expenses"):
                # Remove all corresponding transactions
                data["transactions"] = [t for t in data["transactions"] if not (t.get("type") == "expense" and t.get("category") == "variable")]
                data["variable_expenses"] = []
                st.rerun()
        else:
            st.info("No variable expenses added yet.")

# Savings & Investments Page
elif page == "💰 Savings & Investments":
    st.title("💰 Savings & Investments")
    
    tab1, tab2, tab3 = st.tabs(["💾 Savings Account", "📈 Investment Account", "📊 Net Worth"])
    
    with tab1:
        st.subheader("Savings Accounts")
        
        # Initialize savings_accounts if it doesn't exist or is old format
        if "savings_accounts" not in data["net_worth"] or not isinstance(data["net_worth"]["savings_accounts"], list):
            # Migrate old format to new format
            if "savings_account" in data["net_worth"] and data["net_worth"]["savings_account"] > 0:
                data["net_worth"]["savings_accounts"] = [{
                    "name": "Main Savings Account",
                    "balance": data["net_worth"]["savings_account"]
                }]
            else:
                data["net_worth"]["savings_accounts"] = []
        
        savings_accounts = data["net_worth"]["savings_accounts"]
        total_savings = calculate_total_savings(data)
        
        # Display total savings
        st.metric("Total Savings Across All Accounts", f"€{total_savings:,.2f}")
        
        st.divider()
        
        # Add new account button
        if st.button("➕ Add New Savings Account"):
            if "new_savings_account" not in st.session_state:
                st.session_state.new_savings_account = True
        
        # Form to add new account
        if st.session_state.get("new_savings_account", False):
            with st.form("add_savings_account"):
                account_name = st.text_input("Account Name (e.g., Bank Name)", placeholder="e.g., Banco Santander")
                initial_balance = st.number_input("Initial Balance", min_value=0.0, value=0.0, step=100.0)
                submitted = st.form_submit_button("Add Account")
                if submitted and account_name:
                    savings_accounts.append({
                        "name": account_name,
                        "balance": initial_balance
                    })
                    st.session_state.new_savings_account = False
                    st.rerun()
        
        st.divider()
        
        # Display and manage existing accounts
        if savings_accounts:
            st.subheader("Your Savings Accounts")
            
            for idx, account in enumerate(savings_accounts):
                with st.expander(f"🏦 {account.get('name', 'Unnamed Account')} - €{account.get('balance', 0):,.2f}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        new_name = st.text_input(
                            "Account Name",
                            value=account.get('name', ''),
                            key=f"savings_name_{idx}"
                        )
                        new_balance = st.number_input(
                            "Balance",
                            min_value=0.0,
                            value=float(account.get('balance', 0)),
                            step=100.0,
                            key=f"savings_balance_{idx}"
                        )
                    
                    with col2:
                        st.write("")  # Spacing
                        if st.button("💾 Update", key=f"update_savings_{idx}"):
                            savings_accounts[idx]["name"] = new_name
                            savings_accounts[idx]["balance"] = new_balance
                            st.rerun()
                        if st.button("🗑️ Delete", key=f"delete_savings_{idx}"):
                            savings_accounts.pop(idx)
                            st.rerun()
            
            # Display summary table
            st.divider()
            st.subheader("Summary")
            summary_data = []
            for account in savings_accounts:
                summary_data.append({
                    "Account Name": account.get('name', 'Unnamed'),
                    "Balance": f"€{account.get('balance', 0):,.2f}"
                })
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
        else:
            st.info("No savings accounts added yet. Click 'Add New Savings Account' to get started.")
        
        st.divider()
        st.subheader("Monthly Contributions")
        st.caption("💡 Monthly contributions are considered as consistent 12-month contributions (regardless of salary months)")
        
        if st.button("➕ Add Savings Contribution"):
            if "new_savings_contribution" not in st.session_state:
                st.session_state.new_savings_contribution = True
        
        if st.session_state.get("new_savings_contribution", False):
            with st.form("add_savings_contribution"):
                if savings_accounts:
                    account_names = [acc.get('name', 'Unnamed') for acc in savings_accounts]
                    selected_account = st.selectbox("Select Account", account_names)
                else:
                    selected_account = None
                    st.info("Add a savings account first to track contributions")
                
                amount = st.number_input("Contribution Amount", min_value=0.0, step=50.0)
                date = st.date_input("Date", value=datetime.now())
                submitted = st.form_submit_button("Add Contribution")
                if submitted and amount > 0:
                    contribution_data = {
                        "amount": amount,
                        "date": date.strftime("%Y-%m-%d")
                    }
                    if selected_account:
                        contribution_data["account"] = selected_account
                    
                    data["savings_contributions"].append(contribution_data)
                    
                    # Update account balance if account is selected
                    if selected_account:
                        for acc in savings_accounts:
                            if acc.get('name') == selected_account:
                                acc["balance"] = acc.get("balance", 0) + amount
                                break
                    
                    data["transactions"].append({
                        "type": "savings",
                        "amount": amount,
                        "date": date.strftime("%Y-%m-%d"),
                        "account": selected_account if selected_account else "General"
                    })
                    st.session_state.new_savings_contribution = False
                    st.rerun()
        
        if data["savings_contributions"]:
            contrib_df = pd.DataFrame(data["savings_contributions"])
            if "amount" in contrib_df.columns:
                contrib_df["amount"] = contrib_df["amount"].apply(lambda x: f"€{x:,.2f}")
            st.dataframe(contrib_df, use_container_width=True, hide_index=True)
            
            total_contributions = sum(c.get("amount", 0) for c in data["savings_contributions"])
            st.metric("Total Contributions", f"€{total_contributions:,.2f}")
        else:
            st.info("No savings contributions recorded yet.")
    
    with tab2:
        st.subheader("Investment Account")
        
        current_investments = st.number_input(
            "Current Investment Balance",
            min_value=0.0,
            value=float(data["net_worth"]["investment_account"]),
            step=100.0
        )
        data["net_worth"]["investment_account"] = current_investments
        
        st.divider()
        st.subheader("Monthly Contributions")
        st.caption("💡 Monthly contributions are considered as consistent 12-month contributions (regardless of salary months)")
        
        if st.button("➕ Add Investment Contribution"):
            if "new_investment_contribution" not in st.session_state:
                st.session_state.new_investment_contribution = True
        
        if st.session_state.get("new_investment_contribution", False):
            with st.form("add_investment_contribution"):
                amount = st.number_input("Contribution Amount", min_value=0.0, step=50.0)
                date = st.date_input("Date", value=datetime.now())
                submitted = st.form_submit_button("Add Contribution")
                if submitted:
                    data["investment_contributions"].append({
                        "amount": amount,
                        "date": date.strftime("%Y-%m-%d")
                    })
                    data["net_worth"]["investment_account"] += amount
                    data["transactions"].append({
                        "type": "investment",
                        "amount": amount,
                        "date": date.strftime("%Y-%m-%d")
                    })
                    st.session_state.new_investment_contribution = False
                    st.rerun()
        
        if data["investment_contributions"]:
            contrib_df = pd.DataFrame(data["investment_contributions"])
            contrib_df["amount"] = contrib_df["amount"].apply(lambda x: f"€{x:,.2f}")
            st.dataframe(contrib_df, use_container_width=True, hide_index=True)
            
            total_contributions = sum(c.get("amount", 0) for c in data["investment_contributions"])
            st.metric("Total Contributions", f"€{total_contributions:,.2f}")
        else:
            st.info("No investment contributions recorded yet.")
    
    with tab3:
        st.subheader("Net Worth Overview")
        
        other_assets = st.number_input(
            "Other Assets",
            min_value=0.0,
            value=float(data["net_worth"]["other_assets"]),
            step=100.0
        )
        data["net_worth"]["other_assets"] = other_assets
        
        st.divider()
        
        total_savings = calculate_total_savings(data)
        networth_breakdown = {
            "Savings Accounts": total_savings,
            "Investment Account": data["net_worth"]["investment_account"],
            "Other Assets": data["net_worth"]["other_assets"]
        }
        
        total_networth = sum(networth_breakdown.values())
        st.metric("Total Net Worth", f"€{total_networth:,.2f}")
        
        st.bar_chart(networth_breakdown)
        
        # Show breakdown of savings accounts if any exist
        savings_accounts = data["net_worth"].get("savings_accounts", [])
        if savings_accounts and isinstance(savings_accounts, list):
            st.divider()
            st.subheader("Savings Accounts Breakdown")
            savings_breakdown = {acc.get('name', 'Unnamed'): acc.get('balance', 0) for acc in savings_accounts}
            st.bar_chart(savings_breakdown)

# Simulator Page
elif page == "🔮 Simulator":
    st.title("🔮 Net Worth Simulator")
    
    st.markdown("Simulate your net worth at the end of the year based on your current financial situation.")
    st.info("ℹ️ **Note:** Monthly contributions (savings & investments) are calculated as consistent 12-month contributions, regardless of whether you receive 12 or 14 months salary.")
    
    years = st.slider("Number of Years to Simulate", min_value=1, max_value=10, value=1)
    
    if st.button("🚀 Run Simulation"):
        simulation = simulate_year_end_networth(data, years)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Current Net Worth", f"€{simulation['current_networth']:,.2f}")
            st.metric("Projected Net Worth", f"€{simulation['projected_networth']:,.2f}")
            difference = simulation['projected_networth'] - simulation['current_networth']
            st.metric("Projected Growth", f"€{difference:,.2f}", 
                     delta=f"{(difference/simulation['current_networth']*100):.1f}%" if simulation['current_networth'] > 0 else "0%")
        
        with col2:
            st.metric("Net Monthly Income", f"€{simulation['monthly_income']:,.2f}")
            st.metric("Monthly Expenses", f"€{simulation['monthly_expenses']:,.2f}")
            st.metric("Monthly Surplus", f"€{simulation['monthly_surplus']:,.2f}")
        
        st.divider()
        
        st.subheader("Projected Breakdown")
        projected_data = {
            "Current": simulation['current_networth'],
            "Projected": simulation['projected_networth']
        }
        st.bar_chart(projected_data)
        
        st.subheader("Account Projections")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Projected Savings", f"€{simulation['projected_savings']:,.2f}")
        with col2:
            st.metric("Projected Investments", f"€{simulation['projected_investments']:,.2f}")

# Settings Page
elif page == "⚙️ Settings":
    st.title("⚙️ Settings")
    
    st.subheader("Data Management")
    
    if st.button("💾 Save All Data"):
        save_data(data)
        st.success("Data saved successfully!")
    
    if st.button("🔄 Reset All Data"):
        if st.checkbox("I understand this will delete all my data"):
            data = {
                "net_worth": {
                    "current": 0,
                    "savings_accounts": [],
                    "investment_account": 0,
                    "other_assets": 0
                },
                "income": {
                    "user_salary": 0,
                    "partner_salary": 0,
                    "salary_months": 14
                },
                "fixed_expenses": [],
                "variable_expenses": [],
                "savings_contributions": [],
                "investment_contributions": [],
                "transactions": []
            }
            st.session_state.data = data
            save_data(data)
            st.success("Data reset successfully!")
            st.rerun()

# Auto-save on changes
save_data(data)
st.session_state.data = data


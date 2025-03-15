import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Define Monte Carlo Risk of Ruin function
def monte_carlo_risk_of_ruin(win_rate, risk_per_trade, num_simulations=10000, max_drawdown=0.5):
    """
    Simulates risk of ruin using a Monte Carlo approach.

    Parameters:
    - win_rate: Probability of winning a trade.
    - risk_per_trade: Fraction of capital risked per trade.
    - num_simulations: Number of Monte Carlo simulations.
    - max_drawdown: Maximum allowable drawdown before being considered ruined.

    Returns:
    - Risk of Ruin probability based on simulations.
    """
    num_trades = 100  # Simulating 100 trades per run
    ruin_count = 0

    for _ in range(num_simulations):
        equity = 1.0  # Starting with normalized equity of 1
        for _ in range(num_trades):
            if np.random.rand() < win_rate:
                equity *= (1 + risk_per_trade)  # Win scenario
            else:
                equity *= (1 - risk_per_trade)  # Loss scenario

            if equity <= (1 - max_drawdown):  # If drawdown exceeds limit, count as ruin
                ruin_count += 1
                break

    return ruin_count / num_simulations  # Proportion of simulations where ruin occurred

# Streamlit App Title
st.title("📊 EV Ryno Raper")

# File Upload
uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

if uploaded_file is not None:
    try:
        # Load CSV
        df = pd.read_csv(uploaded_file)
        st.write("✅ File uploaded successfully!")

        # Convert Datetime column if it exists
        if "Datetime" in df.columns:
            df['Datetime'] = pd.to_datetime(df['Datetime'], errors='coerce')

        # Ensure required columns exist
        required_columns = ["Duration", "MAE", "MFE"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if not missing_columns:
            df['Duration'] = pd.to_numeric(df['Duration'], errors='coerce')

            # =============================
            # ✨ Magic Button for Finding Best SL, TP, EV, and Risk of Ruin
            # =============================
            st.header("✨ Quit Your Job Button")

            if st.button("✨ I Quit ✨"):
                best_ev = float('-inf')
                best_sl, best_tp = None, None
                best_win_rate = 0

                # Loop through possible SL and TP combinations
                for sl in np.percentile(df["MAE"], [10, 20, 30, 40, 50, 60, 70, 80, 90]):
                    for tp in np.percentile(df["MFE"], [10, 20, 30, 40, 50, 60, 70, 80, 90]):
                        wins = df[df["MFE"] >= tp].shape[0]
                        losses = df[(df["MAE"] >= sl) | (df["MFE"] < tp)].shape[0]
                        total = wins + losses

                        if total > 0:
                            win_rate = wins / total
                            ev = (win_rate * 1) - ((1 - win_rate) * 1)  # Normalized EV

                            if ev > best_ev:
                                best_ev = ev
                                best_sl, best_tp = sl, tp
                                best_win_rate = win_rate

                # Calculate Risk of Ruin (Kelly & Monte Carlo)
                if best_sl is not None and best_tp is not None:
                    risk_per_trade = 0.01  # Assume 1% risk per trade
                    risk_to_reward = (best_tp / best_sl) if best_sl > 0 else 0

                    # Kelly Criterion Risk of Ruin
                    if risk_to_reward > 0:
                        kelly_criterion = best_win_rate - ((1 - best_win_rate) / risk_to_reward)
                        risk_of_ruin_kelly = np.exp(-5 * kelly_criterion) if kelly_criterion > 0 else 1.0
                    else:
                        risk_of_ruin_kelly = 1.0

                    # Monte Carlo Risk of Ruin
                    risk_of_ruin_monte_carlo = monte_carlo_risk_of_ruin(best_win_rate, risk_per_trade)

                    # Display Best Results
                    st.success("✅ Best Combination Found!")
                    st.write(f"📉 **Optimal Stop-Loss (SL):** {best_sl:.2f}")
                    st.write(f"📈 **Optimal Take-Profit (TP):** {best_tp:.2f}")
                    st.write(f"💰 **Maximum Expected Value (EV):** ${best_ev:.2f}")

                    # Display Risk of Ruin tables
                    st.subheader("📊 Risk of Ruin Calculations")

                    risk_data = pd.DataFrame({
                        "Method": ["Kelly Criterion", "Monte Carlo Simulation"],
                        "Risk of Ruin (%)": [risk_of_ruin_kelly * 100, risk_of_ruin_monte_carlo * 100]
                    })

                    st.table(risk_data)

                    # Cross-Comparison Table
                    st.subheader("🔍 Kelly vs. Monte Carlo Risk Comparison")
                    comparison_data = pd.DataFrame({
                        "Metric": ["Win Rate", "Risk Per Trade (%)", "Risk-to-Reward Ratio", "Kelly Risk of Ruin (%)", "Monte Carlo Risk of Ruin (%)"],
                        "Value": [
                            f"{best_win_rate:.2%}", 
                            f"{risk_per_trade * 100:.2f}%", 
                            f"{risk_to_reward:.2f}",
                            f"{risk_of_ruin_kelly * 100:.2f}%",
                            f"{risk_of_ruin_monte_carlo * 100:.2f}%"
                        ]
                    })

                    st.table(comparison_data)

                else:
                    st.error("⚠️ No optimal combination found. Try adjusting filters.")

    except Exception as e:
        st.error(f"⚠️ Error loading file: {e}")

else:
    st.info("Upload a CSV file to get started.")

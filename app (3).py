import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Streamlit App Title
st.title("📊 MAE & MFE Trading Dashboard")

# File Upload
uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

if uploaded_file is not None:
    try:
        # Load CSV
        df = pd.read_csv(uploaded_file)
        st.write("✅ File uploaded successfully!")

        # Show the full dataset (limit large files to first 1000 rows)
        st.subheader("📊 Full Uploaded Dataset Preview")
        if len(df) > 1000:
            st.write("⚠️ Displaying first 1000 rows (file too large).")
            st.dataframe(df.head(1000))
        else:
            st.dataframe(df)

        # Convert Datetime column if it exists
        if "Datetime" in df.columns:
            df['Datetime'] = pd.to_datetime(df['Datetime'], errors='coerce')
        else:
            st.warning("⚠️ 'Datetime' column not found in CSV.")

        # Ensure required columns exist
        required_columns = ["Duration", "MAE", "MFE"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            st.error(f"⚠️ Missing required columns: {missing_columns}")
        else:
            # Extract Day of the Week from Column C (if exists)
            if len(df.columns) > 2:
                df.rename(columns={df.columns[2]: "DayOfWeek"}, inplace=True)
                df['DayOfWeek'] = df['DayOfWeek'].astype(str)

            df['Duration'] = pd.to_numeric(df['Duration'], errors='coerce')

            # Show updated dataset preview
            st.write("✅ Processed Data Preview:", df.head())

            # =============================
            # 🔍 Select Timeframe: 3, 6, or 12 Months
            # =============================
            st.header("⏳ Select Timeframe for Analysis")
            timeframe_option = st.radio(
                "Choose a timeframe:",
                ["3 Months", "6 Months", "12 Months"],
                index=2
            )

            # Define timeframes based on the latest date in the dataset
            latest_date = df['Datetime'].max()
            three_months_ago = latest_date - pd.DateOffset(months=3)
            six_months_ago = latest_date - pd.DateOffset(months=6)
            one_year_ago = latest_date - pd.DateOffset(years=1)

            # Apply selected timeframe filter
            if timeframe_option == "3 Months":
                df = df[df['Datetime'] >= three_months_ago]
            elif timeframe_option == "6 Months":
                df = df[df['Datetime'] >= six_months_ago]
            elif timeframe_option == "12 Months":
                df = df[df['Datetime'] >= one_year_ago]

            # =============================
            # 🔍 Expected Value (EV) Tester
            # =============================
            st.header("🔍 Expected Value (EV) Tester")

            # User inputs for MAE, MFE thresholds, and dollar amount per trade
            user_mae = st.number_input("Enter MAE Threshold (SL Level)", min_value=0.0, step=0.01, value=0.2)
            user_mfe = st.number_input("Enter MFE Threshold (TP Level)", min_value=0.0, step=0.01, value=0.5)
            trade_amount = st.number_input("Enter Dollar Amount per Trade ($)", min_value=1.0, step=1.0, value=100.0)

            # Day of the week selection filter
            days_selected = st.multiselect(
                "Filter by Days of the Week", 
                df['DayOfWeek'].unique().tolist(), 
                default=df['DayOfWeek'].unique().tolist()
            )

            # Filter dataset based on selected days
            df_filtered = df[df['DayOfWeek'].isin(days_selected)]

            # Count Wins (TP) and Losses (SL)
            win_trades = df_filtered[df_filtered["MFE"] >= user_mfe].shape[0]
            loss_trades = df_filtered[(df_filtered["MAE"] >= user_mae) | (df_filtered["MFE"] < user_mfe)].shape[0]
            total_trades = win_trades + loss_trades

            if total_trades > 0:
                win_rate = win_trades / total_trades
                loss_rate = loss_trades / total_trades

                # Calculate Expected Value (EV)
                expected_value = (win_rate * trade_amount) - (loss_rate * trade_amount)

                # Display Results
                st.subheader("📊 EV Tester Results")
                st.write(f"✔️ **Win Rate:** {win_rate:.2%}")
                st.write(f"❌ **Loss Rate:** {loss_rate:.2%}")
                st.write(f"💰 **Expected Value per Trade:** ${expected_value:.2f}")

            else:
                st.warning("No trades found that match the selected criteria. Adjust your inputs.")

            # =============================
            # ✨ Magic Button for Finding Best SL, TP, and EV
            # =============================
            st.header("✨ Let the Magic Happen!")

            if st.button("✨ Magic ✨"):
                best_ev = float('-inf')
                best_sl, best_tp = None, None

                # Loop through possible SL and TP combinations
                for sl in np.percentile(df_filtered["MAE"], [10, 20, 30, 40, 50, 60, 70, 80, 90]):
                    for tp in np.percentile(df_filtered["MFE"], [10, 20, 30, 40, 50, 60, 70, 80, 90]):
                        wins = df_filtered[df_filtered["MFE"] >= tp].shape[0]
                        losses = df_filtered[(df_filtered["MAE"] >= sl) | (df_filtered["MFE"] < tp)].shape[0]
                        total = wins + losses

                        if total > 0:
                            win_rate = wins / total
                            loss_rate = losses / total
                            ev = (win_rate * trade_amount) - (loss_rate * trade_amount)

                            if ev > best_ev:
                                best_ev = ev
                                best_sl, best_tp = sl, tp

                # Display Best Results
                if best_sl is not None and best_tp is not None:
                    st.success("✅ Best Combination Found!")
                    st.write(f"📉 **Optimal Stop-Loss (SL):** {best_sl:.2f}")
                    st.write(f"📈 **Optimal Take-Profit (TP):** {best_tp:.2f}")
                    st.write(f"💰 **Maximum Expected Value (EV):** ${best_ev:.2f}")
                else:
                    st.error("⚠️ No optimal combination found. Try adjusting filters.")

    except Exception as e:
        st.error(f"⚠️ Error loading file: {e}")

else:
    st.info("Upload a CSV file to get started.")
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
# Calculate Risk of Ruin (Kelly & Monte Carlo)
                if best_sl is not None and best_tp is not None:
                    risk_per_trade = 0.01  
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

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Function to calculate win/loss streaks
def calculate_streaks(results):
    """
    Calculates the longest winning and losing streaks given a list of 'Win' and 'Loss' results.
    """
    max_win_streak = max_loss_streak = 0
    current_win_streak = current_loss_streak = 0

    for result in results:
        if result == "Win":
            current_win_streak += 1
            current_loss_streak = 0
        else:
            current_loss_streak += 1
            current_win_streak = 0

        max_win_streak = max(max_win_streak, current_win_streak)
        max_loss_streak = max(max_loss_streak, current_loss_streak)

    return max_win_streak, max_loss_streak

# Streamlit App Title
st.title("📊 MAE & MFE Trading Dashboard")

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
        required_columns = ["Duration", "MAE", "MFE", "DayOfWeek"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if not missing_columns:
            df['Duration'] = pd.to_numeric(df['Duration'], errors='coerce')

            # =============================
            # ⏳ Select Timeframe: 3, 6, or 12 Months
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
            # 📅 Day of the Week Filter
            # =============================
            st.header("📅 Filter by Day of the Week")
            days_selected = st.multiselect(
                "Select trading days to analyze:",
                df['DayOfWeek'].unique().tolist(),
                default=df['DayOfWeek'].unique().tolist()
            )

            # Apply Day Filter
            df_filtered = df[df['DayOfWeek'].isin(days_selected)]

            # =============================
            # 🔍 Expected Value (EV) Tester
            # =============================
            st.header("🔍 Expected Value (EV) Tester")

            # User inputs for MAE, MFE thresholds, and dollar amount per trade
            user_mae = st.number_input("Enter MAE Threshold (SL Level)", min_value=0.0, step=0.01, value=0.2)
            user_mfe = st.number_input("Enter MFE Threshold (TP Level)", min_value=0.0, step=0.01, value=0.5)
            trade_amount = st.number_input("Enter Dollar Amount per Trade ($)", min_value=1.0, step=1.0, value=100.0)

            # Count Wins (TP) and Losses (SL)
            win_trades = df_filtered[df_filtered["MFE"] >= user_mfe].shape[0]
            loss_trades = df_filtered[(df_filtered["MAE"] >= user_mae) | (df_filtered["MFE"] < user_mfe)].shape[0]
            total_trades = win_trades + loss_trades

            if total_trades > 0:
                win_rate = win_trades / total_trades
                loss_rate = loss_trades / total_trades
                expected_value = (win_rate * trade_amount) - (loss_rate * trade_amount)

                st.subheader("📊 EV Tester Results")
                st.write(f"✔️ **Win Rate:** {win_rate:.2%}")
                st.write(f"❌ **Loss Rate:** {loss_rate:.2%}")
                st.write(f"💰 **Expected Value per Trade:** ${expected_value:.2f}")

            # =============================
            # ✨ Magic Button for Finding Best SL, TP, EV
            # =============================
            st.header("✨ Let the Magic Happen!")

            if st.button("✨ Magic ✨"):
                best_ev = float('-inf')
                best_sl, best_tp = None, None

                for sl in np.percentile(df_filtered["MAE"].dropna(), [10, 20, 30, 40, 50, 60, 70, 80, 90]):
                    for tp in np.percentile(df_filtered["MFE"].dropna(), [10, 20, 30, 40, 50, 60, 70, 80, 90]):
                        wins = df_filtered[df_filtered["MFE"] >= tp].shape[0]
                        losses = df_filtered[(df_filtered["MAE"] >= sl) | (df_filtered["MFE"] < tp)].shape[0]
                        total = wins + losses

                        if total > 0:
                            win_rate = wins / total
                            ev = (win_rate * 100) - ((1 - win_rate) * 100)

                            if ev > best_ev:
                                best_ev = ev
                                best_sl, best_tp = sl, tp

                if best_sl is not None and best_tp is not None:
                    st.success("✅ Best Combination Found!")
                    st.write(f"📉 **Optimal Stop-Loss (SL):** {best_sl:.2f}")
                    st.write(f"📈 **Optimal Take-Profit (TP):** {best_tp:.2f}")
                    st.write(f"💰 **Maximum Expected Value (EV):** ${best_ev:.2f}")

                    # Calculate streaks for Magic Button
                    trade_results = ["Win" if mfe >= best_tp else "Loss" for mfe in df_filtered["MFE"]]
                    max_win_streak, max_loss_streak = calculate_streaks(trade_results)
                    total_wins = trade_results.count("Win")
                    total_losses = trade_results.count("Loss")

                    st.subheader("📊 Win/Loss Streak Data (Magic Button)")
                    st.write(f"🔥 **Biggest Win Streak:** {max_win_streak}")
                    st.write(f"💀 **Biggest Loss Streak:** {max_loss_streak}")
                    st.write(f"✅ **Total Wins:** {total_wins}")
                    st.write(f"❌ **Total Losses:** {total_losses}")

    except Exception as e:
        st.error(f"⚠️ Error loading file: {e}")

else:
    st.info("Upload a CSV file to get started.")

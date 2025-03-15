import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Function to calculate win/loss streaks
def calculate_streaks(results):
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
            # 🔘 Find Best 1:2 RR Combination
            # =============================
            st.header("🔘 Find Best 1:2 Risk-to-Reward Combination")

            if st.button("🔘 Find Best 1:2 RR Setup"):
                best_ev_12 = float('-inf')
                best_sl_12, best_tp_12 = None, None

                for sl_12 in np.percentile(df_filtered["MAE"].dropna(), [10, 20, 30, 40, 50, 60, 70, 80, 90]):
                    tp_12 = sl_12 * 2  # 1:2 Risk-to-Reward Ratio

                    wins_12 = df_filtered[df_filtered["MFE"] >= tp_12].shape[0]
                    losses_12 = df_filtered[(df_filtered["MAE"] >= sl_12) | (df_filtered["MFE"] < tp_12)].shape[0]
                    total_12 = wins_12 + losses_12

                    if total_12 > 0:
                        win_rate_12 = wins_12 / total_12
                        ev_12 = (win_rate_12 * 100) - ((1 - win_rate_12) * 100)

                        if ev_12 > best_ev_12 and win_rate_12 > 0.5:
                            best_ev_12 = ev_12
                            best_sl_12, best_tp_12 = sl_12, tp_12

                if best_sl_12 is not None and best_tp_12 is not None:
                    st.success("✅ Best 1:2 RR Combination Found!")
                    st.write(f"📉 **Optimal Stop-Loss (SL):** {best_sl_12:.2f}")
                    st.write(f"📈 **Optimal Take-Profit (TP):** {best_tp_12:.2f}")
                    st.write(f"💰 **Maximum Expected Value (EV):** ${best_ev_12:.2f}")

                    # Calculate streaks for 1:2 RR Finder
                    trade_results_12 = ["Win" if mfe >= best_tp_12 else "Loss" for mfe in df_filtered["MFE"]]
                    max_win_streak_12, max_loss_streak_12 = calculate_streaks(trade_results_12)
                    total_wins_12 = trade_results_12.count("Win")
                    total_losses_12 = trade_results_12.count("Loss")

                    st.subheader("📊 Win/Loss Streak Data (1:2 RR Finder)")
                    st.write(f"🔥 **Biggest Win Streak:** {max_win_streak_12}")
                    st.write(f"💀 **Biggest Loss Streak:** {max_loss_streak_12}")
                    st.write(f"✅ **Total Wins:** {total_wins_12}")
                    st.write(f"❌ **Total Losses:** {total_losses_12}")

    except Exception as e:
        st.error(f"⚠️ Error loading file: {e}")

else:
    st.info("Upload a CSV file to get started.")

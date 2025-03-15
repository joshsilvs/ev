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
                df_filtered = df[df['Datetime'] >= three_months_ago]
            elif timeframe_option == "6 Months":
                df_filtered = df[df['Datetime'] >= six_months_ago]
            elif timeframe_option == "12 Months":
                df_filtered = df[df['Datetime'] >= one_year_ago]

            # =============================
            # ✨ Magic Button for Finding Best SL, TP, EV
            # =============================
            st.header("✨ Quit Your Job Here")

            if st.button("✨ I Quit ✨"):
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

            # =============================
            # 🔘 Find Best 1:1 RR Combination
            # =============================
            st.header("🔘 Lazy Johnson 1:1 Finder")

            if st.button("🔘 Find Best 1:1 RR Setup"):
                best_ev_rr = float('-inf')
                best_sl_rr, best_tp_rr = None, None

                for sl_rr in np.percentile(df_filtered["MAE"].dropna(), [10, 20, 30, 40, 50, 60, 70, 80, 90]):
                    tp_rr = sl_rr  # 1:1 Risk-to-Reward Ratio

                    wins_rr = df_filtered[df_filtered["MFE"] >= tp_rr].shape[0]
                    losses_rr = df_filtered[(df_filtered["MAE"] >= sl_rr) | (df_filtered["MFE"] < tp_rr)].shape[0]
                    total_rr = wins_rr + losses_rr

                    if total_rr > 0:
                        win_rate_rr = wins_rr / total_rr
                        ev_rr = (win_rate_rr * 100) - ((1 - win_rate_rr) * 100)

                        if ev_rr > best_ev_rr and win_rate_rr > 0.5:
                            best_ev_rr = ev_rr
                            best_sl_rr, best_tp_rr = sl_rr, tp_rr

                if best_sl_rr is not None and best_tp_rr is not None:
                    st.success("✅ Best 1:1 RR Combination Found!")
                    st.write(f"📉 **Optimal Stop-Loss (SL):** {best_sl_rr:.2f}")
                    st.write(f"📈 **Optimal Take-Profit (TP):** {best_tp_rr:.2f}")
                    st.write(f"💰 **Maximum Expected Value (EV):** ${best_ev_rr:.2f}")

                    # Calculate streaks for 1:1 Finder
                    trade_results_rr = ["Win" if mfe >= best_tp_rr else "Loss" for mfe in df_filtered["MFE"]]
                    max_win_streak_rr, max_loss_streak_rr = calculate_streaks(trade_results_rr)
                    total_wins_rr = trade_results_rr.count("Win")
                    total_losses_rr = trade_results_rr.count("Loss")

                    st.subheader("📊 Win/Loss Streak Data (1:1 RR Finder)")
                    st.write(f"🔥 **Biggest Win Streak:** {max_win_streak_rr}")
                    st.write(f"💀 **Biggest Loss Streak:** {max_loss_streak_rr}")
                    st.write(f"✅ **Total Wins:** {total_wins_rr}")
                    st.write(f"❌ **Total Losses:** {total_losses_rr}")

    except Exception as e:
        st.error(f"⚠️ Error loading file: {e}")

else:
    st.info("Upload a CSV file to get started.")

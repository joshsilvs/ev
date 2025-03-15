import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Function to calculate win/loss streaks
def calculate_streaks(results):
    """
    Given a list of 'Win' and 'Loss' results, calculate the longest winning and losing streaks.
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
                df_filtered['DayOfWeek'].unique().tolist(), 
                default=df_filtered['DayOfWeek'].unique().tolist()
            )

            # Filter dataset based on selected days
            df_filtered = df_filtered[df_filtered['DayOfWeek'].isin(days_selected)]

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

                # Generate streak data for EV Tester Results
                df_ev = df_filtered.copy()
                df_ev["Result"] = np.where(df_ev["MFE"] >= user_mfe, "Win", "Loss")
                win_streak, loss_streak = calculate_streaks(df_ev["Result"].tolist())
                total_wins = (df_ev["Result"] == "Win").sum()
                total_losses = (df_ev["Result"] == "Loss").sum()

                # Display streak statistics for EV Tester
                st.subheader("📊 Streak Data for EV Tester")
                ev_streak_data = pd.DataFrame({
                    "Metric": ["Biggest Win Streak", "Biggest Loss Streak", "Total Wins", "Total Losses"],
                    "Value": [win_streak, loss_streak, total_wins, total_losses]
                })

                st.table(ev_streak_data)

            else:
                st.warning("No trades found that match the selected criteria. Adjust your inputs.")

            # =============================
            # ✨ Magic Button for Finding Best SL, TP, EV, and Streak Data
            # =============================
            st.header("✨ How To Quit Your Job")

            if st.button("✨ Click Here ✨"):
                best_ev = float('-inf')
                best_sl, best_tp = None, None

                # Loop through possible SL and TP combinations
                for sl in np.percentile(df_filtered["MAE"].dropna(), [10, 20, 30, 40, 50, 60, 70, 80, 90]):
                    for tp in np.percentile(df_filtered["MFE"].dropna(), [10, 20, 30, 40, 50, 60, 70, 80, 90]):
                        wins = df_filtered[df_filtered["MFE"] >= tp].shape[0]
                        losses = df_filtered[(df_filtered["MAE"] >= sl) | (df_filtered["MFE"] < tp)].shape[0]
                        total = wins + losses

                        if total > 0:
                            win_rate = wins / total
                            ev = (win_rate * trade_amount) - ((1 - win_rate) * trade_amount)

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

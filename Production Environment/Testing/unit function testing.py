from datetime import datetime, timedelta

# Simulated list of NSE trading holidays fetched from https://www.nseindia.com/resources/exchange-communication-holidays
TRADING_HOLIDAYS = [
    "2024-03-29",  # Example: Holi
    "2024-08-15",  # Independence Day
    "2024-10-02",  # Gandhi Jayanti
    # Add more holidays as needed...
]

def is_trading_holiday(date):
    """Check if the given date is a trading holiday."""
    return date.strftime("%Y-%m-%d") in TRADING_HOLIDAYS

def find_previous_working_day(date):
    """Find the most recent working day by recursively skipping trading holidays and weekends."""
    while date.weekday() in [5, 6] or is_trading_holiday(date):  # Saturday=5, Sunday=6
        date -= timedelta(days=1)
    return date

def fetch_dates():
    print("Fetching dates for historical OHLC data...")

    now = datetime.now()
    day_of_week = now.weekday()  # Monday is 0, Sunday is 6
    fixed_time_1 = "09:15"
    fixed_time_2 = "15:30"

    # Step 1: Check if today is a trading holiday or the weekend
    if is_trading_holiday(now) or day_of_week in [5, 6]:  # Trading holiday or weekend (Saturday/Sunday)
        previous_day = find_previous_working_day(now - timedelta(days=1))  # Find last working day
        print(f"Today is a non-working day. Previous working day: {previous_day.strftime('%Y-%m-%d')}")

        # No time logic applied here, just fetch two prior working days
        from_date = find_previous_working_day(previous_day - timedelta(days=1))
        to_date = previous_day

    # Step 2: If today is not a holiday or weekend, follow the time-based logic properly
    else:
        # Case 1: Monday before 9:15 AM -> Treat Monday as Friday
        if day_of_week == 0 and now.time() < datetime.strptime("09:15", "%H:%M").time():
            # Treat as Friday, fetch Wednesday and Thursday
            from_date = now - timedelta(days=5)  # Wednesday
            to_date = now - timedelta(days=4)    # Thursday

        # Case 2: Monday after 9:15 AM -> Fetch Thursday and Friday
        elif day_of_week == 0 and now.time() >= datetime.strptime("09:15", "%H:%M").time():
            from_date = now - timedelta(days=4)  # Thursday
            to_date = now - timedelta(days=3)    # Friday

        # Case 3: Tuesday before 9:15 AM -> Treat Tuesday as Monday
        elif day_of_week == 1 and now.time() < datetime.strptime("09:15", "%H:%M").time():
            from_date = now - timedelta(days=4)  # Thursday
            to_date = now - timedelta(days=3)    # Friday

        # Case 4: Tuesday after 9:15 AM -> Fetch Friday and Monday
        elif day_of_week == 1 and now.time() >= datetime.strptime("09:15", "%H:%M").time():
            from_date = now - timedelta(days=3)  # Friday
            to_date = now - timedelta(days=1)    # Monday

        # Case 5: Wednesday before 9:15 AM -> Treat Wednesday as Tuesday
        elif day_of_week == 2 and now.time() < datetime.strptime("09:15", "%H:%M").time():
            from_date = now - timedelta(days=3)  # Friday
            to_date = now - timedelta(days=1)    # Monday

        # Case 6: Wednesday after 9:15 AM -> Fetch Monday and Tuesday
        elif day_of_week == 2 and now.time() >= datetime.strptime("09:15", "%H:%M").time():
            from_date = now - timedelta(days=2)  # Monday
            to_date = now - timedelta(days=1)    # Tuesday

        # Case 7: Thursday before 9:15 AM -> Treat Thursday as Wednesday
        elif day_of_week == 3 and now.time() < datetime.strptime("09:15", "%H:%M").time():
            from_date = now - timedelta(days=2)  # Monday
            to_date = now - timedelta(days=1)    # Tuesday

        # Case 8: Thursday after 9:15 AM -> Fetch Tuesday and Wednesday
        elif day_of_week == 3 and now.time() >= datetime.strptime("09:15", "%H:%M").time():
            from_date = now - timedelta(days=2)  # Tuesday
            to_date = now - timedelta(days=1)    # Wednesday

        # Case 9: Friday before 9:15 AM -> Treat Friday as Thursday
        elif day_of_week == 4 and now.time() < datetime.strptime("09:15", "%H:%M").time():
            from_date = now - timedelta(days=2)  # Tuesday
            to_date = now - timedelta(days=1)    # Wednesday

        # Case 10: Friday after 9:15 AM -> Fetch Wednesday and Thursday
        elif day_of_week == 4 and now.time() >= datetime.strptime("09:15", "%H:%M").time():
            from_date = now - timedelta(days=2)  # Wednesday
            to_date = now - timedelta(days=1)    # Thursday

    # Step 3: Apply time logic (market open and close times)
    from_date_str = from_date.strftime("%Y-%m-%d ") + fixed_time_1
    to_date_str = to_date.strftime("%Y-%m-%d ") + fixed_time_2

    print(f"From date: {from_date_str}, To date: {to_date_str}")
    return [from_date_str, to_date_str]

# Example of usage
fetch_dates()


'''
Key Scenarios:
Saturday/Sunday:

Logic: Treat both days as if it's Friday.
Fetch data for Wednesday (from date) and Thursday (to date).
No time logic applies on these days since the market is closed.
Monday (Before 9:15 AM):

Logic: Treat Monday as Friday (i.e., consider the market hasn't opened yet).
Fetch data for Wednesday (from date) and Thursday (to date).
Reasoning: We haven't received Monday’s data yet, so we fetch the last two trading days.
Monday (After 9:15 AM):

Logic: The market is open, and we should fetch for Thursday (from date) and Friday (to date).
Reasoning: Monday’s data will start populating after the market opens.
Tuesday (Before 9:15 AM):

Logic: Treat Tuesday as Monday (since the market hasn’t opened).
Fetch data for Thursday (from date) and Friday (to date).
Tuesday (After 9:15 AM):

Logic: Fetch for Friday (from date) and Monday (to date).
Reasoning: We start receiving Monday’s data after the market opens.
Wednesday (Before 9:15 AM):

Logic: Treat Wednesday as Tuesday.
Fetch data for Friday (from date) and Monday (to date).
Wednesday (After 9:15 AM):

Logic: Fetch for Monday (from date) and Tuesday (to date).
Thursday (Before 9:15 AM):

Logic: Treat Thursday as Wednesday.
Fetch data for Monday (from date) and Tuesday (to date).
Thursday (After 9:15 AM):

Logic: Fetch for Tuesday (from date) and Wednesday (to date).
Friday (Before 9:15 AM):

Logic: Treat Friday as Thursday.
Fetch data for Tuesday (from date) and Wednesday (to date).

Friday (After 9:15 AM):
Logic: Fetch for Wednesday (from date) and Thursday (to date).
'''
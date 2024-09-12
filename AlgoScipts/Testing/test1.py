from datetime import datetime, timedelta

def fetch_date(day="today"):
    # Get current date and time
    now = datetime.now()

    # Yesterday's and day-before-yesterday's date and time
    yesterday = now - timedelta(days=1)
    day_before_yesterday = now - timedelta(days=2)

    # Format the time
    fixed_time_1 = "09:15"
    fixed_time_2 = "15:30"

    if day == "today":
        # Return list with yesterday's and today's date in fixed format
        return [yesterday.strftime("%Y-%m-%d ") + fixed_time_1, now.strftime("%Y-%m-%d ") + fixed_time_2]
    elif day == "yesterday":
        # Return list with day-before-yesterday and yesterday's date in fixed format
        return [day_before_yesterday.strftime("%Y-%m-%d ") + fixed_time_1,
                yesterday.strftime("%Y-%m-%d ") + fixed_time_2]


# # Testing the function with "yesterday"
# dateCorrect = fetch_date("yesterday")
# previousDayDate = dateCorrect[0]
# todayDayDate = dateCorrect[1]
#
#
# print(f"previous date {previousDayDate}")
# print(f"today date {todayDayDate}")


# Function to round off the value and show next 3 decimal points
def round_to_three_decimals(value):
    return f"{value:.3f}"

# Example usage
value = -1.1899999999999977
rounded_value = round_to_three_decimals(value)
print(rounded_value)


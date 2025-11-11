import gspread
import os
import re
from datetime import datetime

## Filtering 
# 1. Format sensitivity (could remove after adding GPT)
# 2. Valid time
# 3. Existing Entries
# 4. Day limit

# Check if a time is within valid hours
def is_valid_time(time_str, min_hour=9, max_hour=18):
    time_hour = to_24_hour_format(time_str)
    if(time_hour < min_hour or time_hour > max_hour):
        return False
    return True

# Check if end time is after start time
def is_end_time_after_start(start_str, end_str):
    start_hour = to_24_hour_format(start_str)
    end_hour = to_24_hour_format(end_str)
    if(end_hour <= start_hour):
        return False
    return True

# Convert to 24-hour format
def to_24_hour_format(time_str):
    time_hour = int(time_str.replace("am", "").replace("pm", ""))
    if 'pm' in time_str and time_hour != 12:
        time_hour += 12
    return time_hour

# Check if entry already exists
def entry_exists(worksheet, row, col):
    existing_value = worksheet.cell(row, col).value
    if existing_value:
        return True
    return False
    
# Check if the day limit has been reached (3 people per day)
def day_limit_reached(worksheet, col, limit=3):
    # Get all values in the column (returns list of values)
    col_values = worksheet.col_values(col)
    
    # Skip header (first 2 elements) and count non-empty
    filled_count = sum(1 for value in col_values[2:] if value.strip())
    
    if filled_count >= limit:
        return True
    return False

def main():
    # Get relative path
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, 'credentials.json')
    gc = gspread.service_account(filename)

    # Open the Google Sheet using its key
    sh = gc.open_by_key('134mf9hF5xPVwbH7OwvEquPu5zebDaX_SNuleEt5M8B8')
    worksheet = sh.get_worksheet(0)

    # Get name and day input
    print("Whats your name?")
    name = input()

    while(True):
        print("What day do you want to work?")
        day = input()

        while(True):
            # Search for cell input
            cell_name = worksheet.find(re.compile(name, re.IGNORECASE))
            cell_day = worksheet.find(re.compile(day, re.IGNORECASE))

            # Check if entry already exists
            if entry_exists(worksheet, cell_name.row, cell_day.col):
                print("An entry already exists for this name and day. \n"
                        "Would you like to change it? (yes/no)")
                response = input().strip().lower()
                if response != 'yes':
                    print("Exiting without changes.")
                    return
            break

        # Check if day limit reached
        if day_limit_reached(worksheet, cell_day.col):
            print("The limit for this day has been reached. Please choose another day.")
            continue
        else:
            break
            
    
    # Get start and end time input
    while(True):
        print("What time do you want to start?")
        start_time = input()
        if not is_valid_time(start_time):
            print("Invalid start time. Please enter a time between 9am and 6pm.")
            continue
        else:
            break

    while(True):
        print("What time do you want to end?")
        end_time = input()
        if not is_valid_time(end_time):
            print("Invalid end time. Please enter a time between 9am and 6pm.")
            continue
        elif not is_end_time_after_start(start_time, end_time):
            print("End time must be after start time. Please enter a valid end time.")
            continue
        else:
            break

    worksheet.update_cell(cell_name.row, cell_day.col, f"{start_time}")
    worksheet.update_cell(cell_name.row, cell_day.col + 1, f"{end_time}")
    print("Schedule updated successfully.")

if __name__ == "__main__":
    main()

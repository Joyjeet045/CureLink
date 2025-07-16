from datetime import datetime, timedelta

def print_current_datetime():
    now = datetime.now()+timedelta(hours=5)
    
    print(f"[Utils] Current datetime: {now}")

print_current_datetime()
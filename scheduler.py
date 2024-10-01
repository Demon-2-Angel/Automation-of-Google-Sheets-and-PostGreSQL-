import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from sync import sync_sheet_to_db, sync_db_to_sheet

scheduler = BackgroundScheduler()

# Sync Google Sheets to DB every 5 minutes
scheduler.add_job(func=sync_sheet_to_db, trigger="interval", minutes=1)

# Sync DB to Google Sheets every 5 minutes
scheduler.add_job(func=sync_db_to_sheet, trigger="interval", minutes=1)

scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

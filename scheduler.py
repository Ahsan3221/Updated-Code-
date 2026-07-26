from apscheduler.schedulers.background import BackgroundScheduler
import time

class TaskScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        print("[*] Scheduler Started. Waiting for tasks...")

    def add_auto_sync_job(self, function_to_run, interval_minutes=60):
        """Checks target channels every X minutes for new videos."""
        self.scheduler.add_job(
            function_to_run, 
            'interval', 
            minutes=interval_minutes, 
            id='auto_sync_job',
            replace_existing=True
        )
        print(f"[+] Auto-Sync Job added (Runs every {interval_minutes} minutes)")

    def add_upload_job(self, function_to_run, run_date_time):
        """Schedules a video upload at a specific exact time."""
        self.scheduler.add_job(
            function_to_run, 
            'date', 
            run_date=run_date_time
        )
        print(f"[+] Upload scheduled for: {run_date_time}")

    def stop(self):
        self.scheduler.shutdown()
        print("[-] Scheduler Stopped.")

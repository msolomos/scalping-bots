from crontab import CronTab

# Create a CronTab object for the current user
cron = CronTab(user=True)

# Search for an existing job with a specific comment
job_exists = False
for job in cron:
    if job.comment == 'My Python Job':
        # If the job exists, update the command or its settings
        job.setall('*/5 * * * *')  # Change the execution time
        job.command = 'python /path/to/your_script.py'
        job_exists = True
        break

# If it doesn't exist, create a new job
if not job_exists:
    job = cron.new(command='python /path/to/your_script.py', comment='My Python Job')
    job.minute.every(5)

# Save the changes to the crontab
cron.write()

print("The crontab was updated successfully.")


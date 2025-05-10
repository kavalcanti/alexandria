from datetime import datetime

def logger(string_to_log, log_file):
    truncate_log_file(log_file)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f'[{timestamp}] {string_to_log}\n'

    with open(log_file, 'a+') as file:
        file.write(log_entry)


def truncate_log_file(log_file, max_lines=5000, keep_lines=500):
    # Read all lines from the log file
    with open(log_file, 'r') as file:
        lines = file.readlines()

    if len(lines) > max_lines:
        new_content = lines[-keep_lines:]

        with open(log_file, 'w') as file:
            file.writelines(new_content)
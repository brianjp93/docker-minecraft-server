#!/usr/bin/env python3

import signal
import time
import os
import subprocess


START = time.time()


def send_discord_message(message):
    os.system(f'curl -X POST "$DISCORD_WEBHOOK_URL" --data \'{{"content": "{message}"}}\' -H "Content-Type:application/json"')


def handle_stop_signal(signum, frame):
    print("Received stop signal, running cleanup tasks...")

    end = time.time()
    elapsed = int(end - START)
    total_minutes = elapsed // 60
    seconds = elapsed % 60
    hours = total_minutes // 60
    minutes = total_minutes % 60

    send_discord_message(f"**Shutting Down** : Server was up for {hours}H {minutes}M {seconds}S.")

    print("Cleanup done, exiting.")
    exit(0)


def get_command_output(command: list[str]):
    return subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def do_mc_command(command: list[str]):
    return get_command_output(["mc-send-to-console"] + command)


def do_backup():
    do_mc_command(["save-off"])
    result = get_command_output(["restic",  "--verbose", "backup", "/data/world"])
    do_mc_command(["say", result.stdout])
    do_mc_command(["save-on"])


def do_backup_on_timer(timer=30):
    """timer is time in minutes."""
    last_save = 0
    while now := time.time():
        seconds = now - last_save
        minutes = seconds / 60
        if minutes >= timer:
            last_save = now
            do_backup()
        time.sleep(1)


def notify_on_server_ready():
    start = time.time()
    while True:
        try:
            result = subprocess.run(["mc-health"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            output = result.stdout
            code = result.returncode
            print(output)
            print(code)
        except subprocess.CalledProcessError:
            print('non-zero exit status')
            pass
        else:
            if code == 0:
                end = time.time()
                elapsed = end - start
                send_discord_message(f"**READY** : Took {int(elapsed)} seconds.")
                return
        time.sleep(5)


if __name__ == '__main__':
    send_discord_message("**STARTING** : Please wait while server spins up.")

    # Register the signal handler
    signal.signal(signal.SIGTERM, handle_stop_signal)
    signal.signal(signal.SIGINT, handle_stop_signal)
    notify_on_server_ready()
    do_backup_on_timer(timer=30)
    while True:
        time.sleep(1)

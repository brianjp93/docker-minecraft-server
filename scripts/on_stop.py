#!/usr/bin/env python3

import signal
import time
import os
import subprocess
import asyncio


START = time.time()
BACKUP_COMMAND = ["restic",  "--verbose", "backup", "/data/world"]


def send_discord_message(message):
    os.system(f'curl -X POST "$DISCORD_WEBHOOK_URL" --data \'{{"content": "{message}"}}\' -H "Content-Type:application/json"')


def handle_stop_signal():
    print("Received stop signal, running cleanup tasks...")

    do_mc_command(["save-off"])
    do_mc_command(["save-all"])

    print("Waiting for write.")
    # wait for write
    time.sleep(5)

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


async def do_backup():
    do_mc_command(["save-off"])
    # ensure writing finishes?
    await asyncio.sleep(5)
    result = get_command_output(BACKUP_COMMAND)
    do_mc_command(["save-on"])
    return result.returncode


async def do_backup_on_timer(delay=5, timer=30):
    """timer is time in minutes."""
    print('Starting backup loop.')
    await asyncio.sleep(delay * 60)
    last_save = 0
    while now := time.time():
        seconds = now - last_save
        minutes = seconds / 60
        if minutes >= timer:
            last_save = now
            code = await do_backup()
            if code == 0:
                do_mc_command(["say", f"Backup complete. Next backup in {timer} minutes"])
            else:
                do_mc_command(["say", "Backup may have failed."])
        await asyncio.sleep(1)


async def notify_on_server_ready():
    start = time.time()
    while True:
        try:
            result = get_command_output(["mc-health"])
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
        await asyncio.sleep(5)


async def main():
    send_discord_message("**STARTING** : Please wait while server spins up.")
    await notify_on_server_ready()
    asyncio.create_task(do_backup_on_timer(delay=5, timer=30))

    while True:
        await asyncio.sleep(1)


if __name__ == '__main__':
    # manual creation because of some dumb reason involving the signal handler being set in a different loop
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGTERM, handle_stop_signal)
    loop.add_signal_handler(signal.SIGINT, handle_stop_signal)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

    print("Finished async tasks.")
    exit(0)

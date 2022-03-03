import os
import sys
import time
import json
import logging
import telebot
import requests

from proxmoxer import ProxmoxAPI

logger = logging.getLogger(__name__)

from constants import GLOBAL_PROXMOX_HOST_1, GLOBAL_PROXMOX_USER, GLOBAL_PROXMOX_1_TOKEN_VALUE, \
    GLOBAL_PROXMOX_1_TOKEN_NAME, GLOBAL_OUTPUT_FILE, GLOBAL_PROXMOX_HOST_1_NODE, GLOBAL_OUTPUT_COUNT_FILE, \
    GLOBAL_PROXMOX_3_TOKEN_VALUE, GLOBAL_PROXMOX_3_TOKEN_NAME, GLOBAL_PROXMOX_HOST_3, GLOBAL_PROXMOX_HOST_3_NODE, \
    GLOBAL_PROXMOX_HOST_2_NODE, GLOBAL_PROXMOX_HOST_2, GLOBAL_PROXMOX_2_TOKEN_NAME, GLOBAL_PROXMOX_2_TOKEN_VALUE, \
    GLOBAL_TELEGRAM_TOKEN, GLOBAL_TELEGRAM_CHAT_ID

proxmox_host_1 = ProxmoxAPI(GLOBAL_PROXMOX_HOST_1, user=GLOBAL_PROXMOX_USER, password='', port=8006,
                            verify_ssl=False)
proxmox_host_2 = ProxmoxAPI(GLOBAL_PROXMOX_HOST_2, user=GLOBAL_PROXMOX_USER, password='', port=8006,
                            verify_ssl=False)
proxmox_host_3 = ProxmoxAPI(GLOBAL_PROXMOX_HOST_3, user=GLOBAL_PROXMOX_USER, password='', port=8006,
                            verify_ssl=False)


def write_to_file(line_list, home_path):
    path = '{}/{}'.format(home_path, GLOBAL_OUTPUT_FILE)
    with open(path, "r+") as fp:
        fp.seek(0)
        for line in line_list:
            fp.write(line + "\n")
        fp.truncate()
    time.sleep(0.5)
    fp.close()


def read_vm_file(home_path):
    path = '{}/resources/vmlist.txt'.format(home_path)
    with open(path, 'r') as fs:
        vm_list = []

        for line in fs:
            vm_list.append(line)

    time.sleep(0.5)
    fs.close()
    return vm_list


def get_vm_list():
    try:
        # Get list of VM from Bot Pool
        vm_list = []
        host_1_pool = proxmox_host_1.pools('Bot').get()
        host_1_json_dump = json.dumps(host_1_pool, indent=2)
        host_1_json_load = json.loads(host_1_json_dump)

        host_3_pool = proxmox_host_3.pools('Bot').get()
        host_3_json_dump = json.dumps(host_3_pool, indent=2)
        host_3_json_load = json.loads(host_3_json_dump)

        host_2_pool = proxmox_host_2.pools('Bot').get()
        host_2_json_dump = json.dumps(host_2_pool, indent=2)
        host_2_json_load = json.loads(host_2_json_dump)

        for vm in host_1_json_load['members']:
            # print(vm['vmid'], vm['status'], vm['name'])
            if vm['status'] == 'stopped':
                # line Host#:VMID:Name:TimeStamp
                host_1_line = '1:{}:{}:{}'.format(vm['vmid'], vm['name'], time.time())
                vm_list.append(host_1_line)
                # print('Yes')
            else:
                host_1_line = '1:{}:{}:0.0'.format(vm['vmid'], vm['name'])
                vm_list.append(host_1_line)
                # print('No')

        for vm in host_3_json_load['members']:
            # print(vm['vmid'], vm['status'], vm['name'])
            if vm['status'] == 'stopped':
                # line Host#:VMID:Name:TimeStamp
                host_3_line = '3:{}:{}:{}'.format(vm['vmid'], vm['name'], time.time())
                vm_list.append(host_3_line)
                # print('Yes')
            else:
                host_3_line = '3:{}:{}:0.0'.format(vm['vmid'], vm['name'])
                vm_list.append(host_3_line)
                # print('No')

        for vm in host_2_json_load['members']:
            # print(vm['vmid'], vm['status'], vm['name'])
            if vm['status'] == 'stopped':
                # line Host#:VMID:Name:TimeStamp
                host_2_line = '2:{}:{}:{}'.format(vm['vmid'], vm['name'], time.time())
                vm_list.append(host_2_line)
                # print('Yes')
            else:
                host_2_line = '2:{}:{}:0.0'.format(vm['vmid'], vm['name'])
                vm_list.append(host_2_line)
                # print('No')

        return vm_list

    except Exception as e:
        print("Can't get VM list from API with error: ", e)


def get_vm_to_shutdown():
    try:
        bot = telebot.TeleBot(token=GLOBAL_TELEGRAM_TOKEN)
        home_path = get_correct_path()
        shutdown_list = []
        delete_list = []
        vm_list = read_vm_file(home_path)
        for line in vm_list:
            s_line = line.split(':', 5)
            if s_line[2] != 'VMNAME':
                if 7500.0 < float(s_line[4]) < 7800.0:
                    shutdown_list.append(line)
                elif float(s_line[4]) > 7800.0:
                    if s_line[2] != 'Debian-AppAccount' and s_line[2] != 'Debian-AppAccount2':
                        delete_list.append(line)

        for line in shutdown_list:
            s_line = line.split(':', 4)
            # Check if vm is shutdown
            if float(s_line[3]) != 0.0:
                if s_line[0] == '1':
                    try:
                        proxmox_host_1.nodes(GLOBAL_PROXMOX_HOST_1_NODE).qemu(s_line[1]).status().shutdown().post()
                        logger.info('Host RL20 - Shutting Down VM# %s', s_line[1])
                    except Exception as e:
                        print("Shutdown POST Request error: ", e)

                elif s_line[0] == '3':
                    try:
                        proxmox_host_3.nodes(GLOBAL_PROXMOX_HOST_3_NODE).qemu(s_line[1]).status().shutdown().post()
                        logger.info('Host B106 - Shutting Down VM# %s', s_line[1])
                    except Exception as e:
                        print("Shutdown POST Request error: ", e)

                elif s_line[0] == '2':
                    try:
                        proxmox_host_2.nodes(GLOBAL_PROXMOX_HOST_2_NODE).qemu(s_line[1]).status().shutdown().post()
                        logger.info('Host Debian66 - Shutting Down VM# %s', s_line[1])
                    except Exception as e:
                        print("Shutdown POST Request error: ", e)

        for line in delete_list:
            s_line = line.split(':', 4)
            # Check if vm is shutdown
            if float(s_line[3]) != 0.0:
                if s_line[0] == '1':
                    try:
                        proxmox_host_1.nodes(GLOBAL_PROXMOX_HOST_1_NODE).qemu(s_line[1]).status().stop().post(
                            skiplock=1)
                        logger.info('Host RL20 - Deleting VM# %s', s_line[1])
                        time.sleep(15)
                        proxmox_host_1.nodes(GLOBAL_PROXMOX_HOST_1_NODE).qemu(s_line[1]).delete(purge=1, skiplock=1)
                        message = f'Host RL20 - Deleting VM# {s_line[1]} - Please Re-Create this VM'
                        bot.send_message(GLOBAL_TELEGRAM_CHAT_ID, message)
                    except Exception as e:
                        print("Delete Request error: ", e)

                elif s_line[0] == '3':
                    try:
                        proxmox_host_3.nodes(GLOBAL_PROXMOX_HOST_3_NODE).qemu(s_line[1]).status().stop().post(
                            skiplock=1)
                        logger.info('Host B106 - Deleting VM# %s', s_line[1])
                        time.sleep(15)
                        proxmox_host_3.nodes(GLOBAL_PROXMOX_HOST_3_NODE).qemu(s_line[1]).delete(purge=1, skiplock=1)
                        message = f'Host B106 - Deleting VM# {s_line[1]} - Please Re-Create this VM'
                        bot.send_message(GLOBAL_TELEGRAM_CHAT_ID, message)
                    except Exception as e:
                        print("Delete Request error: ", e)

                elif s_line[0] == '2':
                    try:
                        proxmox_host_2.nodes(GLOBAL_PROXMOX_HOST_2_NODE).qemu(s_line[1]).status().stop().post(
                            skiplock=1)
                        logger.info('Host Debian66 - Deleting VM# %s', s_line[1])
                        time.sleep(15)
                        proxmox_host_2.nodes(GLOBAL_PROXMOX_HOST_2_NODE).qemu(s_line[1]).delete(purge=1, skiplock=1)
                        message = f'Host Debian66 - Deleting VM# {s_line[1]} - Please Re-Create this VM'
                        bot.send_message(GLOBAL_TELEGRAM_CHAT_ID, message)
                    except Exception as e:
                        print("Delete Request error: ", e)

    except Exception as e:
        print('Cant get vm list and shutdown vms with error: {}', e)


def update_file(vm_list):
    home_path = get_correct_path()
    path = '{}/{}'.format(home_path, GLOBAL_OUTPUT_FILE)
    count = 0
    vm_list_old = []
    vm_list_file = []
    if os.path.exists(path):
        try:
            with open(path, 'r') as fp:
                for line in fp:
                    count += 1
                    vm_list_old.append(line)
            time.sleep(0.5)
            fp.close()
        except Exception as e:
            print('Cant read file with error: {}', e)
    else:
        for line in vm_list:
            s_line = line.split(':', 4)
            new_line = '{}:{}:{}:{}:0.0'.format(s_line[0], s_line[1], s_line[2], s_line[3])
            vm_list_file.append(new_line)

    if len(vm_list_old) > 1:
        now = time.time()
        for line2 in vm_list:
            in_old_list = False
            s_line2 = line2.split(':', 4)
            for line in vm_list_old:
                s_line_old_list = line.split(':', 5)
                # Check VM Name
                if s_line_old_list[2] in line2:
                    if float(s_line2[3]) != 0.0:
                        uptime = float(s_line_old_list[3]) - float(s_line2[3])
                        # New line Host#:VMID:Name:TimeStamp:Up_Time
                        new_line = '{}:{}:{}:{}:{}'.format(s_line2[0], s_line2[1], s_line2[2], s_line2[3], uptime)
                        vm_list_file.append(new_line)
                        vm_list_old.remove(line)
                        # print("write ", s_line2[2])
                        in_old_list = True
                        break
                    else:
                        uptime = now - float(s_line_old_list[3])
                        # New line Host#:VMID:Name:TimeStamp:Up_Time
                        new_line = '{}:{}:{}:{}:{}'.format(s_line2[0], s_line2[1], s_line2[2], s_line_old_list[3],
                                                           uptime)
                        vm_list_file.append(new_line)
                        vm_list_old.remove(line)
                        # print("write ", s_line2[2])
                        in_old_list = True
                        break

            if not in_old_list:
                # New line Host#:VMID:Name:TimeStamp:Up_Time
                # print("write ", s_line2[2])
                new_line = '{}:{}:{}:{}:0.0'.format(s_line2[0], s_line2[1], s_line2[2], s_line2[3])
                vm_list_file.append(new_line)

    else:
        for line in vm_list:
            s_line = line.split(':', 4)
            new_line = '{}:{}:{}:{}:0.0'.format(s_line[0], s_line[1], s_line[2], s_line[3])
            vm_list_file.append(new_line)

    # Write to file
    try:
        write_to_file(vm_list_file, home_path)
    except Exception as e:
        print("Can't write to file with error: ", e)

    vm_list_old.clear()
    vm_list_file.clear()


def update_mac(vm_line):
    s_line = vm_line.split(':', 4)
    # Check if vm is shutdown
    if float(s_line[3]) != 0.0:
        if s_line[0] == '1':
            try:
                proxmox_host_1.nodes(GLOBAL_PROXMOX_HOST_1_NODE).qemu(s_line[1]).config().post(
                    net0='virtio,bridge=vmbr1')
                time.sleep(1)
                proxmox_host_1.nodes(GLOBAL_PROXMOX_HOST_1_NODE).qemu(s_line[1]).status().start().post()
                logger.info('Host RL20 - Updated MAC VM# %s', s_line[1])
            except Exception as e:
                print("POST Request error: ", e)

        elif s_line[0] == '3':
            try:
                proxmox_host_3.nodes(GLOBAL_PROXMOX_HOST_3_NODE).qemu(s_line[1]).config().post(
                    net0='virtio,bridge=vmbr0')
                time.sleep(1)
                proxmox_host_3.nodes(GLOBAL_PROXMOX_HOST_3_NODE).qemu(s_line[1]).status().start().post()
                logger.info('Host B106 - Updated MAC VM# %s', s_line[1])
            except Exception as e:
                print("POST Request error: ", e)

        elif s_line[0] == '2':
            try:
                proxmox_host_2.nodes(GLOBAL_PROXMOX_HOST_2_NODE).qemu(s_line[1]).config().post(
                    net0='virtio,bridge=vmbr0')
                time.sleep(1)
                proxmox_host_2.nodes(GLOBAL_PROXMOX_HOST_2_NODE).qemu(s_line[1]).status().start().post()
                logger.info('Host Debian66 - Updated MAC VM# %s', s_line[1])
            except Exception as e:
                print("POST Request error: ", e)


def get_correct_path():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
        return application_path
    elif __file__:
        application_path = os.path.dirname(__file__)
        return application_path
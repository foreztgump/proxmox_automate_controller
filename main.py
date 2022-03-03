import time
import logging

from queue import Queue
from threading import Thread

import telebot

from apicontrol import update_mac, get_vm_list, update_file, get_vm_to_shutdown
from constants import GLOBAL_TELEGRAM_TOKEN, GLOBAL_TELEGRAM_CHAT_ID

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)


class UpdateWorker(Thread):

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            # Get the work from the queue and expand the tuple
            vm_line = self.queue.get()
            try:
                update_mac(vm_line)
            finally:
                self.queue.task_done()


def run():
    vm_list = get_vm_list()
    if vm_list is not None:
        update_file(vm_list)
        get_vm_to_shutdown()
        # Create a queue to communicate with the worker threads
        queue = Queue()
        # Create 3 worker threads
        for x in range(3):
            worker = UpdateWorker(queue)
            # Setting daemon to True will let the main thread exit even though the workers are blocking
            worker.daemon = True
            worker.start()

        # Put the tasks into the queue as a tuple
        for vm_line in vm_list:
            logger.info('Queueing {}'.format(vm_line))
            queue.put(vm_line)

        # Causes the main thread to wait for the queue to finish processing all the tasks
        queue.join()
        vm_list.clear()
    else:
        logger.info('Exception Occurred.')


if __name__ == '__main__':
    bot = telebot.TeleBot(token=GLOBAL_TELEGRAM_TOKEN)
    bot.send_message(GLOBAL_TELEGRAM_CHAT_ID, 'Proxmox Controller Started')
    while True:
        logger.info('Started')
        run()
        logger.info('Sleep')
        time.sleep(25)


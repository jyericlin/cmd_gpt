# Copyright (c) 2023 Jieyu Lin
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import re
from enum import IntEnum

import iterm2
from loguru import logger
from pydantic import BaseModel


def remove_excessive_whitespace(s):
    return re.sub(r'\s+', ' ', s.strip())

class iTerm2MessageType(IntEnum):
    RUN = 1
    READ = 2
    NEW_TAB = 3
    END = 4

class iTerm2Message(BaseModel):
    type: iTerm2MessageType
    text: str
    

class iTerm2Interaction:
    def __init__(self, queue=None, read_max_length=10):
        self.initialized = False
        self.connection = iterm2.Connection()
        if queue is None:
            self.queue = asyncio.Queue()
        else:
            self.queue = queue
        self.last_output = None
        self.read_max_length = read_max_length
        # iterm2.run_until_complete(self._initialize)

    def run(self, loop, retry=True):
        """
        -- from iTerm2 API code 
        Convenience method to start a program.

        Connects to the API endpoint, begins an asyncio event loop, and runs
        the passed in coroutine. Exceptions will be caught and printed to
        stdout.

        :param retry: Keep trying to connect until it succeeds?
        """
        async def async_main(connection):
            # Set __tasks here in case coro returns before
            # _async_dispatch_forever starts.
            self.__tasks = []
            dispatch_forever_task = asyncio.ensure_future(
                self.connection._async_dispatch_forever(connection, loop))
            result = await self.listen()
            dispatch_forever_task.cancel()
            # Make sure the _async_dispatch_to_helper task gets canceled to
            # avoid a warning.
            for task in self.__tasks:
                task.cancel()
            return result

        self.loop = loop
        return self.connection.async_connect(async_main, retry)

    async def initialize(self):
        # Get the current app and session
        app = await iterm2.async_get_app(self.connection)
        self.window = app.current_terminal_window
        if self.window is not None:
            await self.window.async_create_tab() # create a new tab to work on
            self.session = self.window.current_tab.current_session
        else:
            logger.error("No open window. Exiting.")
            self.session = None

    
    async def _async_run_command(self, command):
        
        if self.session:
            await self.session.async_send_text(command + '\n')
        else:
            logger.error("Session is not available.")

    async def _async_read_output(self):
        if self.session:
            return await self.session.async_get_screen_contents()
        else:
            logger.error("Session is not available.")
            return None
    
    async def _async_create_new_tab(self):
        if self.window is not None:
            await self.window.async_create_tab()
            self.session = self.window.current_tab.current_session
        else:
            logger.error("No open window. Exiting.")

    async def _async_send_message(self, message: iTerm2Message):
        await self.queue.put(message)

    def send_message(self, message: iTerm2Message):
        asyncio.run_coroutine_threadsafe(self._async_send_message(message), self.loop)

    def _wait_for_initialization(self):
        count = 0
        MAX_WAIT = 5
        while not self.initialized:
            time.sleep(1)
            count += 1
            if count >= MAX_WAIT:
                logger.error("Waited for too long. Exiting.")
                return False
        return True

    def run_command(self, command):
        self.send_message(iTerm2Message(type=iTerm2MessageType.RUN, text=command))

    def run_command_and_get_reply(self, command):
        self.run_command(command)
        time.sleep(2)
        output = self.read_output(length=self.read_max_length)
        return output


    # check if the input line is a command prompt
    def line_is_cmd_prompt(self, line):
        if re.match(r"^[^@]*@[^$@]*\$", line.strip()): #bash
            return True
        elif re.match(r"^[^@]*@[^$@]*\%", line.strip()): #zsh
            return True
        else:
            return False

    def line_is_cmd_prompt_or_question(self, line):
        if re.match(r"^[^@]*@[^$@]*\$$", line.strip()): # empty bash prompt
            return True
        elif re.match(r"^[^@]*@[^$@]*\%$", line.strip()): #empty zsh prompt
            return True
        elif re.match(r"^[^?]*? [Y/n]$", line.strip()): # for apt-get
            return True
        elif re.match(r"^Password:", line.strip()): #sudo
            return True
        elif re.match(r"[sudo] password for .*:", line.strip()): #sudo
            return True
        elif re.match(r".* password:", line.strip()): # SSH password
            return True
        else:
            return False
    
    def is_command_line_output_the_same(self, output1, output2):
        if output1.number_of_lines != output2.number_of_lines:
            return False
        
        for i in range(output1.number_of_lines):
            if output1.line(i).string != output2.line(i).string:
                return False
            
        return True

    def get_from_last_prompt(self):
        
        future = asyncio.run_coroutine_threadsafe(self._async_read_output(), self.loop)
        result_1 = future.result()
        time.sleep(1)

        while True: # make sure no change in the output 
            future = asyncio.run_coroutine_threadsafe(self._async_read_output(), self.loop)
            result_2 = future.result()

            if not self.is_command_line_output_the_same(result_1, result_2):
                logger.trace("command line still changing, waiting for 3 seconds")
                time.sleep(3)
                result_1 = result_2
                continue

            text_list = []
            prompt_count = 0
            logger.trace("number of lines: ", result_2.number_of_lines)
            for i in range(result_2.number_of_lines-1, -1, -1):
                if remove_excessive_whitespace(result_2.line(i).string) in ["", " ", "\n", "\t"]:
                    continue
                if result_2.line(i).string.strip() != "":
                    if self.line_is_cmd_prompt(result_2.line(i).string):
                        prompt_count += 1
                        if prompt_count == 2:
                            break
                    logger.trace("appending: ", result_2.line(i).string)
                    text_list.append(result_2.line(i).string)

            last_line = text_list[0]

            logger.trace("checking last line is prompt: ", last_line)
            if not self.line_is_cmd_prompt_or_question(last_line):
                logger.trace("last line is not a command prompt, waiting for 3 seconds")
                time.sleep(3)
                result_1 = result_2
                continue

            
            out = list(reversed(text_list))
            return out
            


    def read_output(self, length=0, store_history=False):
        length = int(length)

        success = self._wait_for_initialization()
        if not success:
            return None
        
        try:
            text_list = self.get_from_last_prompt()
        except iterm2.rpc.RPCException:
            logger.debug("RPCException. Exiting.")
            return "E: exit"


        if store_history:
            self.last_output = text_list

        if length > 0 and len(text_list) > length:
            text_list = [f"...({len(text_list) - length} line omited)"] + text_list[-length:]
        
        if len(text_list) > 1:
            for i, r in enumerate(text_list):
                text_list[i] = "\t" + r

        ret = "\n" + "\n".join(text_list)

        return ret

    async def listen(self) -> None:
        await self.initialize()
        self.initialized = True
        while True:
            message = await self.queue.get()
            if type(message) != iTerm2Message:
                logger.error(" tyMessagepe is not iTerm2Message. Exiting.")
                return
            if message.type == iTerm2MessageType.RUN:
                await self._async_run_command(message.text)
            elif message.type == iTerm2MessageType.READ:
                await self._async_read_output(message.text)
            elif message.type == iTerm2MessageType.NEW_TAB:
                await self._async_create_new_tab()
            elif message.type == iTerm2MessageType.END:
                return
    
    def close(self) -> None:
        self.send_message(iTerm2Message(type=iTerm2MessageType.END, text=""))


import threading
import time


# TODO: this doesn't work in jupyter notebook, need to get iterm2 to run in a new event loop
def setup_iterm2_tool(**kwargs):
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()
    term = iTerm2Interaction(queue, **kwargs)

    def start_loop(term, loop):
        loop.run_until_complete(term.run(loop))

    t = threading.Thread(target=start_loop, args=(term, loop))
    t.start()

    return term
from ast import Not
from operator import not_
import os
from unittest import result
import pymem
import struct
import re
import psutil
import subprocess
import time


class MemoryInterface:
    def __init__(self, exe_path, client, process_name="FTLGame.exe"):
        self.client = client
        self.exe_path = exe_path
        self.log_path = os.path.normpath(os.path.join(os.path.dirname(self.exe_path), "FTL_HS.log"))

        self.pm = self.launch_and_wait_for_process(process_name, exe_path)

        while not os.path.exists(self.log_path):
            time.sleep(0.1)  # Wait for the log file to be created

        with open(self.log_path, "r") as log_file:
            log_contents = log_file.read()

        clientToMod_match = re.search(r"clientToMod Vector - <userdata of type 'std::vector< int > \*' at ([0-9a-fA-F]+)>", log_contents)
        modToClient_match = re.search(r"modToClient Vector - <userdata of type 'std::vector< int > \*' at ([0-9a-fA-F]+)>", log_contents)
 
        while not clientToMod_match or not modToClient_match:
            with open(self.log_path, "r") as log_file:
                log_contents = log_file.read()
            clientToMod_match = re.search(r"clientToMod Vector - <userdata of type 'std::vector< int > \*' at ([0-9a-fA-F]+)>", log_contents)
            modToClient_match = re.search(r"modToClient Vector - <userdata of type 'std::vector< int > \*' at ([0-9a-fA-F]+)>", log_contents)
            time.sleep(0.1)  # Wait for the log file to be updated

        if clientToMod_match and modToClient_match:
            self.clientToMod_address = int(clientToMod_match.group(1), 16)
            self.modToClient_address = int(modToClient_match.group(1), 16)
            self.client.log(f"clientToMod address: {(self.clientToMod_address)}")
            self.client.log(f"modToClient address: {(self.modToClient_address)}")
        else:
            self.client.log("Failed to find one or both vector addresses.")

        # initialize variables
        self.vector_size = 4096
        self.vector_metadata_size = 2 # last written index of that vector, last read index for the opposing vector
        self.message_metadata_size = 2 # index of the message, length of the message body

        self.clientToMod_freeSpace = self.vector_size - self.vector_metadata_size
        self.clientToMod_queue = []
        self.clientToMod_writeIndex = -1

        self.modToClient_readIndex = -1

    # Public functions
    def check_messages(self):
        messages = self.split_messages(self.modToClient_address)

        new_messages = []

        for message_id, message_body in messages:
            if message_id > self.modToClient_readIndex:
                message = self.decode(message_body)
                new_messages.append((message_id, message))

                # update metadata
                self.modToClient_readIndex = message_id
                self.update_read_index()

        return new_messages

    def send_message(self, message: str):
        if self.append_message(message):
            self.client.log(f"Sent message: {message}")
        else:
            self.client.log(f"Message queued: {message}")

    # Internal Functions
    def encode(self, string: str) -> list[int]:
        ints = []
        for char in string:
            ints.append(ord(char))
        return ints

    def decode(self, ints: list[int]) -> str:
        chars = []
        for number in ints:
            if 0 < number <= 127:  # Only allow valid ASCII excluding nulls
                chars.append(chr(number))
            else: 
                break
        return ''.join(chars)

    def clear_messages(self):
        for i in range(self.vector_metadata_size, self.vector_size):
            self.write_int(self.clientToMod_address, i, 0)

    def generate_message(self, message: str) -> list[int]:
        encoded = self.encode(message)
        result = [self.clientToMod_writeIndex, len(encoded)]
        result.extend(encoded)

        return result

    def append_message(self, message: str):
        if len(message) + self.message_metadata_size > self.clientToMod_freeSpace:
            self.clientToMod_queue.append(message)
            self.client.log(f"Not enough space to send message: {message}. Message queued.")
            return False

        self.clientToMod_writeIndex += 1 # increment message index

        message_data = self.generate_message(message)

        start_index = self.vector_size - self.clientToMod_freeSpace

        for i in range(len(message_data)):
            self.write_int(self.clientToMod_address, start_index + i, message_data[i])

        self.clientToMod_freeSpace -= len(message_data)

        self.update_write_index() # update metadata in memory

        return True

    def split_messages(self, vector_address: int) -> list[(int, str)]:
        messages = []
        vector_data = self.read_vector(vector_address)
        i = self.vector_metadata_size # Start after metadata
        while i < self.vector_size:
            message_id = vector_data[i]
            message_length = vector_data[i + 1]
            if message_length <= 0 or message_id < 0:
                break

            message_body = vector_data[i + 2 : i + 2 + message_length]

            messages.append((message_id, message_body))

            i += 2 + message_length  # Move to the next message
        return messages

    def update_read_index(self):
        self.write_int(self.clientToMod_address, 1, self.modToClient_readIndex)

    def update_write_index(self):
        self.write_int(self.clientToMod_address, 0, self.clientToMod_writeIndex)

    # Internal Helper Functions
    def read_int(self, vector_address: int, index: int) -> int:
        data_ptr = self.get_data_pointer(vector_address)
        address = data_ptr + index * 4
        data = self.pm.read_bytes(address, 4)
        value = struct.unpack("<i", data)[0]
        return value
    def write_int(self, vector_address: int, index: int, value: int):
        data_ptr = self.get_data_pointer(vector_address)
        address = data_ptr + index * 4
        packed = struct.pack("<i", value)
        self.pm.write_bytes(address, packed, len(packed))

    def read_vector(self, address: int, length: int=4096) -> list[int]:
        data_ptr = self.get_data_pointer(address)
        data_bytes = self.pm.read_bytes(data_ptr, length * 4)
        return struct.unpack(f"<{length}i", data_bytes)
    

    # Helper to get the data pointer from a std::vector structure
    def get_data_pointer(self, address: int) -> int:
        data_ptr_bytes = self.pm.read_bytes(address, 4)
        data_ptr = struct.unpack("<i", data_ptr_bytes)[0]
        return data_ptr
    
    # Launches the process if not running, and waits for it to be available for pymem
    def launch_and_wait_for_process(self, process_name, exe_path, timeout=10) -> pymem.Pymem:
        try:
            return pymem.Pymem(process_name)
        except pymem.exception.ProcessNotFound:
            subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))

            # delete the log file if it exists to ensure we read fresh data
            if os.path.exists(self.log_path): 
                os.remove(self.log_path)
    
            start = time.time()
            while time.time() - start < timeout:
                try:
                    return pymem.Pymem(process_name)
                except pymem.exception.ProcessNotFound:
                    time.sleep(0.2)  # Small delay to let it start
            raise TimeoutError(f"{process_name} did not start in time.")

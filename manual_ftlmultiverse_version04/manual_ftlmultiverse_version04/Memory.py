from ast import Not
from operator import not_
import os
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
        self.last_message = None

    # Public functions
    def check_message(self) -> str:
        message = self.read_vector(self.modToClient_address)

        if self.last_message == None or self.last_message != message:
            self.last_message = message
            return message
        else: 
            return None


    def send_message(self, message: str):
        self.clear_vector(self.clientToMod_address)

        self.write_vector(self.clientToMod_address, self.encode(message))

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

    def get_data_pointer(self, address: int) -> int:
        data_ptr_bytes = self.pm.read_bytes(address, 4)
        data_ptr = struct.unpack("<i", data_ptr_bytes)[0]
        return data_ptr

    def read_vector(self, address: int, length: int=1024) -> str:
        data_ptr = self.get_data_pointer(address)
        data_bytes = self.pm.read_bytes(data_ptr, length * 4)
        string = self.decode(struct.unpack(f"<{length}i", data_bytes))
        return string

    def write_vector(self, address: int, values: list[int]):
        data_ptr = self.get_data_pointer(address)
        packed = struct.pack(f"<{len(values)}i", *values)
        self.pm.write_bytes(data_ptr, packed, len(packed))

    def clear_vector(self, address, length=1024):
        self.write_vector(address, [0] * length)

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

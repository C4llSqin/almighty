import asyncio
import socket
from os import path, listdir
from hashlib import sha1
from formLogic import Form, export, strip_form, hash_form, combine_form
from functools import wraps
import io
import json
import random

def log_brackets(text: str, bracket_text: list[str]):
    print(" ".join([f"[{bracket}]" for bracket in bracket_text]) + text)

def cheat_print(text: str, add_brackets: list[str], output: bool):
    if output: log_brackets(text, ["cheatsheet"] + add_brackets)

##
# Basic socket networking
##

max_file_size = 0xFFFF

def sync_wrap(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))
    
    return wrapper

async def async_recv(handle: socket.socket) -> bytes:
    loop = asyncio.get_event_loop()
    length = await loop.sock_recv(handle, 2)
    length = int.from_bytes(length, 'little', signed=False)
    buffer = b""
    while len(buffer) < length:
        data_part = await loop.sock_recv(handle, length - len(buffer))
        if data_part == b"": raise IOError
        buffer += data_part
    
    return buffer

def sync_recv(handle: socket.socket) -> bytes:
    length = int.from_bytes(handle.recv(2), 'little', signed=False)
    buffer = b""
    while len(buffer) < length:
        data_part = handle.recv(length - len(buffer))
        if data_part == b"": raise IOError
        buffer += data_part
    
    return buffer

async def async_send(handle: socket.socket, data: bytes):
    loop = asyncio.get_event_loop()
    length = len(data).to_bytes(2, 'little', signed=False)
    await loop.sock_sendall(handle, length + data)

def sync_send(handle: socket.socket, data: bytes):
    length = len(data).to_bytes(2, 'little', signed=False)
    handle.sendall(length + data)

##
# File IO.
##

def read_file(fp: str):
    with open(fp, 'rb') as f: return f.read()

def write_file(fp: str, data: bytes):
    with open(fp, 'wb') as f: f.write(data)


##
# Server logic
##

def validate(form_hash: bytes, form_data: bytes) -> tuple[bytes, Form | None]:
    #TODO
    try:
        form_file = io.BytesIO(form_data)
        res_form = Form.from_file(form_file)
        if hash_form(res_form).encode() != form_hash:
            return b"", None
        strip_form(res_form, "scored")
        form_file = io.BytesIO(b"")
        res_form.export(form_file)
        form_file.seek(0)
        return form_file.read(), res_form
    except: return b"", None

def merge_forms(directory: str, form_hash: str, new_form: Form):
    form_file = io.BytesIO(read_file(f"{directory}{form_hash}.form"))
    current_form = Form.from_file(form_file)
    combine_form(current_form, new_form)
    return current_form

def list_hashes(dir_path: str):
    return [fname.removesuffix(".form") for fname in listdir(dir_path)]

class cheatsheet_server():
    def __init__(self, host: socket.socket, name: str, directory: str, output: bool = True) -> None:
        host.setblocking(False)
        self.host = host
        self.name = name
        self.directory = directory
        self.tasks: dict[int, asyncio.Task] = {}
        self.output = output

    async def handle_client(self, handle: socket.socket, addr, num_id: int):
        hex_id = hex(num_id)[2:]
        cheat_print(f"New Connection {addr}", ["server", self.name, hex_id], self.output)
        try:
            while True:
                instruction = await async_recv(handle)
                if instruction == b"":
                    raise IOError("Connection Lost")
                if instruction == b"RETRIVE":
                    form_hash = await async_recv(handle)
                    form_hash = form_hash.decode()
                    fp = f"{self.directory}{form_hash}.form"
                    if path.exists(fp):
                        cheat_print(f"Client requested {form_hash}, which exists", ["server", self.name, hex_id, "RETRIVE"], self.output)
                        data = await asyncio.to_thread(read_file, fp)
                        filehash = sha1(data).hexdigest()
                        await async_send(handle, filehash.encode())
                        recv_instruction = await async_recv(handle)
                        if recv_instruction == b"SEND":
                            cheat_print(f"Client wants to proceed with {form_hash}... sending", ["server", self.name, hex_id, "RETRIVE"], self.output)
                            await async_send(handle, data)
                        else:
                            cheat_print(f"Client aborted with {form_hash}", ["server", self.name, hex_id, "RETRIVE"], self.output)
                            await async_send(handle, b"ABORTED")
                    
                    else:
                        cheat_print(f"Client requested {form_hash}, which doesn't exist", ["server", self.name, hex_id, "RETRIVE"], self.output)
                        await async_send(handle, b"NOTFOUND")
                
                elif instruction == b"STORE":
                    form_hash = await async_recv(handle)
                    fp = f"{self.directory}{form_hash.decode()}.form"
                    if path.exists(fp):
                        cheat_print(f"Client wants to send {form_hash} but it exists... asking for its hash.", ["server", self.name, hex_id, "STORE"], self.output)
                        await async_send(handle, b"HASH")
                        sender_hash = await async_recv(handle)
                        data = await asyncio.to_thread(read_file, fp)
                        file_hash = sha1(data).hexdigest().encode()
                        if sender_hash == file_hash:
                            cheat_print("Client wanted to send an identical file", ["server", self.name, hex_id, "STORE"], self.output)
                            await async_send(handle, b"IDENTICAL")
                        else:
                            cheat_print("Client sent unique hash... proceeding with file sending", ["server", self.name, hex_id, "STORE"], self.output)
                            await async_send(handle, b"SEND")
                            data = await async_recv(handle)
                            if sha1(data).hexdigest().encode() != sender_hash:
                                cheat_print("Client sent hash that doesn't repesent the data", ["server", self.name, hex_id, "STORE"], self.output)
                                await async_send(handle, b"HASHFAIL")
                            else:
                                vaild_data, valid_form = validate(form_hash, data)
                                if vaild_data[0]:
                                    cheat_print("Client sent valid form... merging", ["server", self.name, hex_id, "STORE"], self.output)
                                    assert valid_form != None
                                    form = await asyncio.to_thread(merge_forms, *(self.directory, form_hash.decode(), valid_form))
                                    form_file = io.BytesIO(b"")
                                    form.export(form_file)
                                    form_file.seek(0)
                                    vaild_data = form_file.read()
                                    await async_send(handle, b"GOOD")
                                    await asyncio.to_thread(write_file, fp, vaild_data)
                                else: 
                                    cheat_print("Client sent invalid form data", ["server", self.name, hex_id, "STORE"], self.output)
                                    await async_send(handle, b"INVALID")

                    else:
                        await async_send(handle, b"SEND")
                        data = await async_recv(handle)
                        vaild_data, form = validate(form_hash, data)
                        if vaild_data:
                            cheat_print("Client sent valid form...", ["server", self.name, hex_id, "STORE"], self.output)
                            await async_send(handle, b"GOOD")
                            await asyncio.to_thread(write_file, fp, vaild_data)
                        else: 
                            cheat_print("Client sent invalid form data", ["server", self.name, hex_id, "STORE"], self.output)
                            await async_send(handle, b"INVALID")

                elif instruction == b"LIST":
                    await async_send(handle, "#".join(list_hashes(self.directory)).encode())

                else:
                    cheat_print("Client sent invalid command form...", ["server", self.name, hex_id, "STORE"], self.output)

                    await async_send(handle, b"INVALID")
        


        except Exception as e:
            cheat_print(f"Dropping client: {e}", ["server", self.name, hex_id], self.output)
            handle.close()
            del self.tasks[num_id]

    async def run(self):
        loop = asyncio.get_event_loop()
        while True:
            handle, addr = await loop.sock_accept(self.host)
            handle.setblocking(False)
            handle_id = random.randint(0, max_file_size)
            task = asyncio.create_task(self.handle_client(handle, addr, handle_id))
            while handle_id in self.tasks: task = asyncio.create_task(self.handle_client(handle, addr, handle_id))
            # task.add_done_callback(asyncio.create_task(self.remove_from_tasks(task)))
            self.tasks[handle_id] = task


async def _aquire_form(form_hash: str, handle: socket.socket, cur_hash: bytes = b"") -> Form | None:
    try:
        await async_send(handle, b"RETRIVE")
        await async_send(handle, form_hash.encode())
        response = await async_recv(handle)
        if response == b"NOTFOUND": 
            return None
        if cur_hash == response: 
            await async_send(handle, b"ABORT")
            return None
        await async_send(handle, b"SEND")
        data = await async_recv(handle)
        assert sha1(data).hexdigest().encode() == response # did they actually give the corect file hash?
        form_file = io.BytesIO(data)
        form = Form.from_file(form_file)
        assert hash_form(form) == form_hash # did they actually send what I asked for?
        return form
    except: return None

async def _send_form(form: Form, handle: socket.socket) -> bytes:
    form_hash = hash_form(form).encode()
    form_file = io.BytesIO(b"")
    form.export(form_file)
    form_file.seek(0)
    form_data = form_file.read()
    try:
        await async_send(handle, b"STORE")
        await async_send(handle, form_hash)
        instruction = await async_recv(handle)
        if instruction == b"HASH":
            form_data_hash = sha1(form_data).hexdigest().encode()
            await async_send(handle, form_data_hash)
            instruction = await async_recv(handle)
            if instruction == b"IDENTICAL":
                return instruction
        await async_send(handle, form_data)
        status = await async_recv(handle)
        return status
    except: return b"NET-FAILURE"

async def init_provider(provider: dict[str, str | int], output: bool = True, connect = True) -> socket.socket:
    loop = asyncio.get_event_loop()
    if provider["mode"] == "ipv4": 
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    elif provider["mode"] == "ipv6": 
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    elif provider["mode"] == "blue": 
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    else:
        if output: print(f"Invalid provider {provider['name']}")
        raise ValueError
    sock.setblocking(False)
    if connect: await loop.sock_connect(sock, (provider["addr"], provider["port"]))
    else: #bind and listen
        sock.bind((provider["addr"], provider["port"]))
        sock.listen()
    return sock

##
# User Functions
##

async def request_form(form_hash: str, provider: dict[str, str | int], output=True) -> Form | None:
    if output:
        print(f"[cheatsheet] trying to request form from `{provider['name']}`")
        print("[cheatsheet] initalizing connection... ", end="")

    try:
        sock = await init_provider(provider, True)
        if output: print("Connected\n[cheatsheet] requesting form...", end="")
        form = await _aquire_form(form_hash, sock)
        if output and form != None:
            print("Form Aquried")
        elif output and form == None:
            print("Form Not Found")
        sock.close()
        return form
        
    except: 
        if output: print("Failure.")
        return None

sync_request_form = sync_wrap(request_form)

async def multi_request_form(form_hash: str, provider_list: list[dict[str, str | int]], output = True) -> Form | None:
    if output: print(f"[cheatsheet] multi-requesting from {[provider['name'] for provider in provider_list]}")

    tasks = [asyncio.create_task(request_form(form_hash, provider, output=False)) for provider in provider_list]
    done_tasks, _ = await asyncio.wait(tasks) # _ is not done tasks but we wait for every task so...
    for done_task in done_tasks:
        res = done_task.result()
        if res != None:
            if output: print("Found Form.")
            return res
    if output: print("Unable to locate form from any provider")
    return None

sync_multi_request_form = sync_wrap(multi_request_form)

async def send_form(form: Form, provider: dict[str, str | int], output=True, skip_preprocess: bool = False) -> bytes:
    if not skip_preprocess:
        form = form.copy()
        strip_form(form, "scored")
        form_data = io.BytesIO()
        form.export(form_data)
        data = form_data.read()
        if len(data) > max_file_size: raise ValueError("Trying to Send too large of a form, aborting")
    if output: 
        print(f"[cheatsheet] sending form to `{provider['name']}`")
        print("[cheatsheet] initalizing connection... ", end="")

    try:
        sock = await init_provider(provider)
        print("Connected\n[cheatsheet] sending form...", end="")
        result = await _send_form(form, sock)
        if output: print(result.decode().title())
        sock.close()
        return result
    except:
        if output: print("Failure")
        return b"NET-FAILURE"
    

sync_send_form = sync_wrap(send_form)

async def multi_send_form(form: Form, provider_list: list[dict[str, str | int]], output = True) -> dict[str, bytes]:
    form = form.copy()
    strip_form(form, "scored")
    form_data = io.BytesIO()
    form.export(form_data)
    data = form_data.read()
    names = [provider['name'] for provider in provider_list]
    if len(data) > max_file_size: 
        print("[cheatsheet] unable to send files, its too large of an form")
        return {name:b"TOO-LARGE" for name in names} # type: ignore
    if output: print(f"[cheatsheet] multi-sending to {names}")

    tasks: list[asyncio.Task] = []
    for provider in provider_list:
        task = asyncio.create_task(send_form(form, provider, output=False, skip_preprocess=True))
        task.set_name(provider['name'])
        tasks.append(task)
    done, _ = await asyncio.wait(tasks) # _ is not done tasks but we wait for every task so...
    return {done_task.get_name(): done_task.result() for done_task in done}

sync_multi_send_form = sync_wrap(multi_send_form)

async def host_server(provider_information: dict[str, str | int], output=True):
    if output: print(f"[cheatsheet] Starting an cheatsheet server {provider_information['name']}... ", end="")
    
    try:
        host = await init_provider(provider_information, output=False, connect=False)
        if output: print("Ready")
        srvr = cheatsheet_server(host, provider_information['name'], provider_information["form_directory"]) #type: ignore
        await srvr.run()
    except:
        if output: print("Failure")

sync_host_server = sync_wrap(host_server)

async def multi_host_server(host_list: list[dict[str, str | int]], output=True):
    if output: 
        host_names = [host['name'] for host in host_list]
        print(f"[cheatsheet] multi hosting {host_names}")
    
    tasks = [asyncio.create_task(host_server(host, output=False)) for host in host_list]
    await asyncio.wait(tasks)
    
sync_multi_host_server = sync_wrap(multi_host_server)

def main():
    if not path.exists("config.json"):
        print("Cheatsheet requires config.json, check CONFIG.md")
    
    cfg = json.loads(read_file("config.json"))
    try:
        cheatsheet_cfg = cfg["cheatsheet"]
    except ValueError:
        print("Cheatsheet requires cheatsheet element in config.json, check CONFIG.md")
    
    if not cheatsheet_cfg["enabled"]:
        print("Cheatsheet is not enabled in config, would you like to proceed?")
        usr_in = input("[y/N]> ").lower()
        if usr_in != 'y': return
    
    while True:
        print("There are two modes: client & server")
        mode = input("mode[client,server]> ").lower()
        if mode == "": return 
        if mode == "client":
            while True:
                print("Would you like to send or recv form?")
                client_mode = input("client_mode[send,recv]>")
                if client_mode == "": break
                if client_mode == "send" or client_mode == "recv":
                    print("Providers: ")
                    i = 1
                    for provider in cheatsheet_cfg["providers"]:
                        print(f"{i}: name = {provider['name']} conn_info = ({provider['mode']}){provider['addr']}[{provider['port']}]")
                        i+=1
                    while True:
                        try:
                            choices = input("list of choices (; to split, * for everything)> ")
                            if choices == "*":
                                provider_list = cheatsheet_cfg["providers"]
                                break
                            else:
                                provider_list = [cheatsheet_cfg["providers"][int(i)-1] for i in choices.split(';')]
                                break
                        except ValueError:
                            print("Invalid pramiter")
                    form_hash = input("Form hash> ")
                    if client_mode == "send":
                        fp = f"{cfg['export']['export_dir']}{form_hash}.form"
                        if not path.exists(fp):
                            print("File Doesn't Exist")
                            break
                        form_file = io.BytesIO(read_file(fp))
                        form = Form.from_file(form_file)
                        print(sync_multi_send_form(form, provider_list))
                    else:
                        form = sync_multi_request_form(form_hash, provider_list)
                        if form == None:
                            print("No form returned, not writing")
                            continue
                        else:
                            export(form, "all", cfg['export']['export_dir'], "cheatsheet_recv")
                else: print("Invalid Option")
        elif mode == "server":
            print("Hosting configurations: ")
            i = 1
            for host_cfg in cheatsheet_cfg["hosting"]:
                print(f"{i}: name = {host_cfg['name']} conn_info = ({host_cfg['mode']}){host_cfg['addr']}[{host_cfg['port']}] dir = {host_cfg['form_directory']}")
                i+=1
            while True:
                try:
                    choices = input("list of choices (; to split, * for everything)> ")
                    if choices == "*":
                        host_cfg_list = cheatsheet_cfg["hosting"]
                        break
                    else:
                        host_cfg_list = [cheatsheet_cfg["hosting"][int(i)-1] for i in choices.split(';')]
                        break
                except ValueError:
                    print("Invalid pramiter")
            sync_multi_host_server(host_cfg_list)

if __name__ == "__main__": 
    if path.exists(__file__.removesuffix(path.basename(__file__)) + "main.py"): # If main exists in the same directory as cheatsheet
        main() #User cli
    else:
        print("DEDICATED SERVER SETUP DETECTED.")
        if not path.exists("config.json"): 
            print("Uanble to read config.josn")
        with open("config.json", 'r') as f:
            cfg = json.load(f)
            sync_multi_host_server(cfg["cheatsheet"]["hosting"])
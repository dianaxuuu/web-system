"""MapReduce framework Worker node."""
import os
import heapq
import socket
import threading
import shutil
import tempfile
import contextlib
import subprocess
import hashlib
import logging
import json
import time
import click
from mapreduce.utils import get_message


# Configure logging
LOGGER = logging.getLogger(__name__)


class Worker:
    """A class representing a Worker node in a MapReduce cluster."""

    def __init__(self, host, port, manager_host, manager_port):
        """Construct a Worker instance and start listening for messages."""
        self.shut_down = False
        self.host = host
        self.port = int(port)
        self.manager_host = manager_host
        self.manager_port = int(manager_port)
        LOGGER.info(
            "Starting worker host=%s port=%s pwd=%s",
            host, port, os.getcwd(),
        )
        LOGGER.info(
            "manager_host=%s manager_port=%s",
            manager_host, manager_port,
        )

        reg_thread = threading.Thread(target=self.register)
        reg_thread.start()
        self.run_socket()

    def register(self):
        """Send register message to manager."""
        register_message = {
            "message_type": "register",
            "worker_host": self.host,
            "worker_port": self.port,
        }
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soc:
            soc.connect((self.manager_host, self.manager_port))
            soc.sendall(json.dumps(register_message).encode('utf-8'))

    def run_socket(self):
        """Create a new TCP socket and handle any incoming messages."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Bind the socket to the server
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host, self.port))
            sock.listen()
            # Socket accept() will block for a maximum of 1 second.  If you
            # omit this, it blocks indefinitely, waiting for a connection.
            sock.settimeout(1)
            while not self.shut_down:
                # Wait for a connection for 1s.  The socket library avoids
                # consuming CPU while waiting for a connection.
                try:
                    message = get_message(sock)
                except json.JSONDecodeError:
                    continue
                except socket.timeout:
                    continue
                LOGGER.debug("Worker TCP recv\n%s",
                             json.dumps(message, indent=2))

                if message["message_type"] == "shutdown":
                    self.shut_down = True
                elif message["message_type"] == "register_ack":
                    sendhb_thread = threading.Thread(target=self.send_hb)
                    sendhb_thread.start()
                elif message["message_type"] == "new_map_task":
                    self.mapping(message)
                elif message["message_type"] == "new_reduce_task":
                    self.reducing(message)

    def send_hb(self):
        """Send heartbeat message to manager every 2 seconds."""
        hb_message = {
            "message_type": "heartbeat",
            "worker_host": self.host,
            "worker_port": self.port,
        }
        message_bytes = json.dumps(hb_message).encode('utf-8')
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as hb_sock:
            while not self.shut_down:
                try:
                    hb_sock.connect((self.manager_host, self.manager_port))
                    break
                except ConnectionRefusedError:
                    continue

            while not self.shut_down:
                hb_sock.sendall(message_bytes)
                time.sleep(2)

    def mapping(self, info):
        """Do the mapping job."""
        inputs = info["input_paths"]
        num_parts = info["num_partitions"]

        # create a local temp dir for intermediate files
        prefix = f"mapreduce-local-task{info['task_id']:05d}-"
        with tempfile.TemporaryDirectory(prefix=prefix) as tmpdir:
            LOGGER.info("Worker %s created tmpdir %s", self.host, tmpdir)
            with contextlib.ExitStack() as stack:
                # open the files to be written first to improve efficiency
                outputs = [stack.enter_context(open(
                    str(tmpdir)
                    + f"/maptask{info['task_id']:05d}-part{i:05d}", "a+",
                    encoding="utf-8"
                )) for i in range(num_parts)]
                for input_path in inputs:
                    LOGGER.debug("Worker %s %s working on input %s", self.host,
                                 self.port, input_path)
                    with open(input_path, encoding="utf8") as infile:
                        with subprocess.Popen(
                            [info["executable"]],
                            stdin=infile,
                            stdout=subprocess.PIPE,
                            text=True,
                        ) as map_process:
                            for line in map_process.stdout:
                                # Add line to correct partition output file
                                (outputs[self.partitioning(line, num_parts)].
                                 write(line))

            # Sort each output by line
            for i in range(info["num_partitions"]):
                file_name = f"maptask{info['task_id']:05d}-part" + f"{i:05d}"
                output = str(tmpdir) + "/" + file_name
                subprocess.run(
                    ["sort", "-o", info["output_directory"] + "/" + file_name,
                     output],
                    check=True,
                )

        # send finished message to the manager
        self.send_fin(info)
        LOGGER.info("Worker %s %s finished map task %s",
                    self.host, self.port, info["task_id"])

    def partitioning(self, line, num_partitions):
        """Write the line to the corresponding partition file."""
        if num_partitions == 1:
            return 0
        key = line.partition("\t")[0]
        hexdigest = hashlib.md5(key.encode("utf-8")).hexdigest()
        return int(hexdigest, base=16) % num_partitions

    def reducing(self, info):
        """Do the reducing job."""
        exe = info["executable"]
        with contextlib.ExitStack() as stack:
            # merge input files into one sorted output stream
            files = [stack.enter_context(open(fname, encoding="utf8"))
                     for fname in info["input_paths"]]
            inputs = heapq.merge(*files)

            # create a local temp dir for intermediate files
            prefix = f"mapreduce-local-task{info['task_id']:05d}-"
            with tempfile.TemporaryDirectory(prefix=prefix) as tmpdir:
                LOGGER.info("Worker %s created tmpdir %s", self.host, tmpdir)
                file_name = f"part-{info['task_id']:05d}"
                output_path = str(tmpdir) + "/" + file_name
                # Run the reduce executable on merged input,
                # writing output to a single file.
                with open(output_path, 'a', encoding="utf8") as outfile:
                    with subprocess.Popen(
                        [exe],
                        text=True,
                        stdin=subprocess.PIPE,
                        stdout=outfile,
                    ) as reduce_process:
                        # Pipe input to reduce_process
                        for line in inputs:
                            reduce_process.stdin.write(line)

                # Move the output file to the final output directory.
                shutil.move(output_path,
                            info["output_directory"] + "/" + file_name)

            # send finished message to the manager
            self.send_fin(info)
            LOGGER.info("Worker %s %s finished reduce task %s",
                        self.host, self.port, info["task_id"])

    def send_fin(self, info):
        """Send finished message to the manager."""
        message = {
            "message_type": "finished",
            "task_id": info["task_id"],
            "worker_host": self.host,
            "worker_port": self.port,
        }
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect((self.manager_host, self.manager_port))
                sock.sendall(json.dumps(message).encode('utf-8'))
            except ConnectionRefusedError:
                pass


@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=6001)
@click.option("--manager-host", "manager_host", default="localhost")
@click.option("--manager-port", "manager_port", default=6000)
@click.option("--logfile", "logfile", default=None)
@click.option("--loglevel", "loglevel", default="info")
def main(host, port, manager_host, manager_port, logfile, loglevel):
    """Run Worker."""
    if logfile:
        handler = logging.FileHandler(logfile)
    else:
        handler = logging.StreamHandler()
    formatter = logging.Formatter(f"Worker:{port} [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(loglevel.upper())
    Worker(host, port, manager_host, manager_port)


if __name__ == "__main__":
    main()

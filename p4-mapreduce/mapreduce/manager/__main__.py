"""MapReduce framework Manager node."""
import os
import socket
import threading
import shutil
import glob
import tempfile
import logging
import json
import time
import click
from mapreduce.utils import get_message


# Configure logging
LOGGER = logging.getLogger(__name__)


class Manager:
    """Represent a MapReduce framework Manager node."""

    def __init__(self, host, port):
        """Construct a Manager instance and start listening for messages."""
        self.shutdown = False
        self.ht_pt = (host, int(port))
        self.workers = []   # list for workers
        self.jobs_queue = []
        self.job_id = -1
        self.tasks = []
        self.assigned_tasks = {}
        LOGGER.info(
            "Starting manager host=%s port=%s pwd=%s",
        )

        hb_thread = threading.Thread(target=self.listen_hb)
        hb_thread.start()
        runjob_thread = threading.Thread(target=self.run_job)
        runjob_thread.start()
        ping_thread = threading.Thread(target=self.increase_pings)
        ping_thread.start()

        self.run_socket()
        hb_thread.join()
        runjob_thread.join()
        ping_thread.join()

        LOGGER.info("Manager shutting down")

    def run_socket(self):
        """Create a new TCP socket and handle any incoming messages."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Bind the socket to the server
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.ht_pt[0], self.ht_pt[1]))
            sock.listen()
            # Socket accept() will block for a maximum of 1 second.  If you
            # omit this, it blocks indefinitely, waiting for a connection.
            sock.settimeout(1)
            while not self.shutdown:
                # Wait for a connection for 1s.  The socket library avoids
                # consuming CPU while waiting for a connection.
                try:
                    message = get_message(sock)
                except socket.timeout:
                    continue
                except json.JSONDecodeError:
                    continue
                LOGGER.debug("Manager TCP recv\n%s",
                             json.dumps(message, indent=2))

                if message["message_type"] == "shutdown":
                    self.shutdown_func(message)
                elif message["message_type"] == "register":
                    self.register_helper_func(message)
                elif message["message_type"] == "new_manager_job":
                    self.new_manager_job_func(message)
                elif message["message_type"] == "finished":
                    self.finished_func(message)

    def shutdown_func(self, message):
        """Shutdown function for run_socket."""
        self.shutdown = True
        # forward the message and shut down the workers
        for worker in self.workers:
            if worker["state"] != "dead":
                with (socket.socket(socket.AF_INET,
                                    socket.SOCK_STREAM) as
                        shutdown_sock):
                    try:
                        shutdown_sock.connect((worker["host"],
                                               worker["port"]))
                        shutdown_sock.sendall(json.dumps(message).
                                              encode('utf-8'))
                    except ConnectionRefusedError:
                        pass

    def register_helper_func(self, message_dict):
        """Register function for run_socket."""
        # first, check if the worker is a previously dead worker
        # re-registering
        worker_exists = False
        for worker in self.workers:
            if (worker["host"] == message_dict["worker_host"] and
                    worker["port"] == message_dict["worker_port"]):
                worker_exists = True
                worker["state"] = "ready"
                break

        if not worker_exists:
            new_worker = {
                "host": message_dict["worker_host"],
                "port": message_dict["worker_port"],
                "state": "ready",
                "pings": 0,
            }
            self.workers.append(new_worker)

        # send the registering worker with ack message
        with socket.socket(socket.AF_INET,
                           socket.SOCK_STREAM) as ack_sock:
            message_dict["message_type"] = "register_ack"
            try:
                ack_sock.connect((message_dict["worker_host"],
                                  message_dict["worker_port"]))
                ack_sock.sendall(json.dumps(message_dict).
                                 encode('utf-8'))
            except ConnectionRefusedError:
                self.workers[-1]["state"] = "dead"

    def new_manager_job_func(self, message_dict):
        """Handle new manager job funcion for run_socket."""
        output_dir = message_dict["output_directory"]
        # delete the output directory if it exists
        if os.path.isdir(output_dir):
            shutil.rmtree(output_dir)
        os.mkdir(output_dir)
        # add the job to queue and increment assigned jobid
        self.job_id += 1
        message_dict["id"] = self.job_id
        self.jobs_queue.append(message_dict)

    def finished_func(self, message_dict):
        """Finished function for run_socket."""
        for worker in self.workers:
            if (worker["host"] == message_dict["worker_host"]
                    and worker["port"]
                    == message_dict["worker_port"]):
                self.assigned_tasks.pop(worker["host"]
                                        + str(worker["port"]))
                worker["state"] = "ready"
                break

    def listen_hb(self):
        """Listen for UDP heartbeat messages from the Workers."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as hb_sock:
            hb_sock.settimeout(1)
            while not self.shutdown:
                try:
                    message = hb_sock.recv(4096)
                    message_dict = json.loads(message.decode("utf-8"))
                except socket.timeout:
                    continue
                # reset the pings
                for worker in self.workers:
                    if (worker["host"] == message_dict["worker_host"] and
                            worker["port"] == message_dict["worker_port"]):
                        worker["pings"] = 0
                        if worker["state"] == "dead":
                            worker["state"] = "ready"

    def increase_pings(self):
        """Increase each workers' pings every 2 seconds."""
        while not self.shutdown:
            for worker in self.workers:
                worker["pings"] += 1
                if worker["pings"] == 5:
                    LOGGER.info("Worker %s %s died.", worker["host"],
                                worker["port"])
                    if worker["state"] == "busy":
                        # push the task back to the tasks queue
                        self.tasks.append(self.assigned_tasks.
                                          pop(worker["host"]
                                              + str(worker["port"])))
                    worker["state"] = "dead"
            time.sleep(2)

    def run_job(self):
        """Try to run job in the jobs queues."""
        while not self.shutdown:
            # avoid busy-waiting
            time.sleep(0.1)
            if len(self.jobs_queue) > 0:
                # partition the input of the mapping job
                job = self.jobs_queue[0]
                input_dir = job["input_directory"]
                files = glob.glob(input_dir + "/*")
                files.sort()
                self.tasks = [{
                    "id": i,
                    "files": [],
                } for i in range(job["num_mappers"])]
                for i, file in enumerate(files):
                    (self.tasks[i % job["num_mappers"]]["files"].
                     append(file))

                # create a shared directory for temporary intermediate files
                prefix = f"mapreduce-shared-job{self.job_id:05d}-"
                with tempfile.TemporaryDirectory(prefix=prefix) as tmpdir:
                    LOGGER.info("Created tmpdir %s", tmpdir)
                    if len(self.workers) > 0:
                        # assign mapping tasks to workers
                        self.assigned_tasks = {}
                        self.assign_job("map", job, tmpdir)
                        # partition the input of the reduce job
                        files = glob.glob(str(tmpdir) + "/*")
                        files.sort()
                        self.tasks = [{
                            "id": i,
                            "files": [],
                        } for i in range(job["num_reducers"])]
                        for file in files:
                            self.tasks[int(file[-5:])]["files"].append(file)
                        # assign reducing tasks to workers
                        self.assigned_tasks = {}
                        self.assign_job("reduce", job, tmpdir)
                        self.jobs_queue.pop(0)
                    else:
                        # if there are no workers, skip this job
                        LOGGER.info("Workers do not exist")
                        time.sleep(2)

                LOGGER.info("Cleaned up tmpdir %s", tmpdir)

    def assign_job(self, job_type, job, tmpdir):
        """Assign tasks to workers."""
        while not self.shutdown and len(self.tasks) > 0:
            task = self.tasks[0]
            found_worker = False
            for worker in self.workers:
                if worker["state"] == "ready":
                    message = {
                        "message_type": "new_" + job_type + "_task",
                        "task_id": task["id"],
                        "input_paths": task["files"],
                        "worker_host": worker["host"],
                        "worker_port": worker["port"],
                    }
                    if job_type == "map":
                        message["output_directory"] = str(tmpdir)
                        message["num_partitions"] = job["num_reducers"]
                        message["executable"] = job["mapper_executable"]
                    else:
                        message["output_directory"] = job["output_directory"]
                        message["executable"] = job["reducer_executable"]

                    # connect to worker and send the task msg
                    with socket.socket(socket.AF_INET,
                                       socket.SOCK_STREAM) as task_sock:
                        try:
                            task_sock.connect((worker["host"],
                                               worker["port"]))
                            task_sock.sendall(json.dumps(message).
                                              encode('utf-8'))
                        except ConnectionRefusedError:
                            worker["state"] = "dead"
                            continue
                    # record the worker the task is assigned to
                    # if the worker becomes dead, reassign this task
                    self.assigned_tasks[worker["host"]
                                        + str(worker["port"])] = task
                    LOGGER.info("Assigned worker %s %s with %s task %d",
                                worker["host"], worker["port"], job_type,
                                task["id"])
                    worker["state"] = "busy"
                    # found available worker, continue to next task
                    self.tasks.pop(0)
                    found_worker = True
                    break
            if not found_worker:
                # all workers are busy or dead
                time.sleep(0.1)  # avoid busy waiting

        # wait for all the workers to finished
        while not self.shutdown and (len(self.assigned_tasks) > 0 or
                                     len(self.tasks) > 0):
            time.sleep(0.1)
            if len(self.tasks) > 0:
                self.assign_job(job_type, job, tmpdir)


@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=6000)
@click.option("--logfile", "logfile", default=None)
@click.option("--loglevel", "loglevel", default="info")
@click.option("--shared_dir", "shared_dir", default=None)
def main(host, port, logfile, loglevel, shared_dir):
    """Run Manager."""
    tempfile.tempdir = shared_dir
    if logfile:
        handler = logging.FileHandler(logfile)
    else:
        handler = logging.StreamHandler()
    formatter = logging.Formatter(
        f"Manager:{port} [%(levelname)s] %(message)s"
    )
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(loglevel.upper())
    Manager(host, port)


if __name__ == "__main__":
    main()

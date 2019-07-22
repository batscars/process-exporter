import prometheus_client
from prometheus_client import Gauge
from prometheus_client.core import CollectorRegistry
from flask import Response, Flask
import argparse
from subprocess import Popen, PIPE
import psutil as ps
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = Flask(__name__)

parser = argparse.ArgumentParser(description='process exporter')
parser.add_argument('--host', type=str, default='0.0.0.0', help='host')
parser.add_argument('--port', type=int, default=5000, help='port')
parser.add_argument('--top', type=int, default=10, help='top k processes')
args = parser.parse_args()

REGISTRY = CollectorRegistry(auto_describe=False)
process_memory_util = Gauge("process_memory_percentage",
                            "Percentage of memory used by process",
                            ["pid", "cmd", "username"],
                            registry=REGISTRY)
process_cpu_util = Gauge("process_cpu_percentage",
                         "Percentage of cpu used by process",
                         ["pid", "cmd", "username"],
                         registry=REGISTRY)


def cpu_mem_percentage(top=10):
    top_pipe = Popen("top -b -o +%CPU", stdout=PIPE, shell=True, close_fds=True)
    cpu_res = Popen("head -%d" % (top + 7), stdout=PIPE, shell=True, stdin=top_pipe.stdout, close_fds=True)
    cpu_output = cpu_res.stdout.read().splitlines()
    top_pipe.stdout.close()
    cpu_res.stdout.close()
    for i in range(7, len(cpu_output)):
        line = cpu_output[i]
        line = line.split()
        pid = line[0]
        cpu = float(line[8])
        if cpu == 0.0:
            continue
        p = ps.Process(int(pid))
        cmd = " ".join(p.cmdline())
        if cmd == "":
            cmd = p.name()
        if len(cmd) > 100:
            cmd = cmd[:100] + "+"
        user = p.username()
        logging.info(cmd)
        process_cpu_util.labels(pid, cmd, user).set(cpu)

    top_pipe = Popen("top -b -o +%MEM", stdout=PIPE, shell=True, close_fds=True)
    mem_res = Popen("head -%d" % (top + 7), stdout=PIPE, shell=True, stdin=top_pipe.stdout, close_fds=True)
    mem_output = mem_res.stdout.read().splitlines()
    top_pipe.stdout.close()
    mem_res.stdout.close()
    for i in range(7, len(mem_output)):
        line = mem_output[i]
        line = line.split()
        pid = line[0]
        mem = float(line[9])
        if mem == 0.0:
            continue
        p = ps.Process(int(pid))
        cmd = " ".join(p.cmdline())
        if cmd == "":
            cmd = p.name()
        if len(cmd) > 100:
            cmd = cmd[:100] + "+"
        user = p.username()
        logging.info(cmd)
        process_memory_util.labels(pid, cmd, user).set(mem)


@app.route("/metrics", methods=["GET"])
def metrics():
    process_memory_util._metrics.clear()
    process_cpu_util._metrics.clear()
    cpu_mem_percentage(top=args.top)
    resp = prometheus_client.generate_latest(REGISTRY)
    return Response(resp, mimetype="text/plain")


if __name__ == "__main__":
    app.run(host=args.host, port=args.port)

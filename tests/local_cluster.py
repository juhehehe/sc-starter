"""A stand-in for ssh in the tests that runs each command on a local cluster.

Run as `python local_cluster.py <ssh arguments>`. Where tests/fake_ssh.py
plays back a canned reply, this runs the command in a real `sh`, in the
home folder in LOCAL_CLUSTER_HOME that both hosts share, as on SC. Only the
Slurm commands are stand-ins, from the folder in LOCAL_CLUSTER_BIN; tar,
find and the rest are this computer's own, so this runs on Linux only.
Each call is added to `calls.jsonl` next to the home folder.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    args = sys.argv[1:]
    while args[0] == "-o":
        args = args[2:]
    host, command = args

    home = Path(os.environ["LOCAL_CLUSTER_HOME"])
    with (home.parent / "calls.jsonl").open("a") as calls:
        calls.write(json.dumps({"host": host, "command": command}) + "\n")

    env = {
        **os.environ,
        "HOME": str(home),
        "PATH": f"{os.environ['LOCAL_CLUSTER_BIN']}:{os.environ['PATH']}",
    }
    # Input and output pass straight through, as with ssh.
    return subprocess.run(["sh", "-c", command], cwd=home, env=env).returncode


if __name__ == "__main__":
    sys.exit(main())

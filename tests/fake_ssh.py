"""A stand-in for ssh in the tests: records each call and plays back a reply.

Run as `python fake_ssh.py <ssh arguments>`; a Python script rather than a
shell script, because Windows would not find a fake `ssh.cmd` on the PATH.
The folder in FAKE_SSH_DIR holds `replies.json` (per host: a file with the
output, stderr, exit code, and whether to press Ctrl+C) and receives
`call-<n>.json` and `call-<n>.stdin` per call.
"""

import json
import os
import signal
import sys
from pathlib import Path


def main() -> int:
    folder = Path(os.environ["FAKE_SSH_DIR"])
    args = sys.argv[1:]
    options = []
    while args[0] == "-o":
        options.append(args[1])
        args = args[2:]
    host, command = args

    number = len(list(folder.glob("call-*.json")))
    (folder / f"call-{number}.stdin").write_bytes(sys.stdin.buffer.read())
    call = {"options": options, "host": host, "command": command}
    (folder / f"call-{number}.json").write_text(json.dumps(call))

    replies_file = folder / "replies.json"
    replies = json.loads(replies_file.read_text()) if replies_file.exists() else {}
    reply = replies.get(host, {})
    if reply.get("interrupt"):
        # What the terminal does on Ctrl+C, here only to the tool.
        os.kill(os.getppid(), signal.SIGINT)
    if "stdout_file" in reply:
        sys.stdout.buffer.write(Path(reply["stdout_file"]).read_bytes())
    sys.stderr.write(reply.get("stderr", ""))
    return reply.get("code", 0)


if __name__ == "__main__":
    sys.exit(main())

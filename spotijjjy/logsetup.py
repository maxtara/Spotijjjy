"""
Shared logging setup for Spotijjjy entrypoints.

Goal: a single, nicely formatted log stream to stdout, whether the code runs as a CLI or
inside AWS Lambda - and without fighting whatever handler the runtime already installed.

* Locally / CLI: the root logger has no handlers, so we attach one StreamHandler to
  stdout with a readable format.
* AWS Lambda: the runtime pre-installs a root handler (which adds the request id), so we
  leave it in place and only raise the level. That keeps the familiar CloudWatch format.
"""
import logging
import sys

_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def setup_logging(level=logging.INFO):
    """Configure the root logger to emit nicely formatted records to stdout."""
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_FORMAT))
        root.addHandler(handler)

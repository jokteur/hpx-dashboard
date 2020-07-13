import sys

from .common.logger import Logger


if __name__ == "__main__":
    logger = Logger(name="hpx-dashboard")

    logger.error(
        "this package can not be used as a standalone. "
        "Please use hpx_dashboard.agent or hpx_dashboard.server"
    )
    sys.exit(1)

# -*- coding: utf-8 -*-
#
# HPX - dashboard
#
# Copyright (c) 2020 - ETH Zurich
# All rights reserved
#
# SPDX-License-Identifier: BSD-3-Clause

"""Main entry for the hpx agent parser
"""

import sys

from .cli import agent

if __name__ == "__main__":
    # return_code = asyncio.get_event_loop().run_until_complete(amain(sys.argv))
    return_code = agent(sys.argv)
    sys.exit(return_code)

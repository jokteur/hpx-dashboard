# -*- coding: utf-8 -*-
#
# HPX - dashboard
#
# Copyright (c) 2020 - ETH Zurich
# All rights reserved
#
# SPDX-License-Identifier: BSD-3-Clause

"""Module that defines a metaclass that allows for the creation of Singletons.

Using the ``Singleton`` metaclass, it is possible to transform any ordinary
class into a singleton.
"""

__copyright__ = "Copyright (C) 2020 ETHZ"
__licence__ = "BSD 3"


class Singleton(type):
    """Python metasclass for creating singletons in other classes"""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

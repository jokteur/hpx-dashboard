# -*- coding: utf-8 -*-
#
# HPX - dashboard
#
# Copyright (c) 2020 - ETH Zurich
# All rights reserved
#
# SPDX-License-Identifier: BSD-3-Clause

"""This module is for generating the list of available official hpx counters.

The script is based on the following link:
https://stellar-group.github.io/hpx/docs/sphinx/latest/html/manual/optimizing_hpx_applications.html#two-simple-examples

This scripts excludes aggregate counters such as /statistics/* and  /arithmetics/*.

"""

import sys

counter_types = [
    "/agas/count/<agas_service>",
    "/agas/<agas_service_category>/count",
    "/agas/time/<agas_service>",
    "/agas/<agas_service_category>/time",
    "/agas/count/entries",
    "/agas/count/<cache_statistics>",
    "/agas/count/<full_cache_statistics>",
    "/agas/time/<full_cache_statistics>",
    "/data/count/<connection_type>/<operation>",
    "/data/time/<connection_type>/<operation>",
    "/serialize/count/<connection_type>/<operation>",
    "/serialize/time/<connection_type>/<operation>",
    "/parcels/count/routed",
    "/parcels/count/<connection_type>/<operation>",
    "/messages/count/<connection_type>/<operation>",
    "/parcelport/count/<connection_type>/<cache_statistics>",
    "/parcelqueue/length/<operation>",
    "/threads/count/cumulative",
    "/threads/time/average",
    "/threads/time/average-overhead",
    "/threads/count/cumulative-phases",
    "/threads/time/average-phase",
    "/threads/time/average-phase-overhead",
    "/threads/time/overall",
    "/threads/time/cumulative",
    "/threads/time/cumulative-overheads",
    "/threads/count/instantaneous/<thread-state>",
    "threads/wait-time/<thread-state2>",
    "/threads/idle-rate",
    "/threads/creation-idle-rate",
    "/threads/cleanup-idle-rate",
    "/threadqueue/length",
    "/threads/count/stack-unbinds",
    "/threads/count/stack-recycles",
    "/threads/count/stolen-from-pending",
    "/threads/count/pending-misses",
    "/threads/count/pending-accesses",
    "/threads/count/stolen-from-staged",
    "/threads/count/stolen-to-pending",
    "/threads/count/stolen-to-staged",
    "/threads/count/objects",
    "/scheduler/utilization/instantaneous",
    "/threads/idle-loop-count/instantaneous",
    "/threads/busy-loop-count/instantaneous",
    "/threads/time/background-work-duration",
    "/threads/background-overhead",
    "/threads/time/background-send-duration",
    "/threads/background-send-overhead",
    "/threads/time/background-receive-duration",
    "/threads/background-receive-overhead",
    "/runtime/count/component",
    "/runtime/count/action-invocation",
    "/runtime/count/remote-action-invocation",
    "/runtime/uptime",
    "/runtime/memory/virtual",
    "/runtime/memory/resident",
    "/runtime/memory/total",
    "/runtime/io/read_bytes_issued",
    "/runtime/io/write_bytes_issued",
    "/runtime/io/read_syscalls",
    "/runtime/io/write_syscalls",
    "/runtime/io/read_bytes_transferred",
    "/runtime/io/write_bytes_transferred",
    # "/papi/<papi_event>",
]

replacements = {
    "<agas_service>": [
        "route",
        "bind_gid",
        "resolve_gid",
        "unbind_gid",
        "increment_credit",
        "decrement_credit",
        "allocate",
        "begin_migration",
        "end_migration",
        "bind_prefix",
        "bind_name",
        "resolve_id",
        "unbind_name",
        "iterate_types",
        "get_component_typename",
        "num_localities_type",
        "free",
        "localities",
        "num_localities",
        "num_threads",
        "resolve_locality",
        "resolved_localities",
        "bind",
        "resolve",
        "unbind",
        "iterate_names",
        "on_symbol_namespace_event",
    ],
    "<agas_service_category>": ["primary", "locality", "component", "symbol"],
    "<cache_statistics>": ["cache/evictions", "cache/hits", "cache/insertions", "cache/misses"],
    "<full_cache_statistics>": [
        "cache/get_entry",
        "cache/insert_entry",
        "cache/update_entry",
        "cache/erase_entry",
    ],
    "<connection_type>": ["sent", "received"],
    "<operation>": ["tcp", "mpi"],
    "<thread-state>": ["all", "active", "pending", "suspended", "terminated", "staged"],
    "<thread-state2>": ["pending", "staged"],
}


def replace_in_list(counter_list, replacements):
    """Replaces the <name> in the list recursively until there is nothing to replace."""
    new_list = []
    is_replaced = False

    # Not very efficient, but does the job
    for name in counter_list:
        is_replaced_local = False
        for replacement, replacement_list in replacements.items():
            if replacement in name:
                is_replaced_local = True
                is_replaced = True
                for to_replace in replacement_list:
                    new_list.append(name.replace(replacement, to_replace))
                break

        if not is_replaced_local:
            new_list.append(name)

    if is_replaced:
        return replace_in_list(new_list, replacements)
    else:
        return new_list


counters = replace_in_list(counter_types, replacements)
counters.sort()


if len(sys.argv) == 2:
    with open(sys.argv[1], "w") as file:
        counters = map(lambda x: '"' + x + '",\n', counters)
        file.write("counternames = [")
        file.writelines(counters)
        file.write("]")
else:
    print("counternames = [")
    counters = map(lambda x: '"' + x + '",', counters)
    for line in counters:
        print(line)
    print("]")

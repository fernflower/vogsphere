# -*- coding: utf-8 -*-
import argparse
import logging
import re
import os
import subprocess

import agents

LOG = logging.getLogger(__name__)
LOG_FILENAME = "log.log"
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", help="Yandex disk directory to monitor")
    return parser.parse_args()


def sync():
    return subprocess.call(["yandex-disk", "sync"]) == 0


def main():
    proc_prefix = "PROCESSED_"
    # probably will be set in future somehow
    prefix = u"Агент -"
    division = 0.7
    grouplen = 4
    name_pattern = "[a-zA-Z0-9]*_+(0.[0-9]+)_([0-9]+).*"
    args = parse_args()

    if not sync():
        LOG.error("Could not sync yandex disk")
        exit(1)

    def get_filename(name):
        return os.path.join(args.dir, name)
    newfiles = [f for f in os.listdir(args.dir)
                if os.path.isfile(get_filename(f)) and f.endswith(".xlsx") and
                not f.startswith(proc_prefix)]

    if len(newfiles) == 0:
        LOG.info("Nothing to do, exiting.")
        exit(0)

    tempinput = "input.csv"
    for f in newfiles:
        fullpath = get_filename(f)
        name = os.path.splitext(f)[0]
        m = re.match(name_pattern, f)
        if m:
            division = float(m.group(1))
            grouplen = int(m.group(2))
        else:
            LOG.warning(("Can't parse filename %s, using default division "
                         "(%s) and grouplen (%d) settings") %
                        (f, division, grouplen))
        # xslx -> csv
        with open(tempinput, "w") as fout:
            if subprocess.call(["xlsx2csv", fullpath], stdout=fout) != 0:
                LOG.error("Could not convert %s to csv" % f)
                exit(1)
        resfile = get_filename(name + "_processed.csv")
        res = agents.process(tempinput, percent=division, grouplen=grouplen,
                             prefix=prefix,
                             outfile=resfile)
        if res:
            LOG.info("Successfully processed %s, result stored in %s" %
                     (f, resfile))
        # mark xslx file as processed
        # maybe should delete in future?
        os.rename(get_filename(f), get_filename(proc_prefix + f))
    # delete temp file
    os.remove(tempinput)

    # synchronize
    if not sync():
        LOG.error("Could not sync yandex disk after processing!")
        exit(1)


if __name__ == "__main__":
    main()

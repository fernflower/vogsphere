# -*- coding: utf-8 -*-
import argparse
import itertools
import csv
import logging
import math
import sys


LOG = logging.getLogger(__name__)
LOG_FILENAME = "log.log"
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)


class Debt(object):
    def __init__(self, id, colls, type, amount):
        self.id = id
        self.collectors = colls
        self.type = type
        self.assigned = None
        try:
            self.amount = float(amount)
        except:
            self.amount = 0
            # LOG.warning("Debt #%s has no amount data!" % self.id)

    def __str__(self):
        return "#%s [%s]" % (self.id, self.type)

    def __repr__(self):
        return self.__str__()


def output_data(debts, debt_types, agents, headers):
    for dt in debt_types:
        LOG.info("[%s] distribution (total %d):" % (dt, len(debt_types[dt])))
        for aname in agents:
            count = len(agents[aname][dt]) if dt in agents[aname] else 0
            LOG.info("%s - %d" % (aname, count))
    # form resulting csv
    writer = csv.writer(sys.stdout)
    writer.writerow(headers)
    for debt in debts:
        row = [debt.id]
        for a in agents:
            row.append(a if a in debt.collectors else '')
        row.extend([debt.type, debt.assigned, debt.amount])
        writer.writerow(row)


def read_input(input_file, agents_prefix):
    with open(input_file) as csvfile:
        reader = csv.reader(csvfile)
        # first line has headers
        headers = next(reader)
        agents = {k: {} for k in
                  [v for v in headers[1:]
                   if v.startswith(agents_prefix.encode("utf-8"))]}
        debts = []
        debt_types = {}
        agent_count = len(agents.keys())
        for row in reader:
            collectors = [v for v in row[1:agent_count+1] if v != '']
            debt = Debt(row[0], collectors, row[agent_count+1], row[-1])
            try:
                debt_types[debt.type].append(debt)
            except KeyError:
                debt_types[debt.type] = [debt]
            debts.append(debt)
        return debts, debt_types, agents, headers


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="A csv file to process")
    parser.add_argument("--division", type=float, default=0.7,
                        help=("A percent to give first N agents."
                              "N is determined by --divisionN"))
    parser.add_argument("--divisionN", type=int, default=4,
                        help=("Last number to get percent set up by "
                              "--division"))
    parser.add_argument("--agentPrefix", default=u"Агент -",
                        help="A starting string of an agent csv field")
    return parser.parse_args()


args = parse_args()


def make_even(agent, agents):
    """ Make all agents have more or less the same number of debts.

    Sometimes 1-by-1 debt assignments lead to certain uneven states for some
    agents (when debts have a certain former collectors record).
    """
    pass


def get_limit(agent_name, total, agents):
    if any(agent_name.endswith(str(n)) for n in range(1, args.divisionN + 1)):
        return args.division * total / args.divisionN
    return (1 - args.division) * total / (len(agents) - args.divisionN)


def main():

    debts, debt_types, agents, headers = read_input(args.input,
                                                    args.agentPrefix)

    # same as previous, result is floored
    def get_int_limit(agent_name, total):
        return int(math.floor(get_limit(agent_name, total, agents)))

    def assign_debt(debt):
        for aname in agents:
            # if this agent has already tried
            # to collect the debt - skip
            if aname in debt.collectors:
                continue
            try:
                if (len(agents[aname][debt.type]) + 1 <= get_int_limit(
                        aname, len(debts))):
                    agents[aname][debt.type].append(debt)
                    debt.assigned = aname
                    return True
            except KeyError:
                agents[aname][debt.type] = [debt]
                debt.assigned = aname
                return True
        return False

    for dtname, debts in debt_types.items():
        agents_spin = itertools.cycle(agents)
        for debt in debts:
            if assign_debt(debt):
                continue
            aname = agents_spin.next()
            agents[aname][debt.type].append(debt)
            debt.assigned = aname

    output_data(debts, debt_types, agents, headers)


if __name__ == "__main__":
    main()

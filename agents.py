# -*- coding: utf-8 -*-
import argparse
import csv
import logging
import math
import sys

import exc


LOG = logging.getLogger(__name__)
LOG_FILENAME = "log.log"
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)


class Debt(object):
    types = []

    def __init__(self, id, colls, type, amount):
        self.id = int(id)
        self.collectors = colls
        self.type = type
        self.assigned = None
        try:
            # BUGFIX strip \xa0 and replace ',' for '.'
            # after google docs conversion
            self.amount = float(amount.replace(u"\xa0", "").replace(",", "."))
        except:
            self.amount = 0
            # LOG.warning("Debt #%s has no amount data!" % self.id)

    def __str__(self):
        return "#%s [%s]" % (self.id, self.type)

    def __repr__(self):
        return self.__str__()


class Agent(object):
    def __init__(self, name, percent, grouplen):
        self.name = name
        self.percent = percent
        self.grouplen = grouplen
        # a dictionary type: [debts list]
        self.debts = {}

    def add_debt(self, debt):
        if debt.type not in self.debts:
            self.debts[debt.type] = []
        self.debts[debt.type].append(debt)
        debt.assigned = self.name

    def remove_debt(self, debt):
        if debt in self.debts[debt.type]:
            self.debts[debt.type].remove(debt)
            debt.assigned = None

    def get_limit(self, total):
        return int(math.floor(total * self.percent / self.grouplen))

    def try_to_assign(self, debt, total, overflow=False):
        """Tries to assign the debt to the agent.

        Returns True if debt was assigned, False otherwise
        """
        if self.name in debt.collectors:
            # already tried to collect
            return False
        if (overflow or debt.type not in self.debts or
                (len(self.debts[debt.type]) + 1 <= self.get_limit(total))):
            self.add_debt(debt)
            return True
        return False

    def is_discriminated(self, debt_type, total):
        return len(self.debts[debt_type]) < self.get_limit(total)

    def get_subgroup(self, agents):
        return [a for a in agents if a.percent == self.percent]

    def __str__(self):
        res = "%s\n" % self.name
        for dt in self.debts:
            res += "[%s] - %d\n" % (dt, len(self.debts[dt]))
        return res

    def __repr__(self):
        return self.__str__()


def output_data(debts, agents, headers, encoding):
    for dt in Debt.types:
        LOG.info("[%s] distribution (total %d):" % (dt, len(debts[dt])))
        for agent in agents:
            count = len(agent.debts[dt]) if dt in agent.debts else 0
            LOG.info("%s - %d" % (agent.name, count))
    # form resulting csv
    writer = csv.writer(sys.stdout)
    writer.writerow([h.encode(encoding) for h in headers])
    all_debts = []
    for dt in debts:
        all_debts.extend(debts[dt])
    for debt in sorted(all_debts, key=lambda x: x.id):
        row = [debt.id]
        for a in agents:
            row.append(a.name if a.name in debt.collectors else '')
        row.extend([debt.type, debt.assigned, debt.amount])
        writer.writerow([c.encode(encoding)
                         if isinstance(c, unicode) else c for c in row])


def read_input(input_file, agents_prefix, division, divisionN, encoding):
    with open(input_file) as csvfile:
        reader = csv.reader(csvfile)
        # first line has headers
        headers = [c.decode(encoding) for c in next(reader) if c.strip() != ""]
        agent_names = [a for a in headers[1:] if a.startswith(agents_prefix)]
        if len(agent_names) == 0:
            LOG.error("Could not parse agents!")
            raise exc.ParseException(
                u"Agents could not be retrieved, prefix: %s" % agents_prefix)
        agents = []
        for aname in agent_names:
            if any(aname.endswith(str(n))
                   for n in range(1, divisionN + 1)):
                agent = Agent(aname, percent=division, grouplen=divisionN)
            else:
                agent = Agent(aname, percent=1 - division,
                              grouplen=len(agent_names) - divisionN)
            agents.append(agent)

        debts = {}
        agent_count = len(agents)
        for row in reader:
            row = [c.decode(encoding) for c in row[:len(headers)]]
            collectors = [v for v in row[1:agent_count+1] if v != '']
            debt = Debt(row[0], collectors, row[agent_count+1], row[-1])
            if debt.type not in debts:
                debts[debt.type] = []
            debts[debt.type].append(debt)
            if debt.type not in Debt.types:
                Debt.types.append(debt.type)

        return debts, agents, headers


def eliminate_discrimination(agents, debt, total):
    # need for a swap
    # search for agent with uncompleted plan
    discriminated = next((a for a in agents
                          if a.is_discriminated(debt.type, total)), None)
    if discriminated:
        ok = next((a for a in agents
                   if not a.is_discriminated(debt.type, total)), None)
        if not ok:
            LOG.info("Something went wrong!")
            return (False, discriminated)
        swap_debt = next((d for d in ok.debts[debt.type]
                          if discriminated.name not in d.collectors), None)
        if ok and swap_debt:
            ok.remove_debt(swap_debt)
            ok.add_debt(debt)
            discriminated.add_debt(swap_debt)
            return (True, discriminated)
        LOG.info("Can't find a debt to swap %s with!" % debt.id)
        return (False, None)

    # find agent with least debts in the group
    minDebt = min([len(s.debts[debt.type]) for s in agents])
    agent = next(s for s in agents if len(s.debts[debt.type]) == minDebt)
    if not agent.try_to_assign(debt, total, overflow=True):
        for a in [a for a in agents if a != agent]:
            a.try_to_assign(debt, total, overflow=True)
            return (True, None)
        LOG.info("Something went wrong!")
    return (True, None)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="A csv file to process")
    parser.add_argument("--division", type=float, default=0.7,
                        help=("A percent to give first N agents."
                              "N is determined by --divisionN"))
    parser.add_argument("--divisionN", type=int, default=4,
                        help=("Last number to get percent set up by "
                              "--division"))
    parser.add_argument("--agentPrefix", default="Agent -",
                        help="A starting string of an agent csv field",
                        type=lambda s: unicode(s, "utf-8"))
    parser.add_argument("--encoding", default="utf-8",
                        help=("an encoding used to encode/decode strings "
                              "in input/output"))
    return parser.parse_args()


def main():
    args = parse_args()
    debts, agents, headers = read_input(args.input, args.agentPrefix,
                                        args.division, args.divisionN,
                                        args.encoding)
    for dt in Debt.types:
        ordered_debts = sorted(debts[dt], reverse=True,
                               key=lambda x: len(x.collectors))

        def do_assign(debt):
            for agent in agents:
                if agent.try_to_assign(debt, len(ordered_debts)):
                    return True
            return False

        for debt in ordered_debts:
            if do_assign(debt):
                continue
            eliminate_discrimination(agents, debt, len(ordered_debts))

    output_data(debts, agents, headers, args.encoding)


if __name__ == "__main__":
    main()

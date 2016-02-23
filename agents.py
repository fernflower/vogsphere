# -*- coding: utf-8 -*-
import csv
import logging
import math


LOG = logging.getLogger(__name__)
LOG_FILENAME = "log.log"
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)


class Debt(object):
    def __init__(self, id, colls, type, amount):
        self.id = id
        self.collectors = colls
        self.type = type
        try:
            self.amount = float(amount)
        except:
            self.amount = 0
            #LOG.warning("Debt #%s has no amount data!" % self.id)

    def __str__(self):
        return "#%s [%s] - %s" % (self.id, self.type, self.amount)

    def __repr__(self):
        return self.__str__()


def main():
    debts = []
    agents = dict()
    debt_types = dict()

    # XXX use sysargs
    agents_prefix = u"Агент -"
    # 70% of money goes to 4 agents
    division = 0.7
    agents_div = 4
    agents_total = 7
    input_file = "agents.csv"

    def get_limit(agent_name, total):
        if any(agent_name.endswith(str(n)) for n in range(1, agents_div + 1)):
            return division * total / agents_div
        return (1 - division) * total / (agents_total - agents_div)

    # same as previous, result is floored
    def get_int_limit(agent_name, total):
        return int(math.floor(get_limit(agent_name, total)))

    with open(input_file) as csvfile:
        reader = csv.reader(csvfile)
        # first line has headers
        headers = next(reader)
        agents = {k: {} for k in
                  [v for v in headers[1:]
                   if v.startswith(agents_prefix.encode("utf-8"))]}
        agent_count = len(agents.keys())
        for row in reader:
            collectors = [v for v in row[1:agent_count] if v != '']
            debt = Debt(row[0], collectors, row[agent_count+1], row[-1])
            try:
                debt_types[debt.type].append(debt)
            except KeyError:
                debt_types[debt.type] = [debt]
            debts.append(debt)

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
                        return True
                except KeyError:
                    agents[aname][debt.type] = [debt]
                    return True
            return False

        for dtname, debts in debt_types.items():
            agents_spin = (a for a in agents)
            for debt in debts:
                if assign_debt(debt):
                    continue
                else:
                    # XXX FIXME round robin?
                    agents[next(agents_spin)][debt.type].append(debt)


        # output results
        for dt in debt_types:
            LOG.info("[%s] distribution (total %d):" % (dt,
                                                        len(debt_types[dt])))
            for aname in agents:
                count = len(agents[aname][dt]) if dt in agents[aname] else 0
                LOG.info("%s - %d" % (aname, count))


if __name__ == "__main__":
    main()

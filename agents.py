# -*- coding: utf-8 -*-
import csv
import logging


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
            LOG.warning("Debt #%s has no amount data!" % self.id)

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
    input_file = "agents.csv"

    def get_limit(agent_name, total):
        if any(agent_name.endswith(str(n)) for n in range(1, agents_div)):
            return division * total
        return (1 - division) * total
    # retrieves a next agent that debts can be assigned to

    with open(input_file) as csvfile:
        reader = csv.reader(csvfile)
        # first line has headers
        headers = next(reader)
        agents = {k: {"debts": []} for k in
                  [v for v in headers[1:]
                   if v.startswith(agents_prefix.encode("utf-8"))]}
        agent_count = len(agents.keys())
        for row in reader:
            collectors = [v for v in row[1:agent_count] if v != '']
            debt = Debt(row[0], collectors, row[agent_count+1], row[-1])
            try:
                debt_types[debt.type]["debts"].append(debt)
                debt_types[debt.type]["sum"] += debt.amount
            except KeyError:
                debt_types[debt.type] = {"debts": [debt],
                                         "sum": debt.amount}
            debts.append(debt)

        for dtname, dt in debt_types.items():
            for debt in dt["debts"]:
                for aname in agents:
                    try:
                        # if this agent has already tried
                        # to collect the debt - skip
                        if aname in debt.collectors:
                            continue
                        if (agents[aname][debt.type] +
                                debt.amount <= get_limit(aname, dt["sum"])):
                            agents[aname]["debts"].append(debt)
                        break
                    except KeyError:
                        # no sum has been calculated for this debt type
                        agents[aname][debt.type] = debt.amount
                        agents[aname]["debts"].append(debt)
                        break
                    raise Exception("No agent found!")
        import ipdb; ipdb.set_trace()


if __name__ == "__main__":
    main()

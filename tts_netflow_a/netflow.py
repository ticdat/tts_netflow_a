#
# Core engine file for tts_netflow_a
#

try: # if you don't have gurobipy installed, the code will still load and then fail on solve
    import gurobipy as gu
except:
    gu = None
from ticdat import TicDatFactory, Slicer

# ------------------------ define the input schema --------------------------------
input_schema = TicDatFactory (
    commodities=[["Name"], ["Volume"]],
    nodes=[["Name"], []],
    arcs=[["Source", "Destination"], ["Capacity"]],
    cost=[["Commodity", "Source", "Destination"], ["Cost"]],
    inflow=[["Commodity", "Node"], ["Quantity"]]
)

# Define the foreign key relationships
input_schema.add_foreign_key("arcs", "nodes", ['Source', 'Name'])
input_schema.add_foreign_key("arcs", "nodes", ['Destination', 'Name'])
input_schema.add_foreign_key("cost", "arcs", [['Source', 'Source'],
                                              ['Destination', 'Destination']])
input_schema.add_foreign_key("cost", "commodities", ['Commodity', 'Name'])
input_schema.add_foreign_key("inflow", "commodities", ['Commodity', 'Name'])
input_schema.add_foreign_key("inflow", "nodes", ['Node', 'Name'])

# Define the data types
input_schema.set_data_type("commodities", "Volume", min=0, max=float("inf"),
                           inclusive_min=False, inclusive_max=False)
input_schema.set_data_type("arcs", "Capacity", min=0, max=float("inf"),
                           inclusive_min=True, inclusive_max=True)
input_schema.set_data_type("cost", "Cost", min=0, max=float("inf"),
                           inclusive_min=True, inclusive_max=False)
input_schema.set_data_type("inflow", "Quantity", min=-float("inf"), max=float("inf"),
                           inclusive_min=False, inclusive_max=False)

# The default-default of zero makes sense everywhere except for Capacity
input_schema.set_default_value("arcs", "Capacity", float("inf"))
# ---------------------------------------------------------------------------------

# ------------------------ define the output schema -------------------------------
solution_schema = TicDatFactory(
        flow=[["Commodity", "Source", "Destination"], ["Quantity"]],
        parameters=[["Parameter"], ["Value"]])
# ---------------------------------------------------------------------------------

# ------------------------ solving section-----------------------------------------
def solve(dat):
    """
    core solving routine
    :param dat: a good ticdat for the input_schema
    :return: a good ticdat for the solution_schema, or None
    """
    assert input_schema.good_tic_dat_object(dat), "bad dat check"
    assert not input_schema.find_foreign_key_failures(dat), "foreign key check"
    assert not input_schema.find_data_type_failures(dat), "data type value check"

    mdl = gu.Model("netflow")

    flow = {(h, i, j): mdl.addVar(name=f"flow_{h}_{i}_{j}") for h, i, j in dat.cost}

    flowslice = Slicer(flow)

    # Arc Capacity constraints
    for i,j in dat.arcs:
        mdl.addConstr(gu.quicksum(flow[_h, _i, _j] * dat.commodities[_h]["Volume"]
                                  for _h, _i, _j in flowslice.slice('*', i, j))
                      <= dat.arcs[i,j]["Capacity"],
                      name=f"cap_{i}_{j}")

    # Flow conservation constraints. Constraints are generated only for relevant pairs.
    # So we generate a conservation of flow constraint if there is negative or positive inflow
    # quantity, or at least one inbound flow variable, or at least one outbound flow variable.
    for h,j in set((h, i) for (h, i), v in dat.inflow.items() if abs(v["Quantity"]) > 0)\
               .union({(h, i) for h, i, j in flow}, {(h, j) for h, i, j in flow}):
        mdl.addConstr(
            gu.quicksum(flow[h_i_j] for h_i_j in flowslice.slice(h, '*', j)) +
            dat.inflow.get((h, j), {"Quantity":0})["Quantity"] ==
            gu.quicksum(flow[h_j_i] for h_j_i in flowslice.slice(h, j, '*')),
            name=f"node_{h}_{j}")

    mdl.setObjective(gu.quicksum(flow * dat.cost[h, i, j]["Cost"]
                                 for (h, i, j), flow in flow.items()),
                     sense=gu.GRB.MINIMIZE)
    mdl.optimize()

    if mdl.status == gu.GRB.OPTIMAL:
        rtn = solution_schema.TicDat()
        for (h, i, j), var in flow.items():
            if var.x > 0:
                rtn.flow[h, i, j] = var.x
        rtn.parameters["Total Cost"] = sum(dat.cost[h, i, j]["Cost"] * r["Quantity"]
                                           for (h, i, j), r in rtn.flow.items())
        return rtn
# ---------------------------------------------------------------------------------

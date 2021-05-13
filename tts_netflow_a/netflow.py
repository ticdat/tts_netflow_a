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
input_schema.add_foreign_key("cost", "nodes", ['Source', 'Name'])
input_schema.add_foreign_key("cost", "nodes", ['Destination', 'Name'])
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
    assert input_schema.good_tic_dat_object(dat)
    assert not input_schema.find_foreign_key_failures(dat)
    assert not input_schema.find_data_type_failures(dat)

    mdl = gu.Model("netflow")

    flow = {(i, j): mdl.addVar(name=f"flow_{i}_{j}", ub=r["Capacity"])
            for (i, j), r in dat.arcs.items()}

    flowslice = Slicer(flow)

    # Flow conservation constraints. Constraint is generated for each node.
    for j, r in dat.nodes.items():
        mdl.addConstr(
            gu.quicksum(flow[i_j] for i_j in flowslice.slice('*', j)) + r["Inflow"]
            == gu.quicksum(flow[j_i] for j_i in flowslice.slice(j, '*')),
            name= f"node_{j}")

    mdl.setObjective(gu.quicksum(flow * dat.arcs[i, j]["Cost"] for (i, j), flow in flow.items()),
                     sense=gu.GRB.MINIMIZE)
    mdl.optimize()

    if mdl.status == gu.GRB.OPTIMAL:
        rtn = solution_schema.TicDat()
        for (i, j), var in flow.items():
            if var.x > 0:
                rtn.flow[i, j] = var.x
        rtn.parameters["Total Cost"] = sum(dat.arcs[i, j]["Cost"] * r["Quantity"]
                                           for (i, j), r in rtn.flow.items())
        return rtn

# ---------------------------------------------------------------------------------

#
# Core engine file for tts_netflow_a
#

try: # if you don't have gurobipy installed, the code will still load and then fail on solve
    import gurobipy as gu
except:
    gu = None
from ticdat import TicDatFactory

# ------------------------ define the input schema --------------------------------
input_schema = TicDatFactory (
    nodes=[["Name"], ["Inflow"]],
    arcs= [["Source", "Destination"], ["Cost", "Capacity"]],
)

# Define the foreign key relationships
input_schema.add_foreign_key("arcs", "nodes", ['Source', 'Name'])
input_schema.add_foreign_key("arcs", "nodes", ['Destination', 'Name'])

# Define the data types
input_schema.set_data_type("arcs", "Capacity", min=0, max=float("inf"),
                           inclusive_min=True, inclusive_max=True)
input_schema.set_data_type("arcs", "Cost", min=0, max=float("inf"),
                           inclusive_min=True, inclusive_max=False)
input_schema.set_data_type("nodes", "Inflow", min=-float("inf"), max=float("inf"),
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
# ---------------------------------------------------------------------------------

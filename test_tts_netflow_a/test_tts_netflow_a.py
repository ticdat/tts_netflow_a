import os
import inspect
import tts_netflow_a
import unittest
import collections

def _this_directory() :
    return os.path.dirname(os.path.realpath(os.path.abspath(inspect.getsourcefile(_this_directory))))

def get_test_data(data_set_name):
    path = os.path.join(_this_directory(), "data", data_set_name)
    assert os.path.exists(path), f"bad path {path}"
    # right now assumes data is archived as a single json file for each data set
    if os.path.isfile(path):
        return tts_netflow_a.input_schema.json.create_tic_dat(path)

def _nearly_same(x, y, epsilon=1e-5):
    if x == y or max(abs(x), abs(y)) < epsilon:
        return True
    if min(abs(x), abs(y)) > epsilon:
        return abs(x-y) /  min(abs(x), abs(y)) < epsilon

class TestNetflow(unittest.TestCase):
    def test_netflow_flows_figure_5(self):
        # Pulled from here https://bit.ly/3uLt01I (originally from Ahuja, Magnanti, and Orlin book 1993)
        dat = get_test_data("netflow_flows_figure_5.json")
        sln = tts_netflow_a.solve(dat)
        # Objective = 270 can be read directly from https://bit.ly/3uLt01I
        self.assertTrue(_nearly_same(270, sln.parameters["Total Cost"]["Value"]))

    def test_standard_data_set(self):
        dat = get_test_data("sample_data.json")
        sln = tts_netflow_a.solve(dat)
        self.assertTrue(_nearly_same(5500.0, sln.parameters["Total Cost"]["Value"], epsilon=1e-4))

    def test_sloan_data_set(self):
        # This data set was pulled from this MIT Sloan School of Management example problem here https://bit.ly/3254VpT
        dat = get_test_data("sloan_data_set.json")
        sln = tts_netflow_a.solve(dat)
        self.assertTrue({k: v["Quantity"] for k,v in sln.flow.items()} ==
            {(2, 3, 2): 2.0,
             (2, 2, 5): 2.0,
             (2, 5, 6): 2.0,
             (1, 1, 2): 3.0,
             (1, 2, 5): 3.0,
             (1, 5, 4): 3.0,
             (1, 1, 4): 2.0})

    def test_issue_2(self):
        # I see no problem in refering to GitHub issue numbers in code. Saves a lot of typing.
        dat = get_test_data("sample_data.json")
        sln = tts_netflow_a.solve(dat)
        arc_flows = collections.defaultdict(float)
        for k, v in sln.flow.items():
            arc_flows[k[1:]] += v["Quantity"]
        # remove the least import arc record from the input data
        dat.arcs.pop(sorted(arc_flows, key=lambda x: arc_flows[x])[0])
        # if cost is a compound FK into arcs, then there should now be FK failures
        ex = []
        try:
            tts_netflow_a.solve(dat)
        except AssertionError as e: # safe to assume unit tests aren't run with asserts disabled
            ex.append(e)
        self.assertTrue(ex and 'foreign key check' == ex[0])

# Run the tests via the command line
if __name__ == "__main__":
    unittest.main()
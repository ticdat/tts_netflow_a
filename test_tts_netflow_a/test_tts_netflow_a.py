import os
import inspect
import tts_netflow_a
import unittest

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

def _smaller(x, y, epsilon=1e-5):
    return x < y and not _nearly_same(x, y, epsilon)

class TestNetflow(unittest.TestCase):
    pass

# Run the tests via the command line
if __name__ == "__main__":
    unittest.main()
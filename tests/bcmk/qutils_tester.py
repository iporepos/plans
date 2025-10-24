import inspect
from pathlib import Path
from pprint import pprint

import importlib.util as iu

here = Path(__file__).resolve()
FOLDER_ROOT = here.parent.parent.parent
DATA_DIR = FOLDER_ROOT / "tests/data/biboca/data"

# define the paths to this module
# ----------------------------------------
the_module = f"{FOLDER_ROOT}/src/plans/qutils.py"

# setup module with importlib
# ----------------------------------------
spec = iu.spec_from_file_location("module", the_module)
module = iu.module_from_spec(spec)
spec.loader.exec_module(module)


def test_get_extent_from_raster():
    func_name = inspect.currentframe().f_code.co_name
    src_func_name = func_name.replace("test_", "")
    print(f"\n\ntest: qutils.{func_name}()")
    # setup inputs and outputs
    # ----------------------------------------
    file_input = f"{DATA_DIR}/topo/ldd.tif"

    # call the function
    # ----------------------------------------
    output = module.get_extent_from_raster(file_input)

    print("Output:")
    pprint(output)

    # Assertions
    # ----------------------------------------
    try:
        assert isinstance(output, dict)
        print("test passed")
    except AssertionError:
        print("test failed")


def test_get_extent_from_vector():
    func_name = inspect.currentframe().f_code.co_name
    src_func_name = func_name.replace("test_", "")
    print(f"\n\ntest: qutils.{func_name}()")
    # define input and outputs
    # ----------------------------------------
    input_db = f"{DATA_DIR}/biboca.gpkg"
    layer_name = "roads"

    # call the function
    # ----------------------------------------
    output = module.get_extent_from_vector(input_db=input_db, layer_name=layer_name)

    print("Output:")
    pprint(output)

    # Assertions
    # ----------------------------------------
    try:
        assert isinstance(output, dict)
        print("test passed")
    except AssertionError:
        print("test failed")


def test_count_vector_features():
    func_name = inspect.currentframe().f_code.co_name
    src_func_name = func_name.replace("test_", "")
    print(f"\n\ntest: qutils.{func_name}()")

    # define input and outputs
    # ----------------------------------------
    input_db = f"{DATA_DIR}/biboca.gpkg"
    layer_name = "roads"

    # call the function
    # ----------------------------------------
    output = module.count_vector_features(input_db=input_db, layer_name=layer_name)

    print("Output:")
    pprint(output)

    # Assertions
    # ----------------------------------------
    try:
        assert isinstance(output, int)
        print("test passed")
    except AssertionError:
        print("test failed")


# ... {develop}


# SCRIPT
# ***********************************************************************
# standalone behaviour as a script

test_get_extent_from_raster()
test_get_extent_from_vector()
test_count_vector_features()

# ... {develop}

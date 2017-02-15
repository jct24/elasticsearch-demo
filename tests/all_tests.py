import os
import sys

os.environ['TESTING'] = "true"

here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(here, "../"))
sys.path.append(os.path.join(here, "../sys_packages"))

# Import tests
from integration_tests import *
from unit_tests import *

import os
import sys
where_i_am = os.path.dirname(os.path.realpath(__file__))
sys.path.append(where_i_am + "/dependencies")
sys.path.append(where_i_am + "../expand_term")

from CST_utils.ApplyTolerances.AT import start_tolerance_app
from CompoST import CompositeStandard as cs

path = "D:\\CAD_library_sampling\\CompoST_examples\\097_example"
file = "x_test_142_layup"
D = cs.Open(file,path)
start_tolerance_app(D, file,path=path)
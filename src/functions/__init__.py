from . import *

functions = {
    name[4:]: function
    for name, function in locals().items()
    if name.startswith('cmd_')
}

import os
import inspect
import pkgutil
import importlib



# Gather names of all modules
current_dir = os.path.dirname(__file__)
module_infos = pkgutil.iter_modules([current_dir])
module_names = [module_name for _, module_name, _ in module_infos]
functions = {}
for module_name in module_names:
    # do relative import of module
    module = importlib.import_module('.' + module_name, __name__)
    # Scan all imported names for a subclass of Domino
    for object_name in dir(module):
        obj = getattr(module, object_name)
        if inspect.isfunction(obj):
            if object_name.startswith('cmd_'):
                name = object_name[4:]
                functions[name] = obj

__ALL__ = ['functions']

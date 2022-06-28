import sys
import pkgutil
import importlib
import subprocess

exit_code = 0

packages = ['unified_planning']
while len(packages) > 0:
    package_name = packages.pop()
    return_code = subprocess.call(f'python3 -c "import {package_name}"', shell=True, stderr=subprocess.DEVNULL)
    if return_code != 0:
        exit_code = 1
    print(f'Test import {package_name}: {"DONE" if return_code == 0 else "FAIL"}')
    package = importlib.import_module(package_name)
    for _, modname, ispkg in pkgutil.iter_modules(package.__path__):
        if ispkg:
            packages.append(f'{package_name}.{modname}')

sys.exit(exit_code)

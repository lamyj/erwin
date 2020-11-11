import importlib
import sys

def main():
    module_name = sys.argv[1]
    if module_name.endswith(".py"):
        module_name = module_name[:-3]
    module_name = module_name.strip(".")
    module = importlib.import_module(
        "{}.{}".format(sys.modules[__name__].__package__, module_name))
    
    arguments = sys.argv[1:]
    arguments[0] = "{} {}".format(sys.argv[0], sys.argv[1])
    sys.argv = arguments
    module.main()

if __name__ == "__main__":
    sys.exit(main())

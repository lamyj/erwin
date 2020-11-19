import subprocess

def execute(action):
    if isinstance(action, list):
        subprocess.check_call(action)
    elif isinstance(action, tuple):
        action[0](*action[1])

from . import b0_map, b1_map, diffusion, mt_map, t1_map, t2_map

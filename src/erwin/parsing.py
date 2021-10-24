import argparse

def add_argument(parser, specification):
    names = specification[:-1]
    kwargs = specification[-1]
    kwargs.setdefault("required", True)
    parser.add_argument(*names, **kwargs)

def Optional(specification):
    return [*specification[:-1], {**specification[-1], "required": False}]
def Multiple(specification, nargs="+"):
    return [*specification[:-1], {**specification[-1], "nargs": nargs}]

ImagingFrequency = [
    "--imaging-frequency",
    {"type": float, "help": "Frequency of the scanner (MHz)"}]

FlipAngle = ["--flip-angle", {"type": float, "help": "Flip angle (°)"}]
FlipAngles = Multiple(["--flip-angles", *FlipAngle[1:]])

EchoTime = ["--echo-time", "--te", {"type": float, "help": "Echo time (ms)"}]
EchoTimes = Multiple(["--echo-times", *EchoTime[1:]])

InversionTime = [
    "--inversion-time", "--ti", {"type": float, "help": "Inversion time (ms)"}]
InversionTimes = Multiple(["--inversion-times", *InversionTime[1:]])

RepetitionTime = [
    "--repetition-time", "--tr",
    {"type": float, "help": "Repetition time (ms)"}]

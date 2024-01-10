from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("Refter Client")
except PackageNotFoundError:
    __version__ = "(local)"

del PackageNotFoundError
del version

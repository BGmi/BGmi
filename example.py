from typing import Callable

callable = lambda c: isinstance(c, Callable)
print(callable(0))

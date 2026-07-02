Generally in the code in this repository, which is a kind of database engine, we never wanna have database variables, such as actual columns names, e.g. of our main testing dataset SBB flat, hardcoded in any code!
Keep it flexible! in unit tests of couse its fine!

During development, do NOT run the optimization agent loop. Write and test queries directly (see `research_loop/benchmark_verified.py`). Use `NativeU32`/`NativeU64`/`NativeI64` extern newtypes from the transpiler — do not rely on unsafe postprocessor type rewrites.


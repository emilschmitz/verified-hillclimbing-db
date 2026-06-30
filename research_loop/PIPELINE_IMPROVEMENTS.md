The reason that we made postprocessor.py is that the compiled dafny code was very inefficient.

The issue with postprocessor.py is that it makes the resulting code unverified.

The tests show that this is practically possible.

The agent will get access to postprocessor.py so the worst case is that the agent sees the postprocessor.py, makes something that passes dafny and runs very fast after postprocessor, but is semantically divergent from the spec and, most importantly, sql query intent.This is because fast runtime and passing dafny is the agents only incentives.

Also, we can make the Dafny code faster by using bv64, but that leads to unacceptable verification times.

Assessing that possiblity is one important thing to do!

## So how do we fix this situation and make the pipeline sound?

* The first line of defense agains inefficiency is the dafny optimizer agent. We must operate under the assumption that the agent produces perfect dafny code and only help

* The postprocessor file should be minimal. We only want optimizations that are highly effecti

We want to remove as much as possible from the postprocessor.py. For each replacement in postprocessor.py, especially the brittle stuff, we do the following checks to see if we can compeletely replace and remove the operation.

For every problem that the verification script is solving, we should try to resolve it with these tools, preferring always those higher up this list, so we do not break verification.

* Make sure the agent has sufficient context about how to write code that will compile to efficient rust that verifies in dafny in an acceptable time-frame. It needs information about dafny verification speed, dafny -> rust compilation and the code of postprocessor.py. It should have a comperehensive resource about dafny -> rust, but the most important observations we can put in a .md file and give it to it. Always make sure that the agent can load things by itself into context and the things are not just dumped in there causing bloat. We could consider making a skill with appropraite links and content, abiding by ssot as much as possible. This solution does not damage verification at all and should be easy to implement. It is the absolute first line of defense. The agent should learn to write code that will be efficient with whatever the state of the lemmata and the postprocessing.py is so that we don't have to patch those with a bunch of stuff.
    * remember that running the agent during development is slow and expensive. We wanna primarily make sure it just has all the information it could possibly desire available somehow and clear instructions.
    * Alternatively, make sure that the agent does not have any access to postprocess.py so that we avoid it accidentally breaking it to improve performance. In that case also consider giving the agent only the performance numbers for the direct dafny code it wrote and only run postprocessing once the agent is done. This is an alternative apporoach to avoid agent ingenuity in "reward hacking".

* Use low-level stuff bv64, but add conditions or some lemmata that we can use to manipulate prove things and avoid verification performance issues like bit blasting. E.g. b1 + b2 == (b1 as int) + (b2 as int) as bv64 iff (b1 as int) + (b2 as int) < 2 ** 64 (or whatever, you get the gist). This does not damage verification at all. If it works, and has acceptable performance characteristics, we can use it extensively where the agent fails. The agent can also get information about how and when to write lemmas, but ideally we would have any lemma available, well documented, so that the agent can just use it.

* Use assume statements that are not formally verified if the statement is obviously true, useful to have and the lemma would be either practically impossible to prove or induce significant overhead, like +10sec or more extra verification overhead.

* Restrict the not-formally-verified logic in postprocessor.py to an absolute minimum, without sacrificing maximum ~50% of performance. Try to keep operations
    1. Few, ideally none
    2. Ideally, compeletely verifiable, e.g. we dafny-require that the output is bounded and we switch only the output to bv64
    3. Well testable and tested
    4. Predictable and simple. With complex regexes, it is hard to predict what will happen.
    5. Such that failures cause compilation errors, not semantic divergence.

The bottom line is that we want to avoid risk of semantic divergence as much as possible while keeping performance of the query as fast as before (or slightly slower) and verification under ~30 sec. We put an absolute cap at 45sec. The best way of avoiding divergence is formal verification, the second best (but still considerably worse) way is by keeping the failable system simple and well-tested.

The way to work on this is to make a few, or ideally only one, examples where the postprocessing through one specific type of optimization (e.g. chaing to native u64 type) had a high performance impact. Ideally we'll profile it, e.g. with timer and print statements to see how every change affects the performance. Then we try to optimize the dafny code as much as we can, e.g. with lemmata, or by just writing it well so it stays close to the machine and try to get as close as possible to the postprocessed version. What we notice that we can delete with minimal impact, we then delete. 
Then we restart that with the next type of optimization.

IMPORTANT: any divergence from complete formal deterministic verification of the pipeline output must be well documented.

# Troubleshooting `dotmotif.Neo4jExecutor`

The Neo4j executor has a lot of moving parts, so here are some frequently encountered issues and how to solve them.

## Best-Practices

### Memory Management

Memory variables should almost always be set explicitly; `Neo4jExecutor`s cannot currently "guess" how much memory you want it to use.

- `max_memory`: How much RAM to use (maximum). Suggested value is "XG", where X is the integer number of gigabytes of RAM your machine has, minus a bit. (So for a 128GB machine, `120G` seems like a good start.)
- `initial_memory`: How big the JVM stack should be to start. (You can generally ignore this if you don't know what it means.)

<details>
<summary>Important Warnings</summary>
When creating a new Executor, specify `max_memory` and `initial_memory` so that the Executor can expand to fill the available space. But...a few warnings! **If you set `max_memory` too high, your container will silently fail (as the container will try to allocate too much memory, and then do whatever it is that the JVM does instead of segfaulting noisily).

`initial_memory` should be set high enough that the JVM doesn't have to reprovision memory too many times; but be aware that this amount of memory will be _unavailable_ to the rest of your system while the executor is alive.
</details>

## Errors when starting a new Executor

<ul>
<li>
<details>
<summary><b>I get a warning that "host port 7474 is already in use."</b></summary>

You may already have a running Neo4jExecutor or Neo4j database container which is using the 7474 port. Check with `docker ps`.
</details>
</li>
<li>
<details>
<summary><b>The executor waits for a long time, and then tells me it failed to reach the Neo4j server.</b></summary>

This means that the executor tried to create a new docker container, but was unable to reach it.
</details>
</li>
</ul>

## Errors with executor responses

<ul>
<li>
<details>
<summary><b>After I run <code>Executor.find</code>, the result list is empty! But I know that my graph contains that motif!</b></summary>

The .find() returns a _cursor_ to your results, not your results themselves. Please consider the following:

```python

E = Neo4jExecutor(...)

results = E.find(motif)
A = results.to_table()
B = results.to_table()
```

`A` will contain all of your results; `B` will be EMPTY, since you already "used up" your results in the first call to `to_table`. You can learn more about cursors [here](https://py2neo.org/v4/database.html#cursor-objects). Once you have assigned these values to `A`, you can reuse them as many times as you like.

Common Follow-up Question: _WHYYY DO YOU DO THIS_

In some cases, you may receive too many results to easily process (many gigabytes of results). In these cases, you will want to 'stream' the results instead of getting a list of all of them. Here, `next(results)` is your friend!

If you prefer that the executor return a nicely parsed table of results, you can pass `cursor=False` to `find`. You will then get back a Python data structure instead of a cursor.


</details>
</li>
<li>
<details>
<summary><b>The executor waits for a long time, and then tells me it failed to reach the Neo4j server.</b></summary>

This means that the executor tried to create a new docker container, but was unable to reach it. Make sure you have Docker installed, that you have a Neo4j image either local or reachable over the net, and that your Docker container can be accessed by the current user. Once you have run DotMotif for the first time (or have installed the Neo4j image manually), it will run entirely offline in subsequent runs.
</details>
</li>
</ul>

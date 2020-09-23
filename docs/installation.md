# Installation

You can either install the latest stable version of DotMotif with:

```shell
pip install dotmotif
```

...or you can clone this repository and install from source:

```shell
git clone https://https://github.com/aplbrain/dotmotif/
cd dotmotif
pip3 install -U .
```

## Installing container support for `Neo4jExecutor`

If you expect to use the `Neo4jExecutor` to search for motifs in a large graph, you will need to either have a running Neo4j instance that you can point to, **or you can let DotMotif provision and manage your databases for you.** While this second option is easier (and definitely preferable for most non-production experiments), you will need to make sure that [Docker has been installed on your computer](https://docs.docker.com/install/), and you'll also probably want to make sure that you've already got [a Neo4j Docker image](https://hub.docker.com/_/neo4j).

### Installing Docker

The official Docker documentation has the most up-to-date instructions for installing Docker. Access them [here](https://docs.docker.com/install/). You can check if you have `docker` on your system by typing `docker -v` into your favorite command-line.

> NOTE: Windows users might want to make sure their Docker install is configured to use Linux containers for best results.

### Downloading the Neo4j Docker Image

While this step is optional, you'll likely get a faster first-use of DotMotif if you pre-install a Neo4j Docker image. (Beginner users can skip this, **but be aware that you may get a cryptic timeout error the first time you run a query.**)

To install a Neo4j image, type the following in your favorite shell:

```bash
docker pull neo4j:3.4
```

DotMotif uses [Tamarind](https://github.com/fitmango/tamarind) to provision and manage Neo4j containers. Check [this code](https://github.com/FitMango/tamarind/blob/master/tamarind/__init__.py#L158) for the exact version in use by Tamarind, which we intend to pin and mirror in the DotMotif codebase in the future.

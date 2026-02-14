# Development

This section provides guidance for those who wish to contribute to the project.
It includes instructions for setting up the development environment, cloning the 
repository, installing the project in development mode, running tests, 
and building the documentation.

 To ensure that new features and changes adhere to project standards, 
 maintain quality, and keep the documentation up to date, 
 contributors are required to follow:

* Style-consistent formatting;
* Documentation-oriented practices;
* Test-driven development;


## Minimal Workflow

This is a quick guide for a development protocol. 
Hence, some important but obvious steps are ommited. 
See more details in the sections below.

### Setup

1. Clone the repository to a local branch;

```bash
git clone https://github.com/iporepos/plans.git
``` 

2. Install dependencies in dev mode:

```bash
python -m pip install -e .[dev,docs]
```

### Development loop

3. Develop features under the ``./src/plans/`` folder;
4. Develop unit tests for the features under ``./tests/unit`` or ``./tests/bcmk``;
5. Document features directly using docstrings;
6. Document features in the API by editing ``./docs/api.rst`` file;
7. If ready, proceed to checkout. Repeat otherwise.

### Checkout

8. Apply style:

```bash
python -m dev.style
```

9. Build docs (locally):

```bash
python -m dev.docs --open
```

10. If previous passed, run all CI-based tests:

```bash
python -m dev.tests
```

12. If previous step passed, stage and commit;

```bash
git add .
git commit -m "Message"
```
15. If appropriate, tag and publish.

```bash
git tag -a vX.Y.Z -m "Release X.Y.Z (message)"
git push origin main
git push origin --tags
```

## Cloning

Use your IDE for authenticate in GitHub and clone the repo branch of interest
in your local system.

```{note}
Of course, Git must be set as the version control system
```

Alternatively, clone via terminal:

```bash
git clone https://github.com/iporepos/plans.git
``` 

## Installing as a developer

For developing, it's recommended to set up a python
**Virtual Environment** (`venv`) locally for developing the repo.
This is best for avoiding falling into a [dependency hell](https://en.wikipedia.org/wiki/Dependency_hell) with your
other projects.

```{important}
Of course, you need Python installed in your system
```

Move to the repo root folder:

```bash
cd ./path/to/plans
```

Create a python `venv`:

```bash
python -m venv .venv
```

Activate the `venv` session. On Unix (Linux/Mac):

```bash
source .venv/bin/activate
```
Activate the `venv` on Windows:

```bash
. .venv\Scripts\Activate.ps1
```

Now, under the `venv` session, install all
dependencies in editable mode `-e` (including `dev` and `docs` dependencies with `.[dev, docs]`):

```bash
python -m pip install -e .[dev,docs]
```
This will install all dependecies needed both for
developing and documentation.

---

## Versioning

Versioning system of the project is based on ``git`` and the remote 
is hosted in ``github``. 


### Versioning cycle

Before and after a development session, a health practice is to run:

```bash
git status
```
Considering the status output, add all changed files to the staging area:

```bash
git add .
```
After some substantial development, consider commit 
the changes to the local git system:

```bash
git commit -m "Commit message (eg, 'Bug Fixes')"
```
Repeat the cycle until if feels ready to publish to the remote host.

### Publishing

Before publishing, a health practice is to check the tags available:

```bash
git tag
```
Considering the output, decide a new tag and add it:

```bash
git tag -a vX.Y.Z -m "Release X.Y.Z (message)"
```

After tagging, publish explicitly:

```bash
git push origin main
```
Or simply:
```bash
git push
```
Then append the tags
```bash
git push origin --tags
```

### Tags convention

This project tags follows Semantic Versioning (`vMAJOR.MINOR.PATCH`) 
with the interpretations below.

#### Major `vX.y.z` — Project Maturity Level

- **v0.x.x — Experimental**
  - Playground for exploring architecture and project layout.
  - Breaking changes are expected.

- **v1.x.x — Stable Foundation**
  - Production-ready core architecture.
  - Actively developed.
  - Backward compatibility is expected.

- **v2.x.x — Next Generation**
  - May introduce new syntax or paradigms.
  - Can be incompatible with `v1.x.x`.
  - More mature, better documented, and more stable.

#### Minor `vx.Y.z` — Milestones

- Major feature additions.
- Large refactors within the same architecture.
- Treated as logical restore points.

#### Patch `vx.y.Z` — Maintenance

- Bug fixes.
- Small improvements.
- Documentation corrections.
- No behavioral changes.

### Releases

Releases may receive human-readable names.
Suggested names are South-America rivers, aquifers of other hydrological landscape features.

* Amazon
* Solimões
* Paraná
* São Francisco
* Madeira
* Tapajós
* Xingu
* Capibaripe
* Itacurubi
* Tocantins
* Negro
* Casiquiare
* Uruguay
* Orinoco
* Magdalena
* Essequibo
* Guarany
* Urucuya
* Pantanal
* Iberás
* Iguazu
* Chiquita
* Titicaca
* Patos
* Atacama
* Guahyba
* Taquary
* Jacuhy
* Ibicuhy
* Camaquã
* Itajay
* Capivary
* Paranoa
* Jequitinhonha
* Taramandahy
* Gravatahy
* Piratiny
* Paranapanema
* Parnahyba
* Maracaibo
* Uyuni
* Ucayali


---

## Packaging

This project relies on the PyPI platform for package distribution. 

### First-time distribution workflow

As a first time distribution, manual workflow is recommended.

1. Register and save API tokens from https://pypi.org/ and https://test.pypi.org. 
2. Install packaging utilities:

For building the distribution:
```bash
python -m pip install build
```
For uploading to PyPI
```bash
python -m pip install twine
```
3. Build distro

Cleanup first
```powershell
Remove-Item -Recurse -Force dist, build, *.egg-info
```
Run the build command
```bash
python -m build
```
Output:

```
dist/
  yourpkg-0.1.0.tar.gz
  yourpkg-0.1.0-py3-none-any.whl
```
> these are the packages in the repo. This folder is ignored by git.

4. Validade build
```bash
twine check dist/*
```
5. Publish on TestPyPI
```bash
twine upload --repository testpypi dist/*
```
```{warning}
Use the token from TestPyPI
```
6. Check test package under a clear environment

```bash
python -m pip install --index-url https://test.pypi.org/simple --extra-index-url https://pypi.org/simple <yourpkg>==Z.Y.X
```

7. Publish on PyPI:
```bash
twine upload dist/*
```

8. Check package installation in a clear environment
```bash
python -m pip install <yourpkg>
```

### Continous distribution

An automated system is set for continous distribution via GitHub Actions.
The workflow file lives in ``.github/workflows/dist.yaml`` and 
is only triggered by a new tag being pushed.

```{warning}
To work properly, the API token for PyPI must be included in GitHub 
repository secrets as PYPI_API_TOKEN.
```

---

## Style

In this project, we enforce using [Black](https://black.readthedocs.io) to ensure a consistent code style. 

Since `black` is listed in dev dependencies, you may run manually before push:

```bash
black .
```
> from the repo root, under the venv session

The built-in wrapper is:
```bash
python -m dev.style
```

```{warning}
Unformatted contributions are not going to pass because GitHub checks for style consistency.
```

---

## Documentation

Documentation-oriented development is recommended. Every feature must be documented with standard Sphinx (rST) format.

### Build locally

Use Sphinx for building the documentation website locally. Run this via terminal:

```bash
sphinx-build -b html .\docs .\docs\_build --write-all
```

The built-in wrapper is:

```bash
python -m dev.docs --open
```

```{important}
Build documentation under a virtual environment session.
```

```{note}
The docs website is generated under ``docs/_build``
```

## Testing

Test-driven development is recommended. Tests are split into the following categories:

  * **Unit tests** - short and targeting feature behavior.
  * **Benchmark tests** - may take longer time, targeting full performance, includes inputs and outputs evaluations.
  * **Example tests** - single line tests presented in docstrings.

```{important}
Run tests under a virtual environment session.
```

### Unit tests

Run all unit tests in ``/tests`` via terminal:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

For a single unit test module:

```bash
python -m tests.unit.test_module
```

The built-in wrapper is:

```bash
python -m dev.tests
```
Variations include:

```bash
python -m dev.tests --which "unit"
```
For benchmarks (run this locally)
```bash
python -m dev.tests --which "bcmk"
```
For all tests:
For benchmarks (run this locally)
```bash
python -m dev.tests --all
```

```{seealso}
See more in [unittest library](https://docs.python.org/3/library/doctest.html) for details on unit tests.
```

```{note}
Example tests can be included in unit tests with their own testing script.
A template for this is provided in ``/tests/test_doctest.py``.
```

### Benchmark tests

Benchmark tests are unit tests related to full-integration of features, 
sometimes associated with input and output data. Some benchmark tests 
will install heavy datasets from provided URLs.

#### Enable benchmark tests

For running benchmark tests, they must be enabled. This is 
because benchmarks may take too long and can deplete resources for CI services. 
Once enabled, just run the unit tests as usual.

Enabling benchmarks on Unix:

```bash
RUN_BENCHMARKS=1
```

Enabling benchmarks on Windows:

```bash
$env:RUN_BENCHMARKS="1"
```

#### Enable large benchmark tests

Large benchmark tests are exceptionally large tests. The same logic applies:

Enabling large benchmark tests on Unix:

```bash
RUN_BENCHMARKS_XXL=1
```

Enabling large benchmark tests on Windows:

```bash
$env:RUN_BENCHMARKS_XXL="1"
```

### Example tests

Create single-line example tests in docstring:

```python
def add(num1, num2):
	"""
	
	**Examples**
	
	>>> add(1, 2)
	3
		
	"""
	return num1 + num2
```

Test the module using ``doctest``:
```bash
python -m doctest -v /path/to/module.py
```

Alternatively, test the module in the script part:
```python
if __name__ == "__main__":
    import doctest
    doctest.testmod()
```

```{seealso}
See more in [doctest library](https://docs.python.org/3/library/doctest.html) for details on example tests.
```

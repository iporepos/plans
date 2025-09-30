# Development

This section provides guidance for those who wish to contribute to the project.
It includes instructions for setting up the development environment, cloning the repository, installing the project in development mode, running tests, and building the documentation.

 To ensure that new features and changes adhere to project standards, maintain quality, and keep the documentation up to date, contributors are required to follow:

* Style-consistent formatting;
* Documentation-oriented practices;
* Test-driven development;


## Cloning

Use your IDE for authenticate in GitHub and clone the repo branch of interest
in your local system.

```{note}
Of course, Git must be set as the version control system
```

Alternatively, clone via terminal:

```bash
# [CHECK THIS] adapt this for branches or other repos
git clone https://github.com/iporepos/plans.git
``` 

## Installing

For developing, it's recommended to set up a python
**Virtual Environment** (`venv`) locally for developing the repo.
This is best for avoiding falling into a [dependency hell](https://en.wikipedia.org/wiki/Dependency_hell) with your
other projects.

```{important}
Of course, you need Python installed in your system
```

Move to the repo root folder:


```bash
# [CHANGE THIS] set your own actual local path 
cd ./path/to/{plans}
```

Create a python `venv`:

```bash
python -m venv .venv
```

Activate the `venv` session.

On Unix (Linux/Mac):

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

## Style

In this project, we enforce using [Black](https://black.readthedocs.io) to ensure a consistent code style. 

Since `black` is listed in `dev` dependencies, you may run manually before push:

```bash
black .
```


```{warning}
Unformatted contributions are not going to pass because GitHub checks for style 
consistency.
```

```{seealso}
There are tools for automating `black` before commit. See [https://pre-commit.com/](https://pre-commit.com/)
```

---

## Documentation

Documentation-oriented development is recommended. 
Every feature must be documented with standard Sphinx rST format, like the following docstring:

```python
# a function
def func(x, y):
    """
    This is a docstring of a function.
    
    :param x: the x value
    :type x: float
    :param y: some string
    :type y: str
    :return: a formatted string
    :rtype: str
    """
    return f'{x} {y}'

```

### Build locally

Use Sphinx for building the documentation website locally. Run this via terminal:

```bash
sphinx-build -b html ./docs ./docs/_build --write-all
```

For automating tasks before and after building, consider run:

```bash
python ./docs/docs_update.py
```

```{important}
Build documentation under a virtual environment session.
```

```{note}
The docs website is generated under `docs/_build`
```


## Testing

Test-driven development is recommended. Tests are split into the following categories:

  * **Example tests** - single line tests presented in docstrings.
  * **Unit tests** - short and targeting feature behavior.
  * **Benchmark tests** - may take longer time, targeting full performance, includes inputs and outputs evaluations.

```{important}
Run tests under a virtual environment session.
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

### Unit tests

Run all unit tests in ``/tests`` via terminal:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

For a single unit test module:

```bash
python -m tests.unit.test_module
```

For a single class inside the module:

```bash
python -m unittest -v tests.unit.test_module.TestClass
```

For a single method:

```bash
python -m unittest -v tests.unit.test_module.TestClass.test_method
```

```{seealso}
See more in [unittest library](https://docs.python.org/3/library/doctest.html) for details on unit tests.
```

```{note}
Example tests can be included in unit tests with their own testing script.
A template for this is provided in ``/tests/test_doctest.py``.
```

### Benchmark tests

Benchmark tests are unit tests related to full-integration of features, sometimes associated with input and output data. Some benchmark tests will install heavy datasets from provided URLs.

#### Enable benchmark tests

For running benchmark tests, they must be enabled manually. This is because benchmarks may take too long and can deplete resources for CI services. Once enabled, just run the unit tests as usual.

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
![Style Status](https://github.com/iporepos/plans/actions/workflows/style.yaml/badge.svg)
![Docs Status](https://github.com/iporepos/copyme/actions/workflows/docs.yaml/badge.svg)
![Tests Status](https://github.com/iporepos/plans/actions/workflows/tests.yaml/badge.svg)
![Top Language](https://img.shields.io/github/languages/top/iporepos/copyme)
![Status](https://img.shields.io/badge/status-development-yellow.svg)
[![Code Style](https://img.shields.io/badge/style-black-000000.svg)](https://github.com/psf/black)
[![Documentation](https://img.shields.io/badge/docs-online-blue)](https://iporepos.github.io/plans/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17142043.svg)](https://doi.org/10.5281/zenodo.17142043)

<a logo>
<img src="https://github.com/iporepos/plans-assets/master/docs/figs/logo.png?raw=true" height="130" width="130">
</a>


---

# plans

``plans`` is a tool that helps water resources managers and engineers plan nature-based solutions for water at the hillslope scale.

It is uses a simulation model for estimating *hydrological processes* such as [surface runoff](https://en.wikipedia.org/wiki/Surface_runoff) and [infiltration](https://en.wikipedia.org/wiki/Infiltration_(hydrology)) for a given area of interest. Model outputs include simulated hydrological processes in time (tables) and space (maps). Those results then can be used by water resource managers for effectively planning the expansion of [Nature-based Solutions for Water](https://www.undp.org/publications/nature-based-solutions-water) (*e.g.*, reforestation and soil-conservation agriculture).


> [!NOTE]
> Check out the [documentation website](https://iporepos.github.io/plans/) for more info.

---

## Gallery

<a example1>
<img src="https://github.com/iporepos/plans-assets/blob/main/docs/gallery/example1.gif?raw=true">
</a>

Mapping riparian wetlands dynamics:

<a example2>
<img src="https://github.com/iporepos/plans-assets/blob/main/docs/gallery/example2.gif?raw=true">
</a>


---

# Repository

```txt
plans/
│
├── LICENSE
├── README.md                     # this file (landing page)
├── ...                           # configuration files
│
├── src/                          # source code folder
│    └── plans/                   # source code root
│         ├── analyst.py          # direct modules
│         ├── geo.py              
│         ├── help.py             
│         ├── hydro.py            
│         ├── mini.py             
│         ├── project.py          
│         ├── qutils.py           
│         ├── root.py             
│         ├── tools.py        
│         ├── cli.py 
│         ├── viewer.py
│         ├── datasets/           # package for dataset structures
│         │    ├── core.py
│         │    ├── chrono.py
│         │    └── spatial.py
│         ├── parsers/            # package for specific parsing
│         │    ├── flare.py
│         │    ├── inmet.py
│         │    ├── qgdal.py
│         │    └── snirh.py
│         └── data/               # run-time data
│              └── iofiles.csv    
│
├── tests/                        # testing code folder
├── docs/                         # documentation folder
│
└── examples/                     # learning resources 
     ├── examples_01.ipynb    
     └── examples_02.ipynb            

```

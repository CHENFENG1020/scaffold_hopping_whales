# Scaffold hopping by holistic molecular descriptors in drug design

## Preliminary steps
In order to download and run the code, ensure you have the following software on your machine: <div>
*	Anaconda (for Python 3.7): www.anaconda.com <div>
*	Git: https://www.atlassian.com/git/tutorials/install-git. 

## Getting the code
Clone the repository, as follows:
``
git clone https://github.com/grisoniFr/scaffold_hopping_whales
``
A copy of the repository will be generated on your local machine, in the dedicated GitHub folder. Move to the donwloaded repository to start using it. 

## Setting up the virtual environment
Performing all the calculations within a virtual environment is recommended. You can import the environment information (as provided in the “scaffold_hopping.yml” file) as follows:<div>
``
conda env create -f scaffold_hopping.yml
``

To use the installed packages, activate the environment:<div>
``
conda activate scaffold_hopping
``

## Use the provided Jupyter notebook
Move to the [code](/code) folder, where the Jupyter notebook file is contained, and launch Jupter Notebook, as follows:
``
jupyter notebook
``
Click on the notebook file "virtual_screening_pipeline.jpynb". There, you will find additional information on the required calculation steps.

## Use the provided Python script
Move to the [code](/code) folder, where the Python file is contained. Please make sure you have understand the process by the Jupyter notebook to under stand the output.
Then run the script with Python:
- On a system with a display:
``
python run_win.py 
``
Three file selection dialog boxes will pop up asking you to select files. Select the library file (.sdf), reference molecule file (.sdf or .txt), and settings file (.txt, optional) in that order. Example files are in the data folder.

- On a system without a display: 
``
python run.py library_file.sdf molecule_file.txt settings_file.txt
``
Then just wait for the program to finish running. The output folder is in the main folder.

# If using SMILES strings for the molecules, the mol file should be a plain text file like .txt, .out, .md instead of .sdf
# Read the settings file for more details

## How to cite
If you use this code or parts thereof, please cite the following papers:
* Grisoni F, Merk D, Consonni V, Hiss J.A, Giani Tagliabue S, Todeschini R, Schneider G. "Scaffold hopping from natural products to synthetic mimetics by holistic molecular similarity". *Communications Chemistry* **2018**, 1, 1-9. https://www.nature.com/articles/s42004-018-0043-x
* Grisoni F, Schneider G. *"Molecular scaffold hopping via holistic molecular representation"*, **2020**, *In:* Protein-Ligand Interactions and Drug Design (Eds: F. Ballante), Methods in Molecular Biology (in press).


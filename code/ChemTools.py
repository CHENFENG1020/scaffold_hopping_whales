# Contains all the necessary code to prepare the molecule:
#   - molecule sanitization (check in "import_prepare_mol" to change advanced sanitiization settings")
#   - geometry optimization (if specified by "do_geom = True"), with the specified settings

from rdkit.Chem import AllChem
from rdkit.Chem import rdmolops
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
import numpy as np
from rdkit.Chem.Draw import SimilarityMaps
import matplotlib.pyplot as plt
import matplotlib.text
import matplotlib


def prepare_mol_from_sdf(filename_in, count_num=0, pick_num=0,
                         do_geometry=True, do_charge=False,
                         property_name='_GasteigerCharge',
                         max_iter=1000, mmffvariant='MMFF94', seed=26, max_attempts=100):
    vs_library = Chem.SDMolSupplier(filename_in)
    vs_library_prepared = {}
    vs_library_wrong = {}

    cnt = 0
    cannot_use = 0
    nmol = len(vs_library)  # 库数量
    print('Total molecules in library: ' + str(nmol))

    if count_num == 0:
        count_num = nmol//10
    if pick_num == 0:
        pick_num = 10000

    if nmol >= 100000:
        should_pick = nmol//pick_num
    else:
        should_pick = 10
    print('Should pick: ' + str(should_pick))

    for mol in vs_library:
        cnt += 1

        if cnt % count_num == 0:
            print('Molecule: ' + str(cnt) + '/' + str(nmol))

        if mol is None:
            print('Moleculer ' + str(cnt) + ' cannot be read!')
            cannot_use += 1
            vs_library_wrong.update({cnt: mol})
        elif mol.GetNumAtoms() > 200:
            cannot_use += 1
            print('Molecule ' + str(cnt) + 'too big!')
            vs_library_wrong.update({cnt: mol})
        else:
            mol_opt, err = prepare_mol(mol, do_geometry, do_charge, property_name, max_iter, mmffvariant, seed, max_attempts)
            if err == 1:
                cannot_use += 1
                print('Molecule ' + str(cnt) + ' of ' + str(nmol) + ' not computed.')
                vs_library_wrong.update({cnt: mol})
            else:
                vs_library_prepared.update({cnt: mol_opt})

    print('Molecules err in library: ' + str(cannot_use))
    return vs_library_prepared, should_pick, vs_library_wrong


def prepare_mol(mol, do_geometry=True, do_charge=True, property_name='_GasteigerCharge', max_iter=1000,
                mmffvariant='MMFF94', seed=26, max_attempts=99):
    # 'mmffVariant : “MMFF94” or “MMFF94s”'
    # seeded coordinate generation, if = -1, no random seed provided
    # removes starting coordinates to ensure reproducibility
    # max attempts, to increase if issues are encountered during optimization

    if do_charge is True:
        property_name = '_GasteigerCharge'

    # options for sanitization
    san_opt = Chem.SanitizeFlags.SANITIZE_ALL ^ Chem.SanitizeFlags.SANITIZE_KEKULIZE

    # sanitization
    err = 0
    if mol is None:
        err = 1
    else:
        # sanitize
        sanitize_fail = Chem.SanitizeMol(mol, catchErrors=True, sanitizeOps=san_opt)
        if sanitize_fail:
            err = 1
            raise ValueError(sanitize_fail)

        if do_geometry is True:
            mol, err = opt_geometry(mol, max_iter, mmffvariant, seed, max_attempts)

        # calculates or assigns atom charges based on what annotated in do_charge

        if do_charge is True:
            mol, name, err = get_charge(mol, property_name, do_charge)

    if err == 1:
        print('Error in molecule pre-treatment')

    return mol, err


def opt_geometry(mol, max_iter, mmffvariant, seed, max_attempts):
    err = 0
    try:
        mol = rdmolops.AddHs(mol)
        a = AllChem.EmbedMolecule(mol, useRandomCoords=True, useBasicKnowledge=True, randomSeed=seed, clearConfs=True,
                                  maxAttempts=max_attempts)
        if a == -1:
            err = 0

        AllChem.MMFFOptimizeMolecule(mol, maxIters=max_iter, mmffVariant=mmffvariant)
        mol = rdmolops.RemoveHs(mol)
    except ValueError:
        err = 1
    except TypeError:
        err = 1

    return mol, err


def get_charge(mol, property_name, do_charge):
    err = 0

    # partial charges
    if do_charge is False:
        err = check_mol(mol, property_name, do_charge)
        if err == 0:
            # prepares molecule
            mol = AllChem.RemoveHs(mol)
            n_at = mol.GetNumAtoms()
            # takes properties
            list_prop = mol.GetPropsAsDict()
            string_values = list_prop[property_name]  # extracts the property according to the set name
            string_values = string_values.split("\n")
            w = np.asarray(map(float, string_values))
        else:
            mol = AllChem.AddHs(mol)
            n_at = mol.GetNumAtoms()
            w = np.ones((n_at, 1)) / n_at
            w = np.asarray(map(float, w))  # same format as previous calculation
            property_name = 'equal_w'
            err = 0
        # extract properties
        for atom in range(n_at):
            mol.GetAtomWithIdx(atom).SetDoubleProp(property_name, w[atom])

        mol = AllChem.RemoveHs(mol)

    # Gasteiger-Marsili Charges
    elif (do_charge is True) and (err is 0):
        AllChem.ComputeGasteigerCharges(mol)
        err = check_mol(mol, property_name, do_charge)

    return mol, property_name, err


# ----------------------------------------------------------------------------------------------------------------------
def check_mol(mol, property_name, do_charge):
    """
    checks if the property (as specified by "property_name") is annotated and gives err = 0 if it is
    """
    n_at = mol.GetNumAtoms()
    if do_charge is False:
        list_prop = mol.GetPropsAsDict()
        string_values = list_prop[property_name]  # extracts the property according to the set name
        if string_values == '' or string_values == ['']:
            err = 1
        else:
            err = 0
    else:
        err = 0
        atom = 0
        while atom < n_at:
            value = mol.GetAtomWithIdx(atom).GetProp(property_name)
            # checks for error (-nan, inf, nan)
            if value == '-nan' or value == 'nan' or value == 'inf':
                err = 1
                break

            atom += 1

    # checks for the number of atoms
    if n_at < 4:
        err = 1

    return err


# ----------------------------------------------------------------------------------------------------------------------
def do_map(mol, fig_name=None, lab_atom=False, text=False, MapMin=0, MapMax=1):
    # settings

    scale = -1  # size of dots
    coordscale = 1  # coordinate scaling
    colmap = 'bwr'

    mol, charge, err = get_charge(mol, property_name='_GasteigerCharge', do_charge=True)
    if err == 1:
        print('Error in charge calculation')

    n_at = mol.GetNumAtoms()  # num atoms
    charge = np.zeros((n_at, 1))  # init weights
    # coordinates and property
    for atom in range(n_at):
        charge[atom] = mol.GetAtomWithIdx(atom).GetProp('_GasteigerCharge')

    opts = Chem.Draw.DrawingOptions()
    opts.clearBackground = False
    opts.bgColor = (1, 1, 1)

    fig = SimilarityMaps.GetSimilarityMapFromWeights(mol, charge, coordScale=coordscale, colorMap=colmap,
                                                     colors='w', alpha=0, scale=scale)

    # SimilarityMaps.Draw.MolDrawOptions.clearBackground ???
    if lab_atom is False:
        for elem in fig.axes[0].get_children():
            if isinstance(elem, matplotlib.text.Text):
                elem.set_visible(False)

    plt.axis("off")

    if text is True:
        import matplotlib.patheffects as PathEffects
        for at in range(mol.GetNumAtoms()):
            x = mol._atomPs[at][0]
            y = mol._atomPs[at][1]
            plt.text(x, y, '%.2f' % charge[at],
                     path_effects=[PathEffects.withStroke(linewidth=1, foreground="blue")])

    if fig_name is not None:
        return fig.savefig(fig_name, bbox_inches='tight')



def frequent_scaffolds(suppl, output_type='supplier'):
    """
     starting from a supplier file, the function computes the most frequently recurring scaffolds and returns them as a
     supplier file (if output_type='supplier') or as a counter file.
     """

    from collections import Counter
    scaff_list = []
    for mol in suppl:
        scaff_list.append(MurckoScaffold.MurckoScaffoldSmiles(mol=mol))

    freq_scaffolds = Counter()
    for scaff in scaff_list:
        freq_scaffolds[scaff] += 1

    freq_scaffolds = freq_scaffolds.most_common()

    if output_type is 'supplier':
        # converts it back in a supplier file,
        suppl_new = []
        for row in freq_scaffolds:
            mol = Chem.MolFromSmiles(row[0])
            mol.SetProp("_Name", str(round((row[1] / len(suppl)) * 100,
                                           2)) + '%')  # assigns the molecule name as the percentage occurrence
            suppl_new.append(mol)

        freq_scaffolds = suppl_new

    return freq_scaffolds

import whales
import sys
import os


def printUsage():
    print('please submit the work by:\n'
          'python run.py lib.sdf mol.sdf(mol.txt if use Smiles) setting.txt(optional)\n'
          )


if __name__ == "__main__":

    d_list = []
    if len(sys.argv) < 3:
        printUsage()
        sys.exit(1)
    else:
        for i in range(1, len(sys.argv)):
            if os.path.isfile(sys.argv[i]):
                print("Data found:", sys.argv[i])
                d_list.append(sys.argv[i])
            else:
                print("Data not found:", sys.argv[i])
                sys.exit(1)

    lib = d_list[0]
    mol = d_list[1]
    if len(d_list) == 3:
        set_file = d_list[2]
        with open(set_file) as filein:
            sets = [line.strip("\n") for line in filein]
        output_name = sets[0].split(':')[1]
        num_count = int(sets[1].split(':')[1])
        pick_num = int(sets[2].split(':')[1])
        whales.run(mol, lib, output_name, num_count, pick_num)
    else:
        whales.run(mol, lib)

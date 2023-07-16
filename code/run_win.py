from tkinter.filedialog import askopenfilename
import tkinter as tk
import whales

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    lib = askopenfilename(title='Please select library file:')
    mol = askopenfilename(title='Please select ref mol file:')
    set_file = askopenfilename(title='(Optional)Please select setting file:')
    root.destroy()
    if not set_file:
        whales.run(mol, lib)
    else:
        with open(set_file) as filein:
            sets = [line.strip("\n") for line in filein]
        output_name = sets[0].split(':')[1]
        num_count = int(sets[1].split(':')[1])
        pick_num = int(sets[2].split(':')[1])
        whales.run(mol, lib, output_name, num_count, pick_num)

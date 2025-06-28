# format-re-tools
 A file format reverser's simple tools in Python 3.

 - FileList: creates a file list
 - FindSigs: finds matching bytes for all files in a folder
 - FindRanges: shows possible values for a range of data in all files in a folder
 - FindPtrs: finds pointers referencing data, tweakable (has a sample file: look at findptrs.tst with a hex editor)
 - SigWars: finds which files in a folder have which version of a signature

The scripts have detailed explanations of what they do inside the scripts themselves. Default values apply and can be changed.
Perform `pip install tqdm` (for the nice progress bars).

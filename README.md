# GFF_Format_transformation
The functionality of the GFF.py script allows to control if the first column with the name of the chromosome is in a valid chromosome name format “chr01”, if not, other previous format is replaced by the proper one. In column 2 of the GFF3 file, the name of  type (according to sequence ontology) is appended stiffly. The columns 3,4,5 are preserved from Circos text file. The script GFF.py also gives the possibility to remove all rows with a score value in column 5 equal to zero. 
#!/bin/bash
set -eu

# resource: http://seqanswers.com/forums/showthread.php?t=4914
# Calculate length for each transcript for a GTF file
#substr($NF, length($NF)-16, 15); 

GTF=$1

awk -F"\t" ' $3=="exon" { 
	match($9, /transcript_id ([^;]+)/, arr);
	match($9, /gene_id ([^;]+)/, genes);
    ID=arr[1];
	G[ID]=genes[1];
    L[ID]+=$5-$4+1;
	print "###"; 
} 
END {
	for(i in L)
		{print G[i]"\t"i"\t"L[i]}
}' $GTF  | grep -v "###" 


sed -i -e '/gene_id/b; s|\(.*transcript_id \([^;]*\);.*\)|\1 gene_id \2;|g '

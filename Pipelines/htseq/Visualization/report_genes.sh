ROOT="/misc/pipeline42/mbelmadani/rnaseq/"
if [ $# -lt 1 ]; then
    echo "Missing arguments"
    echo "First argument should be the path to write files"
    echo "Example: ./SCRIPT /misc/pipeline42/mbelmadani/rnaseq/portable"
    exit
else
    ROOT=$1
fi


for EXPERIMENT in "bipolar" "normal"; do
    # For each sample in EXPERIMENT, output a the sum of genes counts
    cat $ROOT/$EXPERIMENT/C*/HTSeq/output.* | grep "^ENSG"  | sort | awk '{arr[$1]+=$2;} END {for (i in arr) print i, arr[i]}' | sort -r -nk 2,2 > $ROOT"reports/"totalgenes_$EXPERIMENT.count
done

# Merge files on ENSG ID
join <(sort $ROOT"reports/totalgenes_bipolar.count") <(sort $ROOT"reports/totalgenes_normal.count") > $ROOT"reports/totalgenes_merged.count"

# Sort by absolute difference
echo -e "Gene\tBipolar\tControl\tDiff" > $ROOT"reports/totalgenes_absdiff.count"
cat $ROOT"/reports/totalgenes_merged.count" | awk '{printf("%s %d %d\n", $0, ($2-$3), sqrt(($2-$3)^2)  ) }' | sort -rnk 5,5 | awk 'BEGIN { OFS = "\t" }{print $1,$2,$3,$4}' >> $ROOT"/reports/totalgenes_absdiff.count"

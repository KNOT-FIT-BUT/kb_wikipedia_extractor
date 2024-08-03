#!/bin/bash

set -o pipefail

cp -v ../HEAD-KB HEAD-KB &&
cp -v ../kb kb &&
cp -v ../VERSION VERSION &&
sed -i '$G' HEAD-KB &&
sed -i '/^$/d' HEAD-KB &&
sed -i '$G' HEAD-KB &&
mv kb kb_with_unknowns &&
cat kb_with_unknowns | grep -vP "(people|geo):unknown\t" > kb &&
python3 prepare_kb_to_stats_and_metrics.py < kb | python3 check_columns_in_kb.py --cat | python3 wiki_stats_to_KB.py > KBstats.all &&
python3 metrics_to_KB.py -k KBstats.all | sed '/^\s*$/d' > KBstatsMetrics.all &&
# echo -n "VERSION=" | cat - VERSION HEAD-KB KBstatsMetrics.all > KB-HEAD.all &&
(mkdir ../outputs 2>/dev/null; (mv -v HEAD-KB ../outputs/ && mv -v KBstatsMetrics.all ../outputs/ && mv -v VERSION ../outputs/))
exit_status=$?

(( exit_status == 0 )) && rm kb KBstats.all wiki_stats

exit $exit_status


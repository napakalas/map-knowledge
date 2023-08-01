poetry run python tools/compare.py --model https://apinatomy.org/uris/models/$1 \
    --endpoint1 $2 \
    --endpoint2 $3 \
    --style tabular > ../../$1-$2-vs-$3.csv
#/bin/sh

# use if ./start.sh returns a few bad lines

echo "./start"
./start.sh 2>bad_lines.log
retVal=$?
if [ $retVal -eq 0 ]; then
    echo ""
    echo "./start.sh executed succesfully"
    exit $retVal
fi

echo "deleting bad lines"
python3 delete_bad_lines.py

echo "removing and moving files"
rm -f kb
rm -f bad_lines.log
mv kb_new ../kb

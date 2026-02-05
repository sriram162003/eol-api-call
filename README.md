A Python tool to check End of Life (EOL) status for software in your inventory using the endoflife.date API

install request for api call:

# python -m pip install requests

create a sample csv file :

# python eol.py --create-sample

ckecking eol in given csv(replace software_inventory.csv with your csv file name)

# python eol.py --inventory software_inventory.csv --output results.csv

return output in result.csv

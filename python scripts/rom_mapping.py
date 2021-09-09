import json
from slpp import slpp as lua

with open('../resources/raw.txt', 'r') as file:
    raw_data = file.read()

data = lua.decode(raw_data)

filters = ['burner-generator']
signals = []
for item in data['item']:
    if 'flags' in data['item'][item] and data['item'][item]['flags'][0] == 'hidden':
        continue
    else:
        signal = dict()
        signal['name'] = item
        signal['type'] = 'item'

        signals.append(signal)

file_name = "../resources/signal_map.json"
with open(file_name, "w", newline="\n") as f:
    json.dump(signals, f, indent=4)

import pandas
import re

# The compute function will be called when the user clicks the node
# Use it to modify the input data frame
def compute(self):
    data = self.inArray.getData().copy()
    if not isinstance(data, pandas.DataFrame): return

    data['file_name'] = data['path'].apply(lambda value: value.name )
    data['population'] = data['path'].apply(lambda value: re.search(r'population(\d+)_(\d+)\..+', str(value)).group(1) )
    data['id'] = data['path'].apply(lambda value: re.search(r'population(\d+)_(\d+)\..+', str(value)).group(2) )

    self.outArray.setData(data)

# The execute function will be called when the user clicks the execute button (from the tool bar)
# Use it to process the data files in the data frame
def execute(self):
    self.executed = True
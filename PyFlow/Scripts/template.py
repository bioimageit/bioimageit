import pandas

# The compute function will be called when the user clicks the node
# Use it to modify the input data frame
def compute(self):
    data = self.inArray.getData()
    if not isinstance(data, pandas.DataFrame): return
    print('Compute data:')
    print(data)
    self.outArray.setData(data)

# The execute function will be called when the user clicks the execute button (from the tool bar)
# Use it to process the data files in the data frame
def execute(self):
    data = self.inArray.getData()
    print('Execute:')
    print(data)
    self.executed = True
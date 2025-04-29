import json
import re
from pyquery import PyQuery as pq

d = pq(filename='SimpleITK_reference.html')

add = False
function_elements = []

# Select all h2 between <h2 class='groupheader'>Function Documentation</h2> and <h2 class='groupheader'>Typedef Documentation</h2>
# They are the functions
for element in d('h2'):
    if pq(element).attr['class'] == 'groupheader' and 'Function Documentation' in pq(element).html():
        add = True
    if pq(element).attr['class'] == 'groupheader' and 'Typedef Documentation' in pq(element).html():
        add = False
    if add:
        function_elements.append(element)

cppTypesToBiitTypes = {str: 'string', 'double': 'float', 'float': 'float', 'uint32_t': 'integer', 'const Image &': 'path', 'Image &&': 'path'}

functions = {}
for function_element in function_elements[1:]:
    function = pq(function_element)
    memitem = function.next()
    proto = memitem.children('.memproto')
    memdoc = memitem.children('.memdoc').text()
    contents = function.contents()
    if len(contents)<2:
        print(f'Warning: function {function.text()} has contents {contents}.')
    function_name = contents[1].strip().replace('()', '')
    parameters = []
    for param_element in proto.find('td.paramtype'):
        name = pq(param_element).next('td.paramname').text()
        name, default = name.split(' = ') if ' = ' in name else (name, '')
        name = ''.join(name.rsplit(',', 1)) # Remove the last comma
        default = ''.join(default.rsplit(',', 1)) # Remove the last comma
        ptype = pq(param_element).text()
        ptype = ('path' if ('Image' in ptype or 'Transform' in ptype) else 
                 'string' if 'vector' in ptype else 
                 'integer' if 'int' in ptype else 
                 'boolean' if ptype == 'bool' else
                 'float' if ('double' in ptype or 'float' in ptype) else 'string')
        try:
            if ptype == 'string':
                default = ''
            elif ptype == 'integer':
                default = int(default.replace('u', ''))
            elif ptype == 'float' and len(default) > 0:
                default = float(default.replace('f', ''))
        except:
            default = ''
        parameters.append(dict(name=name, default=default, type=ptype))
    function_fullname = function_name + ':_' + '_'.join(p['name'] for p in parameters)
    return_and_name = proto.find('td.memname:first').text().split(' ')
    # fullname = return_and_name[-1]
    return_type = ' '.join(return_and_name[:-1])
    if 'const std::string' in return_type:
        return_type = 'string'
    if return_type != 'Image' or return_type != 'Transform' or return_type != 'BSplineTransform':
        print(f'Warning: function {function_name} does not return an Image nor a Transform: {return_type}')
    
    output_name = 'image' if return_type == 'Image' else 'transform'
    functions[function_fullname] = dict(name=function_name, function_name=function_name, description=memdoc, inputs = parameters, outputs = [dict(name=output_name, description=f'Output {output_name} path', type='path')])

# Remove duplicates
for function_fullname, function in functions.items():
    # If simple function name appears multiple time: use full name
    if len([f for ffn, f in functions.items() if f['function_name'] == function['function_name']]) > 1:
        function['name'] = function_fullname

with open('simpleITK_functions.json', 'w') as f:
    json.dump(functions, f, indent=4)


class ClEsperantoTool:

    categories = ['clEsperanto']
    dependencies = dict(conda=['conda-forge::pyopencl', 'conda-forge::pyclesperanto-prototype|win-64,linux-64,osx-64'], pip=[])
    environment = 'clEsperanto'
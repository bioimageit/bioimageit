
class Tool:

    # Taken from https://py.imagej.net/en/latest/Puncta-Segmentation.html
    categories = ['Fiji', 'Segmentation']
    dependencies = dict(python='3.10', conda=['conda-forge::pyimagej==1.5.0', 'conda-forge::openjdk=11'], pip=['numpy==1.26.4'])
    additionalActivateCommands = dict(all=[], mac=['export DYLD_LIBRARY_PATH="/usr/local/lib/"'], windows=['$env:JAVA_HOME = "$env:CONDA_PREFIX\Library\lib\jvm"'])
    environment = 'pyimagej'
    test = ['--input_image', 'test_still.tif', '--output_path', 'test_still_puncta.csv']
        
    name = "Puncta Segmentation"
    description = "Segment puncta from an image using the “Analyze Particles” ImageJ plugin."
    inputs = [
            dict(
                name = 'input_image',
                shortname = 'i',
                help = 'The input image path.',
                required = True,
                type = 'Path',
                autoColumn = True,
            ),
    ]
    outputs = [
            dict(
                name = 'output_path',
                shortname = 'o',
                help = 'The output dataFrame path.',
                default = '{input_image.stem}_puncta.csv',
                type = 'Path',
            ),
    ]

    def initialize(self, args):
        print('Loading libraries...')
        import imagej
        import scyjava as sj

        # initialize imagej
        self.ij = imagej.init('2.15.0', mode='headless', add_legacy=True)
        self.sj = sj
        print(f"ImageJ version: {self.ij.getVersion()}")

        # get additional resources
        self.HyperSphereShape = sj.jimport('net.imglib2.algorithm.neighborhood.HyperSphereShape')
        self.Overlay = sj.jimport('ij.gui.Overlay')
        self.Table = sj.jimport('org.scijava.table.Table')
        self.ParticleAnalyzer = sj.jimport('ij.plugin.filter.ParticleAnalyzer')
    
    def processData(self, args):
        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')
        input_image = str(args.input_image)

        print(f'[[1/4]] Load image {input_image}')
        # load test data
        ds_src = self.ij.io().open(input_image)
        ds_src = self.ij.op().convert().int32(ds_src) # convert image to 32-bit
        # self.ij.py.show(ds_src, cmap='binary')

        # supress background noise
        mean_radius = self.HyperSphereShape(5)
        ds_mean = self.ij.dataset().create(ds_src.copy())
        self.ij.op().filter().mean(ds_mean, ds_src.copy(), mean_radius)
        ds_mul = ds_src * ds_mean
        # self.ij.py.show(ds_mul, cmap='binary')

        # use gaussian subtraction to enhance puncta
        img_blur = self.ij.op().filter().gauss(ds_mul.copy(), 1.2)
        img_enhanced = ds_mul - img_blur
        # ij.py.show(img_enhanced, cmap='binary')
        
        # apply threshold
        img_thres = self.ij.op().threshold().renyiEntropy(img_enhanced)
        # self.ij.py.show(img_thres)

        # convert ImgPlus to ImagePlus
        imp_thres = self.ij.py.to_imageplus(img_thres)

        # tell ImageJ to use a black background
        Prefs = self.sj.jimport('ij.Prefs')
        Prefs.blackBackground = True

        # get ResultsTable and set ParticleAnalyzer
        rt = self.ij.ResultsTable.getResultsTable()
        self.ParticleAnalyzer.setResultsTable(rt)

        # set measurements
        self.ij.IJ.run("Set Measurements...", "area center shape")

        # run the analyze particle plugin
        self.ij.py.run_plugin(plugin="Analyze Particles...", args="clear", imp=imp_thres)

        # convert results table -> scijava table -> pandas dataframe
        sci_table = self.ij.convert().convert(rt, self.Table)
        df = self.ij.py.from_java(sci_table)
        df.to_csv(args.output_path, index=False)


from pathlib import Path

class Tool:

    # Taken from https://py.imagej.net/en/latest/Puncta-Segmentation.html
    categories = ['Fiji', 'Registration']
    dependencies = dict(conda=['conda-forge::openjdk=11'], pip=[])
    additionalInstallCommands = dict(all=[], 
                                     windows=[f'Set-Location -Path "{Path(__file__).parent.resolve()}"',
                                              f'Invoke-WebRequest -URI https://downloads.imagej.net/fiji/releases/2.14.0/fiji-2.14.0-win64.zip -OutFile fiji.zip',
                                              f'Expand-Archive -Force fiji.zip',
                                              f'Remove-Item fiji.zip'
                                              f'Copy-Item "{(Path(__file__).parent / "StackReg").resolve()}" -Destination "{Path("fiji/Fiji.app/plugins").resolve()}"'],
                                     linux=[f'cd {Path(__file__).parent.resolve()}',
                                            'wget https://downloads.imagej.net/fiji/releases/2.14.0/fiji-2.14.0-linux64.zip',
                                            'unzip -o fiji-2.14.0-linux64.zip',
                                            'rm fiji-2.14.0-linux64.zip',
                                            f'cp -a {Path(__file__).parent.resolve()}/StackReg/. ./Fiji.app/plugins'], 
                                     mac=['export DYLD_LIBRARY_PATH="/usr/local/lib/"',
                                            f'cd {Path(__file__).parent.resolve()}',
                                            'wget https://downloads.imagej.net/fiji/releases/2.14.0/fiji-2.14.0-macosx.zip',
                                            'unzip -o fiji-2.14.0-macosx.zip',
                                            'rm fiji-2.14.0-macosx.zip',
                                            f'cp -a {Path(__file__).parent.resolve()}/StackReg/. ./Fiji.app/plugins'])
    # additionalActivateCommands = dict(all=[], mac=['export JAVA_HOME="$CONDA_PREFIX/lib/jvm/"', 'export DYLD_LIBRARY_PATH="/usr/local/lib/"'], windows=['$env:JAVA_HOME = "$env:CONDA_PREFIX\Library\lib\jvm"'])

    environment = 'fiji'
    test = ['--input_image', 'celegans_stack.tif', '--output_image', 'stackreg.tif']
        
    name = "StackReg"
    description = "Stack registration with the StackReg Fiji plugin."
    inputs = [
            dict(
                name = 'input_image',
                shortname = 'i',
                help = 'The input image path.',
                required = True,
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'transformation',
                shortname = 't',
                help = 'The transformation applied on each slice.',
                default = 'Rigid Body',
                choices = ['Translation', 'Rigid Body', 'Scaled rotation', 'Affine'],
                type = 'str',
            ),
    ]
    outputs = [
            dict(
                name = 'output_image',
                shortname = 'o',
                help = 'The output image path.',
                default = '{input_image.stem}_stackreg{input_image.exts}',
                type = 'Path',
            ),
    ]
    
    def processData(self, args):
        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')

        print(f'[[1/1]] Run Fiji macro')
        import subprocess
        import platform
        fijiExecutable = 'Fiji.app/Contents/MacOS/ImageJ-macosx' if platform.system() == 'Darwin' else 'Fiji.app/fiji' if platform.system() == 'Linux' else 'fiji\Fiji.app\ImageJ-win64.exe'
        fijiPath = str(Path(__file__).parent.resolve() / fijiExecutable)
        macroPath = str(Path(__file__).parent.resolve() / 'StackReg' / 'stackreg.ijm')
        transformation = args.transformation.replace(' ', '_')
        pluginsArgs = ['--plugins', str(Path(__file__).parent.resolve() / 'Fiji.app/plugins/')] if platform.system() == 'Darwin' else []
        command = [fijiPath, '--headless', '--console'] + pluginsArgs + ['-macro', macroPath, f'[{args.input_image.resolve()},{transformation},{args.output_image}]']
        print('Execute:', command)
        subprocess.run(command, check=True)
        


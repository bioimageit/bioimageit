from pathlib import Path

class Tool:

    categories = ['Tracking', 'Stracking']
    dependencies = dict(python='3.9', pip=['numpy==1.24.4', 'scipy==1.9.3', 'scikit-image==0.19.3', 'pandas==1.5.3'], conda=['bioimageit::stracking==0.1.5|osx-arm64', 'bioimageit::stracking==v0.1.4|osx-64,win-64,linux-64'])
    environment = 'stracking'
    
    name = "Stracking Linker"
    description = "Linking of particles detected in stracking."
    inputs = [
            dict(
                name = 'input_csv',
                help = 'Input csv from a stracking detector',
                required = True,
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'max_connection_cost',
                help = 'Maximum connection cost (squared maximum Euclidean distance that a particle can move between two consecutive frames)',
                default = 3000,
                type = 'float',
            ),
            dict(
                name = 'gap',
                help = 'For example if gap=2, particles 2 frames apart can be connected',
                default = 2,
                type = 'int',
            ),
    ]
    outputs = [
            dict(
                name = 'output',
                shortname = 'o',
                help = 'Output path for the tracks (the extension can be .st.json or .csv and defines the output format).',
                default = '{input_csv.stem}_tracks.st.json',
                type = 'Path',
            ),
    ]
    
    def processData(self, args):
        print('Performing stracking linking')
        # import subprocess
        # commandArgs = [
        #     'ssplinker', '-i', args.input_csv, '-o', args.output, '-f', 'st.json',
        #     '-c', args.max_connection_cost, '-g', args.gap
        # ]
        # return subprocess.run([str(ca) for ca in commandArgs])
        if (not args.output.name.endswith('.csv')) and (not args.output.name.endswith('.st.json')):
            raise Exception('The output extension must be .csv or .st.json.')
        from stracking.io import read_particles, write_tracks
        from stracking.linkers import SPLinker, EuclideanCost
        particles = read_particles(str(args.input_csv))
        euclidean_cost = EuclideanCost(max_cost=args.max_connection_cost)
        tracker = SPLinker(cost=euclidean_cost, gap=args.gap)
        tracks = tracker.run(particles)
        write_tracks(file_path=str(args.output), tracks=tracks, format_='csv' if args.output.suffix == '.csv' else 'st.json')



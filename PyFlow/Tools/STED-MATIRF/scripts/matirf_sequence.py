#!/usr/bin/python3

import os
import os.path
import sys, getopt
import subprocess


class TxtMovieIO:
    def __init__(self, inputfile):
        self.inputfile = inputfile
        self.input_dir = os.path.dirname(self.inputfile)
        self.frames = []
        with open(inputfile) as infile:
            for line in infile:
                self.frames.append(line.strip())

    def get_frames_files(self):    
        """Create a list of absolute file path from a txt movie file

        Parameters
        ----------
        inputfile: str
            Path of the input file

        Return
        ------
        List of the movie frames paths    
        """
        dirname = os.path.dirname(self.inputfile)
        frames_path = []
        for frame in self.frames:
            frames_path.append(os.path.join(dirname, frame))
        return frames_path

    def frames_count(self):
        return len(self.frames)

    def get_frame_file(self, index): 
        return os.path.join(self.input_dir, self.frames[index])

    def get_output_frame(self, frame_idx, prefix, outputfile):
        output_dirname = os.path.dirname(outputfile)
        return os.path.join(output_dirname, prefix+self.frames[frame_idx])

    def write_output_movie(self, outputfile, prefix):
        with open(outputfile, "w") as outfile:
            for frame in self.frames:
                filename = os.path.join(prefix + frame)
                outfile.write(filename + '\n')
        

def get_frames_files(inputfile):
    """Create a list of absolute file path from a txt movie file

    Parameters
    ----------
    inputfile: str
        Path of the input file

    Return
    ------
    List of the movie frames paths    
    """
    dirname = os.path.dirname(inputfile)
    frames = []
    with open(inputfile) as infile:
        frames.append(os.path.join(dirname, line.strip()))
    return frames


def main(argv):
    inputfile = ''
    output_file = ''
    p = ''
    d = 500
    n = 20
    lambda_ = '0.001,0.001'
    gamma = 10
    iter = 1000
    reg = 1
    zmin  = 0

    try:
        opts, args = getopt.getopt(argv,"hi:o:p:d:n:l:g:t:r:z:",["ifile=","ofile=","params=", "depth=","nplanes=","lambda=","gamma=","iter=","reg=","zmin="])
    except getopt.GetoptError as e:
        print('matirf_sequence.py -i <inputfile> -o <outputfile> ...')
        raise e
    for opt, arg in opts:
        # print('opt=', opt)
        # print('arg=', arg)
        if opt == '-h':
            print('matirf_sequence.py -i <inputfile> -o <outputfile> ...')
            return
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg  
        elif opt in ("-d", "--depth"): 
            d = arg
        elif opt in ("-p", "--params"): 
            p = arg    
        elif opt in ("-n", "--nplanes"): 
            n = arg    
        elif opt in ("-l", "--lambda"): 
            lambda_ = arg  
        elif opt in ("-g", "--gamma"): 
            gamma = arg   
        elif opt in ("-t", "--iter"): 
            iter = arg  
        elif opt in ("-r", "--reg"): 
            reg = arg 
        elif opt in ("-z", "--zmin"): 
            zmin = arg               

    # print params
    print('inputfile:', inputfile)
    print('outputfile:', outputfile)  
    print('p:', p)  
    print('depth:', d)  
    print('nplanes:', n)     
    print('lambda:', lambda_)   
    print('gamma:', gamma)   
    print('iter:', iter)    
    print('reg:', reg)    
    print('zmin:', zmin)    

     # run
    prefix = "o_"
    print('input file=', inputfile)
    if os.path.isfile(inputfile):
        if inputfile.endswith('.txt'):
            print("process the txt movie")
            txt_movie_io = TxtMovieIO(inputfile)
            for index in range(txt_movie_io.frames_count()):
                input_frame = txt_movie_io.get_frame_file(index)
                output_frame = txt_movie_io.get_output_frame(index, prefix, outputfile)
                args = ['matirf', '-i', input_frame, '-o', output_frame, '-p', p, '-d', str(d), '-n', str(n), '-lambda', str(lambda_), '-gamma', str(gamma), '-iter', str(iter), '-reg', str(reg), '-zmin', str(zmin)]
                print("args=", args)
                subprocess.run(args, check=True)
            txt_movie_io.write_output_movie(outputfile, prefix)
    else:
        raise Exception("Error: input file does not exists")

    print('Input file is "', inputfile)
    print('Output file is "', outputfile)


if __name__ == "__main__":
   main(sys.argv[1:])
           
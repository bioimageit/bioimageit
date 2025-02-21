#!/usr/bin/python

import os
import os.path
import sys, getopt
import subprocess


def create_job_input_txt(inputfile, input_file_job):
    dirname = os.path.dirname(inputfile)
    with open(inputfile) as infile:
        with open(input_file_job, "w") as outfile:
            for line in infile:
                filename = os.path.join(dirname, line.strip())
                outfile.write(filename + '\n')


def creates_job_output_txt(inputfile, outputfile_job):
    dirname = os.path.dirname(outputfile_job)
    with open(inputfile) as infile:
        with open(outputfile_job, "w") as outfile:
            for line in infile:
                filename = os.path.join(dirname, 'o_' + line.strip())
                outfile.write(filename + '\n')


def create_job_io_files(inputfile, outputfile):
    job_input_file = os.path.join(os.path.dirname(inputfile), os.path.basename(inputfile) + "_job.txt")
    job_output_file = os.path.join(os.path.dirname(outputfile), os.path.basename(outputfile) + "_job.txt")
    create_job_input_txt(inputfile, job_input_file)
    creates_job_output_txt(inputfile, job_output_file)
    return job_input_file, job_output_file

def convert_job_output_file_to_outputfile(job_output_file, outputfile):
    with open(job_output_file) as infile:
        with open(outputfile, "w") as outfile:
            for line in infile:
                filename = os.path.basename(line.strip())
                outfile.write(filename + '\n')

def batch_ndsafir(inputfile, outputfile, tbatch, args):
    # get inputs
    input_dir = os.path.dirname(inputfile)
    output_dir = os.path.dirname(outputfile)
    frames_num = 0
    frames = []
    output_frames = []
    with open(inputfile) as my_file:
        frames = my_file.read().splitlines()
        frames_num = len(frames)

    # loop on batch
    idx = 0
    step = tbatch - 2  
    start_idx = -step
    end_idx = 0
    while end_idx < frames_num-1:
        start_idx += step
        end_idx = start_idx + tbatch - 1
        if start_idx < 0:
            start_idx += 2
            end_idx += 2 
        if end_idx >= frames_num:
            end_idx = frames_num
   
        safir_sequence(start_idx, input_dir, output_dir, frames[start_idx:end_idx+1], args)  
        idx += tbatch

    # create output file    
    with open(outputfile, "w") as outfile:
        for frame in frames:
            outfile.write("o_" + frame + '\n')


def safir_sequence(idx, inputdir, output_dir, frames, args):

    job_input_file = os.path.join(output_dir, 'job_input.txt')
    with open(job_input_file, "w") as infile:
        for frame in frames:
            infile.write(os.path.join(inputdir, frame) + '\n')
    
    job_output_file = os.path.join(output_dir, 'job_output.txt')
    with open(job_output_file, "w") as outfile:
        for i in range(len(frames)):
            if i == 0:
                if idx == 0:
                    outfile.write(os.path.join(output_dir, "o_" + frames[i]) + '\n')
                else:
                    outfile.write(os.path.join(output_dir, "tmp.tif") + '\n')  
            else:
                outfile.write(os.path.join(output_dir, "o_" + frames[i]) + '\n')               

    args = [item.replace('inputfile', job_input_file) for item in args]      
    args = [item.replace('outputfile', job_output_file) for item in args]    

    print('run args:', args)     
    subprocess.run(args, check=True)

    os.remove(job_input_file) 
    os.remove(job_output_file) 
    tmpfile = os.path.join(output_dir, "tmp.tif")
    if os.path.isfile(tmpfile):
        os.remove(tmpfile) 

def ndsafir_series(inputfile, outputfile, noise, iter, nf, patch, tbatch):

    # print params
    print('inputfile:', inputfile)
    print('outputfile:', outputfile)  
    print('noise:', noise)  
    print('iter:', iter)     
    print('nf:', nf)   
    print('patch:', patch)   
    print('tbatch:', tbatch)                  

    # run
    print('input file=', inputfile)
    if os.path.isfile(inputfile):
        if inputfile.endswith('.txt') and tbatch == '0':
            print('process a series')
            jifile, jofile = create_job_io_files(inputfile, outputfile)
            args = ['ndsafir', '-i', jifile, '-o', jofile, '-noise', noise, '-iter', iter, '-patch', patch, '-nf', nf]
            subprocess.run(args, check=True)
            convert_job_output_file_to_outputfile(jofile, outputfile)
            # clean
            os.remove(jifile) 
            os.remove(jofile) 
        elif inputfile.endswith('.txt') and tbatch != '0':
            print('process a series with batch:')
            args = ['ndsafir', '-i', 'inputfile', '-o', 'outputfile', '-noise', noise, '-iter', iter, '-patch', patch, '-nf', nf]
            batch_ndsafir(inputfile, outputfile, int(tbatch), args)
        else:
            args = ['ndsafir', '-i', "'" + inputfile + "'", '-o', "'" + outputfile + "'", '-noise', noise, '-iter', noise, '-patch', patch, '-nf', nf]
            print("process a single file:", )
            subprocess.run(args, shell=True, check=True)
    else:
        raise Exception("Error: input file does not exists")

    print('Input file is "', inputfile)
    print('Output file is "', outputfile)

def main(argv):
    inputfile = ''
    outputfile = ''
    noise = ''
    iter = ''
    patch = ''
    nf = ''
    tbatch = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:n:t:p:f:b:",["ifile=","ofile=","noise=","iter=","patch=","nf=","tbatch="])
    except getopt.GetoptError as e:
        print('ndsafir_series.py -i <inputfile> -o <outputfile>')
        raise e
    for opt, arg in opts:
        # print('opt=', opt)
        # print('arg=', arg)
        if opt == '-h':
            print('ndsafir_series.py -i <inputfile> -o <outputfile> -n <noise> -t <iter> -p <patch> -f <nf> -b <tbatch>')
            return
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
        elif opt in ("-n", "--noise"):
            noise = arg   
        elif opt in ("-t", "--iter"):
            iter = arg   
        elif opt in ("-p", "--patch"):
            patch = arg  
        elif opt in ("-f", "--nf"):
            nf = arg  
        elif opt in ("-b", "--tbatch"):
            tbatch = arg       

    # default inputs
    if noise == '':
        noise = '2'
    if iter == '':
        iter = '5'
    if nf == '':
        nf = '1' 
    if patch == '':
        patch = '7x7x1'  
    if tbatch == '':
        tbatch = '0'
    ndsafir_series(inputfile, outputfile, noise, iter, nf, patch, tbatch)

if __name__ == "__main__":
   main(sys.argv[1:])

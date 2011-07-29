#!/usr/bin/env python
""" mk_fsf.py - make first-level FSF model

USAGE: mk_level1_fsf.py <taskid> <subnum> <tasknum> <runnum> <smoothing - mm> <use_inplane> <basedir> <nonlinear>

"""

## Copyright 2011, Russell Poldrack. All rights reserved.

## Redistribution and use in source and binary forms, with or without modification, are
## permitted provided that the following conditions are met:

##    1. Redistributions of source code must retain the above copyright notice, this list of
##       conditions and the following disclaimer.

##    2. Redistributions in binary form must reproduce the above copyright notice, this list
##       of conditions and the following disclaimer in the documentation and/or other materials
##       provided with the distribution.

## THIS SOFTWARE IS PROVIDED BY RUSSELL POLDRACK ``AS IS'' AND ANY EXPRESS OR IMPLIED
## WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
## FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL RUSSELL POLDRACK OR
## CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
## CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
## SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
## ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
## NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
## ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


# create fsf file for arbitrary design
import numpy as N
import sys
import os
import subprocess as sub
from openfmri_utils import *

# create as a function that will be called by mk_all_fsf.py
# just set these for testing
## taskid='ds002'
## subnum=1
## tasknum=1
## runnum=2
## smoothing=6
## tr=2.0
## use_inplane=1

## basedir='/corral/utexas/poldracklab/openfmri/shared/'

def mk_level1_fsf(taskid,subnum,tasknum,runnum,smoothing,use_inplane,basedir='/corral/utexas/poldracklab/openfmri/staged/',nonlinear=1):

    subdir='%s/%s/sub%03d'%(basedir,taskid,subnum)

    # read the conditions_key file
    cond_key=load_condkey(basedir+taskid+'/condition_key.txt')

    conditions=cond_key[tasknum].values()

    scan_key=load_scankey(basedir+taskid+'/scan_key.txt')
    tr=float(scan_key['TR'])
    if scan_key.has_key('nskip'):
        nskip=int(scan_key['nskip'])
    else:
        nskip=0
        
    stubfilename='/corral/utexas/poldracklab/code/poldrack/openfmri/design_level1.stub'
    modeldir=subdir+'/model/'
    if not os.path.exists(modeldir):
        os.mkdir(modeldir)

    outfilename='%s/model/task%03d_run%03d.fsf'%(subdir,tasknum,runnum)
    print('%s\n'%outfilename)
    outfile=open(outfilename,'w')
    outfile.write('# Automatically generated by mk_fsf.py\n')

    # first get common lines from stub file
    stubfile=open(stubfilename,'r')
    for l in stubfile:
        outfile.write(l)

    stubfile.close()
    # figure out how many timepoints there are

    p = sub.Popen(['fslinfo','%s/BOLD/task%03d_run%03d/bold_mcf_brain'%(subdir,tasknum,runnum)],stdout=sub.PIPE,stderr=sub.PIPE)
    output, errors = p.communicate()
    ntp=int(output.split('\n')[4].split()[1])

    outfile.write('\n\n### AUTOMATICALLY GENERATED PART###\n\n')
    # now add custom lines
    outfile.write( 'set fmri(regstandard_nonlinear_yn) %d\n'%nonlinear)
    # Delete volumes
    outfile.write('set fmri(ndelete) %d\n'%nskip)


    outfile.write('set fmri(outputdir) "%s/model/task%03d_run%03d.feat"\n'%(subdir,tasknum,runnum))
    outfile.write('set feat_files(1) "%s/BOLD/task%03d_run%03d/bold_mcf_brain"\n'%(subdir,tasknum,runnum))
    if use_inplane==1:
        outfile.write('set fmri(reginitial_highres_yn) 1\n')
        outfile.write('set initial_highres_files(1) "%s/anatomy/inplane001_brain"\n'%subdir)
    else:
        outfile.write('set fmri(reginitial_highres_yn) 0\n')

    outfile.write('set highres_files(1) "%s/anatomy/highres001_brain"\n'%subdir)
    outfile.write('set fmri(npts) %d\n'%ntp)
    outfile.write('set fmri(tr) %0.2f\n'%tr)
    nevs=len(conditions)+6
    outfile.write('set fmri(evs_orig) %d\n'%nevs)
    outfile.write('set fmri(evs_real) %d\n'%(2*nevs))
    outfile.write('set fmri(smooth) %d\n'%smoothing)
    outfile.write('set fmri(ncon_orig) %d\n'%(len(conditions)+1))
    outfile.write('set fmri(ncon_real) %d\n'%(len(conditions)+1))

    # loop through EVs
    convals_real=N.zeros(nevs*2)
    convals_orig=N.zeros(nevs)
    empty_evs=[]

    for ev in range(len(conditions)):
        outfile.write('\n\nset fmri(evtitle%d) "%s"\n'%(ev+1,conditions[ev]))
        condfile='%s/behav/task%03d_run%03d/cond%03d.txt'%(subdir,tasknum,runnum,ev+1)
        if os.path.exists(condfile):
            outfile.write('set fmri(shape%d) 3\n'%(ev+1))
            outfile.write('set fmri(custom%d) "%s"\n'%(ev+1,condfile))
        else:
             outfile.write('set fmri(shape%d) 10\n'%(ev+1))
             print '%s is missing, using empty EV'%condfile
             empty_evs.append(ev+1)
             
        outfile.write('set fmri(convolve%d) 3\n'%(ev+1))
        outfile.write('set fmri(convolve_phase%d) 0\n'%(ev+1))
        outfile.write('set fmri(tempfilt_yn%d) 1\n'%(ev+1))
        outfile.write('set fmri(deriv_yn%d) 1\n'%(ev+1))
        
        for evn in range(nevs+1):
            outfile.write('set fmri(ortho%d.%d) 0\n'%(ev+1,evn))
        # make a T contrast for each EV
        outfile.write('set fmri(conpic_real.%d) 1\n'%(ev+1))
        outfile.write('set fmri(conname_real.%d) "%s"\n'%(ev+1,conditions[ev]))
        outfile.write('set fmri(conname_orig.%d) "%s"\n'%(ev+1,conditions[ev]))
        for evt in range(nevs*2):
            outfile.write('set fmri(con_real%d.%d) %d\n'%(ev+1,evt+1,int(evt==(ev*2))))
            if (evt==(ev*2)):
                convals_real[evt]=1
        for evt in range(nevs):
            outfile.write('set fmri(con_orig%d.%d) %d\n'%(ev+1,evt+1,int(evt==ev)))
            if (evt==ev):
                convals_orig[evt]=1
                
    if len(empty_evs)>0:
        empty_ev_file=open('%s/behav/task%03d_run%03d/empty_evs.txt'%(subdir,tasknum,runnum),'w')
        for eev in empty_evs:
            empty_ev_file.write('%d\n'%eev)
        empty_ev_file.close()

    # make one additional contrast across all conditions
    outfile.write('set fmri(conpic_real.%d) 1\n'%(ev+2))
    outfile.write('set fmri(conname_real.%d) "all"\n'%(ev+2))
    outfile.write('set fmri(conname_orig.%d) "all"\n'%(ev+2))

    for evt in range(nevs*2):
            outfile.write('set fmri(con_real%d.%d) %d\n'%(ev+2,evt+1,convals_real[evt]))
    for evt in range(nevs):
            outfile.write('set fmri(con_orig%d.%d) %d\n'%(ev+2,evt+1,convals_orig[evt]))

    skipnum=1+len(conditions)
    # do motion regressors
    for ev in range(6):
        outfile.write('\n\nset fmri(evtitle%d) "motpar%d"\n'%(ev+skipnum,ev+1))
        outfile.write('set fmri(shape%d) 2\n'%(ev+skipnum))
        outfile.write('set fmri(convolve%d) 0\n'%(ev+skipnum))
        outfile.write('set fmri(convolve_phase%d) 0\n'%(ev+skipnum))
        outfile.write('set fmri(tempfilt_yn%d) 1\n'%(ev+skipnum))
        outfile.write('set fmri(deriv_yn%d) 1\n'%(ev+skipnum))
        outfile.write('set fmri(custom%d) "%s/BOLD/task%03d_run%03d/bold_mcf.par.%d"\n'%(ev+skipnum,subdir,tasknum,runnum,ev+1))
        for evn in range(nevs+1):
            outfile.write('set fmri(ortho%d.%d) 0\n'%(ev+skipnum,evn))

    outfile.close()

    # create the motion files
    motparfile='%s/BOLD/task%03d_run%03d/bold_mcf.par'%(subdir,tasknum,runnum)
    mpf=open(motparfile,'r')


    data = [line.split() for line in mpf]
    mpf.close()

    for p in range(6):
        pfile=open('%s.%s'%(motparfile,p+1),'w')
        for i in range(len(data)):
            pfile.write('%s\n'%data[i][p])
        pfile.close()

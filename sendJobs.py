##python sendJobs.py -n 10 -e 20000  -s
##python sendJobs.py -n 10 -e 20000  -s -p "Higgs/SM_HH" -b SM-HH-13TEV

import glob, os, sys,subprocess,cPickle
import commands
import time
import random
import param
import paramsig
import dicwriter as dicr

mydict=dicr.dicwriter('LHEdict.json')

#__________________________________________________________
def getCommandOutput(command):
    p = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    stdout,stderr = p.communicate()
    return {"stdout":stdout, "stderr":stderr, "returncode":p.returncode}


#__________________________________________________________
def SubmitToBatch(cmd,nbtrials):
    submissionStatus=0
    for i in range(nbtrials):            
        outputCMD = getCommandOutput(cmd)
        stderr=outputCMD["stderr"].split('\n')
        jobid=outputCMD["stdout"].split()[1].replace("<","").replace(">","")

        for line in stderr :
            if line=="":
                print "------------GOOD SUB"
                submissionStatus=1
                break
            else:
                print "++++++++++++ERROR submitting, will retry"
                print "Trial : "+str(i)+" / "+str(nbtrials)
                time.sleep(10)
                break
            
        if submissionStatus==1:
            return 1,jobid
        
        if i==nbtrials-1:
            print "failed sumbmitting after: "+str(nbtrials)+" trials, will exit"
            return 0,jobid

#__________________________________________________________
if __name__=="__main__":
    Dir = os.getcwd()
    
    from optparse import OptionParser
    parser = OptionParser()

    parser.add_option ('-n','--njobs', help='Number of jobs to submit',
                       dest='njobs',
                       default='10')

    parser.add_option ('-e', '--events',  help='Number of event per job. default is 100',
                       dest='events',
                       default='10000')

    parser.add_option ('-m', '--mode',  help='Running mode [batch, local]. Default is batch',
                       dest='mode',
                       default='batch')

    parser.add_option ('-p', '--process',  help='process, example B_4p',
                       dest='process',
                       default='')
    
    parser.add_option ('-b', '--binning',  help='ht binning, example: B-4p-0-1_100TEV',
                       dest='binning',
                       default='')

    parser.add_option ('-q', '--queue',  help='lxbatch queue, default 8nh',
                       dest='queue',
                       default='8nh')

    parser.add_option('-s', '--signal',
                      action='store_true', dest='issignal', default=False,
                      help='this sample is signal')


    (options, args) = parser.parse_args()
    issignal = options.issignal
    njobs    = int(options.njobs)
    events   = int(options.events)
    mode     = options.mode
    process  = options.process
    binning  = options.binning
    queue    = options.queue
    rundir = os.getcwd()
    nbjobsSub=0
     
    if issignal:
        import paramsig as para
    else:
        import param as para

    for pr in para.gridpacklist:
        if process!='' and process !=pr:continue
        i=0
        njobstmp=njobs
        while i<njobstmp:
            if mydict.jobexits(sample=pr,jobid=i): 
                print 'job i ',i,'  exists    njobs ',njobs
                i+=1
                njobstmp+=1
                continue

            else:
                print 'job does not exists: ',i

            logdir="/afs/cern.ch/work/h/helsens/public/FCCGenJobs/%s"%(pr)
            os.system("mkdir -p %s"%logdir+'/job%s/'%str(i))
            frunname = 'job%i.sh'%(i)
            frun = open(logdir+'/job%s/'%str(i)+frunname, 'w')
            commands.getstatusoutput('chmod 777 %s/%s'%(logdir+'/job%s'%str(i),frunname))
            frun.write('mkdir job%i_%s\n'%(i,pr))
            frun.write('export EOS_MGM_URL=\"root://eospublic.cern.ch\"\n')
            frun.write('source /afs/cern.ch/project/eos/installation/client/etc/setup.sh\n')
            frun.write('source /afs/cern.ch/exp/fcc/sw/0.8pre/setup.sh\n')
            frun.write('cd job%i_%s\n'%(i,pr))
            frun.write('/afs/cern.ch/project/eos/installation/0.3.84-aquamarine/bin/eos.select cp %s/%s.tar.gz .\n'%(para.indir,pr))
            frun.write('tar -zxf %s.tar.gz\n'%pr)
            frun.write('./run.sh %i %i\n'%(events,i+1))
            frun.write('/afs/cern.ch/project/eos/installation/0.3.84-aquamarine/bin/eos.select cp events.lhe.gz %s/%s/events%i.lhe.gz\n'%(para.outdir,pr,i))
            frun.write('cd ..\n')
            frun.write('rm -rf job%i_%s\n'%(i,pr))
            print pr

            if mode=='batch':
                    #cmdBatch = 'bsub -o %s%s/%s/log_job%i.log -q 8nh %s/tmp/%s'%(para.outdir,pr,ht.replace('.tar.gz',''),i,Dir,frunname)
                cmdBatch="bsub -M 2000000 -R \"rusage[pool=2000]\" -q %s -outdir %s -cwd %s %s" %(queue,logdir+'/job%s/'%(str(i)),logdir+'/job%s/'%(str(i)),logdir+'/job%s/'%(str(i))+frunname)
                #print cmdBatch
                
                batchid=-1
                job,batchid=SubmitToBatch(cmdBatch,10)
                nbjobsSub+=job
                mydict.addjob(sample=pr,jobid=i,queue='8nh',nevents=events,status='submitted',log='%s/LSFJOB_%i'%(logdir,int(batchid)),out='%s%s/events%i.lhe.gz'%(para.outdir,pr,i),batchid=batchid,script='%s/%s'%(logdir,frunname))

            elif mode=='local':
                os.system('./tmp/%s'%frunname)

            else: 
                print 'unknow running mode: %s'%(mode)
            i+=1

    print 'succesfully sent %i  jobs'%nbjobsSub
    mydict.write()



    

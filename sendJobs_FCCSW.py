#export FCCUSERPATH=/afs/cern.ch/user/h/helsens/FCCsoft/FCCSOFT/newEDM2/FCCSW/
#python sendJobs_FCCSW.py -n 10 -p pp_w012j_5f -q 8nh -e -1 -i $FCCUSERPATH/Generation/data/Pythia_LHEinput_Matching.cmd
#python sendJobs_FCCSW.py -n 100 -p pp_hh_bbaa -q 8nh -e -1 -i $FCCUSERPATH/Generation/data/Pythia_LHEinput.cmd


import glob, os, sys,subprocess,cPickle
import commands
import time
import random
import param
import json
import dicwriter_FCC as dicr


#python sendJobs_FCCSW.py -n 1 -p BBB_4p

indictname='/afs/cern.ch/work/h/helsens/public/FCCDicts/LHEdict.json'
indict=None
with open(indictname) as f:
    indict = json.load(f)
outdict=dicr.dicwriter('/afs/cern.ch/work/h/helsens/public/FCCDicts/PythiaDelphesdict_%s.json'%param.version)

#jets multiplicities for matching
jetmultflags = {
'01j':1, 
'012j':2, 
'0123j':3, 
'01234j':4, 
'012345j':5
}


#__________________________________________________________
def matching(pr):
   ################ find max jet multiplicity
   nJetsMax = -1 
   for flag, jetmult in jetmultflags.iteritems():
      if flag in pr:
          nJetsMax = jetmult

   ################ find qCut value
   
   # case where no matching should be applied
   if nJetsMax < 0:
      print '   No merging applied'
      return ''
      
   
   # if find njetsMax but qCut value is not specified
   elif nJetsMax > 0 and 'qCut' not in desc[2]:
      print '   qCut value not specified for process {}.'.format(pr)
      print '   Please specify qCut value. Not submitting a job for this process...'
      return ''

   else:
      qcutstr = desc[2].split(",")[1]
      qCut = qcutstr.split("=",1)[1].strip()

      print '   Merging with parameters (nJetMax = {}, qCut = {} GeV) will be applied for {}'.format(nJetsMax, qCut, pr)

      os.system('cp {} tmp.cmd'.format(cardmatching))
      with open('tmp.cmd', 'a') as myfile:
         myfile.write('JetMatching:nJetMax = {}\n'.format(nJetsMax))
         myfile.write('JetMatching:qCut = {}\n'.format(qCut))

      
      ### TBD: SEND JOB USING 'tmp.cmd'
      os.system('rm tmp.cmd')


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

        jobid=outputCMD["stdout"].split()[1].replace("<","").replace(">","")
            
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

    parser.add_option ('-q', '--queue',  help='lxbatch queue, default 8nh',
                       dest='queue',
                       default='8nh')

    parser.add_option('-t','--test',
                      action='store_true', dest='test', default=False,
                      help='don\'t send to batch nor write to the dictonary')

    parser.add_option ('-i', '--inputfile',  help='pythia 8 configuration file, example $FCCUSERPATH/Generation/data/Pythia_LHEinput.cmd',
                       dest='inputfile',
                       default='')

    parser.add_option ('-v', '--version',  help='version of the delphes card to use, options are: fcc_v01, cms',
                       dest='version',
                       default='')

    (options, args) = parser.parse_args()
    njobs      = int(options.njobs)
    events     = int(options.events)
    mode       = options.mode
    process    = options.process
    queue      = options.queue
    test       = options.test
    pythiacard = options.inputfile
    version    = options.version
    rundir = os.getcwd()
    nbjobsSub=0


################# Loop over the gridpacks
    for pr in param.gridpacklist:
        if process!='' and process !=pr:continue

        i=0
        njobstmp=njobs
        ################# continue if job already exist and process if not
        while i<njobstmp:
            if outdict.jobexits(sample=pr,jobid=i): 
                print 'job i ',i,'  exists    njobs ',njobs
                i+=1
                njobstmp+=1
                continue
            else:
                print 'job does not exists: ',i

            LHEexist=False
            LHEfile=''
            ################# break if already exist
            for j in indict[pr]:
                if i==j['jobid'] and j['status']=='done':
                    LHEexist=True
                    LHEfile=j['out']
                    break
                
            ################# if no LHE proceed
            if not LHEexist:
                print 'LHE does not exist, continue'
                i+=1
                njobstmp+=1
                if i>len(indict[pr]): break
                continue

            eosbase='/afs/cern.ch/project/eos/installation/0.3.84-aquamarine/bin/eos.select'
            logdir=Dir+"/BatchOutputs/%s/%s/"%(version,pr)
            os.system("mkdir -p %s"%logdir)
            frunname = 'job%i.sh'%(i)
            frun = open(logdir+'/'+frunname, 'w')
            commands.getstatusoutput('chmod 777 %s/%s'%(logdir,frunname))
            frun.write('#!/bin/bash\n')
            frun.write('unset LD_LIBRARY_PATH\n')
            frun.write('unset PYTHONHOME\n')
            frun.write('unset PYTHONPATH\n')
            frun.write('source %s\n'%(stack))
            frun.write('mkdir job%i_%s\n'%(i,pr))
            frun.write('cd job%i_%s\n'%(i,pr))
            frun.write('export EOS_MGM_URL=\"root://eospublic.cern.ch\"\n')
            frun.write('source /afs/cern.ch/project/eos/installation/client/etc/setup.sh\n')
            frun.write('%s mkdir %s%s\n'%(eosbase,param.delphes_dir,pr))
            frun.write('%s cp %s .\n'%(eosbase,LHEfile))
            frun.write('gunzip -c %s > events.lhe\n'%LHEfile.split('/')[-1])
            
            frun.write('%s cp %s%s/card.tcl .\n'%(eosbase,))
            if 'fcc' in version:
                frun.write('%s cp %s%s/muonMomentumResolutionVsP.tcl .\n'%(eosbase,))
                frun.write('%s cp %s%s/momentumResolutionVsP.tcl .\n'%(eosbase,))


            

            frun.write('cp %s/Sim/SimDelphesInterface/options/PythiaDelphes_config.py .\n'%(FCCSW))
#            frun.write('cp %sGeneration/data/Pythia_LHEinput_batch.cmd card.cmd\n'%(FCCSW))
            frun.write('cp %s card.cmd\n'%(pythiacard))
            frun.write('echo "Beams:LHEF = events.lhe" >> card.cmd\n')
           
            frun.write('%s/run fccrun.py PythiaDelphes_config.py --delphescard=card.tcl --inputfile=card.cmd --outputfile=events%i.root --nevents=%i\n'%(FCCSW,i,events))
            frun.write('/afs/cern.ch/project/eos/installation/0.3.84-aquamarine/bin/eos.select cp events%i.root %s%s/events%i.root\n'%(i,param.delphes_dir,pr,i))
            frun.write('cd ..\n')
            frun.write('rm -rf job%i_%s\n'%(i,pr))
            print pr

            if mode=='batch':
                cmdBatch="bsub -M 2000000 -R \"rusage[pool=2000]\" -q %s -cwd%s %s" %(queue, logdir,logdir+'/'+frunname)
                batchid=-1
                if test==False:
                    job,batchid=SubmitToBatch(cmdBatch,10)
                    nbjobsSub+=job
                    outdict.addjob(sample=pr,jobid=i,queue=queue,nevents=events,status='submitted',log='%s/LSFJOB_%i'%(logdir,int(batchid)),out='%s%s/events%i.root'%(param.delphes_dir,pr,i),batchid=batchid,script='%s/%s'%(logdir,frunname),inputlhe=LHEfile,plots='none')
            elif mode=='local':
                os.system('./tmp/%s'%frunname)

            else: 
                print 'unknow running mode: %s'%(mode)
            i+=1
    print 'succesfully sent %i  jobs'%nbjobsSub
    outdict.write()



    


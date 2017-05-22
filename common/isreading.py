import json
import os, sys
import time
import datetime

#__________________________________________________________
class isreading():
    def __init__(self,inread, indic):
        self.read=inread
        self.readf = None
        with open(self.read,'r') as f:
            self.readf = json.load(f)

        self.user=os.environ['USER']
        self.dicread=indic
        self.localdic=''

#__________________________________________________________
    def backup(self,code):
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H-%M-%S')
        self.localdic='%s_%s_%s_%s'%(self.dicread,self.user,code,st)
        os.system('cp %s %s'%(self.dicread,self.localdic))
        return


#__________________________________________________________
    def comparedics(self,nf=0,ns=0):
        size_ld=os.path.getsize(self.localdic)
        size_od=os.path.getsize(self.dicread)
        ns_local=0
        ns_read=0
        nf_local=0
        nf_read=0

        with open(self.localdic,'r') as f:
            try:
                readf = json.load(f)
                for s in readf:
                    ns_local+=1
                    for j in readf[s]:
                        nf_local+=1
            except ValueError:
                print '\033[91m ----Local dictionnary is corrupted, can not be opened----  \033[0m'
                print '\033[91m ----Please contact clement.helsens@cern.ch or michele.selvaggi@cern.ch---- \033[0m'
                return
            
            
        with open(self.dicread,'r') as f:
            try:
                readf = json.load(f)
                for s in readf:
                    ns_read+=1
                    for j in readf[s]:
                        nf_read+=1
            except ValueError:
                print '\033[91m ----Official dictionnary is corrupted, can not be opened----  \033[0m'
                print '\033[91m ----Please contact clement.helsens@cern.ch or michele.selvaggi@cern.ch---- \033[0m'
                return

        print 'ns_read ',ns_read,'  ns_local  ',ns_local,'  nf_read  ',nf_read,'  nf_local  ',nf_local
        if nf==0 and ns==0:
            if nf_read>nf_local:
                print 'entries have been correctly added. remove local dictionnary.'
                os.system('rm %s'%(self.localdic))
            elif nf_read==nf_local and ns_read==ns_local:
                print 'no entries have been added, only changed job status. Remove local dictionnary.'
                os.system('rm %s'%(self.localdic))
            else:
                print '\033[91m ----Entries have been incorrectly added, dictionnary is truncated----  \033[0m'
                print '\033[91m ----Please contact clement.helsens@cern.ch or michele.selvaggi@cern.ch---- \033[0m'

        elif nf==0 and ns!=0:
            if ns_read+ns==ns_local:
                print '%i samples have been removed. Remove local dictionnary.'%ns
                os.system('rm %s'%(self.localdic))

        else:
            if nf_read+nf>nf_local:
                print 'entries have been correctly added. remove local dictionnary.'
                os.system('rm %s'%(self.localdic))
            elif nf_read+nf==nf_local and ns_read==ns_local:
                print '%i entries have been removed, for failed jobs. Remove local dictionnary.'%nf
                os.system('rm %s'%(self.localdic))
            else:
                print '\033[91m ----Entries have been incorrectly added, dictionnary is truncated----  \033[0m'
                print '\033[91m ----Please contact clement.helsens@cern.ch or michele.selvaggi@cern.ch---- \033[0m'


        return

#__________________________________________________________
    def finalize(self):
        if self.readf['read']['value'] == "True":
            self.readf['read']['value'] = "False"
        else:
            print 'unknown value, not sure why you are here: ',self.readf['read']['value']
        self.write()


#__________________________________________________________
    def reading(self):
        if self.readf['read']['value'] == "True":
            print 'can not run jobs now, an other script is already linked to the dictonary, please retry a bit later.'
            print 'If it continues to happend, please contact clement.helsens@cern.ch or michele.selvaggi@cern.ch'
            sys.exit(3)
        elif self.readf['read']['value'] == "False":
            self.readf['read']['value'] = "True"
        else:
            print 'unknown value: ',self.readf['read']['value']
        self.write()
        return
 
#__________________________________________________________
    def write(self):
        with open(self.read, 'w') as f:
            json.dump(self.readf, f)
        return

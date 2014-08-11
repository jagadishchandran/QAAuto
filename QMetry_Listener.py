import os.path
import tempfile
import sys
import IntegrateQMetry
import datetime

class QMetry_Listener:
    ROBOT_LISTENER_API_VERSION = 2    
    

    def __init__(self, QMetry_Project, QMetry_Release, QMetry_Build, QMetry_RunTimeFolder, filename='listen.txt'):
        outpath = os.path.join(tempfile.gettempdir(), filename)
        self.outfile = open(outpath, 'w')        
        RunTime_TestFolder_Name = ''       
        self.QMetryProject=QMetry_Project
        self.QMetryRelease=QMetry_Release
        self.QMetryBuild=QMetry_Build
        self.RunTime_TestFolder_Name = QMetry_RunTimeFolder  
		
    def start_suite(self, name, attrs):
        self.outfile.write("%s '%s'\n" % (name, attrs['doc']))         
        self.Test_Suite_Name = name 		
        sys.stderr.write('Project Name: %s\n'  % self.QMetryProject)
        sys.stderr.write('Release Name: %s\n'  % self.QMetryRelease)
        sys.stderr.write('Build Name: %s\n'  % self.QMetryBuild)		
				
    def start_test(self, name, attrs):
        tags = ' '.join(attrs['tags'])
        self.outfile.write("- %s '%s' [ %s ] :: " % (name, attrs['doc'], tags))
        sys.stderr.write('Run Time Folder Name Created in QMetry: %s\n'  % self.RunTime_TestFolder_Name)

    def start_keyword(self, name, attrs):
        self.outfile.write("Executing Keyword %s" % name)
		
    def end_test(self, name, attrs):
        if attrs['status'] == 'PASS':
            stat = 'Pass'
        else:
            stat = 'Fail'
        test = IntegrateQMetry.IntegrateQMetry()
        flag = test.update_Test_Case(self.QMetryProject,self.QMetryRelease,self.QMetryBuild,'QA',self.RunTime_TestFolder_Name,self.Test_Suite_Name,'RFW-POC',name,stat,'Update')        

    def end_suite(self, name, attrs):
        self.outfile.write('%s\n%s\n' % (attrs['status'], attrs['message']))

    def close(self):
        self.outfile.close()
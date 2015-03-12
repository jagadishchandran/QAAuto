import os.path
import tempfile
import sys
import IntegrateQMetry
import IntegrateJira
import datetime

class QMetryJira_Listener:
    ROBOT_LISTENER_API_VERSION = 2    
    

    def __init__(self, QMetry_Project, QMetry_Release, QMetry_Build, QMetry_RunTimeFolder, UpdateQMetry, UpdateJira,  filename='listen.txt'):
        outpath = os.path.join(tempfile.gettempdir(), filename)
        self.outfile = open(outpath, 'w')
        RunTime_TestFolder_Name = ''
        self.QMetryProject=QMetry_Project
        self.QMetryRelease=QMetry_Release
        self.QMetryBuild=QMetry_Build
        self.RunTime_TestFolder_Name = QMetry_RunTimeFolder
        self.UpdateQMetry=UpdateQMetry
        self.UpdateJira=UpdateJira
		
    def start_suite(self, name, attrs):
        self.outfile.write("%s '%s'\n" % (name, attrs['doc']))         
        self.Test_Suite_Name = name 		
        sys.stderr.write('Project Name: %s\n'  % self.QMetryProject)
        sys.stderr.write('Release Name: %s\n'  % self.QMetryRelease)
        sys.stderr.write('Build Name: %s\n'  % self.QMetryBuild)
        sys.stderr.write('Update QMetry: %s\n'  % self.UpdateQMetry)
        sys.stderr.write('Update Jira: %s\n'  % self.UpdateJira)		
				
    def start_test(self, name, attrs):
        tags = ' '.join(attrs['tags'])
        self.outfile.write("- %s '%s' [ %s ] :: " % (name, attrs['doc'], tags))
        sys.stderr.write('Run Time Folder Name Created in QMetry: %s\n'  % self.RunTime_TestFolder_Name)

    def start_keyword(self, name, attrs):
        self.outfile.write("Executing Keyword %s" % name)
		
    def end_test(self, name, attrs):
        sys.stderr.write('Test case result: %s\n' % attrs['status'].title())
        stat = attrs['status'].title()
        documentation = attrs['doc']
        if self.UpdateQMetry == "1":
            test = IntegrateQMetry.IntegrateQMetry()
            flag = test.update_Test_Case(self.QMetryProject,self.QMetryRelease,self.QMetryBuild,'QA',self.RunTime_TestFolder_Name,self.Test_Suite_Name,'RFW-POC',name,stat,'Update')
        if (self.UpdateJira == "1" and stat == 'Fail'):
            bug = IntegrateJira.IntegrateJira()
            bugcreate = bug.update_defect(self.QMetryProject,name,documentation)

			
			

    def end_suite(self, name, attrs):
        self.outfile.write('%s\n%s\n' % (attrs['status'], attrs['message']))

    def close(self):
        self.outfile.close()
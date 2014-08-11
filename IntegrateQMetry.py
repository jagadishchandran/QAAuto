from suds.client import Client
from suds.xsd.doctor import ImportDoctor, Import
#from xml.dom.minidom import parse
#import xml.dom.minidom
import xml.etree.ElementTree as ET

# To download suds go to
#       https://fedorahosted.org/suds/
# 1. Download python-suds-0.4.tar.gz
# 2. Run python setup.py install
# Notes: 1. '&' in XML has to be like '&amp;'
class IntegrateQMetry:

    DEBUG_ON = True
    FOLDER_TYPES = ['Requirement', 'Testcase', 'Testsuite']
    TEST_CASE_STATUS = ['Pass', 'Fail', 'NotRun', 'Blocked', 'Not Applicable']
    QMETRY_PROJECT = 'eCL_RegressionSuite'                   # QMetry Project Name
    QMETRY_RELEASE = 'appraisal workflow'                         # QMetry Release Name
    QMETRY_BUILD = 'Release 1'                             # QMetry Build Name

    url = 'http://10.134.8.17/qmetry/WEB-INF/ws/service.php?wsdl'
    
    # Create SOAP Client
    # Then use python suds library to call the services exposed by QMetry WSDL
    #imp = Import('http://schemas.xmlsoap.org/soap/encoding/')
    #imp.filter.add('http://www.wso2.org/php/xsd')
    #impDoc = ImportDoctor(imp)
    __client = Client(url)

    #########################################
    # Function: get_QMetry_Auth_Token
    # Login QMetry and get Authentication Token
    def get_QMetry_Auth_Token(self, QMetry_Project=QMETRY_PROJECT, \
                                    QMetry_Release=QMETRY_RELEASE, \
                                    QMetry_Build=QMETRY_BUILD):
        
        QMETRY_USERNAME = 'QMetryQARJ'          # QMetry User name
        QMETRY_PASSWORD = 'DTpass11'         # QMetry Password

        # Log into QMetry and get authentication token
        authToken = ''
        if (QMETRY_USERNAME == '' or QMETRY_PASSWORD == ''):
            print 'Please provide user name and password for QMetry!'
            return authToken
        try:
            authToken = self.__client.service.login(QMETRY_USERNAME, QMETRY_PASSWORD)
            print 'IntegrateQMetry.py - Log into QMetry and get Token: ' + authToken
        except:
            print 'IntegrateQMetry.py - Got Exception when try to get authentication token!'
            return authToken
        try:
            #Set Scope
            message = self.__client.service.setScope(authToken,\
                                              QMetry_Project,\
                                              QMetry_Release,\
                                              QMetry_Build)
            print 'IntegrateQMetry.py - Set scope and get message: ' + message
            #self.QMETRY_BUILD = QMetry_Build
            return authToken
        except Exception, e:
            print 'IntegrateQMetry.py - Cannot set scope! ' + str(e)
            self.__client.service.logout(authToken)
            return authToken
    
    def logout_QMetry(self, authToken):
        self.__client.service.logout(authToken)


    #########################################
    # Function: get_Release_List
    def get_Release_List(self, QMetry_Project, QMetry_Release, QMetry_Build):
        authToken = self.get_QMetry_Auth_Token(QMetry_Project, QMetry_Release, QMetry_Build)
        releaseList = self.__client.service.listReleases(authToken)
        for release in releaseList:
            print 'IntegrateQMetry.py - Release: ' + release.name
            self.__client.service.setRelease(authToken, release.name)
        self.__client.service.logout(authToken)
        return releaseList
    #########################################
    # Function: get_Folder_List
    # folderType = Requirement, Testcase or Testsuite
    # otherwise will list all folders under the scope
    def get_Folder_List(self, authToken, folderType=''): 

        folderList = []
        if (folderType in self.FOLDER_TYPES):
            folderList = self.__client.service.listFolders(authToken, folderType)
        else:
            print 'IntegrateQMetry.py - List all folders since FolderType is not provided properly!'
            for type in self.FOLDER_TYPES:
                folderList.extend(self.__client.service.listFolders(authToken, type))

        if (len(folderList) == 0):
            print 'IntegrateQMetry.py - No folder found!'
        elif (self.DEBUG_ON):   #For Debug
            for folderDetail in folderList:
                print '========================================================'
                print 'IntegrateQMetry.py - Folder Name: ' + folderDetail.name
                print 'IntegrateQMetry.py - Folder description: ' + repr(folderDetail.description)
                print 'IntegrateQMetry.py - Folder id: ' + repr(folderDetail.id)
                print 'IntegrateQMetry.py - Folder parent id: ' + repr(folderDetail.parentId)
            print '========================================================'

        return folderList

    #########################################
    # Function: get_Scope_Root_Folder
    # Return root folder info (name, ID ...) under current scope
    # folderType = Requirement, Testcase or Testsuite
    def get_Scope_Root_Folder(self, authToken, folderType): 

        folderDetail = None
        folderList = []
        if (folderType in self.FOLDER_TYPES):
            folderList = self.get_Folder_List(authToken, folderType)
        else:
            print 'IntegrateQMetry.py - FolderType is not provided properly!'
        if (len(folderList) != 0):
            for folder in folderList:
                if (folder.parentId == 0):
                    folderDetail = folder
                    break
            if (self.DEBUG_ON):   #For Debug
                print '========================================================'
                print 'IntegrateQMetry.py - Root Folder Name: ' + folderDetail.name
                print 'IntegrateQMetry.py - Root Folder description: ' + repr(folderDetail.description)
                print 'IntegrateQMetry.py - Root Folder id: ' + repr(folderDetail.id)
                print 'IntegrateQMetry.py - Root Folder parent id: ' + repr(folderDetail.parentId)
                print '========================================================'

        return folderDetail

    #########################################
    # Function: parse_FolderString
    # folderString: "folder1/folder2/folder3"
    #             or "folder1\\folder2\\folder3"
    # return: folder list like [folder1,folder2,fodler3]
    def parse_FolderString(self, authToken, folderString):

        newFolderString = folderString.replace('\\', '/')
        folderList = newFolderString.split('/')
        # If the root folder is "build" name or "project" name, then remove it
        if (self.QMETRY_BUILD == folderList[0] or 
            self.QMETRY_PROJECT == folderList[0]):
            del folderList[0]

        for folder in folderList:
            if (folder == ''):
                folderList.remove(folder)

        if (self.DEBUG_ON):
            print folderList
        return folderList

    #########################################
    # Function: get_FolderId_By_PId
    # When some sub folders have same name
    # We need to call this function using
    # folder name and its parent folder ID
    # to find out its ID.
    # folderList: the whole folders list of
    #             Test Case or Test Suite
    def get_FolderId_By_PId(self, authToken, folderName, \
                             parentFolderId, folderList):

        folderId = -1
        for folder in folderList:
            if (folderName == folder.name and \
                parentFolderId == folder.parentId):
                folderId = folder.id
                break
        return folderId

    #########################################
    # Function: get_Child_Folder_Id
    # folderString: "folder1/folder2/folder3"
    #             or "folder1\\folder2\\folder3"
    # We have to assume the "folder1" is unique
    # folderType: Testcase or Testsuite
    # Return the folder Id of "folder3".
    def get_Child_Folder_Id(self, authToken, folderString, folderType):

        folderNameList = self.parse_FolderString(authToken, folderString)
        wholeFolderList = self.get_Folder_List(authToken, folderType)
        parentFolderId = -1

        for folder in wholeFolderList:
            if (folderNameList[0] == folder.name):
                parentFolderId = folder.id
        # Don't need the first folder any more since got its ID
        del folderNameList[0]
        for folderName in folderNameList:
            parentFolderId = self.get_FolderId_By_PId(authToken, \
                             folderName, parentFolderId, wholeFolderList)
            if (self.DEBUG_ON):
                print 'IntegrateQMetry.py - Folder Name: ' + folderString
                print 'IntegrateQMetry.py - Folder ID: ' + repr(parentFolderId)
        return parentFolderId

    #########################################
    # Function: get_Test_Suite_List
    def get_Test_Suite_List(self, authToken):

        #listTestSuitesFromFolderId(string token, int folderId)
        #folderId - Folder Id (0 to list all Test Suite)
        testSuiteList = self.__client.service.listTestSuitesFromFolderId(authToken, 0)
        if (len(testSuiteList) == 0):
            print 'IntegrateQMetry.py - No Test Suite Found!'
        elif (self.DEBUG_ON):    #For Debug
            for testSuite in testSuiteList:
                print '========================================================'
                print 'IntegrateQMetry.py - Folder Path: ' + testSuite.folderPath
                print 'IntegrateQMetry.py - Test Suite Name: ' + testSuite.name
                print 'IntegrateQMetry.py - Test Suite ID: ' + repr(testSuite.id)
            print '========================================================'

        return testSuiteList

    #########################################
    # Function: get_Test_Suite_And_Case_List
    def get_Test_Suite_And_Case_List(self, authToken):

        testSuiteList = self.__client.service.listTestSuitesFromFolderId(authToken, 0)
        if (len(testSuiteList) == 0):
            print 'IntegrateQMetry.py - No Test Suite Found!'
        else:
            for testSuite in testSuiteList:
                print '========================================================'
                print 'IntegrateQMetry.py - Folder Path: ' + testSuite.folderPath
                print 'IntegrateQMetry.py - Test Suite Name: ' + testSuite.name
                print 'IntegrateQMetry.py - Test Suite ID: ' + repr(testSuite.id)
                try:
                    testCaseList = self.__client.service.listTestCases(authToken, {'key': 'testsuiteid', 'value': testSuite.id})
                except Exception, e:
                    print 'IntegrateQMetry.py - Error:' + str(e)
                    continue
                for testCase in testCaseList:
                    print '\tIntegrateQMetry.py - Test Case Name: ' + testCase.name
                    print '\tIntegrateQMetry.py - Test Case ID: ' + repr(testCase.id)
            print '========================================================'

    #########################################
    # Function: Export_Test_Suite_And_Case_List
    # Save the test cases grouped by test suite
    # within a build to a XML formatted file.
    def export_Test_Suite_And_Case_List(self, QMetry_Project,\
                                              QMetry_Release,\
                                              QMetry_Build, \
                                              outputFile):

        authToken = self.get_QMetry_Auth_Token(QMetry_Project, QMetry_Release, QMetry_Build)
        if (authToken == ''):
            print 'IntegrateQMetry.py - Could not get authentication token!'
            return False
        if (outputFile == ''):
            outputFile = QMetry_Project + '_' + QMetry_Release + '_' + QMetry_Build + '.xml'

        testSuiteList = self.__client.service.listTestSuitesFromFolderId(authToken, 0)
        if (len(testSuiteList) != 0):
            output = open(outputFile, 'w')
            output.write('<RFTestCaseKeys>\n')
            output.write('<Scope>' + '\n')
            output.write('\t<Project>' + QMetry_Project + '</Project>\n')
            output.write('\t<Release>' + QMetry_Release + '</Release>\n')
            output.write('\t<Build>' + QMetry_Build + '</Build>\n')
            output.write('</Scope>\n')
            count = 0
            for testSuite in testSuiteList:
                count = count + 1
                output.write('<RFTC_KEY value=\"RFTC_KEY ' + repr(count) + '\">\n')
                output.write('\t<comments></comments>\n')
                testSuiteName = testSuite.name.replace('&', '&amp;')
                testSuitePath = testSuite.folderPath.replace('&', '&amp;')
                testSuitePath = testSuitePath.replace('/'+QMetry_Project, '')
                print 'IntegrateQMetry.py - Folder Path: ' + testSuite.folderPath
                output.write('\t<TestSuite name=\"'  + testSuiteName.encode('UTF-8') + \
                             '\" path=\"' + testSuitePath.encode('UTF-8') + '\">\n')

                try:
                    testCaseList = self.__client.service.listTestCases(authToken, {'key': 'testsuiteid', 'value': testSuite.id})
                except Exception, e:
                    print 'IntegrateQMetry.py - Error:' + str(e)
                    output.write('\t</TestSuite>\n')
                    output.write('</RFTC_KEY>\n')
                    continue
                for testCase in testCaseList:
                    testCaseName = testCase.name.replace('&', '&amp;')
                    testCaseName = testCaseName.replace('<', '&lt;')
                    testCaseName = testCaseName.replace('>', '&gt;')
                    print 'IntegrateQMetry.py - Test Case: ' + testCaseName
                    #output.write('\t\t<TestCase>' + testCaseName.encode('UTF-8') +  '</TestCase>\n')
                    output.write('\t\t<TestCase>' + str(testCase.id) +  '</TestCase>\n')
                output.write('\t</TestSuite>\n')
                output.write('</RFTC_KEY>\n')
            output.write('</RFTestCaseKeys>\n')
            output.close()
            tree = ET.parse(outputFile)
            tree.write(outputFile)
        self.__client.service.logout(authToken)
        return True
    #########################################
    # Function: get_Test_Case_List
    # More for debug purpose
    def get_Test_Case_List(self, authToken):

        #listTestCasesFromFolderId(token, folderId, currentscope)
        #folderId - Folder Id (0 to list all Test Cases)
        #currentscope - 1 to list all Test Cases for current Release/Build, 
        #               0 to list All Test Cases belongs to current Project 
        testCaseList = self.__client.service.listTestCasesFromFolderId(authToken, 0, 1)
        if (len(testCaseList) == 0):
            print 'IntegrateQMetry.py - No Test Case Found!'
        elif (self.DEBUG_ON):    #For Debug
            folderPath = ''
            for testCase in testCaseList:
                if testCase.type != 0 and testCase.type == '133':
                    if folderPath != testCase.folderPath:
                        print '========================================================'
                        #print 'Test Case ID: ' + repr(testCase.id)
                        print 'Test Case Folder: ' + testCase.folderPath
                    print '\n\tTest Case Name: ' + testCase.name
                    print '\tTest Case Type: ' + testCase.typeValue
                    folderPath = testCase.folderPath
            print '========================================================'

        return testCaseList

    #########################################
    # Function: is_Folder_Id_Exist
    # folderType = Requirement, Testcase or Testsuite
    # otherwise will search all folders under the scope
    def is_Folder_Id_Exist(self, authToken, folderId=0, folderType=''):
        isExist = False
        debugMessage = 'IntegrateQMetry.py - Folder: ' + repr(folderId) + ' cannot be found!'
        folderList = self.get_Folder_List(authToken, folderType)
        if (len(folderList) != 0):
            for folderDetail in folderList:
                if (folderDetail.id == int(folderId)):
                   debugMessage = 'IntegrateQMetry.py - Folder: ' + repr(folderId) + ' is found!'
                   isExist = True
                   break
        print debugMessage
        return isExist

    #########################################
    # Function: is_Folder_Name_Exist
    # folderType = Requirement, Testcase or Testsuite
    # otherwise will search all folders under the scope
    def is_Folder_Name_Exist(self, authToken, folderName, folderType=''):
        isExist = False
        folderId = self.get_Folder_Id(authToken, folderName, folderType)
        if (folderId != -1):
            isExist = True
        return isExist

    #########################################
    # Function: is_Test_Suite_Exist
    def is_Test_Suite_Exist(self, authToken, testSuitePath, testSuiteName=''):
        isExist = False
        testSuiteId = self.get_Test_Suite_Id(authToken, testSuitePath, testSuiteName)
        if (testSuiteId != 0):
            isExist = True
        return isExist

    #########################################
    # Function: is_Test_Case_Exist
    def is_Test_Case_Exist(self, authToken, testCaseName=''):
        isExist = False
        debugMessage = 'IntegrateQMetry.py - Test Case: ' + testCaseName + ' cannot be found!'
        testCaseList = self.get_Test_Case_List(authToken)
        if (len(testCaseList) != 0):
            for testCase in testCaseList:
                if (testCase.name == testCaseName):
                    debugMessage = 'IntegrateQMetry.py - Test Case: ' + testCaseName + ' is found!'
                    isExist = True
        print debugMessage
        return isExist

    #########################################
    # Function: get_Platform_Id
    def get_Platform_Id(self, authToken, platformName=''):

        platformId = 0
        debugMessage = 'IntegrateQMetry.py - Platform: ' + platformName + ' cannot be found!'
        platformList = self.__client.service.listCustomizedListValues(authToken, 'platform')
        if (len(platformList) != 0):
            for platform in platformList:
                if (platform.name == platformName):
                    debugMessage = 'IntegrateQMetry.py - Platform: ' + repr(platform.id) + ' is found!'
                    platformId = platform.id
                if (self.DEBUG_ON):
                    print '===================================================='
                    print 'IntegrateQMetry.py - Platform Name: ' + platform.name
                    print 'IntegrateQMetry.py - Platform ID: ' + repr(platform.id)

        print debugMessage
        return platformId

    #########################################
    # Function: get_Folder_Id
    def get_Folder_Id(self, authToken, folderName, folderType):
        folderId = -1
        debugMessage = 'IntegrateQMetry.py - Folder: ' + folderName + ' cannot be found!'
        folderList = self.get_Folder_List(authToken, folderType)
        if (len(folderList) != 0):
            for folderDetail in folderList:
                if (folderDetail.name == folderName):
                   debugMessage = 'IntegrateQMetry.py - Folder: ' + folderName + ' is found!'
                   folderId = folderDetail.id
                   break
        print debugMessage
        return folderId

    #########################################
    # Function: get_Test_Suite_Id
    # Return Test Suite ID. 0 - not found
    def get_Test_Suite_Id(self, authToken, testSuitePath, testSuiteName):

        testSuiteId = 0
        debugMessage = 'IntegrateQMetry.py - Test Suite: ' + testSuiteName + ' cannot be Found!'

        testSuiteFolderId = self.get_Child_Folder_Id(authToken, testSuitePath, 'Testsuite')
        if (testSuiteFolderId == -1):
            return testSuiteId

        testSuiteList = self.get_Test_Suite_List(authToken)
        if (len(testSuiteList) != 0):
            for testSuite in testSuiteList:
                if (testSuite.name == testSuiteName and
                    testSuiteFolderId == testSuite.folderId):
                        debugMessage = 'IntegrateQMetry.py - Test Suite: ' + testSuite.name + ' is found!'
                        testSuiteId = testSuite.id
                        break

        print debugMessage
        return testSuiteId

    #########################################
    # Function: get_Test_Case_Id
    def get_Test_Case_Id(self, authToken, testCaseName):

        testCaseId = 0
        debugMessage = 'IntegrateQMetry.py - Test Case: ' + testCaseName + ' cannot be Found!'
        testCaseList = self.get_Test_Case_List(authToken)
        if (len(testCaseList) != 0):
            for testCase in testCaseList:
                if (testCase.name == testCaseName):
                    debugMessage = 'IntegrateQMetry.py - Test Case: ' + testCase.name + ' is found!'
                    testCaseId = testCase.id
        print debugMessage
        return testCaseId

    #########################################
    # Function: _create_Folder
    # To be called inside this file
    # Return: Folder ID or -1 - cannot create folder
    # folderType = "TestCase" OR "TestSuite" OR "Requirement".
    # folderName = 'folder1/folder2/folder3'
    def _create_Folder(self,\
                       authToken, \
                       folderNames='', \
                       folderDesc='', \
                       folderType='', \
                       parentId=-1):
        folderId = -1
        
        if (folderNames == '' ):
            print 'IntegrateQMetry.py - Folder: ' + folderNames + ' cannot be created!'
            return folderId

        # Folder Type has to be provide correctly
        if (folderType not in self.FOLDER_TYPES):
            print 'IntegrateQMetry.py - FolderType is not provided properly!'
            return folderId

        folderNameList = self.parse_FolderString(authToken, folderNames)
        print 'IntegrateQMetry.py - Folders: ' + str(folderNameList )
        wholeFolderList = self.get_Folder_List(authToken, folderType)
        folderId = -1

        for folder in wholeFolderList:
            if (folderNameList[0] == folder.name):
                folderId = folder.id
        if (folderId == -1):
            print 'IntegrateQMetry.py - Creating Folder Name: ' + folderNameList[0]
            print 'IntegrateQMetry.py - Parent folder ID: ' + repr(parentId)
            folderId = self.__client.service.createFolder(authToken, folderNameList[0], folderDesc, folderType, parentId)
        # Don't need the first folder any more since got its ID
        del folderNameList[0]
        for folderName in folderNameList:
            parentFolderId = folderId
            folderId = self.get_FolderId_By_PId(authToken, \
                             folderName, parentFolderId, wholeFolderList)
            if (folderId == -1):
                print 'IntegrateQMetry.py - Creating Folder Name: ' + folderName
                print 'IntegrateQMetry.py - Parent folder ID: ' + repr(parentFolderId)
                folderId = self.__client.service.createFolder(authToken, folderName, folderDesc, folderType, parentFolderId)
            #parentFolderId = folderId
            if (self.DEBUG_ON):
                print 'IntegrateQMetry.py - Folder Name: ' + folderName
                print 'IntegrateQMetry.py - Folder ID: ' + repr(folderId)
        return folderId


        ## Check if folder exists
        #folderId = self.get_Folder_Id(authToken, folderName, folderType)
        #if (folderId != -1):  # Folder already exist
        #    return folderId
        #
        ## Check if parent folder exists
        #parentIdExist = self.is_Folder_Id_Exist(authToken, parentId, folderType)
        #if (not parentIdExist):
        #    print 'IntegrateQMetry.py - Parent folder: ' + repr(parentId) + ' does not exist!'
        #    return folderId
        #
        ## Create folder
        #folderId = self.__client.service.createFolder(authToken, folderName, folderDesc, folderType, parentId)
        #if (folderId > 0):
        #    print 'IntegrateQMetry.py - Folder: ' + folderName + ' has been created!'
        #
        #return folderId

    #########################################
    # Function: create_Folder
    # Return: Folder ID or -1 - cannot be created.
    # folderType = "TestCase" OR "TestSuite" OR "Requirement".
    def create_Folder(self,\
                      QMetry_Project=QMETRY_PROJECT, \
                      QMetry_Release=QMETRY_RELEASE, \
                      QMetry_Build=QMETRY_BUILD, \
                      folderName='', \
                      folderDesc='', \
                      folderType='', \
                      parentId=-1):

        self.DEBUG_ON = False
        folderId = -1

        authToken = self.get_QMetry_Auth_Token(QMetry_Project, QMetry_Release, QMetry_Build)
        if (authToken == ''):
            print 'IntegrateQMetry.py - Could not get authentication token!'
            return folderId

        folderId = self._create_Folder(authToken, folderName, folderDesc, folderType, parentId)

        self.__client.service.logout(authToken)
        return folderId

    #########################################
    # Function: _create_Test_Suite
    # To be called inside this file
    def _create_Test_Suite(self, \
                           authToken, \
                           testSuiteName='', \
                           testSuiteDesc='', \
                           testSuitePath=''):

        testSuiteId = 0
        FOLDER_TYPE_SUITE = 'Testsuite'
        if (testSuiteName == ''):
            print 'IntegrateQMetry.py - Test Suite Parent Name is empty! '
            return testSuiteId

        # Check parent folder
        if (testSuitePath == ''):
            print 'IntegrateQMetry.py - Test Suite Parent Folder name is empty!'
            return testSuiteId

        # Check if parent folder exist. If not, then create one.
        parentFolderId = self.get_Child_Folder_Id(authToken, testSuitePath, FOLDER_TYPE_SUITE)
        if (parentFolderId == -1):
            rootFolder = self.get_Scope_Root_Folder(authToken, FOLDER_TYPE_SUITE)
            if (rootFolder):
                parentFolderId = self._create_Folder(authToken, testSuitePath, '', FOLDER_TYPE_SUITE, rootFolder.id)

        # Check if parent is created
        if (parentFolderId == -1):
            print 'IntegrateQMetry.py - Test Suite Folder cannot be created!'
            return testSuiteId

        # Check if Test Suite exists
        testSuiteExist = self.is_Test_Suite_Exist(authToken, testSuitePath, testSuiteName)
        if (testSuiteExist):
            testSuiteId = self.get_Test_Suite_Id(authToken, testSuitePath, testSuiteName)
            return testSuiteId

        # Create Test Suite
        testSuiteId = self.__client.service.createTestSuite(authToken, testSuiteName, testSuiteDesc, parentFolderId)
        if (testSuiteId > 0):
            print 'IntegrateQMetry.py - Test Suite: ' + testSuiteName + ' has been created!'

        return testSuiteId

    #########################################
    # Function: create_Test_Suite
    # Return Test Suite ID. 
    # 0 - Test Suite wasn't created.
    def create_Test_Suite(self, \
                          QMetry_Project=QMETRY_PROJECT, \
                          QMetry_Release=QMETRY_RELEASE, \
                          QMetry_Build=QMETRY_BUILD, \
                          testSuiteName='', \
                          testSuiteDesc='', \
                          testSuitePath=''):

        self.DEBUG_ON = False
        testSuiteId = 0

        authToken = self.get_QMetry_Auth_Token(QMetry_Project, QMetry_Release, QMetry_Build)
        if (authToken == ''):
            print 'IntegrateQMetry.py - Could not get authentication token!'
            return testSuiteId

        # Create Test Suite
        testSuiteId = self._create_Test_Suite(authToken, testSuiteName, testSuiteDesc, testSuitePath)

        self.__client.service.logout(authToken)
        return testSuiteId

    #########################################
    # Function: _create_Test_Case
    # To be call inside this file
    # parentFolderName: must provide
    # testCaseName:     must provide
    def _create_Test_Case(self, \
                         authToken, \
                         testCaseName='', \
                         testCaseObjective='', \
                         parentFolderName='', \
                         component=0, \
                         testCaseStatus=0, \
                         assignTo=0, \
                         preCondition='', \
                         postCondition='', \
                         priority=0, \
                         executionTime='0', \
                         testcaseType=0, \
                         modifiedReason=0, \
                         testingType=0):

        testCaseId = 0
        FOLDER_TYPE_CASE = 'Testcase'
        if (testCaseName == ''):
            print 'IntegrateQMetry.py - Test Case Name is empty!'
            return testCaseId

        # Check parent folder
        if (parentFolderName == ''):
            print 'IntegrateQMetry.py - Test Case Parent Folder name is empty!'
            return testCaseId

        # Check if parent folder exist. If not, then create one.
        parentFolderId = self.get_Folder_Id(authToken, parentFolderName, FOLDER_TYPE_CASE)
        if (parentFolderId == -1):
            rootFolder = self.get_Scope_Root_Folder(authToken, FOLDER_TYPE_CASE)
            if (rootFolder):
                parentFolderId = self._create_Folder(authToken, parentFolderName, '', FOLDER_TYPE_CASE, rootFolder.id)

        # Check if parent is created
        if (parentFolderId == -1):
            print 'IntegrateQMetry.py - Test Case Parent Folder cannot be created!'
            return testCaseId

        # Check if Test Case exists
        testCaseExist = self.is_Test_Case_Exist(authToken, testCaseName)
        if (testCaseExist):
            testCaseId = self.get_Test_Case_Id(authToken, testCaseName)
            return testCaseId

        # Create Test Case
        testCaseId = self.__client.service.createTestCase(authToken, \
                                                          parentFolderId, \
                                                          testCaseName, \
                                                          testCaseObjective, \
                                                          component, \
                                                          testCaseStatus, \
                                                          assignTo, \
                                                          preCondition, \
                                                          postCondition, \
                                                          priority, \
                                                          executionTime, \
                                                          testcaseType, \
                                                          modifiedReason, \
                                                          testingType)
        if (testCaseId > 0):
            print 'IntegrateQMetry.py - Test Case: ' + testCaseName + ' has been created!'

        return testCaseId

     #########################################
    # Function: create_Test_Case
    # parentFolderName: must provide
    # testCaseName:     must provide
    # Return Test Case ID. 
    # 0 - Test Case wasn't created.
    def create_Test_Case(self, \
                         QMetry_Project=QMETRY_PROJECT, \
                         QMetry_Release=QMETRY_RELEASE, \
                         QMetry_Build=QMETRY_BUILD, \
                         testCaseName='', \
                         testCaseObjective='', \
                         parentFolderName='', \
                         component=0, \
                         testCaseStatus=0, \
                         assignTo=0, \
                         preCondition='', \
                         postCondition='', \
                         priority=0, \
                         executionTime='0', \
                         testCaseType=0, \
                         modifiedReason=0, \
                         testingType=0):

        self.DEBUG_ON = False
        testCaseId = 0

        authToken = self.get_QMetry_Auth_Token(QMetry_Project, QMetry_Release, QMetry_Build)
        if (authToken == ''):
            print 'IntegrateQMetry.py - Could not get authentication token!'
            return testCaseId
        
        # Create Test Case
        testCaseId = self._create_Test_Case(authToken, \
                                            testCaseName, \
                                            testCaseObjective, \
                                            parentFolderName, \
                                            component, \
                                            testCaseStatus, \
                                            assignTo, \
                                            preCondition, \
                                            postCondition, \
                                            priority, \
                                            executionTime, \
                                            testCaseType, \
                                            modifiedReason, \
                                            testingType)


        self.__client.service.logout(authToken)
        return testCaseId


    #########################################
    # Function: import_Test_Case_By_XML
    # Import XMl to QMetry, create folders,
    # test suites and test cases.
    def import_Test_Suite_And_Case_By_XML(self, XMLFile):

        self.DEBUG_ON = False
        isUpdated = False

        # Check XML file
        if (XMLFile == ''):
            print 'IntegrateQMetry.py - The XML file is not provided!'
            return isUpdated
        # Read scope for XML file and will use it to set scope
        try:
            tree = ET.parse(XMLFile)
        except IOError:
           print 'IntegrateQMetry.py - The XML file ' + XMLFile + ' does not exist!'
           return isUpdated
        root = tree.getroot()
        for scope in root.findall('Scope'):
            self.QMETRY_PROJECT = scope.find('Project').text
            self.QMETRY_RELEASE = scope.find('Release').text
            self.QMETRY_BUILD = scope.find('Build').text
        testPlatform = 'IE9'
        testCaseStatus = 'NotRun'
        testCaseFolderName = 'Regression - TestCases'
        for key in root.findall('RFTC_KEY'):
            comments = key.find('comments').text
            for folder in key.findall('TestSuite'):
                testSuitePath = folder.get('path')
                testSuiteName = folder.get('name')
                for case in folder.findall("TestCase"):
                    testCaseId = case.text 
                    isUpdated = self.update_Test_Case_By_TCId(self.QMETRY_PROJECT, \
                                          self.QMETRY_RELEASE, \
                                          self.QMETRY_BUILD, \
                                          testPlatform, \
                                          testSuitePath, \
                                          testSuiteName, \
                                          testCaseFolderName, \
                                          testCaseId, \
                                          testCaseStatus, \
                                          comments)
            
        return isUpdated
    #########################################
    # Function: update_Test_Case_By_Key
    # Using the key to look up XML file
    # and find out test case info.
    def update_Test_Case_By_Key(self,\
                        testPlatform='No Platform', \
                        RFTestCaseKey='', \
                        testCaseStatus='Pass', \
                        XMLFile='TestCaseInfo.xml'):
        self.DEBUG_ON = False
        isUpdated = False

        # Check RFTestCaseKey
        if (RFTestCaseKey == ''):
            print 'IntegrateQMetry.py - RF Test Case Key is empty!'
            return isUpdated

        # Check XML file
        if (XMLFile == ''):
            print 'IntegrateQMetry.py - The XML file is not provided!'
            return isUpdated
        # Read scope for XML file and will use it to set scope
        try:
            tree = ET.parse(XMLFile)
        except IOError:
           print 'IntegrateQMetry.py - The XML file ' + XMLFile + ' does not exist!'
           return isUpdated
        root = tree.getroot()
        for scope in root.findall('Scope'):
            self.QMETRY_PROJECT = scope.find('Project').text
            self.QMETRY_RELEASE = scope.find('Release').text
            self.QMETRY_BUILD = scope.find('Build').text

        for key in root.findall('RFTC_KEY'):
            if (key.get("value") == RFTestCaseKey):
                print 'Found RF Test Case Key: ' + RFTestCaseKey
                comments = key.find('comments').text
                #print 'Comments: ' + comments
                for folder in key.findall('TestSuite'):
                    testSuitePath = folder.get('path')
                    testSuiteName = folder.get('name')
                    print 'Test Suite Folder: ' + testSuitePath
                    print 'Test Suite: ' + testSuiteName
                    for case in folder.findall("TestCase"):
                        testCaseId = case.text 
                        print 'Start to update Test Case: ' + testCaseId
                        # Just use the test case name for its folder
                        testCaseFolderName = testCaseId
                        #isUpdated = self.update_Test_Case(self.QMETRY_PROJECT, \
                        isUpdated = self.update_Test_Case_By_TCId(self.QMETRY_PROJECT, \
                                              self.QMETRY_RELEASE, \
                                              self.QMETRY_BUILD, \
                                              testPlatform, \
                                              testSuitePath, \
                                              testSuiteName, \
                                              testCaseFolderName, \
                                              testCaseId, \
                                              testCaseStatus, \
                                              comments)
                break
        return isUpdated
    #########################################
    # Function: update_Test_Case
    # If testSuite and/or testCase not exist
    # then create it under testSuitePath and /or
    # testCaseFolderName provided.
    # Must call get_QMetry_Auth_Token first to 
    # get authentication token and set scope
    # In QMetry, to execute a Test Case, it must belong to a Test Suite 
    # and this Test Suite must be linked with one or more Platforms. 
    # When a Test Case is linked to Test Suite and Platform, 
    # QMetry generates a unique identifier (Test Case Run Id) for this Test Case. 
    # The ID represents its execution related information and differentiates this 
    # execution with other executions of the same Test Case in different Test Suite or Platform.
    # testCasestatus - Valid values are Pass, Fail, NotRun, Blocked, Not Applicable 
    def update_Test_Case(self,\
                        QMetry_Project=QMETRY_PROJECT, \
                        QMetry_Release=QMETRY_RELEASE, \
                        QMetry_Build=QMETRY_BUILD, \
                        testPlatform='No Platform', \
                        testSuitePath='', \
                        testSuiteName='', \
                        testCaseFolderName='', \
                        testCaseName='', \
                        testCaseStatus='Pass', \
                        comments='Update from Jenkins!'):

        self.DEBUG_ON = False
        isUpdated = False
        authToken = self.get_QMetry_Auth_Token(QMetry_Project, QMetry_Release, QMetry_Build)
        if (authToken == ''):
            print 'IntegrateQMetry.py - Could not get authentication token!'
            return isUpdated

        # Check Test Suite name and Test Case name
        if (testSuiteName == '' or testCaseName == ''):
            print 'IntegrateQMetry.py - Test Suite Name and/or Test Case name is empty!'
            return isUpdated

        # Check Teat Case Status
        if (testCaseStatus not in self.TEST_CASE_STATUS):
            print 'IntegrateQMetry.py - Test Case Status can only be one of Pass, Fail, NotRun, Blocked, or Not Applicable!'
            return isUpdated

        # Get Platform ID. If it doesn't exist (ID=0), then create one
        platformId = self.get_Platform_Id(authToken, testPlatform)
        if (platformId == 0):
            if (self.__client.service.createPlatform(authToken, testPlatform)):
                platformId = self.get_Platform_Id(authToken, testPlatform)
            else:
                print 'IntegrateQMetry.py - Cannot create the platform ' + testPlatform
                return isUpdated
        if (platformId == 0):
                print 'IntegrateQMetry.py - Cannot find the platform ' + testPlatform
                return isUpdated
        #Get the ID of the Test Suite. If it doesn't exist (ID=0), then create one
        testSuiteId = self.get_Test_Suite_Id(authToken, testSuitePath, testSuiteName)
        if (testSuiteId == 0):
            if (testSuitePath == ''):
                print 'IntegrateQMetry.py - Test Suite Folder Name is empty!'
                return isUpdated
            testSuiteId = self._create_Test_Suite(authToken, testSuiteName, '', testSuitePath)
            # link platform to this Test Suite
            self.__client.service.linkPlatformToTestSuite(authToken, testSuiteId, platformId)

        # Check if the platform linked to test suite. If not, then link them.
        #if (platformId == 0):
        linkedPlatformList = self.__client.service.listPlatformsByTestSuite(\
                                                            authToken,\
                                                            testSuiteId)
        isLinked = False 
        if (len(linkedPlatformList) > 0):
            for platformDetail in linkedPlatformList:
                #print 'IntegrateQMetry.py - platform is: ' + platformDetail.name
                #print 'IntegrateQMetry.py - platform ID: ' + repr(platformDetail.id)
                if (platformDetail.name.upper() == testPlatform.upper()):
                    isLinked = True
                    break
        if (not isLinked):
            self.__client.service.linkPlatformToTestSuite(authToken, testSuiteId, platformId)

        # Get Test Case ID. If it doesn't exist (ID=0), then create one
        # and link it to Test Suite.
        testCaseId = self.get_Test_Case_Id(authToken, testCaseName)
        if (testCaseId == 0):
            if (testCaseFolderName == ''):
                print 'IntegrateQMetry.py - Test Case Folder Name is empty!'
                return isUpdated
            testCaseId = self._create_Test_Case(authToken, testCaseName, '', testCaseFolderName)
        print 'IntegrateQMetry.py - TestCase ID =' + repr(testCaseId)
        # Check if test case has been linked to a test suite, then it'll return a run Id.
        testCaseRunID = self.__client.service.getTestCaseRunIds(authToken, testSuiteId, platformId, testCaseId)
        if (len(testCaseRunID) == 0): 
            # Link Test Case to Test Suite.
            linkOk = self.__client.service.linkTestCaseWithTestSuite(authToken, testCaseId, testSuiteId)
            if (not linkOk):
                print 'IntegrateQMetry.py - Test Suite ' + testSuiteName + \
                            ' and Test Case ' + testCaseName + ' cannot be linked!'
                return isUpdated

        print 'IntegrateQMetry.py - Platform ID=' + repr(platformId) + \
                   '. Test Suite ID=' + repr(testSuiteId) + \
                   '. Test Case ID=' + repr(testCaseId)
        if (platformId != 0 and testCaseId != 0):
            try:
                isUpdated = self.__client.service.executeTestCaseWithComments (\
                                                         authToken,\
                                                         testSuiteId, \
                                                         platformId,\
                                                         testCaseId, \
                                                         testCaseStatus, \
                                                         comments)
            except Exception, e:
                print 'IntegrateQMetry.py - Failed to update Test Cases. Error is: ' + str(e)
                self.__client.service.logout(authToken)
                return isUpdated
        self.__client.service.logout(authToken)
        return isUpdated

    def update_Test_Case_By_TCId(self,\
                        QMetry_Project=QMETRY_PROJECT, \
                        QMetry_Release=QMETRY_RELEASE, \
                        QMetry_Build=QMETRY_BUILD, \
                        testPlatform='No Platform', \
                        testSuitePath='', \
                        testSuiteName='', \
                        testCaseFolderName='', \
                        testCaseId=0, \
                        testCaseStatus='Pass', \
                        comments='Update from Jenkins!'):

        self.DEBUG_ON = False
        isUpdated = False
        authToken = self.get_QMetry_Auth_Token(QMetry_Project, QMetry_Release, QMetry_Build)
        if (authToken == ''):
            print 'IntegrateQMetry.py - Could not get authentication token!'
            return isUpdated

        # Check Test Suite name and Test Case name
        if (testSuiteName == ''):
            print 'IntegrateQMetry.py - Test Suite Name and/or Test Case name is empty!'
            return isUpdated

        # Check Teat Case Status
        if (testCaseStatus not in self.TEST_CASE_STATUS):
            print 'IntegrateQMetry.py - Test Case Status can only be one of Pass, Fail, NotRun, Blocked, or Not Applicable!'
            return isUpdated

        # Get Platform ID. If it doesn't exist (ID=0), then create one
        platformId = self.get_Platform_Id(authToken, testPlatform)
        if (platformId == 0):
            if (self.__client.service.createPlatform(authToken, testPlatform)):
                platformId = self.get_Platform_Id(authToken, testPlatform)
            else:
                print 'IntegrateQMetry.py - Cannot create the platform ' + testPlatform
                return isUpdated
        if (platformId == 0):
                print 'IntegrateQMetry.py - Cannot find the platform ' + testPlatform
                return isUpdated
        #Get the ID of the Test Suite. If it doesn't exist (ID=0), then create one
        testSuiteId = self.get_Test_Suite_Id(authToken, testSuitePath, testSuiteName)
        if (testSuiteId == 0):
            if (testSuitePath == ''):
                print 'IntegrateQMetry.py - Test Suite Folder Name is empty!'
                return isUpdated
            testSuiteId = self._create_Test_Suite(authToken, testSuiteName, '', testSuitePath)
            # link platform to this Test Suite
            self.__client.service.linkPlatformToTestSuite(authToken, testSuiteId, platformId)

        # Check if the platform linked to test suite. If not, then link them.
        #if (platformId == 0):
        linkedPlatformList = self.__client.service.listPlatformsByTestSuite(\
                                                            authToken,\
                                                            testSuiteId)
        isLinked = False 
        if (len(linkedPlatformList) > 0):
            for platformDetail in linkedPlatformList:
                #print 'IntegrateQMetry.py - platform is: ' + platformDetail.name
                #print 'IntegrateQMetry.py - platform ID: ' + repr(platformDetail.id)
                if (platformDetail.name.upper() == testPlatform.upper()):
                    isLinked = True
                    break
        if (not isLinked):
            self.__client.service.linkPlatformToTestSuite(authToken, testSuiteId, platformId)

        # Get Test Case by ID. If it doesn't exist, then return with error message.
        try:
            self.__client.service.getTestCaseById(authToken, testCaseId)
        except:
            print 'IntegrateQMetry.py - ERROR. Test Case ' + str(testCaseId) + ' does not exist!'
            return isUpdated

        # Check if test case has been linked to a test suite, then it'll return a run Id.
        testCaseRunID = self.__client.service.getTestCaseRunIds(authToken, testSuiteId, platformId, testCaseId)
        if (len(testCaseRunID) == 0): 
            # Link Test Case to Test Suite.
            linkOk = self.__client.service.linkTestCaseWithTestSuite(authToken, testCaseId, testSuiteId)
            if (not linkOk):
                print 'IntegrateQMetry.py - Test Suite ' + testSuiteName + \
                            ' and Test Case ' + testCaseId + ' cannot be linked!'
                return isUpdated

        print 'IntegrateQMetry.py - Platform ID=' + repr(platformId) + \
                   '. Test Suite ID=' + repr(testSuiteId) + \
                   '. Test Case ID=' + repr(testCaseId)
        if (platformId != 0 and testCaseId != 0):
            try:
                isUpdated = self.__client.service.executeTestCaseWithComments (\
                                                         authToken,\
                                                         testSuiteId, \
                                                         platformId,\
                                                         testCaseId, \
                                                         testCaseStatus, \
                                                         comments)
            except Exception, e:
                print 'IntegrateQMetry.py - Failed to update Test Cases. Error is: ' + str(e)
                self.__client.service.logout(authToken)
                return isUpdated
        self.__client.service.logout(authToken)
        return isUpdated
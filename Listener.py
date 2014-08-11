import os.path
import tempfile
import sys
import IntegrateQMetry
import datetime

class Listener:
    ROBOT_LISTENER_API_VERSION = 2    
    

    def __init__(self, A, B, C):           
        self.QMetryProject=A
        self.QMetryRelease=B
        self.QMetryBuild=C
        sys.stderr.write('Project Name: %s\n'  % self.QMetryProject)
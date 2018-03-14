import json
import os
import requests
from requests.auth import HTTPBasicAuth


class GemmaClientAPI():
    """
    Client from Gemma API
    """
	
    def __init__(self, base_url=None, key="data", *argv, **kwargs):
        if base_url:
            self.base_url = base_url
        else:
            self.base_url = "http://gemma.msl.ubc.ca/rest/v2/"

        self.key = key
        self.data = None
        self.response = None
        self.auth = None
        self.endpoint = None

        if 'dataset' in kwargs.keys():
            self.setDataset(kwargs['dataset'])

    def setCredentials(self, username, password):
        self.auth = HTTPBasicAuth(username, password)
        return

    def setEndpoint(self, endpoint):
        self.clear()
        self.endpoint = endpoint
        return

    def setDataset(self, shortname):
        self.setEndpoint( "datasets/" + shortname )
        return

    def getUrl(self):
        return self.base_url + str(self.endpoint)

    def clear(self):
        self.data = None
        self.response = None

    def getResponse(self):
        if self.response:
            return self.data

        # Call API and return response as JSON
        self.response = requests.get(self.getUrl(), auth=self.auth)
	self.data = self.response.json()

	return self.data

    def isEmpty(self):
        # Checks if response object is empty (e.g. ExpressionExperiment doesn't exist.)
        response = self.getResponse()
        
	if len(response.keys()) < 1:
            return True
        else:
            if self.key not in response.keys():
                raise Exception("Could not find key '"+self.key+"' in response from " + self.url )

            if len( response[self.key] ) < 1:
                return True
            else:
                return False

    def toString(self):
        return json.dumps(self.data)
		
if __name__ == "__main__":
    # Example
    
    g = GemmaClientAPI(dataset = "GSE67130")
    username, password = [os.getenv(x) for x in ["GEMMAUSERNAME", "GEMMAPASSWORD"] ]
    g.setCredentials(username, password)

    print "===== Should exist ====="
    print "response", g.getResponse()
    print "data", g.data
    print "g.isEmpty(): ", g.isEmpty()

    print "===== Should not exist ====="
    g.setDataset("blurrr")
    print "response", g.getResponse()
    print "data", g.data
    print "g.isEmpty(): ", g.isEmpty()

    print "===== Should exist ====="
    g.setDataset("GSE12345")
    print "response", g.getResponse()
    print "data", g.data
    print "g.isEmpty(): ", g.isEmpty()

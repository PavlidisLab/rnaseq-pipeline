import urllib
import json

class Parson():
    """
    Small class to parse JSON objects.
    """
	
    def __init__(self, url, key="data"):
        self.url = url
        self.key = key

    def getResponse(self):
	response = urllib.urlopen(self.url)
	data = json.loads(response.read())
	return data

    def isEmpty(self):
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


    	
		
	

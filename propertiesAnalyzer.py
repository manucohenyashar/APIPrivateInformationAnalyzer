import json

class PropertiesAnalyzer:
    def __init__(self, piiPropertiesFileName):
        
        self.privatePropDic = {}
        if piiPropertiesFileName and piiPropertiesFileName.endswith('.json'):
            with open(piiPropertiesFileName, 'r') as f:  
                self.privatePropDic = json.load(f)

    def analyze(self, parameterName):
        if (len(parameterName) >= 5):
            result = {parameterName:"propertyName_contains-{0}".format(k) for (k,v) in self.privatePropDic.items() for p in v if parameterName.lower() in p.lower()}
        else:
            result = {parameterName:"propertyName_contains-{0}".format(k) for (k,v) in self.privatePropDic.items() for p in v if parameterName.lower() == p.lower()}
        
        return result



        
import json

class ParameterAnalyzer:
    def __init__(self, piiParametersFileName):
        
        self.privateParamsDic = {}
        if piiParametersFileName and piiParametersFileName.endswith('.json'):
            with open(piiParametersFileName, 'r') as f:  
                self.privateParamsDic = json.load(f)

    def analyze(self, parameterName):
        if (len(parameterName) >= 5):
            result = {parameterName:"paramName_contains-{0}".format(k) for (k,v) in self.privateParamsDic.items() for p in v if parameterName.lower() in p.lower()}
        else:
            result = {parameterName:"paramName_contains-{0}".format(k) for (k,v) in self.privateParamsDic.items() for p in v if parameterName.lower() == p.lower()}
        
        return result



        
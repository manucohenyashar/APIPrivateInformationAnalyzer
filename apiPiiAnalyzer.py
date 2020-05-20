from regexAnalyzer import RegexAnalyzer
from parametersAnalyzer import ParameterAnalyzer
from nerAnalyzer import NerAnalyzer

import json
import collections
import optparse

import urllib.parse as urlparse
from urllib.parse import parse_qs

def flatten(x): return [a for i in x for a in flatten(i)] if isinstance(x, list) else [x]


def MergeDictionaries(d1, d2): 
    res = {**d1, **d2} 

    duplicates = set(d1.keys()).intersection(d2.keys())
    if (any(duplicates)):
        ds = [d1, d2]                                                                                                                           
        for k in duplicates:
            l = list(d[k] for d in ds)
            res[k] = flatten(l)

    return res 

def is_json(myjson):
  try:
    json_object = json.loads(myjson)
  except ValueError as e:
    return False
  return True

class ApiPiiAnalyzer(object):
    def __init__(self, regexFile, privateArgFile, nerModelFileFile, nerJarFile):
        
        self.regexAnalayzer = RegexAnalyzer(regexFile) 
        self.parameterAnalyzer = ParameterAnalyzer(privateArgFile) 
        self.nerAnalyzer = None 
        
        if (nerModelFileFile and nerJarFile):
            self.nerAnalyzer = NerAnalyzer(nerModelFileFile, nerJarFile)

    
    def analyzeRequestUri(self, requestString): 
        #dictionary of pii identified in the API request uri
        req_args_pii_dic  = {} 
        arg_pii_dic = {}
        parsed_req = urlparse.urlparse(requestString)
        req_arguments_dir = parse_qs(parsed_req.query)
        for arg_name,arg_values in req_arguments_dir.items():
            arg_pii_dic = MergeDictionaries(arg_pii_dic, self.parameterAnalyzer.analyze(arg_name))
            pii_dic = self.regexAnalayzer.summary(" ".join(arg_values))
            if (any(pii_dic)):
                req_args_pii_dic[arg_name] = pii_dic
        
        return MergeDictionaries(req_args_pii_dic, arg_pii_dic)
    
    def analyzeHeaders(self, headers): 
        """finds the pii in the collection of headers

        Arguments:
            headers {list} -- a list of headers from the request or response objects (e.g. record['headers'] or record['responseHeaders'])

        Returns:
            [dictionary[str,dictionary]] -- dictionary of header names and the pii dictionary computred for the header values 
        """
        headers_pii_dic  = {}
        arg_pii_dic = {} 
        for header in headers:
            header_val = list(header.values())[0]
            header_name = list(header.keys())[0]
            pii_dic = self.regexAnalayzer.summary(header_val)

            if (self.nerAnalyzer):
                ner_dic = self.nerAnalyzer.analyze(header_val)
                if (any(ner_dic)):
                    pii_dic = MergeDictionaries(pii_dic, ner_dic)

            arg_pii_dic = MergeDictionaries(arg_pii_dic, self.parameterAnalyzer.analyze(header_name))
            if (any(pii_dic)):
                headers_pii_dic[header_name] = pii_dic

        return  MergeDictionaries(headers_pii_dic, arg_pii_dic) 

    def analyzePayload(self, payload, parentObj):
        payload_pii_dic  = {} 
        arg_pii_dic = {}
        if (isinstance(payload,dict)):
            for k,v in payload.items():
                payload_pii_dic = MergeDictionaries(payload_pii_dic, self.analyzePayload(v,k))
        elif (isinstance(payload, list)):
            i = 0
            for item in payload:
                payload_pii_dic = MergeDictionaries(payload_pii_dic, self.analyzePayload(item, "{0}-item-{1}".format(parentObj, i)))
        elif isinstance(payload, str) and is_json(payload):
            v = json.loads(payload)
            payload_pii_dic = MergeDictionaries(payload_pii_dic, self.analyzePayload(v,parentObj))      
        else: 
            payload = str(payload)
            pii_dic = self.regexAnalayzer.summary(payload)
            if (self.nerAnalyzer):
                ner_dic = self.nerAnalyzer.analyze(payload)
                if (any(ner_dic)):
                    pii_dic = MergeDictionaries(pii_dic, ner_dic)

            arg_pii_dic = MergeDictionaries(arg_pii_dic, self.parameterAnalyzer.analyze(parentObj))  
            if (any(pii_dic)):
                payload_pii_dic[parentObj] = pii_dic
       
        
        return  MergeDictionaries(payload_pii_dic, arg_pii_dic)     
 
    
    def analyze(self, filepath):
        res = []
        with open(filepath, 'r') as filedata:
            records = json.load(filedata)
            for record in records:
                record_pii = {"id": record['uri']}

                uri_pii = self.analyzeRequestUri(record['uri'])
                if (any(uri_pii)):
                        record_pii['uri_pii'] = uri_pii

                if 'headers' in record.keys():
                    req_header_pii = self.analyzeHeaders(record['headers'])
                    if (any(req_header_pii)):
                        record_pii['req_header_pii'] = req_header_pii
                
                if 'body' in record.keys():
                    req_payload_pii = self.analyzePayload(record['body'], 'request')
                    if (any(req_payload_pii)):
                        record_pii['req_payload_pii'] = req_payload_pii

                if 'responseHeaders' in record.keys():
                    res_header_pii = self.analyzeHeaders(record['responseHeaders'])
                    if (any(res_header_pii)):
                        record_pii['res_header_pii'] = res_header_pii

                if 'responseBody' in record.keys():
                    res_payload_pii = self.analyzePayload(record['responseBody'], 'response')
                    if (any(res_payload_pii)):
                        record_pii['res_payload_pii'] = res_payload_pii

                if (any(record_pii.keys())):
                    res.append(record_pii)
        return res    
                

if __name__ == '__main__':

    parser = optparse.OptionParser() 
    parser.add_option('-i', '--input', action="store", dest="input", default="input.json", help="File path to the json file containing the API payload to analyze")
    parser.add_option('-r', '--regexFile', action="store", dest="regexFile", help="File path to the json file containing the extra regex expressions that define piis") #default="piiRegexs.json"
    parser.add_option('-a', '--privateArgFile', action="store", dest="privateArgFile", default="privateParamaters.json", help="File path to the json file containing the list parameters names that should be considered private ")
    parser.add_option('-m', '--nerModelFileFile', action="store", dest="nerModelFileFile", help="File path to the NER model") #default="./Models/stanford-ner-2018-10-16/classifiers/english.all.3class.distsim.crf.ser.gz"
    parser.add_option('-j', '--nerJarFile', action="store", dest="nerJarFile", help="File path to the NER engine jar") #default="./Models/stanford-ner-2018-10-16/stanford-ner.jar"
    parser.add_option('-o', '--output', action="store", dest="out", default="result.json", help="output file")
    
    options, args = parser.parse_args()

    a = ApiPiiAnalyzer(options.regexFile, options.privateArgFile, options.nerModelFileFile, options.nerJarFile)
    result = a.analyze(options.input)

    with open(options.out, 'w') as outfile:
        json.dump(result, outfile)




               


# coding: utf-8
from apiPiiAnalyzer import ApiPiiAnalyzer
import apiPiiAnalyzer
import unittest
import json


class ApiPiiAnalyzerTestCase(unittest.TestCase):

    def setUp(self):
        self.analyzer = ApiPiiAnalyzer(regexFile="piiRegexs.json", privatePropFile="privateProperties.json" , nerJarFile=None, nerModelFileFile=None )
        
        self.analyzerWithNer = ApiPiiAnalyzer(regexFile="piiRegexs.json", privatePropFile="privateProperties.json" , nerJarFile='./Models/stanford-ner-2018-10-16/stanford-ner.jar', nerModelFileFile="./Models/stanford-ner-2018-10-16/classifiers/english.all.3class.distsim.crf.ser.gz" )

class Test_Helpers(ApiPiiAnalyzerTestCase):

    def test_mergeDictionaries(self):
        d1 = {"a": 1, "b":2}
        d2 = {"c": 3, "d":4}
        d3 = {"a": 1, "b":2, "c": 3, "d":4}
        res = apiPiiAnalyzer.MergeDictionaries(d1,d2)
        self.assertEqual(res, d3)

    def test_mergeDictionariesWithOverlap(self):
        d1 = {"a": 1, "b":2}
        d2 = {"a": 3, "b":4}
        d3 = {"a": [1,3], "b":[2,4]}
        res = apiPiiAnalyzer.MergeDictionaries(d1,d2)
        self.assertEqual(res, d3)

    def test_mergeDictionariesWithOverlapAndMerge(self):
        d1 = {"a": 1, "b":2}
        d2 = {"a": 3, "b":[4,5]}
        d3 = {"a": [1,3], "b":[2,4,5]}
        res = apiPiiAnalyzer.MergeDictionaries(d1,d2)
       
        self.assertEqual(res, d3)

class Test_analyzeRequestUri(ApiPiiAnalyzerTestCase):

    def test_RequestUriWithPiis(self):
        actual = self.analyzer.analyzeRequestUri("GET https://localhost?ssn=123-56-4567&phone=123-456-1111")
        self.assertIn("ssn", actual.keys())       
        self.assertEqual(actual['ssn'][0]['ssn_number'], ['123-56-4567'])
        self.assertEqual(actual['ssn'][1], 'propertyName_contains-personalIdentification')
        self.assertEqual(actual['phone'], {"phones" : ['123-456-1111']})
    def test_RequestUriWithoutPiis(self):
        actual = self.analyzer.analyzeRequestUri("GET https://localhost?p1=xyz")
        self.assertEqual(len(actual.keys()), 0)  
        
class Test_analyzeRequestHeaders(ApiPiiAnalyzerTestCase):  
    def test_headersWithPiis(self):
        headers =  [
            {"ipaddress": "1.2.3.4"},
            {"n": "123-56-4567"}
        ]

        actual = self.analyzer.analyzeHeaders(headers)             
        
        self.assertIn("ipaddress", actual.keys())
        self.assertIn("n", actual.keys())

        self.assertEqual(actual['ipaddress'][0]['ips'], ['1.2.3.4']) 
        self.assertEqual(actual['ipaddress'][1], 'propertyName_contains-ip')  
        self.assertEqual(actual['n']['ssn_number'], ['123-56-4567'])

    def test_headersWithNoPiis(self):
        headers =  [
            {"x": "a"},
            {"y": "b"}
        ]
        actual = self.analyzer.analyzeHeaders(headers)
        self.assertEqual(len(actual.keys()), 0)  

class Test_analyzeRequestPayload(ApiPiiAnalyzerTestCase):
    def test_PayloadWithNoPiis(self):
        body = {"x": "y"}
        actual = self.analyzer.analyzePayload(body, "request")
        self.assertEqual(len(actual.keys()), 0)

    def test_SimplePayloadWithPiis(self):
        body = {"ssn": "123-45-6789"}
        actual = self.analyzer.analyzePayload(body, "request")
        
        self.assertIn("ssn", actual.keys())       
        self.assertEqual(actual['ssn'][0]['ssn_number'], ['123-45-6789'])
        self.assertEqual(actual['ssn'][1], 'propertyName_contains-personalIdentification')    

    def test_ListOfSimplePayloadWithPiis(self):
        body = [{"ssn": "123-45-6789"}, {"address": "23 main st"}] 
        actual = self.analyzer.analyzePayload(body, "request")
        
        self.assertIn("ssn", actual.keys())       
        self.assertEqual(actual['ssn'][0]['ssn_number'], ['123-45-6789'])
        self.assertEqual(actual['ssn'][1], 'propertyName_contains-personalIdentification') 
        self.assertEqual(actual['address'][0]['street_addresses'], ['23 main st'])       
         

    def test_PayloadWithJsonStringWithPii(self):
         body = {"ssn": "123-45-6789"}
         s = json.dumps(body)
         actual = self.analyzer.analyzePayload(s, "request")        
        
         self.assertIn("ssn", actual.keys())       
         self.assertEqual(actual['ssn'][0]['ssn_number'], ['123-45-6789'])
         self.assertEqual(actual['ssn'][1], 'propertyName_contains-personalIdentification')  

class Test_CompleteEntry(ApiPiiAnalyzerTestCase):

    def test_inputTestFile(self):
        
        actual = self.analyzer.analyze("input.json")        

        d0 = {'phone': {'phones': ['123-456-1111']}}
        d1 = {'n': {'ssn_number': ['123-45-6789']}, 'ssn': 'propertyName_contains-personalIdentification'}
        d2 = {'ssn': 'propertyName_contains-personalIdentification', 'n': {'ssn_number': ['123-45-6789']}}
        d3 = {'n': {'ssn_number': ['123-45-6789']}, 'ssn': 'propertyName_contains-personalIdentification'}
        d4 = {'ssn': 'propertyName_contains-personalIdentification', 'n': {'ssn_number': ['123-45-6789']}}

        self.assertEqual(actual[0]['id'], 'GET http://localhost/myapi/op1?phone=123-456-1111')
        self.assertEqual(actual[0]['uri_pii'], d0)

        self.assertEqual(actual[1]['id'], 'POST http://localhost/myapi/op2')
        self.assertEqual(actual[1]['req_header_pii'], d1)

        self.assertEqual(actual[2]['id'], 'PUT http://localhost/myapi/op3')
        self.assertEqual(actual[2]['req_payload_pii'], d2)

        self.assertEqual(actual[3]['id'], 'PUT http://localhost/myapi/op4')
        self.assertEqual(actual[3]['res_header_pii'], d3)

        self.assertEqual(actual[4]['id'], 'PUT http://localhost/myapi/op5')
        self.assertEqual(actual[4]['res_payload_pii'], d4)

    def test_inputTestFileWithCsvSer(self):
        
        results = self.analyzer.analyze("input2.json")
        rows = apiPiiAnalyzer.formatDicAsCsvRows(results)

        r0 = {'Uri': 'POST http://localhost/myapi/op1?phone=123-456-1111&ssn=123-45-6789', 'Payload Area': 'uri_pii', 'Field': 'phone', 'Identified Pii Type': 'phones', 'Value': ['123-456-1111'], 'Field Name Category': ''} 
        r1 = {'Uri': 'POST http://localhost/myapi/op1?phone=123-456-1111&ssn=123-45-6789', 'Payload Area': 'uri_pii', 'Field': 'ssn', 'Identified Pii Type': 'ssn_number', 'Value': ['123-45-6789'], 'Field Name Category': 'personalIdentification'} 
        r2 = {'Uri': 'POST http://localhost/myapi/op1?phone=123-456-1111&ssn=123-45-6789', 'Payload Area': 'req_header_pii', 'Field': 'ssn', 'Identified Pii Type': 'ssn_number', 'Value': ['123-45-6789'], 'Field Name Category': 'personalIdentification'}
        r3 = {'Uri': 'POST http://localhost/myapi/op1?phone=123-456-1111&ssn=123-45-6789', 'Payload Area': 'req_header_pii', 'Field': 'phone', 'Identified Pii Type': 'phones', 'Value': ['+1123-458-1234'], 'Field Name Category': ''} 
        r4 = {'Uri': 'POST http://localhost/myapi/op1?phone=123-456-1111&ssn=123-45-6789', 'Payload Area': 'req_payload_pii', 'Field': 'ssn', 'Identified Pii Type': 'ssn_number', 'Value': ['123-45-6789'], 'Field Name Category': 'personalIdentification'}   
        r5 = {'Uri': 'POST http://localhost/myapi/op1?phone=123-456-1111&ssn=123-45-6789', 'Payload Area': 'req_payload_pii', 'Field': 'phone', 'Identified Pii Type': 'phones', 'Value': ['+1123-458-1234'], 'Field Name Category': ''}
        r6 = {'Uri': 'POST http://localhost/myapi/op1?phone=123-456-1111&ssn=123-45-6789', 'Payload Area': 'res_header_pii', 'Field': 'ssn', 'Identified Pii Type': 'ssn_number', 'Value': ['123-45-6789'], 'Field Name Category': 'personalIdentification'}
        r7 = {'Uri': 'POST http://localhost/myapi/op1?phone=123-456-1111&ssn=123-45-6789', 'Payload Area': 'res_header_pii', 'Field': 'phone', 'Identified Pii Type': 'phones', 'Value': ['+1123-458-1234'], 'Field Name Category': ''}
        r8 = {'Uri': 'POST http://localhost/myapi/op1?phone=123-456-1111&ssn=123-45-6789', 'Payload Area': 'res_payload_pii', 'Field': 'ssn', 'Identified Pii Type': 'ssn_number', 'Value': ['123-45-6789'], 'Field Name Category': 'personalIdentification'} 
        r9 = {'Uri': 'POST http://localhost/myapi/op1?phone=123-456-1111&ssn=123-45-6789', 'Payload Area': 'res_payload_pii', 'Field': 'address', 'Identified Pii Type': '', 'Value': '', 'Field Name Category': 'ip'} 
        r10 = {'Uri': 'POST http://localhost/myapi/op1?phone=123-456-1111&ssn=123-45-6789', 'Payload Area': 'res_payload_pii', 'Field': 'phone', 'Identified Pii Type': 'phones', 'Value': ['+1123-458-1234'], 'Field Name Category': ''} 
    
        self.assertEqual(len(rows), 22)
        self.assertEqual(rows[0], r0)
        self.assertEqual(rows[1], r1)
        self.assertEqual(rows[2], r2)
        self.assertEqual(rows[3], r3)
        self.assertEqual(rows[4], r4)
        self.assertEqual(rows[5], r5)
        self.assertEqual(rows[6], r6)
        self.assertEqual(rows[7], r7)
        self.assertEqual(rows[8], r8)
        self.assertEqual(rows[9], r9)
        self.assertEqual(rows[10], r10)

    
  #  def test_input2TestFileWithNer(self):
  #      
  #      actual = self.analyzerWithNer.analyze("input2.json")
  #      self.assertEqual(actual[0]["req_payload_pii"]["name"]["Person tags by NER"], ['john', 'lennon'])  

if __name__ == '__main__':
    # Auto-detect test classes to reduce friction of adding a new one.
    test_cases = [clas for name, clas in list(locals().items()) if name.startswith('Test')]
    suites = []
    for case in test_cases:
        suites.append(unittest.TestLoader().loadTestsFromTestCase(case))

    all_tests = unittest.TestSuite(suites)
    unittest.TextTestRunner(verbosity=2).run(all_tests)
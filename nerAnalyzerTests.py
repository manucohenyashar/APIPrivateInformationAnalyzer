from nerAnalyzer import NerAnalyzer
import unittest


class NerAnalyzerTestCase(unittest.TestCase):

    def setUp(self):
        self.analyzer = NerAnalyzer(modelFileFile="./Models/stanford-ner-2018-10-16/classifiers/english.all.3class.distsim.crf.ser.gz", nerJarFile='./Models/stanford-ner-2018-10-16/stanford-ner.jar')

class TestBasicPersonalTagging(NerAnalyzerTestCase):

    def test_basicPersonaltagging(self):
        actual = self.analyzer.analyze('Rami Eid is studying at Stony Brook University in NY at 3 main street Andover MA his phone number is 978-111-1234')
        expected = {'Person tags by NER': ['Rami', 'Eid']}
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    # Auto-detect test classes to reduce friction of adding a new one.
    test_cases = [clas for name, clas in list(locals().items()) if name.startswith('Test')]
    suites = []
    for case in test_cases:
        suites.append(unittest.TestLoader().loadTestsFromTestCase(case))

    all_tests = unittest.TestSuite(suites)
    unittest.TextTestRunner(verbosity=2).run(all_tests)
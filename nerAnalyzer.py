from nltk.tag import StanfordNERTagger

'''
# test
st = StanfordNERTagger('./Models/stanford-ner-2018-10-16/classifiers/english.all.3class.distsim.crf.ser.gz', './Models/stanford-ner-2018-10-16/stanford-ner.jar' )
res = st.tag('Rami Eid is studying at Stony Brook University in NY at 3 main street Andover MA his phone number is 978-111-1234'.split()) 
print(res)
'''

class NerAnalyzer:

    def __init__(self, modelFileFile, nerJarFile):           
        self.st = StanfordNERTagger(modelFileFile, nerJarFile)

    def analyze(self, text):
        result = {}
        if (text):
            tags = self.st.tag(str(text).split())
            personTags = [item[0] for item in tags if item[1] == 'PERSON']
            if (any(personTags)):
                result['Person tags by NER'] = personTags

        return result

    

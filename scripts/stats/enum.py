# data.py 

guidelines = {'Write Short Units of Code':'\\textbf{Write Short}\n\\textbf{Units of Code}\nUnit Size',
                'Write Simple Units of Code':'\\textbf{Write Simple}\n\\textbf{Units of Code}\nMcCabe Complexity',
                'Write Code Once':'\\textbf{Write Code}\n\\textbf{Once}\nDuplication',
                'Keep Unit Interfaces Small':'\\textbf{Keep Unit}\n\\textbf{Interfaces Small}\nUnit Interfacing',
                'Separate Concerns in Modules':'\\textbf{Separate Concerns}\n\\textbf{in Modules}\nModule Coupling',
                'Couple Architecture Components Loosely':'\\textbf{Couple Architecture}\n\\textbf{Components Loosely}\nComponent Independence',
                'Keep Architecture Components Balanced':'\\textbf{Keep Architecture}\n\\textbf{Components Balanced}\nComponent Balance',
                'Write Clean Code':'\\textbf{Write Clean}\n\\textbf{Code}\nCode Smells'}


languages = {'Java': ['java', 'scala', 'js'], 
                'Python': ['py'], 
                'Groovy': ['groovy'], 
                'PHP': ['ctp', 'php', 'inc', 'tpl'], 
                'Objective-C/C++': ['m', 'mm'], 
                'Ruby': ['rb'], 
                'C/C++': ['cpp', 'cc', 'h', 'c'], 
                'Config. Files': ['template', 'gemspec', 'VERSION', 'Gemfile', 'classpath', 'gradle', 'json', 'xml', 'bash', 'lock']}

severity = ['LOW', 'MEDIUM', 'HIGH']

def get_language(key):
    for k, v in languages.items():
        if key in languages[k]:
            return k
    return None

def read_cwe_composites(file):
    composites = {}
    with open(file, 'r') as i:
        f = i.readlines()
        for group in f:
            cwes = group.strip().split('\t')
            if cwes[0] not in composites:
                composites[cwes[0]] = cwes[1::]
    return composites

def check_if_belongs_to_cwe(composites, key):
    if key in composites.keys():
        return key
    for i in composites:
        if key in composites[i]:
            return i
    return None
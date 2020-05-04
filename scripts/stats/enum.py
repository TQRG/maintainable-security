# data.py 

guidelines = {'Write Short Units of Code':'\\textbf{WShortUC}\nUnit Size',
                'Write Simple Units of Code':'\\textbf{WSimpleUC}\nMcCabe Complexity',
                'Write Code Once':'\\textbf{WCO}\nDuplication',
                'Keep Unit Interfaces Small':'\\textbf{KUIS}\nUnit Interfacing',
                'Separate Concerns in Modules':'\\textbf{SCM}\nModule Coupling',
                'Couple Architecture Components Loosely':'\\textbf{CACL}\nComponent Independence',
                'Keep Architecture Components Balanced':'\\textbf{KACB}\nComponent Balance',
                'Write Clean Code':'\\textbf{WCC}\nCode Smells'}

languages = {'Java': ['java', 'scala'], 
                'Python': ['py'], 
                'Groovy': ['groovy'], 
                'JavaScript': ['js'] , 
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
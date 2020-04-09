# data.py 

guidelines = {'Write Short Units of Code':'WShortUC', 
                'Write Simple Units of Code':'WSimpleUC', 
                'Write Code Once':'WCO', 
                'Keep Unit Interfaces Small':'KUIS', 
                'Separate Concerns in Modules':'SCM',
                'Couple Architecture Components Loosely':'CACL', 
                'Keep Architecture Components Balanced':'KACB', 
                'Write Clean Code':'WCC'}

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
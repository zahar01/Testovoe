from bs4 import BeautifulSoup
import json
import os
import copy
import time

class ovalAPI:
    """_summary_
    """

    def __init__(self, path):
        """_summary_

        Args:
            path (_type_): _description_
        """
        self.basePath = path
        self.path = self.basePath / 'module'
        self.savePath = self.basePath / 'data' / 'result_files'
        self.ovalsPath = self.basePath / 'data' / 'ovals'

        self.ovalDict = {
            'namespaces': {},
            'generator' : {
                'product_name' : '',
                'product_version' : '',
                'schema_version' : '',
                'timestamp' : '',
                'content_version' : '',
            },
            'definitions' : [],
            'tests' : [],
            'objects' : [],
            'states' : [],
            'variables' : []
        }

################################################################################################
    # def getCriteria(self, criteria, criteriaTree = {}):
    #     res1 = []
    #     cr1 = {}
    #     cr1 = {**cr1, **criteria.attrs}
    #     cr1['criterion'] = []

    #     for criterion in criteria.find_all('criterion'):
    #         cr1['criterion'].append(criterion.attrs)

    #     res1.append(cr1)

    #     print('LEN --> ', criteria.find_previous_siblings(['criteria', 'criterion']))
    #     print("________")
    #     for criteriaSibling in criteria.find_previous_siblings(['criteria', 'criterion']):
    #         if criteriaSibling.name == 'criteria':
    #             sibl = {}
    #             sibl = {**sibl, **criteriaSibling.attrs}
    #             sibl['criterion'] = []

    #             for criterion in criteriaSibling.find_all('criterion'):
    #                 sibl['criterion'].append(criterion.attrs)

    #             res1.append(sibl)

    #         elif criteriaSibling.name == 'criterion':
    #             sibl = {'criterion':criteriaSibling.attrs}

    #             res1.append(sibl)
            
    #     print(res1)


        # criteriaTree['criterion'] = []
        # criteriaTree = {**criteriaTree, **criteria.attrs}
            # print(criteriaTree)

        # for criterion in criteria.find_all('criterion'):
        #     criteriaTree['criterion'].append(criterion.attrs)

        # newCriteriaTree = {'criteria' : criteriaTree}
        # parent = criteria.find_parent('criteria')

        # if parent:
        #     criteria.clear()
        #     return self.getCriteria(parent, newCriteriaTree)
        # return newCriteriaTree
################################################################################################
        

    def load(self):
        """
        Парсинг овал-файла
        """

        print(f'##########\nПарсинг OVAL файла\n##########\n')
        for file in self.ovalsPath.iterdir():
            if file.is_file():
                print(f"название файла - {file.name}")
                fileDataBS = BeautifulSoup(file.read_text(), "xml")

                self.ovalDict['namespaces'] = fileDataBS.find('oval_definitions').attrs

                generator = fileDataBS.find('generator')
                self.ovalDict['generator']['product_name'] = generator.find('oval:product_name').text
                self.ovalDict['generator']['product_version'] = generator.find('oval:product_version').text
                self.ovalDict['generator']['schema_version'] = generator.find('oval:schema_version').text
                self.ovalDict['generator']['timestamp'] = generator.find('oval:timestamp').text
                self.ovalDict['generator']['content_version'] = generator.find('oval:content_version').text

                defs = fileDataBS.find_all('definition')[0:3]
                for item in defs:
                    definition = {}
                    definition = {**definition, **item.attrs}
                    definition['metadata'] = {}
                    definition['metadata']['title'] = item.find('title').text
                    definition['metadata']['affected'] = { 'platform' : item.find('platform').text }
                    definition['metadata']['affected'] = {**definition['metadata']['affected'], **item.find('affected').attrs}
                    definition['metadata']['references'] = [x.attrs for x in item.find_all('reference')]
                    definition['metadata']['description'] = item.find('description').text
                    definition['metadata']['advisory'] = {}
                    definition['metadata']['advisory'] = {**definition['metadata']['advisory'], **item.find('advisory').attrs}
                    definition['metadata']['advisory']['severity'] = item.find('severity').text
                    definition['metadata']['advisory']['rights'] = item.find('rights').text
                    definition['metadata']['advisory']['issued'] = item.find('issued').attrs['date']
                    definition['metadata']['advisory']['updated'] = item.find('updated').attrs['date']
                    
                    definition['metadata']['advisory']['cve'] = []
                    for cveItem in item.find_all('cve'):
                        cve = { 'cve_id' : cveItem.text}
                        cve = {**cve, **cveItem.attrs}
                        definition['metadata']['advisory']['cve'].append(cve)

                    definition['metadata']['advisory']['bugzilla'] = []
                    for bugItem in item.find_all('bugzilla'):
                        bug = { 'info' : bugItem.text }
                        bug = {**bug, **bugItem.attrs}
                        definition['metadata']['advisory']['bugzilla'].append(bug)
                    
                    definition['metadata']['advisory']['affected_cpe_list'] = [ x.text for x in item.find_all('cpe')]

                    ##################################################################################
                    # criteriaDict = {}
                    # mainCrt = item.find('criteria')

                    # print(item.select('criteria:not(:has(criteria))')[-1])
                    # print('____________')

                    # for cr in item.select('criteria:not(:has(criteria))'):
                        # print('id --> ', definition['id'])
                        # print('cr --> ', cr)
                        # criteriaDict = self.getCriteria(item.select('criteria:not(:has(criteria))')[-1])
                        # break
                        # definition['criteria'] = criteriaDict['criteria']
                        # print(json.dumps(definition['criteria']))

                    # self.ovalDict['definitions'].append(definition)

                    # import xml.etree.ElementTree as ET

                    # path = self.ovalsPath / file.name
                    # tree = ET.parse(path)
                    # root = tree.getroot()
                    # print(root.find("definitions"))
                    # for elem in root.iter():
                    #     print(elem.tag, elem.attrib)

                    ##################################################################################
                    # Сбор критериев оставил на последний момент, пытался делать рекурсивно снизу вверх и наоборот, но бс4 оказался неудобным для этого.
                    # Пока пытался придумать/найти решение, наткнулся на читерску библиотеку, которая автоматически разбирает xml на словарь.
                    # Т.к. у меня все, кроме критериев уже было сделано на бс4, я воспользовался ей только для сбора критериев :)
                    import xmltodict

                    definition['criteria'] = {}
                    obj = xmltodict.parse(f'''{item.find('criteria')}''')
                    definition['criteria'] = obj['criteria']
                    
                    self.ovalDict['definitions'].append(definition)

                print(f'Собрано описаний - {len(self.ovalDict["definitions"])}')

                #Tests
                tests = fileDataBS.find_all(['red-def:rpminfo_test', 'red-def:rpmverifyfile_test', 'ind-def:textfilecontent54_test'])[:100]
                for item in tests:
                    test = {}
                    test = {**test, **item.attrs}

                    try:
                        test['object'] = item.find('red-def:object').attrs if item.find('red-def:object') else {}
                        test['state'] = item.find('red-def:state').attrs if item.find('red-def:state') else {}

                        self.ovalDict['tests'].append(test)
                    except AttributeError:
                        print(f'Что-то пошло не так...\ntestId - {test["id"]}')
                
                print(f'Собрано тестов - {len(self.ovalDict["tests"])}')


                #Objects
                objects = fileDataBS.find_all(['red-def:rpminfo_object', 'red-def:rpmverifyfile_object'])[:100]
                for item in objects:
                    obj = {}
                    obj = {**obj, **item.attrs}

                    if item.name == 'rpminfo_object':
                        obj['name'] = item.find('red-def:name').text
                    elif item.name == 'rpmverifyfile_object':
                        obj['behaviors'] = item.find('red-def:behaviors').attrs
                        obj['name'] = item.find('red-def:name').attrs
                        obj['epoch'] = item.find('red-def:epoch').attrs
                        obj['version'] = item.find('red-def:version').attrs
                        obj['release'] = item.find('red-def:release').attrs
                        obj['arch'] = item.find('red-def:arch').attrs
                        obj['filepath'] = item.find('red-def:filepath').text

                    self.ovalDict['objects'].append(obj)
                
                print(f'Собрано обьектов - {len(self.ovalDict["objects"])}')

                #States
                states = fileDataBS.find_all(['red-def:rpminfo_state', 'red-def:rpmverifyfile_state'])[:100]
                for item in states:
                    state = {}
                    state = {**state, **item.attrs}

                    if item.name == 'rpminfo_state':
                        if item.find('red-def:arch'):
                            state['arch'] = {'architecture' : item.find('red-def:arch').text}
                            state['arch'] = {**state['arch'], **item.find('red-def:arch').attrs}

                        if item.find('red-def:evr'):
                            state['evr'] = {'version' : item.find('red-def:evr').text}
                            state['evr'] = {**state['evr'], **item.find('red-def:evr').attrs}

                        if item.find('red-def:signature_keyid'):
                            state['signature_keyid'] = {'keyid' : item.find('red-def:signature_keyid').text}
                            state['signature_keyid'] = {**state['signature_keyid'], **item.find('red-def:signature_keyid').attrs}

                    if item.name == 'rpmverifyfile_state':
                        if item.find('red-def:name'):
                            state['name'] = {'name_regx' : item.find('red-def:name').text}
                            state['name'] = {**state['name'], **item.find('red-def:name').attrs}

                        if item.find('red-def:version'):
                            state['version'] = {'vers' : item.find('red-def:version').text}
                            state['version'] = {**state['version'], **item.find('red-def:version').attrs}
                        
                        if item.find('red-def:D'):
                            state['D'] = {'d' : item.find('red-def:D').text}
                            state['D'] = {**state['D'], **item.find('red-def:D').attrs}

                    self.ovalDict['states'].append(state)
                
                print(f'Собрано стейтов - {len(self.ovalDict["objects"])}')


                #Variables
                variables = fileDataBS.find_all(['local_variable'])
                for item in variables:
                    variable = {}
                    variable = {**variable, **item.attrs}

                    variable['arithmetic'] = {}

                    variable['arithmetic']['literal_component'] = {'value' : item.find('literal_component').text}
                    variable['arithmetic']['literal_component'] = {**variable['arithmetic']['literal_component'], **item.find('literal_component').attrs}

                    variable['arithmetic']['object_component'] = item.find('object_component').attrs

                    variable['arithmetic'] = {**variable['arithmetic'], **item.attrs}

                    self.ovalDict['variables'].append(variable)
                
                print(f'Собрано переменных - {len(self.ovalDict["variables"])}')

        print(f'\n##########\nПарсинг OVAL файла закончен\n##########')

    
    def replaceTest(self, dictCp, testId):
        dictCp = copy.deepcopy(dictCp)
        test = [x for x in dictCp['tests'] if x['id'] == testId][0]
        objectRef = [x for x in dictCp['objects'] if x['id'] == test['object']['object_ref']][0]
        stateRef = [x for x in dictCp['states'] if x['id'] == test['state']['state_ref']][0]
        test['object']['object_ref'] = objectRef
        test['state']['state_ref'] = stateRef
    
        return test

    def rec(self, current_object, ovalDict):
        try:
            if isinstance(current_object, dict):
                if '@test_ref' in current_object.keys():
                    testId = current_object['@test_ref']
                    current_object['@test_ref'] = self.replaceTest(ovalDict, testId)

                if 'criterion' in current_object.keys():
                    self.rec(current_object['criterion'], ovalDict)

                if 'criteria' in current_object.keys():
                    self.rec(current_object['criteria'], ovalDict)

            if isinstance(current_object, list):
                for item in current_object:
                    if '@test_ref' in item.keys():
                        testId = item['@test_ref']
                        item['@test_ref'] = self.replaceTest(ovalDict, testId)
                    else:
                        self.rec(item, ovalDict)


        except:
            pass

    def convert(self):
        """
        Конвертация в упрощенный формат:
            definition:
                id - идентификатор уязвимости
                title - красткая сводка, заголовок уязвимости
                references - список альтернативных идентификаторов и источников
                affected_cpe_list - я решил убрать поле affected, так как оно не полностью описывает затронутые ОС и оставить детальное перечисление всех затронутых ОС
                issued - дата обнаружения
                updated - дата последнего обновления
                cvss - вектор cvss содержит в себе много полезной информации, например score с оценкой серьезности уязвимости и т.п.
                severity - текстовая оценка критичности уязвимости
                criteria - критерии выявления
                    в criterion буду подставлять сразу тест, обьект и стейт, это будет удобно, например, если описания хранятся в одной БД и не придется прыгать по коллекциям и сслыкам, чтобы проследить связь
        """

        print(f'\n##########\nКонвертация описаний\n##########\n')

        self.convertedDefinitions = []

        for item in copy.deepcopy(self.ovalDict)['definitions']:
            definition = {}
            item = copy.deepcopy(item)
            definition['id'] = item['id']
            definition['title'] = item['metadata']['title']
            definition['references'] = item['metadata']['references']
            definition['affected_cpe_list'] = item['metadata']['advisory']['affected_cpe_list']
            definition['issued'] = item['metadata']['advisory']['issued']
            definition['updated'] = item['metadata']['advisory']['updated']
            definition['severity'] = item['metadata']['advisory']['severity']
            definition['criteria'] = item['criteria']

            self.rec(definition['criteria'], self.ovalDict)

            self.convertedDefinitions.append(definition)

        print(f'Обработано описаний - {len(self.convertedDefinitions)}')
        print(f'\n##########\nКонвертация описаний закончена\n##########\n')


    def save(self):
        """
            Сохранение двух файлов - parsed_OVAL.json (обработанный xml) и converted_definitions.json (конвертированные записи)
        """

        print(f'\n##########\nСохранение\n##########\n')

        if not os.path.isdir(self.savePath):
            os.mkdir(self.savePath)
        
        with open(self.savePath / 'parsed_OVAL.json', 'w') as f:
            f.write(json.dumps(self.ovalDict))
            print(f'Файл parsed_OVAL.json сохранен по пути - {self.savePath}')


        with open(self.savePath / 'converted_definitions.json', 'w') as f:
            f.write(json.dumps(self.convertedDefinitions))
            print(f'Файл converted_definitions.json сохранен по пути - {self.savePath}')

        print(f'\n##########\nСохранение окончено\n##########\n')
        

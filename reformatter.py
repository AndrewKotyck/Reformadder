
from internalfunction import InternalFunction
from datatypes import DataNode, HolderNode, ValueNode, create_holdernode_structure

def merge_function_outputs(output1: list[str]|list[list[str]], output2: list[str]|list[list[str]]) -> None:
    assert len(output1) == len(output2)
    if output1 != [] and isinstance(output1[0], str):
        raise Exception ("MERGING 1D LISTS NOT IMPLEMENTED")
    elif output1 != [] and isinstance(output1[0], list):
        for i in range(len(output1)):
            output1[i].extend(output2[i])
    return output1




class Engine:

    #rawconfig: dict
    internal_functions: dict[str:InternalFunction]
    headers: list[str]

    #config dictionaries
    sections: dict
    sectionname_to_displayname:dict
    nameorder: list
    merges:dict
    max_group_size:int
    name_to_group:dict

    grouporder: list[list[int]]

    root_datanode: DataNode

    _exportsize:int
    testmode:bool
    """
    holds all the important stuff for processing a row of data
    as well as creating a node tree of all processed data,
    and a generator which yields a node path as a reformatted list,
    all according to the config 
    
    """
    """
    planning
    how would i sort the data and what configurability would i want
    convert data into objects nested within each other
        (resp company group -> resp company -> resp -> ratings)
        section relations are obviously static, but column display is modifiable


    <<< data movement >>>
    engine takes in row and spits out class structure
        class structure stored in dict (compn name : class)

    reformatter takes in class structure and spits out reformatted data

    
    
    """
    

    def __init__(self, rawconfig: dict, testmode:bool = False):
        """
        Loads config data and creates function structures for all functions defined in the config
        

        """
        self.root_datanode:HolderNode = HolderNode("0")

        #self.rawconfig = rawconfig
        self.internal_functions = {}

        self.sections:dict = rawconfig["data"]["sections"]
        self.sectionname_to_displayname:dict = rawconfig["data"]["section_to_name"]
        self.nameorder:list = rawconfig["data"]["name_order"]
        self.merges:dict = rawconfig["data"]["merges"]
        self.max_group_size:int = int(rawconfig["data"]["max_group_size"])
        self.name_to_group:dict = {sectionname: sectiondata["group"] for sectionname, sectiondata in self.sections.items()}

        for name, section in self.sections.items():
            self.internal_functions[name] = InternalFunction(section) #, dictionaries)

        self._exportsize = 0
        self.testmode = testmode


    def load_indexes(self, header_row: list[str]):
        self.headers = header_row
        for name in self.internal_functions.keys():
            self.internal_functions[name].get_indexes(header_row)


    def _merge_into_root(self, holderstructure: HolderNode):
        #check if linear holderstructure in root nextnodes
        if holderstructure in self.root_datanode:
            if self.testmode: print(f" --- <<< MERGE - holderstructure in root - MERGE >>> --- \n         \
Rootnode Values: {self.root_datanode._get_nextnode_values()}\n         \
linear HolderNode value: {holderstructure.nodes[-1].value}\n") ##TESTING
            # find node with valuenode match
            for hn in self.root_datanode.nextnodes:
                if holderstructure == hn:
                    hn.nextnodes.extend(holderstructure.nextnodes)
                    #delete holderstructure             make sure memory efficient
            
            return
        if self.testmode: print(f"- < ADD - holderstructure NOT in root - ADD > -   \n    \
Rootnode Values: {self.root_datanode._get_nextnode_values()}\n    \
linear HolderNode value: {holderstructure.nodes[-1].value}\n") ##TESTING
        self.root_datanode.nextnodes.append(holderstructure)


    def eval_row(self, row: list[str]):
        """
        evaluate returns a list(s) (or string? cant rember) for each internal function,
            merge any datasections to be merged
            group em into datanodes based on group,
            merge nodes with main datanode structure
        """
        rowdata: dict = {}
        ## EVALUATE
        for name in self.internal_functions.keys():
            internal_function:InternalFunction = self.internal_functions[name]
            rowdata[name] = internal_function.evaluate(row, self.headers)
        
        ## MERGE DATA
        for mergeto, sectionname in self.merges.items():            
            rowdata[sectionname] = merge_function_outputs(rowdata[sectionname], rowdata[mergeto])
            rowdata.pop(mergeto)
        
        ## CREATE HOLDERNODE STRUCTURE
        groupcount:int = self.max_group_size
        row_holderstructure = create_holdernode_structure(groupcount)
        #print(row_holdernode)

        ## fill holderstructure with new valuenodes based on config names
        row_holderstructure.add_new_valuenodes(rowdata, self.sections, self.sectionname_to_displayname)
        
        if self.testmode: print(row_holderstructure._show_structure(_max_shown_VNs=1)) ##TESTING

        ## MERGE INTO ROOT
        self._merge_into_root(row_holderstructure)



    def row_values(self):
        """
        recursively walk down holdernode structure collecting ValueNodes
        """
        #get collection of valuenodes
        valuenodelist_generator:list[ValueNode] = self.root_datanode.yield_deepest()

        for valuenodes in valuenodelist_generator:
            valuedict: dict = {} # fresh per output row, so no values carry over from the previous row
            #print(valuenodes)
            for valuenode in valuenodes:
                #print(valuenode.display_name, " : ", valuenode.value)
                if isinstance(valuenode.value, tuple):
                    for display_name, value in zip(valuenode.display_name, valuenode.value):
                        valuedict[display_name] = value
                else:
                    valuedict[valuenode.display_name] = valuenode.value
            yield [valuedict[displayname] for displayname in self.nameorder]



class Reformatter:
    engine:Engine
    datalength:int
    testmode:bool

    def __init__(self, configdict:dict, headers:list[str] = [], testmode:bool = False):
        self.engine = Engine(configdict, testmode=testmode)
        if headers != []:
            self.engine.load_indexes(headers)
        
        self.testmode = testmode

    def preprocess_data(self, data: list[list[str]]):
        """
        takes in the dataset, but only uses the first row (headers)
        """
        self.engine.load_indexes(data[0])
        self.datalength = len(data[1:])

    def load_data(self, data: list[list[str]], process_over_time: float = None):
        for row in data[1:]:
            ## sleep/delay by "process_over_time/datalength"
            self.engine.eval_row(row)
        ## update valuenode counts in engine node tree 
        self.engine.root_datanode._update_valuenode_count()
        
        


    def reformat(self, process_over_time: float = None) -> list[list[str]]:
        """
        use engine root_holdernode structure + config name_to_display
        to restructure dataset 
        """
        if self.testmode: 
            print(" - - - < < < ROOTNODE STRUCTURE > > > - - - ") ##TESTING
            print(self.engine.root_datanode) ##TESTING
        print("\n - - - < < < BEGINNING REFORMAT > > > - - - \n") ##TESTING # show always

        output = [self.engine.nameorder]

        data_row_count = self.engine.root_datanode.get_valuenode_count(self.engine.max_group_size)
        
        rowcounter = 0
        ## genna raida
        for newrow in self.engine.row_values():
            ## sleep/delay by "process_over_time/datalength"
            if True: ##TESTING # if self.testmode: #show always
                rowcounter += 1
                # print(data_row_count//10, rowcounter%(data_row_count//10))
                if not rowcounter%(data_row_count//10): print(f"Successfully reformatted rows up to {rowcounter}...")
                
            output.append(newrow)
        else:
            #if self.testmode: 
            print(f"Successfully reformatted all {rowcounter} rows.") # show always
        #if self.testmode: 
        print("\n - - - < < < REFORMAT COMPLETE > > > - - - \n") ##TESTING # show always
        return output




        # if newconfigdict is not None:
        #     self.engine
        






if __name__=="__main__":
    from excelporter import ExcelPorter as ep

    rawdata = input("Enter the filepath of the data to refromat: ")

    configpath = input("Enter the filepath of the config file: ")

    configdict = ep.loadJson(configpath)

    refo = Reformatter(configdict)

    eng = Engine(ep.loadJson(configpath))

    data = ep.loadExcelData_ll(rawdata, rowindexes = [])

    refo.preprocess_data(data)

    refo.load_data(data)

    reformatted = refo.reformat()

    



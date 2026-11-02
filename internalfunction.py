from searchparser import SearchParser
from functiontypes import FUNCTIONS
SET_DATA = ["<value>","<header>","<row>","<column>"]





class FunctionNode:
    value: str
    arguments: list
    _function_name: str
    _function: None
    internal_function: None

    def _split_rawfuncstring(self, functionstring: str) -> tuple[str, list[str]]:
        """
        get index of first bracket - data before is function
        get index of last bracket
        textsplit string when bracket count is equal
        

        """
        #print(functionstring)
        left_bracket_index = functionstring.index("(")
        func = functionstring[0:left_bracket_index]
        right_bracket_index = len(functionstring) - functionstring[::-1].index(")")

        args = []
        arg_string = functionstring[left_bracket_index + 1:right_bracket_index]
        bracketcount = 0
        start_i = 0
        i = 0
        while i < len(arg_string):
            if arg_string[i] == "(":
                bracketcount += 1
            elif arg_string[i] == ")":
                bracketcount -= 1
            elif arg_string[i] == "," and bracketcount == 0:
                args.append(arg_string[start_i:i])
                start_i = i + 1
            i += 1
        else:
            args.append(arg_string[start_i:i-1])
        #print(func, args)
        return (func, args)
        
    def __str__(self) -> str:
        if hasattr(self, "_function") and hasattr(self, "arguments"):
            out = str(self._function_name) + "\n"
            for i in self.arguments:
                out += str(i) + "\n"
            return out
        else:
            return self.value
        
    def __init__(self, functionstring, owner: None) -> None:
        #print(functionstring)
        self.internal_function:InternalFunction = owner

        self.value = None
        self.arguments = []
        
        if "(" in functionstring:
            funcstuff:tuple = self._split_rawfuncstring(functionstring)
            self._function_name = funcstuff[0]
            self._function = FUNCTIONS[funcstuff[0]]
            internal_function_parameters = funcstuff[1]
            for arg in internal_function_parameters:
                self.arguments.append(FunctionNode(arg, self.internal_function))
        elif "{" in functionstring:
            #print("DICTIONARY")
            dict_key = functionstring[1:-1]
            self.value = self.internal_function.dictionaries[dict_key]

        else:
            self.value = functionstring
    
    def evaluate(self) -> None: #, row: list[str]
        #print(type(self.value), self.value)
        row = self.internal_function.row_values
        #headers = self.internal_function.header_values
        if self.value is not None:
            grab: str = self.value
            if grab =="<value>":
                return row
            elif grab == "<header>":
                return self.internal_function.header_values
            elif isinstance(self.value, str):
                return self.value

        args = [argument.evaluate() for argument in self.arguments] # row, headers
        return self._function(*args) # row, headers
            

            

def return_all_indexes(row: list[str], searchparser: SearchParser) -> list[int]:
    out = []
    for i in range(len(row)):
        if searchparser.is_match(row[i]): 
            out.append(i)
    return out
    
def return_index(row: list[str], searchparser: SearchParser, first_index: bool = True) -> int:
    index1 = None
    for i in range(len(row)):
        if searchparser.is_match(row[i]): 
            index1 = i
            if first_index: return index1
    else:
        return index1


def index_lists_intercept(indexlists: list[list[int]]) -> list[int]:
    if len(indexlists) <= 1: return indexlists
    out = indexlists[0]
    for i in range(1,len(indexlists)):
        out = list(set(out) & set(indexlists[i]))
    return out

def get_nested_values_by_index(mainlist: list[list[str]], indexlist: list[int]) -> list[list[str]]:
    outlist = [[] for _ in mainlist]
    for index in indexlist:
        for i in range(len(mainlist)):
            outlist[i].append(mainlist[i][index])
    return outlist


class InternalFunction:
    root_node: FunctionNode
    indexes: list[int]

    grabtype:bool
    start:str
    end:str

    target:list[str]
    group:list[int]
    grouphead: bool = False

    dictionaries:dict
    header_values: list[str]
    row_values: list[str]


    def __init__(self, function_specs: dict, dictionaries: dict = {}):
        
        self.grabtype:bool = bool(function_specs["grab_type_single"])
        self.start:str = function_specs["start"]
        self.end:str = function_specs["end"]
        self.target:list[str] = function_specs["target"]
        rawgroup = function_specs["group"] # DONT NEED
        for i in range(len(rawgroup)): # DONT NEED
            if rawgroup[i][0] == "!": # DONT NEED 
                self.grouphead = True # DONT NEED
                rawgroup[i] = rawgroup[i][1:] # DONT NEED
        self.group:list[int] = [int(item) for item in rawgroup] # error check here # DONT NEED

        self.dictionaries = dictionaries

        raw_function:str = function_specs["function"]
        """
        check which "set" values are needed - <value>,<header>
        
        general flow - get range of indexes - remove all depending on target
         - those indexes go into function

        internalfunction receives indexes, 
        """
        self.root_node = FunctionNode(raw_function, self)
        #print(root_functionnode)

    def get_indexes(self, header_row: list[str]): # clean input data for processing
        index2 = None

        start_sp = SearchParser(self.start)
        index1 = return_index(header_row, start_sp)
        out = [index1] # single value

        if not self.grabtype: #multiple values
            end_sp = SearchParser(self.end)
            index2 = return_index(header_row[index1:], end_sp, False) + index1
            out = list(range(index1,index2 + 1))
        
        if self.target != []: #removing skipped headers from index list
            remove_by_prefix = []
            for item in self.target:
                if item.startswith("<header>"): remove_by_prefix.append(item[item.index(">")+1:])
            
            for remove_val in remove_by_prefix:     # CAN MAKE THIS MORE EFFICIENT
                skip_sp = SearchParser(remove_val)
                indexes = return_all_indexes(header_row, skip_sp)
                out = list(set(out) & set(indexes)) 
        
        #return [header_row[i] for i in out] # UNCOMMENT FOR TESTING
        self.header_values = [header_row[i] for i in out]
        self.indexes = out

    def evaluate(self, row: list[str], headers: list[str]) -> list: # use propagate_args and depending on group, assign to class node structure
        """
        return class structure - nah
        """
        #row_values = [row[i] for i in self.indexes]
        #header_values = [headers[i] for i in self.indexes]

        self.row_values = [row[i] for i in self.indexes]
        values = self.root_node.evaluate()

        remove_values = []
        for item in self.target: # get list of values to remove 
            if item.startswith("<value>"): remove_values.append(item[item.index(">")+1:])
        if remove_values == []: return values

        # THE CODE BELOW FUCKING SUCKS BUT IT WORKS - FUTURE PROJECT - FIX IT
        if values != [] and isinstance(values[0], str): # values contains strings
            for remove_val in remove_values:
                skip_sp = SearchParser(remove_val)
                indexes = return_all_indexes(values, skip_sp)
            return [values[index] for index in indexes]
        elif values != [] and isinstance(values[0], list): # values contains lists of strings
            rawindexlist = []
            for remove_val in remove_values:
                skip_sp = SearchParser(remove_val)
                rawindexlist.append(return_all_indexes(values[-1], skip_sp)) # skipall works off of last val of list returning functions
            return get_nested_values_by_index(values, index_lists_intercept(rawindexlist))
        else: #                                                               MAKE THE ABOVE PATTERN RECURSIVE (currently it is only 2 lists deep)
            raise Exception (f"WHAT IS VALUES??? values type: {type(values)}")
        

    def __str__(self) -> str:
        out = f"Index length: {len(self.indexes)} FunctionNode structure:\n{str(self.root_node)}"
        return out

if __name__ == "__main__":
    abc = r"{name}"
    #print(abc[1:-1])

    abc = "<value>"
    a = abc[abc.index(">")+1:]
    #print(type(a), a=="",len(a))

    aaa = [0,1,2]
    bbb = [3]
    print(aaa + bbb)

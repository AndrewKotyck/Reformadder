


# HELPERS
def _get_between_function_index(string: str, item1: str|int, item2: str|int) -> tuple[int, int]:
    ind1:int = item1
    ind2:int = item2
    if isinstance(item1, str):
        if item1 == "~":
            ind1 = 0
        else:
            ind1 = string.index(item1) + len(item1)
    if isinstance(item2, str):
        if item2 == "~":
            ind2 = len(string)
        else:
            ind2 = string.index(item2)
    return (ind1, ind2)
def _between_function_helper(string: str, item1: str|int, item2: str|int) -> str:
    indexes = _get_between_function_index(string, item1, item2)
    index1 = indexes[0]
    index2 = indexes[1]
    return string[index1:index2]       



# filtersplit
def if_function(*args) -> str|list[str]:
    """
    WIP
    """
    pass

# MAY NOT NEED config - "function":"lookup({role},<value>)",
def lookup_function(*args) -> str|list[str]:
    """
    check if len of args is 2, and optional_args[0] is type dict
    if no lookup found return NOT FOUND IN LOOKUP + value
    """
    dataslice = args[0]
    lookupdict:dict = args[1]
    valuetolookup:str|list[str] = args[2]

    if isinstance(dataslice, str):
        return lookupdict[valuetolookup]
    
    out = []
    for value in valuetolookup:
        out.append(lookupdict[value])
    return out

#join(; ,cross(split(between(<header>,Q3,~),<value>)))
def join_function(*args) -> str|list[str]:
    delimiter:str = args[0]
    values = args[1]
    return [delimiter.join(values)]

def cross_function(*args) -> str|list[str]:
    """
    values - items to be crossed - [a, b, c, d]
    crosses - basically indexes to keep - [1,0,0,1]
    output - [a, d]
    """
    values = args[0][0]
    crosses = args[0][1]
    #print(values, crosses)
    out = []
    for i in range(len(crosses)):
        #print(crosses[i], "1")
        if crosses[i] == "1":
            out.append(values[i])
        else: #     
            pass
            #out.append(values[i])
    #print(out, "\n")
    return out


def between_function(*args) -> str|list[str]:
    dataslice = args[0]
    item1 = args[1]
    item2 = args[2]
    try: item1 = int(item1)
    except: pass
    try: item2 = int(item2)
    except: pass

    if isinstance(dataslice, str):
        return _between_function_helper(dataslice[0], item1, item2)
    
    out = []
    for string in dataslice:
        out.append(_between_function_helper(string, item1, item2))
    return out

def split_function(*args) -> list[list[str]]:
    return args


FUNCTIONS = {
    #"value" : value_function,
    "lookup" : lookup_function,
    "between" : between_function,
    "split" : split_function,
    "join" : join_function,
    "cross" : cross_function
}

            
        

#






if __name__ == "__main__":
    testval1 = "abc_def-ghi"


SEARCH_FUNCTIONS:dict = {
        "start": lambda string, value: string.startswith(value),
        "mid" : lambda string, value: value in string,
        "end" : lambda string, value: string.endswith(value)
    }




def split_raw_pattern(rawpattern: str) -> list[str]:
    out = []
    i1 = 1
    i2 = 0
    while i1 < len(rawpattern) - 1:
        if rawpattern[i1] == "~":
            i1 += 1
            out.append(rawpattern[i2:i1])
            i2 = i1 - 1
        i1 += 1
    else:
        out.append(rawpattern[i2:i1 + 1])
    return out

def categorizer(pattern: str) -> str:
    if pattern[0] == "~":
        if pattern[-1] == "~":
            return ("mid", pattern[1:-1])
        return ("end", pattern[1:])
    else:
        return ("start", pattern[:-1])



class SearchParser:

    patterns:list[str] = []
    not_match:bool = False
    total_match:bool = False
    
    """
    skipall in json should be renamed to "targets"
    
    beginning
    $ - remove all that match
    (blank) - keep all that match
    
    pattern
    ~ - any number of characters

    """

    def __init__(self, raw_pattern: str):
        rawpattern = raw_pattern
        if raw_pattern[0] =="$": 
            self.not_match = True
            rawpattern = raw_pattern[1:]

        if "~" not in rawpattern: 
            self.total_match = True
            self.patterns = rawpattern
            return
        
        temp_patterns = split_raw_pattern(rawpattern)
        self.patterns = [categorizer(ptrn) for ptrn in temp_patterns]

    def is_match(self, value: str) -> bool:
        if self.total_match: 
            if self.not_match: return not value == self.patterns 
            else: return value == self.patterns 
        tempstring = value
        for searchtype, searchvalue in self.patterns:
            if not SEARCH_FUNCTIONS[searchtype](tempstring, searchvalue) or len(searchvalue) > len(tempstring): 
                return True if self.not_match else False
            sv_index = tempstring.index(searchvalue) + len(searchvalue)
            tempstring = tempstring[sv_index:]
        return False if self.not_match else True
            
            

        



if __name__ == "__main__":
    test1 = "abc"
    test2 = "abc~"
    test3 = "~abc"
    test4 = "~abc~"
    test5 = "abc~def"
    test6 = "abc~def~"
    test7 = "~abc~def"
    test8 = "~abc~def~"
    test9 = "abc~def~ghi"
    test10 = "abc~def~ghi~"
    test11 = "~abc~def~ghi"
    test12 = "~abc~def~ghi~"
    
    testpatterns = [test1,test2,test3,test4,test5,test6,test7,test8,test9,test10,test11,test12]
    true_testmatches = ["abc","abcde","zyabc","_abc_","abcxyzdef","abcxyzdefijk","ijkabcxyzdef","ijkabcxyzdefijk","abcdefghi","abc_def_ghi___","____abc_def_ghi","_abc_def_ghi_",]

    #print(len(testpatterns), len(true_testmatches))
    #for i in testcases: print(split_raw_pattern(i))

    searchparsers = []
    for testpattern in testpatterns:
        temp_searchparser = SearchParser(testpattern)
        searchparsers.append(temp_searchparser)
    
    for testmatch, searchparser in zip(true_testmatches, searchparsers):
        #print(searchparser.patterns, "     ", testmatch)
        assert searchparser.is_match(testmatch), f"SearchParser with pattern {searchparser.patterns} FAILED on testmatch: {testmatch}"
        
    




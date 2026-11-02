"""
ExcelPorter
2025-05-08

Andrew Kotyck

Advantage Group International
"""
class Rating:
    subj_compn: str
    comp_code: str
    rating: int

class Respondent:
    fname: str
    lname: str
    email: str
    seniority_codes: list[str]
    role_codes: list[str]
    br_pl_code: str
    bu_cat_codes: list[str]

    ratings: list[Rating]


class Entry:
    responsecode: str
    resp_compn_code: str
    people: list[Respondent]







class DataNode:
    
    previous: None
    
    depth:int
    _spacer:str

    def __init__(self, group: str, previous = None):
        #self.nextitem: DataNode|str = None
        self.group = group
        self.previous:HolderNode = previous

        self.depth:int = None
        if previous is None: 
            self.depth = 0
        else:
            self.depth = self.previous.depth + 1
        
        self._spacer:str ="   "
        #self._spacer = spacer*self.depth



class HolderNode(DataNode):

    group: str
    nodes: list[DataNode]

    #nextnode: DataNode
    nextnodes: list[DataNode]

    _max_shown_VNs:int
    _valuenode_count:int

    def __init__(self, group, previous = None):
        super().__init__(group, previous)
        self.nodes:ValueNode = []

        #self.nextnode:HolderNode = None
        self.nextnodes:list[HolderNode] = []

        self._max_shown_VNs = 5
        self._valuenode_count = 0

        

    def _show_structure_helper(self, indent:str, valuenode_attribute = "value", _max_shown_VNs:int = 5) -> str:
        """
        return valuenode structure
        """
        _indent = indent + self._spacer
        self
        #spacer = self._spacer
        out = ""
        
        if len(self.nodes) > _max_shown_VNs: # lots of valuenodes
            for node in self.nodes[:_max_shown_VNs]: 
                out += f"{_indent}|___ value: {node.__getattribute__(valuenode_attribute)}\n"
            out += f"{_indent}|___ ...plus {len(self.nodes)-_max_shown_VNs} more\n"

        else: # few valuenodes
            for node in self.nodes: 
                out += f"{_indent}|___ value: {node.__getattribute__(valuenode_attribute)}\n"
                
        return out

    def _show_structure(self, indent="", valuenode_attribute = "value", _max_shown_VNs:int = 5) -> str:
        branch = "|" if self.nextnodes != [] else " "

        #show group
        out = indent + f"Group: {self.group} ValueNodes = {len(self.nodes)}\n"

        #add valuenode values
        out += self._show_structure_helper(indent + branch + self._spacer, valuenode_attribute = "value", _max_shown_VNs=_max_shown_VNs)

        if self.nextnodes == []: return out

        for i in range(len(self.nextnodes)):
            nextnode:HolderNode = self.nextnodes[i]
            if i + 1 == len(self.nextnodes):
                out += indent + f"|__\n{nextnode._show_structure(indent + " " + self._spacer, valuenode_attribute = "value", _max_shown_VNs=_max_shown_VNs)}"
                continue
            out += indent + f"|__\n{nextnode._show_structure(indent + branch + self._spacer, valuenode_attribute = "value", _max_shown_VNs=_max_shown_VNs)}"
        return out
    
    def __str__(self):

        return self._show_structure(_max_shown_VNs=self._max_shown_VNs)

        # spacer = self._spacer
        # out = f"Group: {self.group} ValueNodes = {len(self.nodes)}\n"
        # if self.nextnodes == []: return out
        # for nextnode in self.nextnodes:
        #     out += nextnode._show_structure()

    def valuenode_amount(self) -> int:
        pass

    def __eq__(self, node:DataNode) -> bool:
        return self.nodes[-1].value == node.nodes[-1].value
    
    def _get_nextnode_values(self, index: int =-1) -> set:
        return set([hnode.nodes[index].value for hnode in self.nextnodes])

    def __contains__(self, item:DataNode):
        """
        item should be holdernode, the "in" operator is to be used to check if a 
        holdernode has a match within another holdernodes children
        """
        assert isinstance(item, HolderNode), "ITEM to be compared within HolderNode is not HolderNode"
        #self_nextnode_values = [hnode.nodes[-1].value for hnode in self.nextnodes]
        return item.nodes[-1].value in self._get_nextnode_values()

    def get_valuenode_count(self, at_depth:int) -> int:
        if not at_depth: return len(self.nodes)
        vn_count = 0
        for holdernode in self.nextnodes:
            vn_count += holdernode.get_valuenode_count(at_depth-1)
        return vn_count

    def _update_valuenode_count(self) -> int:
        vn_count = len(self.nodes)
        for holdernode in self.nextnodes:
            vn_count += holdernode._update_valuenode_count()
        self._valuenode_count = vn_count
        return vn_count


    def add_new_valuenodes(self, value_dict:dict, sections:dict, sectionname_to_displayname:dict):
        ## DONT UPDATE _valuenode_count HERE. DO IT ALL AT ONCE IN Reformatter ROOT
        for section_name, values in value_dict.items():
            datagroup = sections[section_name]["group"][0]
            display_names = sectionname_to_displayname[section_name]
            target_holdernode:HolderNode = self.get_holdernode_at(datagroup)
            assert target_holdernode is not None, f"HolderNode with group: {datagroup} not found in row_holderstructure"
            if len(values) <= 1: #single value
                target_holdernode.nodes.append(ValueNode(datagroup, target_holdernode, section_name, display_names[0], values[0]))
            else: # multiple values
                for grouped_value in zip(*values):
                    target_holdernode.nodes.append(ValueNode(datagroup, target_holdernode, section_name, tuple(display_names), grouped_value))
        # self._update_valuenode_count()

    def get_holdernode_at(self, group: str) -> DataNode:
        """
        works in branching and linear structure
        group is not an ID
        note to self, make ID's for holdernodes
            ^ use valuenodes
        """
        if self.group == group: return self
        if self.nextnodes is None: return None
        for node in self.nextnodes:
            out = node.get_holdernode_at(group)
            if out is not None: return out
        return None

    def yield_deepest(self, path: list | None = None):
        """
        yields one list per ValueNode at the bottom of the tree:
            [ancestor ValueNodes from the top level down..., this bottom ValueNode]

        path holds only the ValueNodes of THIS branch's ancestors. Each child gets
        its own new list (path + nodes) instead of a shared one being extended,
        so siblings never see each other's values and nothing carries over
        between calls.
        (the old version used a mutable default argument `valuenodes: list = []`,
        which python creates ONCE and reuses forever - it grew with every node
        visited, so each output row re-read every previous row's values: O(n^2))
        """
        if path is None:
            path = []

        if self.nextnodes == []: # bottom level - one output row per ValueNode
            for valuenode in self.nodes:
                yield path + [valuenode]
            return

        for holdernode in self.nextnodes:
            if holdernode.nextnodes != []: # middle level - pass its values down
                child_path = path + holdernode.nodes
            else: # bottom level - its values are yielded one at a time, not passed down
                child_path = path
            yield from holdernode.yield_deepest(child_path)


class ValueNode(DataNode):

    section_name: str
    display_name: str | list[str]

    value: str | tuple[str]

    def __init__(self, group, previous, section_name: str, display_name: str | list[str], value: str | list[str]):
        super().__init__(group, previous)
        self.section_name = section_name 
        self.display_name:str | tuple[str] = display_name 
        self.value:str | tuple[str] = value
    
def create_holdernode_structure(depth: int, _startnum: int = 1, previous: HolderNode = None) -> HolderNode:
    tempnode = HolderNode(str(_startnum), previous)
    if depth == _startnum: return tempnode
    tempnode.nextnodes.append(create_holdernode_structure(depth, _startnum + 1, tempnode))
    return tempnode







if __name__ == "__main__":
    _abc = ["1","2","3"]
    _def = ["a","b","c"]

    # for i, j in enumerate(zip(_abc, _def)):
    #     print(i,j[0],j[1])

    

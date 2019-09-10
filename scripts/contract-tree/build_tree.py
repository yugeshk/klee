#!/usr/bin/env python
# vim: set ts=2 sts=2 sw=2 et si tw=80:

import sys
import string
import os

# https://anytree.readthedocs.io/en/latest/index.html
from anytree import NodeMixin, RenderTree, PostOrderIter
from anytree.search import find, findall_by_attr
from anytree.exporter import DotExporter

tags_file = sys.argv[1]
perf_file = sys.argv[2]
formula_file = sys.argv[3]
perf_metric = sys.argv[4]
tree_file = sys.argv[5]
perf_resolution = int(sys.argv[6])
op_var_file = sys.argv[7]
op_formula_file = sys.argv[8]


class MyNode:

    def __init__(self, name, id, depth):
        self._name = name
        self._id = id
        self._depth = depth
        self._tags = []
        self._perf = -1
        self._sat = 1
        self._formula = ""

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def depth(self):
        return self._depth

    @depth.setter
    def depth(self, value):
        self._depth = value

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, value):
        self._tags = value

    @property
    def perf(self):
        return self._perf

    @perf.setter
    def perf(self, value):
        self._perf = value

    @property
    def formula(self):
        return self._formula

    @formula.setter
    def formula(self, value):
        self._formula = value

    @property
    def sat(self):
        return self._sat

    @sat.setter
    def sat(self, value):
        assert(0 == value or 1 == value)
        self._sat = value


class TreeNode(MyNode, NodeMixin):
    def __init__(self, name, id, depth, parent=None, children=None):
        MyNode.__init__(self, name, id, depth)
        self.parent = parent
        if children:
            self.children = children


traces_perf = {}
traces_tags = {}
traces_perf_formula = {}
unique_tags = list()
perf_var = {}
perf_formula_var = {}

tree_root = TreeNode("ROOT", -1, -1)


def main():
    global tree_root

    get_traces_perf()
    get_traces_tags()
    get_traces_perf_formula()

    with open(tree_file, 'r') as f:
        for line in f:
            text = line.rstrip()
            assert(text[len(text)-1] == ',')
            text = text[:-1]
            sequence = text.split(',')
            subtree_root = tree_root
            depth = 0
            for node_id in sequence:

                next_hop = find(
                    subtree_root, lambda TreeNode: TreeNode.id == node_id and TreeNode.depth == depth)
                if(next_hop):
                    subtree_root = next_hop
                else:
                    if(depth == (len(sequence)-1)):  # Leaf Node
                        node_name = "test"+f"{int(node_id):06d}"
                    else:
                        node_name = "call"

                    node = TreeNode(node_name, node_id, depth,
                                    parent=subtree_root)
                    subtree_root = node

                depth = depth+1

        # Finished constructing tree, now coalesce spurious nodes.
        for node in list(PostOrderIter(tree_root))[:]:

            while(len(node.siblings) == 0):
                # We do not want to coalesce the root or the first node
                if(node.parent == tree_root or node.is_root):
                    break
                else:
                    curr_parent = node.parent
                    new_parent = curr_parent.parent
                    node.parent = new_parent
                    curr_parent.parent = None

        # Let's assign tags and performance resolution now
        for node in list(PostOrderIter(tree_root)):
            if(node.is_leaf):
                if(node.name in traces_perf):  # Trace must be SAT to have a perf
                    node.perf = traces_perf[node.name]
                    node.formula = traces_perf_formula[node.name]
                    if(node.name in traces_tags):
                        node.tags = traces_tags[node.name]

                else:
                    node.perf = -1
                    node.sat = 0
                    node.tags = ["UNSAT"]

            else:
                node.perf = get_perf_variability(node)
                assign_tags(node)

        # Now, let's coalesce nodes with no perf difference!
        for node in list(PostOrderIter(tree_root)):
            if(not node.is_leaf and node.perf < perf_resolution):
                children = list(node.children)
                for child in children:
                    child.parent = None

        # Get perf variability, including formula variability for each tag
        for tag in unique_tags:
            perf_var[tuple(tag)] = set()
            perf_formula_var[tuple(tag)] = set()

        for trace, perf in traces_perf.items():
            if trace in traces_tags:
                perf_var[tuple(traces_tags[trace])].add(perf)
                if(trace in traces_perf_formula):
                    perf_formula_var[tuple(traces_tags[trace])].add(
                        traces_perf_formula[trace])

        with open(op_var_file, "w") as op:
            op.write("#Packet Class #Perf-Variability\n")
            for tag in unique_tags:
                op.write("%s %d\n" %
                         (tag, (max(perf_var[tuple(tag)])
                                - min(perf_var[tuple(tag)]))))

        with open(op_formula_file, "w") as op:
            op.write("#Tag #Formula-Variability\n")
            for tag in unique_tags:
                if(check_for_clarity(perf_formula_var[tuple(tag)])):
                    op.write("%s Clarity was caught\n" % (tag))
                else:
                    op.write("%s Wild Clarity fled\n" % (tag))

            # Pretty printing the contract
            op.write("\n\nContract with Formulae\n\n")
            column1 = "#Packet Class"
            column2 = "#Possible Formulae"
            line_break = "-" * 150 + "\n"
            op.write("%s | \t%s \n\n" %
                     ("{:<75}".format(column1), column2))
            op.write(line_break)
            for tag in unique_tags:
                ctr = 0
                for formula in perf_formula_var[tuple(tag)]:
                    if(ctr == 0):
                        column1 = str(tag)[1:-1]
                    else:
                        column1 = ""
                    op.write("%s |\t%s \n" %
                             ("{:<75}".format(column1), formula))
                    ctr = ctr + 1
                op.write(line_break)

        DotExporter(tree_root,
                    nodenamefunc=node_identifier_fn,
                    nodeattrfunc=node_colour_fn).to_dotfile("tree.dot")


def check_for_clarity(formula_var):
    if(len(formula_var) == 0):
        return False

    pcvs_used = {}
    for formula in formula_var:
        pcvs_used[formula] = list()
        formula_terms = formula.split("+")
        for term in formula_terms:
            term = term.strip()
            if("*" in term):
                pcvs = term.replace("*", "")
            else:
                pcvs = ""
            pcvs_used[formula].append(pcvs)
    expected_pcv_set = set(pcvs_used[list(formula_var)[0]])
    return all(set(pcv_list) == expected_pcv_set for pcv_list in pcvs_used.values())


def assign_tags(node):
    # Returns tags for an intermediate node in the tree.
    # A node has a particular tag iff all its descendants have that tag
    children = list(node.children)
    assert(len(children) > 0)
    children_tags = list(child.tags for child in children)
    node.tags = os.path.commonprefix(children_tags)


def get_perf_variability(node):
    # Returns perf variability for an intermediate node in the tree.
    leaves = list(findall_by_attr(node, 1, name='is_leaf'))
    leaves_perf = list(leaf.perf for leaf in leaves)
    if (-1 in leaves_perf):  # Remove all unsat nodes
        leaves_perf.remove(-1)
    if (len(leaves_perf)):
        return max(leaves_perf) - min(leaves_perf)
    return 0


def node_colour_fn(node):
    if(node.name.startswith("test")):  # Cannot use is_leaf because of perf_var coalescing
        colour = "fillcolor = red,fontcolor = white"
    else:
        colour = "fillcolor = white,fontcolor = black"
    return colour+",style = filled"


def node_identifier_fn(node):
    if(node.name.startswith("test")):  # Cannot use is_leaf because of perf_var coalescing
        identifier = '%s' % (node.name)
        if (node.sat):
            identifier += '\nPerf = %s' % (node.perf)
            identifier += '\nFormula = %s' % (node.formula)

    else:
        identifier = '%s:%s:%s\n Perf Var = %s' % (
            node.name, node.id, node.depth, node.perf)
    tag = str(node.tags)[1:-1]
    tag = tag.replace(", ", "\n")
    identifier += "\n%s" % (tag)
    return identifier


def print_tree(root):
    for pre, _, node in RenderTree(root):
        treestr = "%s%s" % (pre, node.name)
        sys.stdout.buffer.write(treestr.encode('utf-8')+b"\n")


def get_traces_perf():
    global traces_perf
    with open(perf_file, 'r') as f:
        for line in f:
            text = line.rstrip()
            test_id = text[0:
                           find_nth(text, ",", 1)]
            metric = text[(find_nth(text, ",", 1)+1):
                          find_nth(text, ",", 2)]
            perf = text[(find_nth(text, ",", 2)+1):]

            if (metric == perf_metric):
                traces_perf[test_id] = int(perf)


def get_traces_tags():
    global traces_tags
    global unique_tags
    with open(tags_file, 'r') as f:
        lines = f.readlines()  # Small file, so OK.
        # Hack to access next element too
        lines_hack = lines[1:]
        lines_hack.append(None)
        for line, next_line in zip(lines, lines_hack):
            text = line.rstrip()
            test_id = text[0:
                           find_nth(text, ",", 1)]
            tag = text[(find_nth(text, ",", 2)+1):]

            # Assign all tags for current test in a list
            if test_id in traces_tags:
                traces_tags[test_id].append(tag)
            else:
                list_tags = []
                list_tags.append(tag)
                traces_tags[test_id] = list_tags

            # Getting unique tags
            if(next_line != None):
                next_text = next_line.rstrip()
                next_test_id = next_text[0:
                                         find_nth(next_text, ",", 1)]
            else:
                next_test_id = ""

            if(test_id != next_test_id):  # Reached the leaf tag
                if(traces_tags[test_id] not in unique_tags):
                    unique_tags.append(traces_tags[test_id])


def get_traces_perf_formula():
    global traces_perf_formula
    with open(formula_file, 'r') as f:
        for line in f:
            text = line.rstrip()
            test_id = text[0:
                           find_nth(text, ",", 1)]
            metric = text[(find_nth(text, ",", 1)+1):
                          find_nth(text, ",", 2)]
            perf = str(text[(find_nth(text, ",", 2)+1):])

            if (metric == perf_metric):
                traces_perf_formula[test_id] = perf


def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start


main()

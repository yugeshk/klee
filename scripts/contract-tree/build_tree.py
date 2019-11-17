#!/usr/bin/env python
# vim: set ts=2 sts=2 sw=2 et si tw=80:

import sys
import string
import os

# https://anytree.readthedocs.io/en/latest/index.html
from anytree import NodeMixin, RenderTree, PostOrderIter
from anytree.search import find, findall_by_attr
from anytree.exporter import DotExporter

sys.setrecursionlimit(1000000)

tags_file = sys.argv[1]
perf_file = sys.argv[2]
formula_file = sys.argv[3]
perf_metric = sys.argv[4]
tree_file = sys.argv[5]
tree_type = sys.argv[6]
perf_resolution = int(sys.argv[7])
op_var_file = sys.argv[8]
op_formula_file = sys.argv[9]


class MyNode:

    def __init__(self, name, id, depth):
        self._name = name
        self._id = id
        self._depth = depth
        self._tags = []
        self._perf = -1
        self._formula = ""
        self._sub_tests = []

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
    def sub_tests(self):
        return self._sub_tests

    @sub_tests.setter
    def sub_tests(self, value):
        self._sub_tests = value


class TreeNode(MyNode, NodeMixin):
    def __init__(self, name, id, depth, parent=None, children=None):
        MyNode.__init__(self, name, id, depth)
        self.parent = parent
        if children:
            self.children = children


traces_perf = {}
traces_tags = {}
traces_perf_formula = {}
leaf_tags = list()
all_tag_prefixes = list()
perf_var = {}
perf_formula_var = {}
merged_tuples = list()

tree_root = TreeNode("ROOT", -1, -1)


def main():
    global tree_root

    assert(tree_type == "full-tree" or tree_type == "call-tree")
    get_traces_perf()
    get_traces_tags()
    get_traces_perf_formula()

    with open(tree_file, 'r') as f:
        id_ctr = 0
        for line in f:
            text = line.rstrip()
            if(tree_type == "call-tree"):
                assert(text[len(text)-1] == ',')
                text = text[:-1]
                sequence = text.split(',')
                subtree_root = tree_root
                depth = 0
                for node_id in sequence:

                    children = list(subtree_root.children)
                    next_hop = next(
                        (x for x in children if x.id == node_id and x.depth == depth), None)

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

            elif(tree_type == "full-tree"):
                index = find_nth(text, ":", 1)
                leaf_id = text[0:index]
                text = text[index+1:]
                leaf_node_name = "test"+f"{int(leaf_id):06d}"
                if(leaf_node_name in traces_perf):
                    print("inserting node %s" % (leaf_node_name))
                    sequence = text.split(',')
                    subtree_root = tree_root
                    depth = 0
                    for node_id in sequence:
                        children = list(subtree_root.children)
                        next_hop = next(
                            (x for x in children if x.id == node_id and x.depth == depth), None)
                        if(next_hop):
                            subtree_root = next_hop
                        else:
                            if(depth == (len(sequence)-1)):  # Leaf Node
                                node_name = leaf_node_name
                            else:
                                node_name = "branch"+f"{int(id_ctr):06d}"

                            node = TreeNode(node_name, node_id, depth,
                                            parent=subtree_root)
                            subtree_root = node
                            id_ctr = id_ctr + 1

                        subtree_root.sub_tests.append(leaf_node_name)
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
                node.perf = traces_perf[node.name]
                node.formula = traces_perf_formula[node.name]
                if(node.name in traces_tags):
                    node.tags = traces_tags[node.name]

            else:
                node.perf = get_perf_variability(node)
                assign_tags(node)

        # Now, let's coalesce nodes perf variability less than input resolution!
        for node in list(PostOrderIter(tree_root)):
            if(not node.is_leaf and node.perf < perf_resolution):
                children = list(node.children)
                children_perf = list(child.perf for child in children)
                node.perf = int((max(children_perf) + min(children_perf))/2)
                # TODO:HACK HACK HACK. Needs actual coalescing
                node.formula = children[0].formula
                for child in children:
                    child.parent = None

        # Now, let's remove spurious, perf-unrelated branching.
        # This is an iterative process which will repeat until we hit a fixed point
        changed = 1
        while(changed):
            changed = 0

            # First remove spurious branching
            for node in list(PostOrderIter(tree_root)):
                if(not node.is_leaf and not node.is_root):  # Root has only 1 child in our tree
                    children = list(node.children)
                    # Only dealing with binary trees
                    assert(len(children) == 2)
                    merged_tuples.clear()
                    if(compare_trees(children[0], children[1])):
                        # print(merged_tuples)
                        for pair in merged_tuples:
                            # Sanity check that the tuple always has a node from child zero and then child one.
                            # Mostly redundant, but left here in any case
                            assert(len(findall_by_attr(children[0], pair[0], name='name')) == 1
                                   and len(findall_by_attr(children[1], pair[1], name='name')) == 1)
                            final = findall_by_attr(
                                children[0], pair[0], name='name')[0]
                            merged_in = findall_by_attr(
                                children[1], pair[1], name='name')[0]
                            merged_nodes = merged_in.sub_tests
                            final.sub_tests.append(merged_nodes)
                        children[1].parent = None
                        changed = 1

            # Then remove spurious nodes
            if(changed):
                changed = 0
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
                            changed = 1

        # Get perf variability, including formula variability for each tag
        for tag in all_tag_prefixes:
            perf_var[tuple(tag)] = set()
            perf_formula_var[tuple(tag)] = set()

        for trace, perf in traces_perf.items():
            if trace in traces_tags:
                for x in range(1, len(traces_tags[trace])+1):
                    perf_var[tuple(traces_tags[trace][0:x])].add(perf)
                if(trace in traces_perf_formula):
                    for x in range(1, len(traces_tags[trace])+1):
                        perf_formula_var[tuple(traces_tags[trace][0:x])].add(
                            traces_perf_formula[trace])

        with open(op_var_file, "w") as op:
            op.write("#Packet Class #Perf-Variability\n")
            for tag in all_tag_prefixes:
                if(len(perf_var[tuple(tag)])):
                    op.write("%s %d\n" %
                             (tag, (max(perf_var[tuple(tag)])
                                    - min(perf_var[tuple(tag)]))))

        with open(op_formula_file, "w") as op:
            op.write("#Tag #Formula-Variability\n")
            for tag in all_tag_prefixes:
                if(check_for_clarity(perf_formula_var[tuple(tag)])):
                    op.write("%s Clarity was caught\n" % (tag))
                else:
                    op.write("%s Wild Clarity fled\n" % (tag))

            # Pretty printing the contract
            op.write("\n\nContract with Formulae\n\n")
            column1 = "#Packet Class"
            column2 = "#Possible Formulae"
            line_break = "-" * 200 + "\n"
            op.write("%s | \t%s \n\n" %
                     ("{:<100}".format(column1), column2))
            op.write(line_break)
            for tag in all_tag_prefixes:  # Only input classes that extend upto the leaf
                ctr = 0
                for formula in perf_formula_var[tuple(tag)]:
                    if(ctr == 0):
                        column1 = str(tag)[1:-1]
                    elif(ctr == 1):
                        column1 = "Perf Var = %d" % ((max(perf_var[tuple(tag)])
                                                      - min(perf_var[tuple(tag)])))
                    elif(ctr == 2):
                        if(check_for_clarity(perf_formula_var[tuple(tag)])):
                            column1 = "Clarity was caught"
                        else:
                            column1 = "Wild Clarity fled"
                    else:
                        column1 = ""
                    op.write("%s |\t%s \n" %
                             ("{:<100}".format(column1), formula))
                    ctr = ctr + 1
                op.write(line_break)

        DotExporter(tree_root,
                    nodenamefunc=node_identifier_fn,
                    nodeattrfunc=node_colour_fn).to_dotfile("tree.dot")


def compare_trees(node1, node2):
    # print("Call to compare trees with %s, %s" % (node1.name, node2.name))
    # print(merged_tuples)
    if(len(node1.children) != len(node2.children)):
        check = 0
    elif(node1.is_leaf):
        # Node2 is also a leaf node because of above check
        if(abs(node1.perf-node2.perf) < perf_resolution):
            check = 1
        else:
            check = 0
    else:  # Can have one child because coalescing is done later
        if(len(node1.children) == 1):
            if(compare_trees(node1.children[0], node2.children[0])):
                check = 1
            else:
                check = 0
        else:
            if(
                (compare_trees(node1.children[0], node2.children[0]) and compare_trees(
                    node1.children[1], node2.children[1]))
                or
                    (compare_trees(node1.children[0], node2.children[1]) and compare_trees(
                        node1.children[1], node2.children[0]))
            ):
                check = 1
            else:
                check = 2
    if(check == 1):
        merged_tuples.append((node1.name, node2.name))
        return 1
    elif(check == 2):  # Only need to clear here, when both matching possibilities are deemed impossible
        merged_tuples.clear()
    return 0


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
    if (len(leaves_perf)):
        return max(leaves_perf) - min(leaves_perf)
    return 0


def node_colour_fn(node):
    if(node.is_leaf):
        colour = "fillcolor = red,fontcolor = white"
    else:
        colour = "fillcolor = white,fontcolor = black"
    return colour+",style = filled"


def node_identifier_fn(node):
    if(node.is_leaf):
        identifier = 'Name: %s\n' % (node.name)
        tests = str(node.sub_tests)[1:-1]
        tests = tests.replace(", ", "\n")
        identifier += '%s' % (tests)

        identifier += '\nPerf = %s' % (node.perf)
        identifier += '\nFormula = %s' % (node.formula)

    else:
        identifier = '%s:%s:%s\n Perf Var = %s' % (
            node.name, node.id, node.depth, node.perf)

    tag = str(node.tags)[1:-1]  # Removes the square brackets around the list
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
    global leaf_tags
    global all_tag_prefixes
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
                if(traces_tags[test_id] not in leaf_tags):
                    leaf_tags.append(traces_tags[test_id])
                    for x in range(1, len(traces_tags[test_id])+1):
                        if(traces_tags[test_id][0:x] not in all_tag_prefixes):
                            all_tag_prefixes.append(traces_tags[test_id][0:x])
    all_tag_prefixes = list(all_tag_prefixes)
    all_tag_prefixes.sort(key=lambda x: len(x))


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

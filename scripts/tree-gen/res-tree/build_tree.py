#!/usr/bin/env python
# vim: set ts=2 sts=2 sw=2 et si tw=80:

import sys
import string
import os
import math
import operator

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
constraint_file = sys.argv[6]
perf_resolution = int(sys.argv[7])
op_var_file = sys.argv[8]
op_formula_file = sys.argv[9]
constraint_node = sys.argv[10]


class Constraint:

    def __init__(self, subject=None, sbranch=None, lbranch=None, sind=None):
        self._subject = subject  # Main clause of constraint
        self._sbranch = sbranch  # True branch
        self._lbranch = lbranch  # False branch
        self._sind = sind  # Used to indicate if first or second child follows true branch

    @property
    def subject(self):
        return self._subject

    @subject.setter
    def subject(self, value):
        self._subject = value

    @property
    def sbranch(self):
        return self._sbranch

    @sbranch.setter
    def sbranch(self, value):
        self._sbranch = value

    @property
    def lbranch(self):
        return self._lbranch

    @lbranch.setter
    def lbranch(self, value):
        self._lbranch = value

    @property
    def sind(self):
        return self._sind

    @sind.setter
    def sind(self, value):
        self._sind = value


class MyNode(Constraint):

    def __init__(self, name, id, depth):
        self._name = name
        self._id = id
        self._depth = depth
        self._tags = []
        self._max_perf = -1
        self._min_perf = -1
        self._formula = ""
        self._sub_tests = []
        self._constraints = Constraint()

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
    def max_perf(self):
        return self._max_perf

    @max_perf.setter
    def max_perf(self, value):
        self._max_perf = value

    @property
    def min_perf(self):
        return self._min_perf

    @min_perf.setter
    def min_perf(self, value):
        self._min_perf = value

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

    @property
    def constraints(self):
        return self._constraints

    @constraints.setter
    def constraints(self, value):
        self._constraints = value


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
prefix_match_lengths = [[]]
prefix_branch_constraints = [[[]]]

tree_root = TreeNode("ROOT", -1, -1)


def main():
    global tree_root

    get_traces_perf()
    get_traces_tags()
    get_traces_perf_formula()
    assert(len(traces_perf) == len(traces_perf_formula))

    build_tree(tree_file)

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

    # Assigning constraints to each node. Has to be done once we have a binary tree (remove spurious nodes)
    for node in list(PostOrderIter(tree_root)):
        if(not node.is_leaf and not node.is_root):
            node.constraints = get_node_constraints(node)

    # Let's assign tags and performance resolution now
    for node in list(PostOrderIter(tree_root)):
        if(node.is_leaf):
            node.max_perf = traces_perf[node.name]
            node.min_perf = node.max_perf
            node.formula = traces_perf_formula[node.name]
            if(node.name in traces_tags):
                node.tags = traces_tags[node.name]

        else:
            node.max_perf, node.min_perf = get_perf_variability(node)
            assign_tags(node)

    # Now, let's coalesce nodes perf variability less than input resolution!
    for node in list(PostOrderIter(tree_root)):
        if(not node.is_leaf and perf_within_resolution(node.max_perf, node.min_perf)):
            # TODO: Need to coalesce formula
            for child in list(node.children):
                child.parent = None
            node.constraints = Constraint()  # Because it is now a leaf

    # Now, let's remove spurious, perf-unrelated branching.
    # This is used to eliminate the following redundancy:
    # Assume a resolution of 10, we want to coalesce Node2, Node3, but not either of them individually
    #               Node1
    #   Node2 --------|---------Node3
    # 5--|--200                6--|--201
    #
    # This is an iterative process which will repeat until we hit a fixed point
    # Does not work for the call tree (we don't care about it anyway)
    merged_nodes = list()
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
                    assert(compare_node_constraints(
                        children[0], children[1]) and "Merging children with different constraints")
                    merged_nodes.append(node)
                    for pair in merged_tuples:
                        # Sanity check that the tuple always has a node from child zero and then child one.
                        # Mostly redundant, but left here in any case
                        assert(len(findall_by_attr(children[0], pair[0], name='name')) == 1
                               and len(findall_by_attr(children[1], pair[1], name='name')) == 1)
                        final = findall_by_attr(
                            children[0], pair[0], name='name')[0]
                        merged_in = findall_by_attr(
                            children[1], pair[1], name='name')[0]
                        final.sub_tests.append(merged_in.sub_tests)
                        final.max_perf = max(
                            final.max_perf, merged_in.max_perf)
                        final.min_perf = min(
                            final.min_perf, merged_in.min_perf)
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
                        assert(node.parent in merged_nodes)
                        merged_nodes.remove(node.parent)
                        curr_parent = node.parent
                        new_parent = curr_parent.parent
                        node.parent = new_parent
                        curr_parent.parent = None
                        changed = 1

    # Re-assigning constraints to each node after the re-structuring. Some stuff causes a weird change in children order
    for node in list(PostOrderIter(tree_root)):
        if(not node.is_leaf and not node.is_root):
            node.constraints = get_node_constraints(node)

    # Final step - constraint coalescing
    for node in PostOrderIter(tree_root):
        if(not node.is_leaf and not node.is_root):
            children = list(node.children)
            grandchildren_1 = list(children[0].children)
            grandchildren_2 = list(children[1].children)
            # Now constraint coalescing is possible
            if(len(grandchildren_2) > 1 and len(grandchildren_1) > 1):
                uncle = None
                dad = None
                nephew = None
                neice = None

                # If merging works, uncle == nephew. Hence, dad, nephew are lost and neice gets promoted.

                if(compare_node_constraints(children[0], grandchildren_2[0])):
                    uncle = children[0]
                    dad = children[1]
                    nephew = grandchildren_2[0]
                    neice = grandchildren_2[1]
                elif(compare_node_constraints(children[0], grandchildren_2[1])):
                    uncle = children[0]
                    dad = children[1]
                    nephew = grandchildren_2[1]
                    neice = grandchildren_2[0]
                elif(compare_node_constraints(children[1], grandchildren_1[0])):
                    uncle = children[1]
                    dad = children[0]
                    nephew = grandchildren_1[0]
                    neice = grandchildren_1[1]
                elif(compare_node_constraints(children[1], grandchildren_1[1])):
                    uncle = children[1]
                    dad = children[0]
                    nephew = grandchildren_1[1]
                    neice = grandchildren_1[0]

                if(uncle != None):  # Merging the two nodes if within resolution
                    if(compare_trees(uncle, nephew)):
                        for pair in merged_tuples:
                            # Sanity check that the tuple always has a node from uncle and then nephew.
                            # Mostly redundant, but left here in any case
                            assert(len(findall_by_attr(uncle, pair[0], name='name')) == 1
                                   and len(findall_by_attr(nephew, pair[1], name='name')) == 1)
                            final = findall_by_attr(
                                uncle, pair[0], name='name')[0]
                            merged_in = findall_by_attr(
                                nephew, pair[1], name='name')[0]
                            final.sub_tests.append(merged_in.sub_tests)
                            final.max_perf = max(
                                final.max_perf, merged_in.max_perf)
                            final.min_perf = min(
                                final.min_perf, merged_in.min_perf)

                        # Modify the constraints in the current node
                        curr_constraints = node.constraints
                        merged_in_constraints = dad.constraints
                        dad_ind = children.index(dad)
                        neice_ind = list(
                            children[dad_ind].children).index(neice)

                        # Fix the branching
                        dad.parent = None
                        nephew.parent = None
                        neice.parent = node
                        merged_tuples.clear()
                        new_neice_ind = list(node.children).index(neice)

                        if(curr_constraints.lbranch == merged_in_constraints.lbranch and
                           (neice_ind + merged_in_constraints.sind) % 2 == (dad_ind + curr_constraints.sind) % 2):
                            # This implies that we simply have to and/or the subject and we're good. Since neice is at the end of a double branch (both true or both false)
                            if(merged_in_constraints.lbranch == "(Eq false"):
                                if(neice_ind != merged_in_constraints.sind):  # Neice was both false
                                    conjunction = "OR"
                                    sind = (new_neice_ind + 1) % 2
                                else:
                                    conjunction = "AND"  # Neice was both true
                                    sind = new_neice_ind
                                subject = curr_constraints.subject + "\n" + \
                                    conjunction + "\n" + merged_in_constraints.subject
                                sbranch = curr_constraints.sbranch
                                lbranch = curr_constraints.lbranch
                                node.constraints = Constraint(
                                    subject, sbranch, lbranch, sind)

                            else:
                                assert(0 and "Constraint merging not supported")

                        else:
                            assert(0 and "Constraint merging not supported")

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

    if(constraint_node != "none"):
        node = find(
            tree_root, lambda node: node.name == constraint_node)
        pretty_print_constraints(node)


def perf_within_resolution(perf1, perf2):
    return (abs(perf1-perf2) < perf_resolution)


def pretty_print_constraints(node):
    assert(len(node.constraints.subject) > 0)

    print("Constraints for node %s" % (node.name))
    print("Subject is %s" % (node.constraints.subject))
    print("branch to node %s is %s" %
          (node.children[node.constraints.sind].name, node.constraints.sbranch))
    print("branch to node %s is %s" %
          (node.children[(node.constraints.sind + 1) % 2].name, node.constraints.lbranch))


def compare_node_constraints(node1, node2):
    return (node1.constraints.subject == node2.constraints.subject)


def compare_trees(node1, node2):
    # Checks if the sub-trees below node1 and node2 are identical given a resolution
    if(len(node1.children) != len(node2.children)):
        check = 0
    elif(node1.is_leaf):
        # Node2 is also a leaf node because of above check
        if(perf_within_resolution(max(node1.max_perf, node2.max_perf), min(node1.min_perf, node2.min_perf))):
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
    elif(check == 2):  # Only need to clear the recursion here, when both matching possibilities are deemed impossible
        merged_tuples.clear()
    return 0


def check_for_clarity(formula_var):
    # Checks if a set of formulae only differ in terms of the constant
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
    children = list(node.children)
    assert(len(children) <= 2 and len(children) > 0)
    max_perf = max(list(node.max_perf for node in children))
    min_perf = min(list(node.min_perf for node in children))
    return max_perf, min_perf


def node_colour_fn(node):
    if(node.is_leaf):
        colour = "fillcolor = blue,fontcolor = white"
    else:
        colour = "fillcolor = white,fontcolor = black"
    return colour+",style = filled"


def node_identifier_fn(node):
    if(node.is_leaf):
        identifier = 'Name: %s\n' % (node.name)
        # tests = str(node.sub_tests)[1:-1]
        # tests = tests.replace(", ", "\n")
        # identifier += '%s' % (tests)

        identifier += '\nPerf = %s' % ((node.max_perf + node.min_perf)/2)
        identifier += '\nFormula = %s' % (node.formula)

    else:
        identifier = '%s:%s:%s\n Perf Var = %s' % (
            node.name, node.id, node.depth, (node.max_perf - node.min_perf))

    tag = str(node.tags)[1:-1]  # Removes the square brackets around the list
    tag = tag.replace(", ", "\n")
    identifier += "\n%s" % (tag)

    return identifier


def print_tree(root):
    for pre, _, node in RenderTree(root):
        treestr = "%s%s" % (pre, node.name)
        sys.stdout.buffer.write(treestr.encode('utf-8')+b"\n")


def find_lpm_node(root, node_id, lpm, leaf_id):

    if(lpm == 0):  # Small hack, since it doesn't fit in well with the while loop
        return root

    node_name = "test"+f"{node_id:06d}"
    leaf_node_name = "test"+f"{leaf_id:06d}"
    while(lpm >= 0):
        lpm = lpm - 1
        children = list(root.children)
        root.sub_tests.append(leaf_node_name)
        # print("Looking for %s in subtree with root %s" %
        #       (node_name, root.name))
        root = next((x for x in children if node_name in x.sub_tests), None)
        assert(root != None)

    root.sub_tests.append(leaf_node_name)  # Needs to be done one last time

    return root


def del_node(node):
    while(1):
        if(len(node.siblings) > 0):
            node.parent = None
            break
        else:
            parent = node.parent
            node.parent = None
            node = parent


def get_node_constraints(node):
    assert(node != None and "node not present")
    assert(len(node.children) == 2 and "Leaf node provided")
    children = list(node.children)
    assert(len(children[0].sub_tests) > 0 and len(children[1].sub_tests))
    test1 = int(children[0].sub_tests[0].replace("test", ""))
    test2 = int(children[1].sub_tests[0].replace("test", ""))
    constraints = prefix_branch_constraints[test1][test2]
    # In the above matrix, the first constraint in the list always points to the test with the smaller numeric value.
    # That is a property of how the constraints are dumped from KLEE
    if(test1 > test2):  # Need to re-order the list.
        constraints = [constraints[1], constraints[0]]
    # Now we can be sure that the constraints are ordered by the children
    assert(len(constraints) > 0)
    if(len(constraints[0]) > len(constraints[1])):
        short_constraint = constraints[1]
        long_constraint = constraints[0]
        short_ind = 1
    else:
        short_constraint = constraints[0]
        long_constraint = constraints[1]
        short_ind = 0

    short_constraint = short_constraint.rstrip()
    long_constraint = long_constraint.replace('\n', '')
    short_constraint = short_constraint.replace('\n', '')
    assert(long_constraint[0:long_constraint.find(
        short_constraint)] == "(Eq false")

    subject = short_constraint
    branch1 = "(Eq true"
    branch2 = "(Eq false"
    return Constraint(subject, branch1, branch2, short_ind)


def build_tree(tree_file):
    global tree_root
    global prefix_match_lengths
    global prefix_branch_constraints
    # stupid code to get length of file. Makes everything much easier
    ctr = 0
    with open(tree_file, 'r') as f:
        for line in f:
            ctr = ctr + 1

    num_lines = int(math.sqrt(2*ctr))
    prefix_match_lengths = [
        [-1 for i in range(num_lines)] for i in range(num_lines)]
    prefix_branch_constraints = [
        [list() for i in range(num_lines)] for i in range(num_lines)]
    with open(tree_file, 'r') as f:
        for line in f:
            text = line.rstrip()
            text = text.split(',')
            assert(len(text) == 3)
            text = [int(x) for x in text]
            prefix_match_lengths[text[0]][text[1]] = text[2]
            prefix_match_lengths[text[1]][text[0]] = text[2]

    with open(constraint_file, 'r') as f:
        acc = ""
        for line in f:
            text = line.strip()+"\n"
            if("," in line):
                if(acc != ""):
                    assert(
                        len(prefix_branch_constraints[index1][index2]) < 2)
                    prefix_branch_constraints[index1][index2].append(acc)
                    prefix_branch_constraints[index2][index1].append(acc)
                text = text.split(",")
                assert(len(text) == 3)
                index1 = int(text[0])
                index2 = int(text[1])
                acc = text[2]
            else:
                acc = acc+text

    id_ctr = 0
    for i in range(num_lines):
        if(i != 0):
            lpm_index, lpm = max(
                enumerate(prefix_match_lengths[i][0:i]), key=operator.itemgetter(1))
        else:
            lpm = 0
            lpm_index = 0

        subtree_root = tree_root
        subtree_root = find_lpm_node(subtree_root, lpm_index, lpm, i)
        rem_len = prefix_match_lengths[i][i] - lpm
        leaf_node_name = "test"+f"{i:06d}"
        # print("inserting node %s" % (leaf_node_name))
        depth = lpm
        while(rem_len >= 0):
            id = len(subtree_root.children)
            assert(id <= 1)
            if(rem_len == 0):
                node_name = leaf_node_name
            else:
                node_name = "branch"+f"{int(id_ctr):06d}"
                id_ctr = id_ctr + 1
            node = TreeNode(node_name, id, depth, parent=subtree_root)
            subtree_root = node
            subtree_root.sub_tests.append(leaf_node_name)
            depth = depth + 1
            rem_len = rem_len - 1

    # Extra hack for constraint tree, to retain assumptions made during other tree formations
    for i in range(num_lines):
        leaf_node_name = "test"+f"{i:06d}"
        if(leaf_node_name not in traces_perf):
            leaf_node = find(
                tree_root, lambda node: node.name == leaf_node_name)
            del_node(leaf_node)


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

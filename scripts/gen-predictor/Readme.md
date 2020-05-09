# Python performance oracle generator

This application generates a python performance oracle based on them
output of the bolt, provided in the form

```
<branch-constraints>,<perf>
```

## Running

To generate the oracle, run:

```
bash generate.sh <constraints-file>
```

The oracle will be written to `<constraints-file>.py`

## Dependencies

The tool is written in OCaml, using the Core library,
as well as sexplib, str, and may be a few others.

## Rewrite rules

This codegenerator simplifies the resulting python code by applying
user-defined domain-specific rewrite rules, listed in the function `rewrite`
in `domain.ml`.

You can add your custom domain-specific rules to that file,
if you want to get simpler oracle code.

To find out the internal representation of an expression you would like to match,

you can run the code generator with the `-debug` key, like this:

```
bash generate.sh <constraints-file> -debug
```

This will output the IR for each constraint,
as it is represented using the `term`s from `ir.ml`.

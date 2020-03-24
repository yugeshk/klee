# Python performance oracle generator

This application generates a python performance oracle based on them
output of the bolt, provided in the form

```
<branch-constraints>,<perf>
```

To generate the oracle, run:

```
bash generate.sh <constraints-file>
```

The oracle will be written to `<constraints-file>.py`

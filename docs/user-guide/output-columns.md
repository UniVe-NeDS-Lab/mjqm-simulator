---
title: Output Columns
tags:
  - user-guide
---

# Output columns

There are two types of values that can be output: configuration values, and computed values.
In particular, configuration values can be classified as pivots, if they are part of a `[[pivot]]` section or a command line override.

## Output order

The order of output columns will be:

1. Pivot values (in order of appearance)
2. Custom additional configuration values (class or simulation related).
   _These will retain the order of appearance in the configuration_
3. Statistics per class
4. Global statistics

## Output selection

The following shows examples of how to configure output columns, including or excluding a single or a set of columns.
As noted before, the order of the definition is generally relevant only for custom additional columns.
If you want to exclude one or more columns, you can use the `-` prefix, and that will be evaluated following the list order.

```toml
[output]
columns = [
  # include the configuration value for each class (when the value is not explicit and the default is available, the latter is used)
  "cores[*]",
  "arrival.prob[*]",
  "service.mean[*]",
  # include the configuration value for a specific class (identified by the cores value, or by name if defined)
  "arrival.prob[50]",
  # include values of the whole simulation configuration
  "cores",
  "policy",
  # include default values of class configurations
  "arrival.rate",
  "service.mean",
  # include or exclude pivot values
  "pivots",
  "-pivots",

  "-Window Size",     # exclude a specific computed column
  "-*",               # exclude all computed columns, useful to only choose a handful of columns
]
```

## Base configuration

By default, all statistics and pivot values are included.

```toml
[output]
columns = [
  "*",
  "pivots",
]
```

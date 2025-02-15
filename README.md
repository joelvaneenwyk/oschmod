<!-- markdownlint-disable no-inline-html first-line-h1 no-alt-text !-->

# oschmod

[![License](https://img.shields.io/github/license/YakDriver/oschmod.svg)](./LICENSE)
[![Python package](https://github.com/joelvaneenwyk/oschmod/actions/workflows/python-package.yml/badge.svg)](https://github.com/joelvaneenwyk/oschmod/actions/workflows/python-package.yml)

**_oschmod_** sets consistent file permissions across Windows, Linux and macOS.

## Overview

**_oschmod_** brings `chmod` functionality to **Windows**, macOS, and Linux! If you're not familiar, `chmod` is a handy macOS and Linux-only tool for setting file permissions.

Prior to **_oschmod_**, Windows file permissions couldn't be set in the familiar `chmod` way. Tools did not translate `chmod`-style permissions into Windows-style file permissions. Even though Python's `os.chmod()` sets read, write, and execute file permissions, on Windows, `os.chmod()` basically has no effect. Even worse, Python on Windows gives no warnings or errors. If you think you set file permissions on Windows with `os.chmod()`, you're wrong!

**_oschmod_** allows you to set consistent file permissions in a consistent way across platforms.

- Read more about [oschmod](https://medium.com/@dirk.avery/securing-files-on-windows-macos-and-linux-7b2b9899992) on Medium
- For more background, have a look at the [oschmod Wiki](https://github.com/YakDriver/oschmod/wiki).

## Installation

```bash
pip install oschmod
```

## GNU Documentation

**_oschmod_** changes the file mode bits of each given file according to mode, which can be either a symbolic representation of changes to make, or an octal number representing the bit pattern for the new mode bits.

The format of a symbolic mode is `[ugoa...][+-=][perms...]` where perms is zero or more letters from the set `rwx`. Multiple symbolic modes can be given, separated by commas.

A combination of the letters `ugoa` controls which users' access to the file will be changed: the user who owns it (`u`), other users in the file's group (`g`), other users not in the file's group (`o`), or all users (`a`). If none of these are given, the effect is as if `a` were given.

_Modified from the GNU manpage for chmod._

## Command line interface

**_oschmod_** brings the ability to set consistent file permissions using the command line to Windows, macOS, and Linux platforms. If you are familiar with `chmod`, **_oschmod_** works similarly, albeit with fewer options.

```bash
$ oschmod -h
usage: oschmod [-h] [-R] mode object

Change the mode (permissions) of a file or directory

positional arguments:
  mode        octal or symbolic mode of the object
  object      file or directory

optional arguments:
  -h, --help  show this help message and exit
  -R          apply mode recursively
```

## Command line examples

You can use symbolic (e.g., "u+rw") or octal (e.g., "600) representations of modes. Multiple mode modifications can be made in a single call by separating modifiers with commas.

### Symbolic representation examples

Symbolic representation mode modifiers have three parts:

1. **whom:** To whom does the modification apply? You can include zero or more of `[ugoa]*` where `a` is for all, `u` is for the file owner (i.e., "**u**ser"), `g` is for the file group, and `o` is for others. In other words, `ugo` is equivalent to `a`. Also, if you do not provide a "whom," **_oschmod_** assumes you mean `a` (everyone).
2. **operation:** Which operation should be applied? You must include one and only one operation, `[+-=]{1}`, per modifier (although you can have multiple modifiers). `+` adds permissions, `-` removes permissions, and `=` sets permissions regardless of previous permissions. `+` and `-` modifications often depend on the current permissions.
3. **permission:** Which permission or permissions will be affected? You can include zero or more of `[rwx]*` where `r` is for read, `w` is for write, and `x` is for execute. If you do not include a permission with `+` or `-` (e.g., `u-`), the modifier has no effect. However, if you use no permissions with `=` (e.g., `o=`), all permissions are removed.

#### Example 1

To give everyone execute permissions on a file (all of these are equivalent):

```bash
oschmod +x <file name>
oschmod a+x <file name>
oschmod ugo+x <file name>
```

#### Example 2

To remove read, write, and execute permissions from the file group and all others (these are equivalent):

```bash
oschmod go-rwx <file name>
oschmod go= <file name>
```

#### Example 3

To give the file owner read and execute permissions, and remove execute permissions from the group and all others:

```bash
oschmod u+rx,go-x <file name>
```

#### Example 4

To give everyone all permissions, and then remove execute write from the group, and execute from all others:

```bash
oschmod a+rwx,g-w,o-x <file name>
```

### Octal representation examples

For more about what octal representations mean, see [this article](https://medium.com/@dirk.avery/securing-files-on-windows-macos-and-linux-7b2b9899992) on Medium.

#### Example 5

To give everyone read, write, and execute permissions on a file:

```bash
oschmod 777 <file name>
```

#### Example 6

To lock down a file to just give the file owner read, write, and execute permissions and deny all permissions to everyone else:

```bash
oschmod 700 <file name>
```

## Python usage

You can use **_oschmod_** from Python code. Any of the command line examples above will work very similarly. For example, _Example 4_ above, in Python code, would look like this:

```python
import oschmod
oschmod.set_mode("my_file", "a+rwx,g-w,o-x")
```

_Example 5_ above, in Python code, could be done in two ways:

```python
import oschmod
oschmod.set_mode("my_file", "777")
oschmod.set_mode("my_file", 0o777)
```

**_oschmod_** is compatible with bitwise permissions as defined in the `stat` module. To give a file's owner read, write, and execute permissions and deny the group and others any permissions (i.e., equivalent of `700`):

```python
import oschmod
import stat
oschmod.set_mode('my_file', stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
```

Replacing `os.chmod()` with **_oschmod_** should usually be an easy drop-in replacement. Replacement will allow you to get consistent file permission settings on Windows, macOS, and Linux:

If this is your Python code using `os.chmod()`:

```python
import os
os.chmod('my_file1', 'u+x')
os.chmod('my_file2', 0o777)
```

The replacement using **_oschmod_** is very similar:

```python
import oschmod
oschmod.set_mode('my_file1', 'u+x')
oschmod.set_mode('my_file2', 0o777)
```

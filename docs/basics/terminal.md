# Working in the terminal

This page shows how to open a terminal and the few commands you need for
this guide. If you have used one before, you can skip it.

## Opening a terminal

Each system has a terminal built in:

- On Windows, open the Start menu, type `PowerShell` and open
  Windows PowerShell.
- On macOS, open Finder, then Applications › Utilities › Terminal.
- On Linux, open the program called Terminal from your applications.

The code editor VS Code also has a terminal. Choose Terminal › New
Terminal, and it opens at the bottom of the window, already in the folder
you are working on.

The terminal shows a short line of text and waits. This line is the
*prompt*. It usually ends with `$`, `%` or `>`, and it often shows the
folder you are in. You type a command after it and press Enter. The
computer runs the command, prints its answer and shows the prompt again.

## The commands you need

A terminal always works in one folder at a time, the *current folder*. A
new terminal starts in your user folder. These commands exist on all
three systems. In PowerShell, their output looks a little different:

| Command | What it does |
|---|---|
| `pwd` | shows the current folder |
| `ls` | lists the files and folders in the current folder |
| `ls -a` | also lists hidden files, whose names start with a dot; in PowerShell, type `ls -Force` |
| `cd Documents` | moves into the folder `Documents` |
| `cd ..` | moves up one folder |
| `mkdir my-project` | creates a new folder `my-project` |
| `cat runs.txt` | shows the content of the file `runs.txt` |

A folder name with spaces needs quotation marks:
`cd "My Documents"`. If `ls` shows your documents folder under another
name, for example `Dokumente`, use that name.

For example, to create a folder for a project in your documents and move
into it:

```bash title="Your computer"
cd Documents
mkdir my-project
cd my-project
pwd
```

The last command shows where you are now, for example:

```text title="Output"
/home/you/Documents/my-project
```

On Windows the folder looks like `C:\Users\you\Documents\my-project`.

## Opening a terminal in a folder

Often you want a terminal that is already in the folder of a project:

- On Windows, open the folder in File Explorer, click into the address
  bar, type `powershell` and press Enter.
- On macOS, type `cd` and a space in the terminal, drag the folder from
  Finder into the window and press Enter.
- On Linux, right-click the folder in the file manager and choose
  Open in Terminal.
- In VS Code, open the folder with File › Open Folder, then choose
  Terminal › New Terminal.

## Tips that save time

The Tab key completes names. Type the first letters of a file or folder
and press Tab, and the terminal fills in the rest.

The arrow keys up and down bring back the commands you typed before, so
you can run a command again without typing it.

Ctrl+C stops a command that is still running. It does not copy text in
most terminals. To paste a command, use Ctrl+Shift+V on Linux, Cmd+V on
macOS and Ctrl+V or a right click in PowerShell.

## The terminal on the cluster

After the [setup](setup.md), the command `ssh sc-login` connects the
terminal to the cluster. `sc-login` is this guide's short name for the
server you log in to. The prompt changes to show the name of that server,
and every command runs there. The commands on this page work the same
way. Type `exit` to go back to your computer.

Commands on the cluster run in bash, the usual shell on Linux.

## Further reading

- [The Unix shell](https://swcarpentry.github.io/shell-novice/), a
  beginner's course by Software Carpentry, which covers these commands
  and many more.
- [Terminal basics](https://code.visualstudio.com/docs/terminal/basics)
  in the VS Code documentation.

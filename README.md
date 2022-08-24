# 20th Century Food Court Save File Parser

A library for parsing/validating solutions to 20th Century Food Court, a subgame of [Last Call BBS](https://zachtronics.com/last-call-bbs/).

Very much a work in progress. Save file parsing works, but simulation is not supported yet.

## Usage

```
python -m foodcourt_sim <solution_file_path>
```
will parse and dump a solution.

Solution files are usually located under:
```
Windows: %USERPROFILE%\Documents\My Games\Last Call BBS\<user-id>\20th Century Food Court\
Linux: $HOME/.local/share/Last Call BBS/<user-id>/20th Century Food Court/
```

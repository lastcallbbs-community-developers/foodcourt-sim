# 20th Century Food Court Save File Parser

A library for parsing/validating solutions to 20th Century Food Court, a subgame of [Last Call BBS](https://zachtronics.com/last-call-bbs/).

## Usage

To validate all solved solutions in a directory, use
```
python -m foodcourt_sim validate_all [--json] <solution_directory>
```

To simulate a single solution, use
```
python -m foodcourt_sim simulate [--json] <solution_file_path>
```

Solution files are usually located under:
```
Windows: %USERPROFILE%\Documents\My Games\Last Call BBS\<user-id>\20th Century Food Court\
Linux: $HOME/.local/share/Last Call BBS/<user-id>/20th Century Food Court/
```

To run tests locally on your entire solutions folder (on Linux):
```
mkdir -p tests/solutions/$USER && cp -r "$HOME/.local/share/Last Call BBS"/*/"20th Century Food Court"/*.solution tests/solutions/$USER/
python -m pytest --show-capture no --tb no -k $USER
```

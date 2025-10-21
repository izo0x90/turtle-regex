
```
          _____     ____
         /      \  |  o | 
        |        |/ ___\| 
        |_________/     
        |_|_| |_|_|                                                            Turtle part of the logo credit goes to:
--====:::Turtle RegEx                                                 https://www.asciiart.eu/animals/reptiles/turtles
```
This is an incomplete (and likely incorrect in someways) implementation of a RegEx engine is pure Python.

It consists of 3 modules:
- The parser - which parses RegEx strings into match expressions represented as a tree of Match Node objects
- The matcher - which implements a `match` function to execute the match tree/ pattern against a source string
- The regex - That provides two ways to search across a source string for substrings that match a pattern
    - `search` function that takes a RegEx string and a source string and preforms the search
    - `complie` function that takes a RegEx string and returns a Matcher object that has a pre-complied match tree
        - The `search` method on the Matcher object takes a source string and performs the match to the match pattern
        stored on the instance

And main.py which provides a super basic CLI access to the underlying functionality.

# Why ?
On occasion I find it fun to build random software projects that implement some silly idea or a fundamental software engineering concept.
Hopefully it can also serve as a illustration around the basics of some of these core concepts work, in this case Regular Expressions as a way
to search in machine readable text.

More or less because it was fun for me to try and build this without referencing other implementations or going back to
the computer science/ math theory behind it.

There is no pressing need in the world for another actually correct and performant implementation, much smarter folks
have build those already, but building one in Python that can show the concepts in a simple way brought me joy! *shurg*

I call projects like these my "How it's made - Software edition" series, you can find more of them in my repos.

# Install deps.
```
pip install uv
```

# Install
```
uv install --dev
```

# Run as CLI
```
uv main.py "some regex string" "some source string"
```
or 
```
cat somefile.txt | uv main.py "some regex string"
```

# Run the different examples
## Parser built in examples
```
uv run parser.py
```
## Matcher built in examples
```
uv run matcher.py
```
## RegEx built in examples
```
uv run regex.py
```

# TODO: (Maybe)
- TODO: (Hristo) Fix range matching for upper limit (if exceeded only stop, match is still true)
- TODO: (Hristo) Fix Matching `.` any char is not lazy so consumes all
- Maybe possibly add more functionality

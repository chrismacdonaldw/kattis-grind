# Kattis Grind
A small easy-to-use package of Python 3 scripts which can help speed up the process for competitive programming on [Kattis](https://open.kattis.com). The scripts will download a local copy of the question (html file), and can automate testing inputs / outputs.

# Requirements
Kattis Grind uses Python 3. To check if you have it:
```console
foo@bar:~$ python3 --version
Python 3.7.3
```
If you don't have Python 3, you can install it from the [Python Website](https://www.python.org/downloads/).

The Kattis Grind setup requires two modules. To install them:
```console
foo@bar:~$ pip3 install bs4
foo@bar:~$ pip3 install fake-useragent
```
# How do I use it?
## Fetch a question!
Simple! If you wanted to fetch a question, you can simply run
```console
foo@bar:~/kattis-grind$ ./get_q.py
Enter ID:
```
If you prefer to use command line arguments instead, you can! For example, if I wanted to get question 'hello':
```console
foo@bar:~/kattis-grind$ ./get_q.py --id hello
```

## Test your solution!
The useful feature for Kattis Grind is that you can easily test your solutions! To do so:
```console
foo@bar:~/kattis-grind$ ./test_q.py
Enter ID:
```
Similarly to fetching a question, you can pass in an optional ID argument! Using 'hello' as an example again:
```console
foo@bar:~/kattis-grind$ ./test_q.py --id hello
```
## Generating random questions!
The best feature of this program is that you can fetch random questions from Kattis too! If I was interested in five questions between a range of 1.4 to 1.6, I can run the script like this:
```console
foo@bar:~/kattis-grind$ ./rand_n.py
Enter lower bound: 1.4
Enter upper bound: 1.6
How many questions: 5
```
It's as simple as that! But as you may have guessed, there are optional command line arguments for these too! Although they're less useful, you can use them like this:
```console
foo@bar:~/kattis-grind$ ./rand_n.py --lobound 1.4 --upbound 1.6 --qamount 5
```
Depending on how many questions you want, and what range they're between, this operation *may* take several seconds (sometimes a good 10 - 40 seconds!!). Keep in mind that while it takes long, it definitely works!

# Current Bugs
Currently, Windows seems to have some trouble with encoding characters and Python crashes as a result of trying to save HTML files without proper encoding. This does not occur on Linux. Be wary of questions with foreign characters in them, for example: ő

# License
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE) file for details

# Acknowledgments
* Thanks to [JarateKing](https://github.com/JarateKing) and [Ben Boyle](https://github.com/benbdevd) for the original grinding idea.
* Thanks to [Will Taylor](https://github.com/wtaylor17) for fixing test_q.py to work on Windows machines.
* Thanks to the UPEI SMCSS for all the motivation!!!

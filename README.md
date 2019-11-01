# Kattis-Grind Setup
A grind setup for the competitive programming website [Kattis](https://open.kattis.com). Can grab questions with specific ID's and can even fetch N amount of questions within a specified difficulty range.
As a note, this does utilize web scraping. If this is against Kattis terms of service, please notify me and I will take it down immediately.
These scripts can be utilized to simulate a tournament environment where you may want to generate a random amount of questions between a set range of difficulty.

### Prerequisites
It uses Python3.7.3 so there are some modules you will need.
Some pip3 modules you need to install
```
BeautifulSoup4
fake-useragent
```
The folder requires full read and write permissions, so on Linux just 
```
chmod 777 -R *sourcefolder*
```

### Usage
It's pretty intuitive and obvious in use, but here are examples.

**Fetching a question**
```
./get_q.py --id *problem id*
```
ID argument is optional, if wanted, you can enter it via the prompt.

**Testing a question**
```
./test_y.py
```
Doesn't have an ID argument just yet, but enter the ID via prompt and it will run your code through the test cases and output either PASSED or FAILED for the respective test case. There may be false positives, but I highly doubt it.

**Generating N random questions between a difficulty range**
```
./rand_n.py
```
You will be prompted for a lower bound (1.2 is the lowest, but it doesn't matter what you put here).

You will be prompted for an upper bound (Upper bound max is 10).

You will be prompted for n, how many questions you want to generate.

Once the questions are selected, they are shuffled, randomly selected and added to a textfile called seen.txt. This is so that the same questions may not be selected a second time. If you want it generated again, simply erase it's line from the text file.

## License
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments
* Thanks to [JarateKing](https://github.com/JarateKing) and [Ben Boyle](https://github.com/benbdevd) for the original grinding idea.

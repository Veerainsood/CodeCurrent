"""
1. Write a Python program to read an entire text file.
"""

# It is good practice to use the with keyword when dealing with file objects.
# The advantage is that the file is properly closed after its suite finishes,
# even if an exception is raised at some point. 
with open('exercises.txt') as f:
    read_data = f.read()
    print(read_data)
print(f.closed)

with open('exercises.txt') as f:
    read_data = f.read()
    print(read_data)
    print(f.closed)
print(f.closed)

"""
2. Write a Python program to read first n lines of a file.
"""

# solution 1
n = 5
with open('exercises.txt') as f:
    for _ in range(n):
        print(f.readline())
# solution 2
n = 5
with open('exercises.txt') as f:
    lines = list(f)
    for line in lines[:n]:
        print(line)

# solution 3
n = 5
with open('exercises.txt') as f:
    lines = f.readlines()
    for line in lines[:n]:
        print(line)

# solution 4
from itertools import islice
n = 5
with open('exercises.txt') as f:
    for line in islice(f, n):
        print(line)

"""
3. Write a Python program to append text to a file and display the text.
"""

with open('exercises.txt', 'a') as f:
    f.write('\nappending a line at the end of the file')
with open('exercises.txt', 'r') as f:
    print(f.read())
"""
4. Write a Python program to read last n lines of a file.
"""

n = 6
with open('exercises.txt') as f:
    lines = list(f)
    for line in lines[-n:]:
        print(line)
"""
5. Write a Python program to read a file line by line and store it into a list.
"""

with open('exercises.txt') as f:
    lines = list(f)
    print(lines)

"""
6. Write a Python program to read a file line by line store it into a variable.
"""

with open('exercises.txt') as f:
    for line in f:
        my_string = line
        print(my_string)

"""
8. Write a python program to find the longest words.
"""

# solution 1 (finds 1 longest word)
with open('exercises.txt') as f:
    lines = list(f)
    longest = ''
    for line in lines:
        for word in line.split():
            if len(longest) < len(word):
                longest = word
    print(longest)

# solution 2 (finds 1 longest word)
with open('exercises.txt') as f:
    words = f.read().split()
    longest = max(words, key=len)
    print(longest)

# solution 3 (finds all words with greatest length)
with open('exercises.txt') as f:
    words = f.read().split()
    max_length = len(max(words, key=len))
    all_longest = [word for word in words if len(word) == max_length]
    print(set(all_longest))

"""
9. Write a Python program to count the number of lines in a text file.
"""

# solution 1
with open('exercises.txt') as f:
    print(len(list(f)))

# solution 2
with open('exercises.txt') as f:
    counter = sum(1 for _ in f)
    print(counter)

"""
10. Write a Python program to count the frequency of words in a file.
"""

# solution 1
import string

with open('exercises.txt') as f:
    # remove punctuation marks from the text 
    intab = string.punctuation
    outtab = " "*len(string.punctuation)
    trans_table = str.maketrans(intab, outtab)
    text = f.read().translate(trans_table)

    # create list of words (all words lowercased)
    words = text.lower().split()

    # create dictionary and populate it with count for each word
    words_freq = {}
    for word in words:
        if word in words_freq:
            words_freq[word] += 1
        else:
           words_freq[word] = 1

print(words_freq)

# solution 2
from collections import Counter
import string

with open('exercises.txt') as f:
    # remove punctuation marks from the text
    intab = string.punctuation
    outtab = " "*len(string.punctuation)
    trans_table = str.maketrans(intab, outtab)
    text = f.read().translate(trans_table)

    # split text to list of words (all lowercased)
    words = text.lower().split()

    # create a Counter object
    words_freq = Counter(words)

print(words_freq)

"""
11. Write a Python program to get the file size of a plain file.
"""
from os import stat

# os.stat() - Get the status of a file or a file descriptor.
# st_size - Size of the file in bytes
statinfo = stat('exercises.txt')
print(statinfo.st_size)

"""
12. Write a Python program to write a list to a file.
"""
my_list = [1, 2, 3, 4]
with open('list-to-file.txt', 'w+') as f:
    f.write(' '.join(map(str, my_list)))

"""
13. Write a Python program to copy the contents of a file to another file.
"""

with open('list-to-file.txt') as f:
    f1 = open('exercises.txt', 'a')
    f1.write(f.read())
f1.close()

# solution 2 (copy with deleting all previous data in target file)
import shutil
shutil.copyfile('list-to-file.txt', 'exercises.txt')

"""
14. Write a Python program to combine each line from first file with the
corresponding line in second file.
"""

with open('fruits.txt') as f1:
    f2 = open('vegetables.txt')
    for line1, line2 in zip(f1, f2):
        print(line1.strip('\n'), line2.strip('\n'))
f2.close()

"""
15. Write a Python program to read a random line from a file.
"""

import random
with open('fruits.txt') as f:
    print(random.choice(f.readlines()))

"""
16. Write a Python program to assess if a file is closed or not.
"""
with open('fruits.txt') as f:
    print(f.closed)
print(f.closed)

"""
17. Write a Python program to remove newline characters from a file.
"""

with open('fruits.txt') as f:
    my_string = ' '.join(map(lambda x: x.strip('\n'), f.readlines()))
    print(my_string)

    f.seek(0)
    print(f.read())

# 18. Write a Python program that takes a text file as input and returns the number of words of a given text file. Go to the editor
def count_words(filepath):
   with open(filepath) as f:
       data = f.read()
       data.replace(",", " ")
       return len(data.split(" "))
print(count_words("words.txt"))

# 19. Write a Python program to extract characters from various text files and puts them into a list. 
import glob
char_list = []
files_list = glob.glob("*.txt")
for file_elem in files_list:
   with open(file_elem, "r") as f:
       char_list.append(f.read())
print(char_list)

# 20. Write a Python program to generate 26 text files named A.txt, B.txt, and so on up to Z.txt. 
import string, os
if not os.path.exists("letters"):
   os.makedirs("letters")
for letter in string.ascii_uppercase:
    with open(f"{letter}.txt", "w") as f:
        f.writelines(letter)

# 21. Write a Python program to create a file where all letters of English alphabet are listed by specified number of letters on each line. 
import string
def letters_file_line(n):
   with open("words1.txt", "w") as f:
       alphabet = string.ascii_uppercase
       letters = [alphabet[i:i + n] + "\n" for i in range(0, len(alphabet), n)]
       f.writelines(letters)
letters_file_line(3)
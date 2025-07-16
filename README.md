# Yugioh-FM hundo router

A program that reads PS1 memory card images that contain *Yu-Gi-Oh! Forbidden Memories* and uses an SQL database with the data for the game to give you the "best" route. Indicating the next opponents and which cards you can obtain. This assumes you can beat all opponents.

This was heavily inspired by [this 100% spreadsheet](https://docs.google.com/spreadsheets/d/1itRIuMimb5V8MvUvhijNrmo-gVGR58UTeTZN0KXwPno/edit?gid=558946044#gid=558946044) and by [FM-librarian](https://github.com/sg4e/FM-Librarian). I just wanted more convenience, but those tools are much more accessible for people that are not familiarized with python than this.

## Usage
To properly use this you need tome familiarity with python. Currently I have a bunch of things hard coded.

## Tested memory card formats
* Raw memory card dump

This should work with any emulator that accurately saves memory card data and saves the game in the first slot.

## Command-line usage
```
python router.py [memory card image file]
```

## Game info database

I also included the sql code in `yugiohFM.sql` to recreate the game info database.

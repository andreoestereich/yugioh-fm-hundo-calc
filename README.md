# Yugioh-FM hundo router

A program that reads PS1 memory card images that contain *Yu-Gi-Oh! Forbidden Memories* and uses an sql database with the data for the game to give you the "best" route. Indicating the next oponents and which cards you can obtain. This assumes you can beat all oponents.

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

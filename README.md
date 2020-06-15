# GOG Galaxy 2.0 CSV export HTML5 formatter

This script helps users convert the CSV data exported through [GOG Galaxy Export Script](https://github.com/AB1908/GOG-Galaxy-Export-Script) to a nice, searchable, customizable HTML5 format.

![Screenshot](https://user-images.githubusercontent.com/284077/84387704-b5940200-abf3-11ea-9cf4-058c20d4049b.png)

## Features

* Customizable HTML5, game partials, CSS and JS
* Vanilla JS implementation
* Live cover images resizing and spacing
* Interactive offline search

## Usage

### CLI

#### File specification
* `-i Filename` or `--input Filename` to specify the full path of the CSV file (defaults to `./gameDB.csv`)
* `-l Filename` or `--list Filename` to specify the full path of the output cover list URLs file (defaults to `./imagelist.txt`)
* `-o Filename` or `--output Filename` to specify the full path of the output HTML5 file (defaults to `./index.html`)

#### Commands
* `--image-list` creates a list containing the best matching URL for each game in the library
* `--html5` creates the HTML5 game library
  * `--title` custom title for the html page
  * `--embed` embeds .css and .js files instead of linking them

### Customization

Each of the files in the template can be overridden by creating a new file ending in `.custom.<extension>`, such as `style.custom.css` or `game.custom.html`. This allows minimal and personalised changes only where needed.

### HTML5 controls

You can open the controls by pressing `CTRL`+`Space`. From there you can search games, resize the game covers width, and the spacing between each other.

## Requirements

* Python 3
  * csv
  * natsort
  * unidecode
* A CSV exported through [GOG Galaxy Export Script](https://github.com/AB1908/GOG-Galaxy-Export-Script)
* `wget`, if you want the images in an easy way

## Known current limitations

* Works better when the CSV is extracted with the `-a` command
* Game data toopltip is not pretty enough
* The search results aren't weighted yet, and only consider titles

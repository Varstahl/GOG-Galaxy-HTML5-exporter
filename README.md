# GOG Galaxy 2.0 CSV export HTML5 formatter

This script helps users convert the CSV data exported through [GOG Galaxy Export Script](https://github.com/AB1908/GOG-Galaxy-Export-Script) to a nice, searchable, customizable HTML5 format.

![Screenshot](https://user-images.githubusercontent.com/284077/84957536-acc39480-b0fb-11ea-9df0-4ca14db38731.png)

## Features

* Customizable HTML5, game partials, CSS and JS
* Vanilla JS implementation
* Live cover images resizing and spacing
* Interactive offline search

## Usage

### Standard example
```
python csv_parser.py --image-list
wget -nc -P images -i ./imagelist.txt
python csv_parser.py --html5
```

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

**Note:** while exporting, a few other actions are automatically performed:
* delete unused images that have been replaced in the catalog
* `--html5`: rename image files to remove the HTML5 attributes if necessary (i.e. renames `image.webp?namespace=gamesdb` into `image.webp`)

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
* The search results aren't weighted yet, and only consider titles

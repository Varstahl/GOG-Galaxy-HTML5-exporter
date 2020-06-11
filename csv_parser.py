#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from html import escape
import json
from math import floor
from operator import itemgetter
from os import getcwd, makedirs
from os.path import join, exists
import re
from string import Formatter

from csv import DictReader
from natsort import natsorted
from unidecode import unidecode

__maintainer__ = "Bruno “Varstahl” Passeri"

class Arguments():
	""" argparse wrapper, to reduce code verbosity """
	__parser = None
	__args = None

	def __init__(self, args, **kwargs):
		self.__parser = argparse.ArgumentParser(**kwargs)
		for arg in args:
			self.__parser.add_argument(*arg[0], **arg[1])
		self.__args = self.__parser.parse_args()

	def help(self):
		self.__parser.print_help()

	def anyOption(self, exceptions):
		for k,v in self.__args.__dict__.items():
			if (k not in exceptions) and v:
				return True
		return False

	def __getattr__(self, name):
		ret = getattr(self.__args, name)
		if isinstance(ret, list) and (1 == len(ret)):
			ret = ret[0]
		return ret

class CustomStringFormatter(str):
	""" Custom template formatters, allows non used parameters to be left alone
	    instead of raising a Key/Index exception
	"""
	class CustomFormatter(Formatter):
		_usedArgs = set()

		def __init__(self, default='{{{0}}}'):
			self.default=default

		def get_value(self, key, args, kwargs):
			try:
				ret = super().get_value(key, args, kwargs)
				self._usedArgs.add(key)
				return ret
			except (IndexError, KeyError):
				return self.default.format(key)

	_formatter = CustomFormatter()

	def used_keys(self):
		""" All the keys used while formatting """
		return self._formatter._usedArgs

	def format(self, *args, **kwargs):
		self._formatter._usedArgs = set()
		return self._formatter.format(self, *args, **kwargs)

def roman_numeral(s):
	""" Returns a roman numeral converted to an integer if valid, or the source string """
	def roman_to_int(s):
		d = {'m': 1000, 'd': 500, 'c': 100, 'l': 50, 'x': 10, 'v': 5, 'i': 1}
		n = [d[i] for i in s if i in d]
		return str(sum([i if i>=n[min(j+1, len(n)-1)] else -i for j,i in enumerate(n)]))

	if not re.match(r'^(?=[mdclxvi])m*(c[md]|d?c{0,3})(x[cl]|l?x{0,3})(i[xv]|v?i{0,3})$', s):
		return s

	return roman_to_int(s)

def repeatable_fields(mo):
	""" Repeats '{rep}…{/rep}' template partial to format a list
		of name:values generated from the static variable `params`.
		Uses `0` and `1` from the matching group for the whitespace and
		repeatable content.
	"""
	rf = ''
	for k,v in repeatable_fields.params.items():
		if v:
			rf += mo.group(1) + mo.group(2).format(k, v)
	return rf

def duration(t):
	""" Converts minutes into a "Xd Yh Zm" format """
	t = int(t)
	m = floor(t % 60)
	h = floor((t / 60) % 24)
	d = floor(t / 1440)
	t = ''
	if m: t = str(m) + 'm'
	if h: t = str(h) + 'h ' + t
	if d: t = str(d) + 'd ' + t
	return t.strip()

def html(s):
	""" HTML sanitisation """
	return re.sub(r'[ \t]*\n', '<br/>', escape(s))

def delist(s):
	""" Explodes a list into a nicely spaced list """
	return ', '.join([html(x) for x in s.split(',')]).replace('  ', ' ')

def Main(args):
	games = []
	articles = '(' + '|'.join([
		r'an?\s+', r'the\s+',  # English
		r'il?\s+', r'l[oiae]\s+', r'gli\s+', r'un[oa]?\s+', r'(?:l|un)\''  # Italian
	]) + ')'
	titleReplaceList = [
		(r'\.\.\.', '…'),
	]  # Cleans the title
	transliteratedTitleReplaceList = [
		(r', ' + articles + r'$', ''),
		(r'\(tm\)', ''),
		(r'\(r\)', ''),
	]  # Cleans the transliterated title, and removes useless things
	searchReplaceList = [
		[
			(r'[,.…]', ''),
		], [
			(r'[;:\'-]', ''),
			(r'[|\\/()]', ' '),
			(r'\s{2,}', ' '),
		], [
			(r'([0-9])0{12}(\s|$)', r'\1t\2'),
			(r'([0-9])0{9}(\s|$)', r'\1g\2'),
			(r'([0-9])0{6}(\s|$)', r'\1m\2'),
			(r'([0-9])0{3}(\s|$)', r'\1k\2'),
		]
	]  # Each list group creates a new permutation of the search string

	# Build the game data list
	with open(args.fileCSV, "r", encoding='utf-8', newline='') as csvfile:
		for row in DictReader(csvfile, delimiter=args.delimiter):
			try:
				# Set the default image
				for t in ['verticalCover', 'backgroundImage', 'squareIcon']:
					if row[t]:
						row['_defaultImage'] = row[t]
						break
			except KeyError:
				print('Unable to find images: forgot to select a delimiter or to export them?')
				return

			if '_defaultImage' not in row:
				continue

			# Fix common problems with titles
			for i in titleReplaceList:
				row['title'] = re.sub(i[0], i[1], row['title'])

			# Transliterate and transform the title in a sortable/searchable ascii format
			row['_titleTL'] = re.sub(r'^' + articles + r'(.+?)$', r'\2, \1', unidecode(row['title']).lower()).strip()
			for i in transliteratedTitleReplaceList:
				row['_titleTL'] = re.sub(i[0], i[1], row['_titleTL'])

			# Facilitate searches
			row['_searchable'] = list(set([row['title'].lower(), row['_titleTL']]))
			searchItem = row['_titleTL']
			for srl in searchReplaceList:
				for i in srl:
					searchItem = re.sub(i[0], i[1], searchItem).strip()
				if searchItem not in row['_searchable']:
					row['_searchable'].append(searchItem)

			# Try a roman numerals to digits conversion
			searchItem = ' '.join([roman_numeral(x) for x in searchItem.split(' ')])
			if searchItem not in row['_searchable']:
				row['_searchable'].append(searchItem)

			games.append(row)

	games = natsorted(games, key=itemgetter('_titleTL'))

	# Export list of images
	if args.imageList:
		try:
			makedirs(join(getcwd(), 'images'))
		except: pass

		# Find the best match for the image
		try:
			with open(args.fileImageList, "w", encoding='utf-8') as ll:
				for game in games:
					ll.write(game['_defaultImage'] + '\n')
		except FileNotFoundError:
			print('Unable to write to “{}”, make sure the path exists and you have permissions'.format(args.fileImageList))
			return

		# Reset header for future use and notify success
		print('Image list exported, it\'s suggested to download with `wget -nc -P images -i "{}"`'.format(args.fileImageList))

	# Export HTML5
	if args.htmlExport:
		# Load the templates
		templates = {}
		for k,l in {
			'index': ['index', '.html'],
			'game': ['game', '.html'],
			'script': ['script', '.js'],
			'style': ['style', '.css'],
		}.items():
			fn = 'templates/{0}{2}{1}'.format(l[0], l[1], '.custom' if exists('templates/{0}.custom{1}'.format(l[0], l[1])) else '')
			if args.embed or (k not in ['script', 'style']):
				with open(fn, 'r', encoding='utf-8') as f:
					templates[k] = CustomStringFormatter(f.read(-1))
			else:
				templates[k] = fn
				continue

		# Single game HTML
		gameID = len(games)  # start the ids from N (games count), to allow re-ordering in the range [0:N-1]
		games_html = ''
		games_css = ''
		for game in games:
			# Image URL modifier
			imgFN = re.sub(r'^[^/]*//[^/]*/', '', game['_defaultImage'].replace('?namespace', '@namespace'))
			game['_imageURL'] = 'images/{}'.format(imgFN)
			params = {
				'id': gameID,
				'title': html(game['title']),
				'description': html(game['summary']),
				'search': json.dumps(game['_searchable']).replace("'", "&apos;"),
				'developers': delist(game['developers']),
				'platforms': delist(game['platformList']),
				'score': html(game['criticsScore']),
				'publishers': delist(game['publishers']),
				'released': html(game['releaseDate']),
				'genres': delist(game['genres']),
				'themes': delist(game['themes']),
				'playtime': duration(game['gameMins'])
			}

			game_html = templates['game'].format('a', **params)
			games_css += '#game-{0}{{order:{0};background-image:url("{1}");}}'.format(gameID, game['_imageURL'])
			gameID += 1

			# Remove parameters already printed
			repeatable_fields.params = {x:params[x] for x in params if x not in templates['game'].used_keys() and isinstance(x, str)}
			games_html += re.sub(r'(\s*){rep}(.*?){/rep}', repeatable_fields, game_html)

		try:
			with open(args.fileHTML, 'w', encoding='utf-8') as f:
				css = ('<style>' + templates['style'] + '</style>') if args.embed else ('<link rel="stylesheet" type="text/css" href="' + templates['style'] + '">')
				js = ('<script>' + templates['script'] + '</script>') if args.embed else ('<script src="' + templates['script'] + '"></script>')
				f.write(templates['index'].format(**{
					'language': 'en',
					'title': args.title,
					'style': css,
					'javascript': js,
					'imageCSS': games_css,
					'content': games_html
				}))
			print('HTML5 list exported')
		except FileNotFoundError:
			print('Unable to write to “{}”, make sure the path exists and you have permissions'.format(args.fileHTML))
			return

if "__main__" == __name__:
	def ba(variableName, description, defaultValue=False):
		""" Boolean argument: creates a default boolean argument with the name of the storage variable and
			the description to be shown in the help screen
		"""
		return {
			'action': 'store_true',
			'required': defaultValue,
			'help': description,
			'dest': variableName,
		}

	args = Arguments(
		[
			[
				['-d'],
				{
					'default': ',',
					'type': str,
					'required': False,
					'metavar': 'CHARACTER',
					'help': 'CSV field separator, defaults to comma',
					'dest': 'delimiter',
				}
			],
			[
				['-i', '--input'],
				{
					'default': 'gameDB.csv',
					'type': str,
					'nargs': 1,
					'required': False,
					'metavar': 'FN',
					'help': 'CSV file path',
					'dest': 'fileCSV',
				}
			],
			[
				['-l', '--list'],
				{
					'default': 'imagelist.txt',
					'type': str,
					'nargs': 1,
					'required': False,
					'metavar': 'FN',
					'help': 'pathname of the generated list of cover URLs',
					'dest': 'fileImageList',
				}
			],
			[
				['-o', '--output'],
				{
					'default': 'index.html',
					'type': str,
					'nargs': 1,
					'required': False,
					'metavar': 'FN',
					'help': 'pathname of the generated HTML5 games list',
					'dest': 'fileHTML',
				}
			],
			[['--image-list'], ba('imageList', 'create an image list')],
			[['--html5'], ba('htmlExport', 'export the game list in html5 format')],
			[
				['--title'],
				{
					'default': 'GOG Galaxy 2 game library',
					'type': str,
					'nargs': 1,
					'required': False,
					'metavar': 'TITLE',
					'help': 'title of the HTML5 file',
					'dest': 'title',
				}
			],
			[['--embed'], ba('embed', 'embeds CSS & JS instead of linking the resources')],
		],
		description='GOG Galaxy 2 export converter: parses the “GOG Galaxy 2 exporter” CSV to generate a list of cover images and/or a searchable HTML5 list of games.'
	)

	if args.anyOption(['delimiter', 'fileCSV', 'fileImageList', 'fileHTML', 'title']):
		if exists(args.fileCSV):
			Main(args)
		else:
			print('Unable to find “{}”, make sure to specify the proper path with “-i” (see --help)'.format(args.fileCSV))
	else:
		args.help()

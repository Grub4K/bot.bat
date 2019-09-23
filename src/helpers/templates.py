from textwrap import dedent



FUNCTION_HELP = '''\
{bot.name} function help:
{short_help}'''

SHORT_HELPS = '{settings.prefix}{commandname}: {shortdoc}'

LEVEL_UP = 'Congratz! <@{author.id}> is now at level {lvl}!'

LEADERBOARD = '''\
```Leaderboards:
{data}```'''

LEADERBOARD_DATA = '''\
{rank} {name}
Level: {level}[{current_exp}/{needed_exp}]
{exp_bar}'''

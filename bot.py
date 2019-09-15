import discord
import asyncio
import logging
from pathlib import Path
from random import randint
from collections import namedtuple

import functions
import templates



SETTINGS_FILE = Path('settings.ini')

# TODO implement lastsend
User = namedtuple('User', 'id exp')

class Settings:
    ...
    exp_bar_size = 20
    prefix = '.'
    submissions_file = 'submissions'
    leaderboard_file = 'leaderboard'
    react_emoji = '\N{THUMBS UP SIGN}'
    lvl_up_msg = 'Congratz! <@{0.autior.id}> is now at level {1:d}!'
    edit_delay = 5

class Bot(discord.Client):
    def __init__(self, settings_path, *args, **kwargs):
        # Load settings file
        self.settings = Settings()
        try:
            with settings_path.open() as s_file:
                for line in s_file:
                    key, _, value = line.partition('=')
                    setattr(self.settings, key, value)
        except IOError:
            raise ValueError('Could not parse settings file')
        # prepare leaderboard
        # TODO implement indexing
        self.leaderboard = []
        leaderboard_file = Path(self.settings.leaderboard_file)
        try:
            with leaderboard_file.open() as lb_file:
                for line in lb_file:
                    # Ignore comments
                    if line.lstrip().startswith('#'):
                        continue
                    try:
                        # Append user to leaderboard
                        user_id, _, user_exp = s.partition("=")
                        user = User(user_id, user_exp)
                        self.leaderboard.append(user)
                    except ValueError:
                        raise Error('Unexpected leaderboardfile structure.')
        except IOError:
            leaderboard_file.touch()
        # Set values, raise speciic error on fail
        try:
            self.owner = self.settings.owner
            self.update_channel = self.settings.update_channel
        except:
            raise ...
        # Enable first time leaderboard update
        self.update_leaderboard = True
        # populat some other properties
        self.ignored_channels = []
        ...
    def is_owner(author):
        return author.id == self.settings.owner
    def run(self):
        self.run(self.settings.token)
    async def on_ready(self):
        # TODO maybe move some of the stuff from __init__ to here
        # Get leaderboard message
        self.leaderboard_message = await self.get_channel(
            self.settings.leaderboard_id).fetch_message(0)
        print(leaderboard_message.id)
        # Signal ready
        await client.change_presence(status=discord.Status.online,
            activity=discord.Game(self.settings.prefix + "help"))
        print('Bot is ready.')
    async def on_raw_reaction_add(self, payload):
        ...
    async def on_message(self, message):
        # Process base commands
        # TODO verify if this is needed
        ...
        # Skip if message from ignored channel
        if message.channel.id in self.ignored_channels:
            return
        # Skip if message from bot
        if message.author.id == self.user.id:
            return
        # Check if its a command
        if message.content.startswith(self.settings.prefix):
            # Split message content into components
            command, _, arguments = message.content.partition(' ')
            try:
                # Try to execute corresponding function
                function = functions.functions[command]
                await function(self, message, arguments)
            except:
                # Log unknown command
                print('Unknown command: "{0}"'.format(command))
                # TODO add handler that prints unknown command message
                ...
        else:
            # Raise exp of sender by random value between 1 and 10
            exp_value = randint(1, 10)
            ...
            # Check for level up:
            if ...:
                # Notify of level up
                ...
            # update leaderboard if a change occured
            sorted_leaderboard = sorted(self.leaderboard, lambda x: x.exp)
            disp_len = self.settings.display_length
            if sorted_leaderboard == self.leaderboard:
                # Update indexing
                ...
                # If visible leaderboard changed update that
                if sorted_leaderboard[:disp_len] == self.leaderboard[:disp_len]:
                    self.update_leaderboard = True
            self.leaderboard = sorted_leaderboard

    # ATTENTION: This is utter trash that needs to be fixed.
    # TODO fix this and await it somewhere lol
    async def update_leaderboard_loop(self):
        while True:
            # check if should update
            if self.update_leaderboard:
                self._update_leaderboard = False
                # perform message edit
                # TODO edit this to new style thing
                s = '```Leaderboards:\n'
                s += '\n'.join(
                    dedent('''\
                        {rank} {name}
                        Level: {level}[{current_exp}/{needed_exp}]
                        {exp_bar}
                    ''').strip().format(**{
                        'rank' : i+1,
                        'name' : client(rank[i]).get_user.display_name,
                        'level' : lvl[rank[i]],
                        'current_exp' : exp[rank[i]],
                        'needed_exp' : exp_next_lvl(lvl[rank[i]]),
                        'exp_bar' : exp_bar(rank[i])
                    })
                    for i in range(len(rank))
                )
                s += "```"
                await leaderboard.edit(content=s)
            await asyncio.sleep(self.settings.edit_delay)
    def generate_help(self):
        return_str = ''
        short_helps = []
        for name, function in functions.functions:
            # Get function
            doc = function.__doc__ or ''
            shortdoc, *_ = doc.splitlines(False) or ('',)
            short_help = self.expand_template('SHORT_HELPS',
                commandname=name,
                shortdoc=shortdoc
            )
            short_helps.append(short_help)
        return self.expand_template('FUNCTION_HELP',
            short_help='\n'.join(
                short_helps
            )
        )
    def expand_template(self, template, **kwargs):
        templ = getattr(templates, template)
        # TODO fill with useful info
        bot_data = {
            'prefix': self.settings.prefix,
            'name': self.user.name,
        }
        return templ.format(**bot_data, **kwargs)

if __name__ == '__main__':
    bot = Bot(SETTINGS_FILE)
    bot.run()

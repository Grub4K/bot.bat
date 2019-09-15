import discord
import asyncio
import logging
from pathlib import Path
from random import randint
from collections import namedtuple

from helpers import (
    exp,
    access_control,
    templates
)
import functions



SETTINGS_FILE = Path('settings.ini')

# TODO implement lastsend
User = namedtuple('User', 'id exp lvl')

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
        logging.info('leaderboard id: {0}'.format(leaderboard_message.id))
        # Signal ready
        await client.change_presence(status=discord.Status.online,
            activity=discord.Game(self.settings.prefix + "help"))
        logging.info('Bot is ready.')
    async def on_raw_reaction_add(self, payload):
        ...
    async def on_message(self, message):
        # Skip if message from ignored channel
        if message.channel.id in self.ignored_channels:
            return
        # Skip if message from bot
        if message.author.id == self.user.id:
            return
        # Check if its a command
        if message.content.startswith(self.settings.prefix):
            # Split message content into components
            msg = message.content.lstrip(self.settings.prefix)
            command, _, arguments = msg.partition(' ')
            try:
                # Try to fetch corresponding function
                function = functions.functions[command]
            except:
                # Log unknown command
                logging.warning('Unknown command: "{0}"'.format(command))
            else:
                # Try to execute corresponding function
                try:
                    logging.info('Executing command {0}'.format(command))
                    await function(self, message, arguments)
                except Exception as exception:
                    logging.exception('Exception while executing command:',
                        exception)
        else:
            await self.add_exp(message)
    async def add_exp(self, message, lower=10, upper=25):
        """\
            Adds exp to the user that send message
        """
        disp_len = self.settings.display_length
        # Create new user if not already in users dictionary
        if not user_id in self.users:
            user = User(user_id)
            self.users[user_id] = user
        else:
            user = self.users[user_id]
        # Check amount of current exp and exp needed
        exp_amount = randint(lower, upper)
        user.exp += exp_amount
        exp_needed = helpers.exp.exp_next_lvl(user.lvl)
        if user.exp >= exp_needed:
            # User leveled up, increase level and send message
            user.lvl += 1
            user.exp -= exp_needed:
            # TODO send message
            ...
        # get new order of users (sort by total exp)
        sorted_users = sorted(self.users.values(), reverse=True)
        # Slice sequence to leaderboard places
        new_leaderboard = [*itertools.islice(sorted_users, disp_len)]
        # Check if leaderboard changed
        if self.leaderboard != new_leaderboard:
            # Set update leaderboard flag
            self.update_leaderboard = True
            self.leaderboard = new_leaderboard
    # ATTENTION: This is utter trash that needs to be fixed.
    # TODO fix this and await it somewhere lol
    async def update_leaderboard(self):
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
    # TODO implement custom loop to accept timer function
    bot.run()

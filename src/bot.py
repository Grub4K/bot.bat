import discord
import asyncio
import logging
from pathlib import Path
from random import randint
from dataclasses import dataclass

from helpers import (
    exp,
    access_control,
    templates
)
import functions



SETTINGS_FILE = Path('settings.json')

@dataclass
class User:
    """\
        Class that symbolizes a discord user
    """
    id : str
    exp : int = 0
    lvl : int = 0
    next_send_time : float = time.time()
    def __lt__(self, other):
        return (self.lvl, self.exp) < (other.lvl, other.exp)

@dataclass
class Settings:
    """\
        Settings class that symbolizes settings for the bot
    """
    token : str
    leaderboard_id : str
    exp_bar_size : int = 20
    prefix : str = '.'
    submissions_file : str = 'submissions.txt'
    settings_file : str = 'leaderboard.json'
    ignored_channels : list = []
    react_emoji : str = '\N{THUMBS UP SIGN}'
    edit_delay : int = 5
    ...

class Bot(discord.Client):
    """\
        Discord bot with leaderboard support
    """
    def __init__(self, settings_path, *args, **kwargs):
        """\
            Prepare bot, read settings and users file.
        """
        # Load settings file json
        try:
            with settings_path.open() as s_file:
                json_data = json.load(s_file)
        except IOError as e:
            logging.exception('Error opening settings file.', e)
            raise SystemExit
        except json.JSONDecodeError as e:
            logging.exception('Error parsing settings json.', e)
            raise SystemExit
        # Construct settings
        try:
            self.settings = Settings(**json_data)
        except TypeError as e:
            logging.exception('Unexpected settings file structure.', e)
            raise SystemExit
        # prepare leaderboard
        self.users = {}
        self.users_file = Path(self.settings.users_file)
        try:
            with self.users_file.open() as lb_file:
                json_data = json.load(lb_file)
        except IOError:
            self.users_file.touch()
        except json.JSONDecodeError as e:
            logging.exception('Error parsing users json.', e)
            raise SystemExit
        try:
            self.leaderboard = [User(**user_dict) for user_dict in json_data]
        # TODO: Specify exception
        except TypeError as e:
            logging.exception('Unexpected user file structure.', e)
            raise SystemExit
        # Enable first time leaderboard update
        self.update_leaderboard = True
    def is_owner(author):
        """\
            Check if an autor is the owner.
        """
        return author.id == self.settings.owner
    def run(self):
        """\
            Start the bot.
        """
        # TODO: rework call to also start timer
        super().run(self.settings.token)
    def close(self):
        """\
            Safely store settings and users in a file and then end bot.
        """
        self.safe_settings()
        self.save_users()
        super().close()
    def save_users(self):
        """\
            Saves the current user state to the users file
        """
        def convert_user(user):
            return user.__dict__
        user_list = [*self.users.values()]
        with self.users_file.open('w') as users_file:
            json.dump(users_file, user_list, default=convert_user)
    async def on_ready(self):
        # Get leaderboard message
        self.leaderboard_message = await self.get_channel(
            self.settings.leaderboard_id).fetch_message(0)
        logging.info('leaderboard id: {0}'.format(self.leaderboard_message.id))
        # Signal ready
        await client.change_presence(status=discord.Status.online,
            activity=discord.Game(self.settings.prefix + "help"))
        logging.info('Bot is ready.')
    async def on_raw_reaction_add(self, payload):
        # TODO: implement this
        ...
    async def on_message(self, message):
        """\
            Handle a message that got send into a channel.

            Actual processing gets done in the corresponding functions.
        """
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
    async def add_exp(self, message, lower=10, upper=25, delay=10):
        """\
            Adds exp to the user that send message
        """
        disp_len = self.settings.display_length
        # Create new user if not already in users dictionary
        if not user_id in self.users:
            logging.info('Adding id "{0}" to users'.format(user_id))
            user = User(id=user_id)
            self.users[user_id] = user
        else:
            user = self.users[user_id]
        # Check if delay expired
        time_now = time.time()
        if user.next_send_time >= time_now:
            return
        # Set new delay
        user.next_send_time = time_now + delay
        # Check amount of current exp and exp needed
        exp_amount = randint(lower, upper)
        user.exp += exp_amount
        exp_needed = helpers.exp.exp_next_lvl(user.lvl)
        if user.exp >= exp_needed:
            # User leveled up, increase level and send message
            user.lvl += 1
            user.exp -= exp_needed:
            logging.info('User "{0.id}" reached level {0.lvl}.'.format(user))
            level_up_message = self.expand_template('LEVEL_UP',
                author=message.author, lvl=user.lvl)
            await message.channel.send(level_up_message)
        # get new order of users (sort by total exp)
        sorted_users = sorted(self.users.values(), reverse=True)
        # Slice sequence to leaderboard places
        new_leaderboard = [*itertools.islice(sorted_users, disp_len)]
        # Check if leaderboard changed
        if self.leaderboard != new_leaderboard:
            # Set update leaderboard flag
            self.update_leaderboard = True
            self.leaderboard = new_leaderboard
        self.save_users()
    # ATTENTION: This is utter trash that needs to be fixed.
    # TODO: fix this and await it somewhere lol
    async def update_leaderboard(self):
        """\
            Async loop that updates the leaderboard.
        """
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
                await self.leaderboard_message.edit(content=s)
            await asyncio.sleep(self.settings.edit_delay)
    def generate_help(self):
        """\
            Generate short help for all commands available
        """
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
        """\
            Expand a text template from the templates module
        """
        templ = getattr(templates, template)
        # TODO fill with useful info
        bot_data = {
            'prefix': self.settings.prefix,
            'name': self.user.name,
        }
        return templ.format(**bot_data, **kwargs)

if __name__ == '__main__':
    """\
        Main entry point
    """
    bot = Bot(SETTINGS_FILE)
    bot.run()

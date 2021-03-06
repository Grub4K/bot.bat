import discord
import asyncio
import logging
import json
from pathlib import Path
from random import randint
from dataclasses import dataclass, field
from typing import List, Optional

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
    exp_bar_size : int = 20
    prefix : str = '.'
    lb_id : int
    lb_message_id : Optional[int] = None
    submissions_file : str = 'submissions.txt'
    users_file : str = 'users.json'
    ignored_channels : List[int] = field(default_factory=list)
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
            json_data = []
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
        self.should_update_leaderboard = True
        self.functions = functions.functions
        super().__init__()
    def is_owner(author):
        """\
            Check if an autor is the owner.
        """
        return author.id == self.settings.owner
    def run(self):
        """\
            Start the bot.
        """
        loop = asyncio.get_event_loop()
        try:
            discord_coro = super().start(self.settings.token)
            lb_coro = self.update_leaderboard()
            loop.run_until_complete(asyncio.gather(discord_coro, lb_coro))
        except KeyboardInterrupt:
            loop.run_until_complete(self.close())
            # cancel all tasks lingering
        except Exception as e:
            logging.exception('Error in main loop, exiting...')
        finally:
            loop.close()
    async def close(self):
        """\
            Safely store settings and users in a file and then end bot.
        """
        self.safe_settings()
        self.save_users()
        await super().close()
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
        lb_channel = await self.get_channel(self.settings.lb_id)
        if self.settings.lb_message_id is None:
            self.leaderboard_message = lb_channel.send('_ _')
            self.settings.lb_message_id = self.leaderboard_message.id
        else:
            self.leaderboard_message = lb_channel.fetch_message(
                self.settings.lb_message_id)
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
        user_id = message.author.id
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
            # TODO fix this to send to a specified channel instead
            await message.channel.send(level_up_message)
        # get new order of users (sort by total exp)
        sorted_users = sorted(self.users.values(), reverse=True)
        # Slice sequence to leaderboard places
        new_leaderboard = [*itertools.islice(sorted_users, disp_len)]
        # Check if leaderboard changed
        if self.leaderboard != new_leaderboard:
            # Set update leaderboard flag
            self.should_update_leaderboard = True
            self.leaderboard = new_leaderboard
        self.save_users()
    async def update_leaderboard(self):
        """\
            Async loop that updates the leaderboard.
        """
        while True:
            # check if should update
            if self.should_update_leaderboard:
                self.should_update_leaderboard = False
                # perform message edit
                leaderboard_data = '\n'.join(
                    self.expand_template(
                        'LEADERBOARD_DATA'
                        rank=rank,
                        name=self.get_user(int(user.id)),
                        level=user.lvl,
                        current_exp=user.exp,
                        needed_exp=exp.exp_next_lvl(user.lvl),
                        exp_bar=exp.exp_bar(user)
                    )
                    for rank, user in enumerate(self.leaderboard, 1)
                )
                msg = self.expand_template('LEADERBOARD', data=leaderboard_data)
                await self.leaderboard_message.edit(content=msg)
            await asyncio.sleep(self.settings.edit_delay)
    def expand_template(self, template, **kwargs):
        """\
        Expand a text template from the templates module
        """
        templ = getattr(templates, template)
        return self.format(templ, **kwargs)
    def format(self, message, **kwargs):
        # TODO fill with useful info
        bot_data = {
        'settings': self.settings,
        'bot': self.user,
        }
        return message.format(**bot_data, **kwargs)

if __name__ == '__main__':
    """\
        Main entry point
    """
    bot = Bot(SETTINGS_FILE)
    bot.run()

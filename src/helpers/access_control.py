import functools
from textwrap import dedent



def owner_only(function):
    @functools.wraps(function)
    async def wrapped(self, message, arguments):
        if self.is_owner(message.author):
            await function(self, message, arguments)
        else:
            await message.channel.send('Not authorized')
    wrapped.__doc__ = '(owner only) ' + dedent(function.__doc__)
    return wrapped

def exp_next_lvl(lvl):
    """\
    returns the ammount of exp needed to reach next level"""
    return 5 * (lvl * (lvl + 10) + 20)

def exp_bar(self, user, size=20):
    """\
        Returns a string visualizing the current exp of the user as a bar.
    """
    bar_length = user.exp * size // exp_next_lvl(user.lvl)
    space_length = size - bar_length
    bar = '#' * bar_length + '.' * space_length
    return '[' + bar + ']'

def exp_total(lvl, exp):
    """\
    returns the ammount of xp you have as value from lvl"""
    return 5 * lvl * (lvl + 7) * (2 * lvl + 13) // 6 + exp

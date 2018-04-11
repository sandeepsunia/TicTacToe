import tkinter
from itertools import product
from math import trunc
from functools import lru_cache, wraps
from random import choice
from sys import modules

################################################################################

class Cross(tkinter.Frame):

    @classmethod
    def main(cls):
        tkinter.NoDefaultRoot()
        root = tkinter.Tk()
        root.title('Demo')
        root.resizable(False, False)
        widget = cls(root)
        widget.grid()
        root.mainloop()

    def __init__(self, master=None, cnf={}, **kw):
        super().__init__(master, cnf, **kw)
        self.__ai = CrossAI()
        space = ' ' * 11
        self.__buttons = {}
        for r, c in product(range(3), range(3)):
            b = tkinter.Button(self, text=space, command=self.__bind(r, c))
            b.grid(row=r, column=c, padx=10, pady=10)
            self.__buttons.setdefault(r, {})[c] = b

    def __bind(self, row, column):
        return lambda: self.click(row, column)

    def click(self, row, column):
        r, c = self.__ai.move(row, column)
        if r != -1 != c:
            self.__buttons[row][column]['text'] = '    X    '
            if r != -2 != c:
                self.__buttons[r][c]['text'] = '    O    '

################################################################################

def enum(names):
    "Create a simple enumeration having similarities to C."
    return type('enum', (), dict(map(reversed, enumerate(
        names.replace(',', ' ').split())), __slots__=()))()

################################################################################

class Static(type):

    def __new__(cls, name, bases, members):
        for name, member in members.items():
            if callable(member):
                members[name] = cls.__wrap(member)
            elif isinstance(member, property):
                members[name] = property(cls.__wrap(member.fget),
                                         cls.__wrap(member.fset),
                                         cls.__wrap(member.fdel),
                                         member.__doc__)
            elif isinstance(member, (classmethod, staticmethod)):
                members[name] = type(member)(cls.__wrap(member.__func__))
        return super().__new__(cls, name, bases, members)

    @classmethod
    def __wrap(cls, function):
        if function:
            annotations = function.__annotations__
            co_varnames = function.__code__.co_varnames
            if not annotations:
                return function
            @wraps(function)
            def wrapper(*args):
                for arg, name in zip(args, co_varnames):
                    cls.__raise(arg, annotations[name])
                value = function(*args)
                cls.__raise(value, annotations['return'])
                return value
            return wrapper

    @staticmethod
    def __raise(item, klass):
        if klass is None:
            klass = type(None)
        elif isinstance(klass, str):
            klass = vars(modules[item.__module__])[klass]
        if not isinstance(item, klass):
            raise TypeError('{} must be of type {}'.format(item, klass))

################################################################################

class CrossAI(metaclass=Static):

    STATE = enum('changing, victory, defeat, error, draw')

    def __init__(self: 'CrossAI') -> None:
        self.__db = State(((0, 0, 0), (0, 0, 0), (0, 0, 0)), 1)

    def move(self: 'CrossAI', row: int, column: int) -> tuple:
        if not self.__db.moves:
            return -1, -1
        self.__make_move(row, column)
        return self.__best_move()

    def __make_move(self: 'CrossAI', row: int, column: int) -> None:
        copy = tuple(map(list, self.__db.grid))
        copy[row][column] = 1
        self.__db = State(tuple(map(tuple, copy)), -1)

    def __best_move(self: 'CrossAI') -> tuple:
        if not self.__db.moves:
            return -2, -2
        score = min(move.grade for move in self.__db.moves)
        moves = tuple(move for move in self.__db.moves if move.grade == score)
        final = choice(moves)
        for r, c in product(range(3), range(3)):
            if self.__db.grid[r][c] != final.grid[r][c]:
                self.__db = State(final.grid, 1)
                return r, c

################################################################################

class State(tuple):

    @lru_cache(None)
    def __new__(cls, grid, next_move):
        return super().__new__(cls, (grid, make_moves(grid, next_move)))

    @property
    def grid(self):
        return self[0]

    @property
    def moves(self):
        return self[1]

    @property
    def grade(self):
        return grade(*self)

################################################################################

@lru_cache(None)
def make_moves(grid, next_move):
    moves = []
    for r, c in available_moves(grid):
        copy = tuple(map(list, grid))
        copy[r][c] = next_move
        moves.append(State(tuple(map(tuple, copy)), -next_move))
    return frozenset(moves)

@lru_cache(None)
def available_moves(grid):
    return () if grade_grid(grid) else \
        tuple((r, c) for r, c in product(range(3), range(3)) if not grid[r][c])

@lru_cache(None)
def grade(grid, moves):
    return grade_grid(grid) + grade_moves(moves)

@lru_cache(None)
def grade_grid(grid):
    for triplet in combinations(grid):
        grade = trunc(sum(triplet) / 3)
        if grade:
            return grade
    return 0

@lru_cache(None)
def combinations(grid):
    combos = list(grid)
    for c in range(3):
        combos.append(tuple(grid[r][c] for r in range(3)))
    combos.append(tuple(grid[i][i] for i in range(3)))
    combos.append(tuple(grid[i][2 - i] for i in range(3)))
    return combos

@lru_cache(None)
def grade_moves(moves):
    return sum(grade(*move) for move in moves)

################################################################################

if __name__ == '__main__':
    Cross.main()

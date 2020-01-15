# coding=utf-8
import shutil
from colorama import Fore, Back, Style
import datetime


def shim_print(main_msg, additional_msg="",  level=None):
    cols, rows = shutil.get_terminal_size()
    stars = round((cols - len(" NEAT PYTHON SHIM ")) / 2)
    minusen = False

    starsRight = "*" * stars
    if (stars * 2) + len(" NEAT PYTHON SHIM ") > cols:
        starsRight = "*" * (stars - 1)

    print(Fore.YELLOW)
    print(f'{"*" * stars} NEAT PYTHON SHIM {starsRight}')
    print()
    print(f"🐍 ({datetime.datetime.now()}) - [{main_msg}{Fore.RESET}{Fore.YELLOW}]")
    print()
    if additional_msg:
        print(f'{additional_msg}')
    print("*" * cols)
    print(Fore.RESET)
    #mport time; time.sleep(5)

# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.

import os, shutil, logging
import pandas as pd
import time
import tkinter as tk
from tkinter import filedialog
from plans import project

root_name = "plans"
project_name = ""
my_project = None


# ---------------------------------- LOGGER ----------------------------------
def logger_setup(
    logger_name="plans", streamhandler=True, filehandler=False, logfile=None
):
    # ---------------------- LOGGER ----------------------
    # Basic logging config
    logging.basicConfig(level=logging.INFO)
    # Create a logger with a specific name
    logger = logging.getLogger(logger_name)
    logger.propagate = False

    # ---------------------- CONSOLE ----------------------
    # Create a console handler and set its level
    if streamhandler:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # Set the handler level

    # ---------------------- FILE ----------------------
    if filehandler:
        # Create a file handler and set its level
        if logfile is None:
            logfile = "plans.log"
        file_handler = logging.FileHandler(logfile)
        file_handler.setLevel(logging.INFO)  # Set the handler level

    # ---------------------- FORMAT ----------------------
    # Create a formatter and set it for both parsers
    formatter = logging.Formatter(
        "%(asctime)s  %(levelname)8s >>> %(message)s ",
        datefmt="%Y-%m0-%d %H:%M:%S",
    )
    if streamhandler:
        console_handler.setFormatter(formatter)
    if filehandler:
        file_handler.setFormatter(formatter)

    # ---------------------- ADD ----------------------
    if streamhandler:
        logger.addHandler(console_handler)
    if filehandler:
        logger.addHandler(file_handler)
    return logger


def the_prompt():
    global projet_name, root_name
    str_aux = root_name[:]
    if project_name == "":
        pass
    else:
        str_aux = str_aux + "@" + projet_name
    return "{}:".format(str_aux)


def sleeper():
    time.sleep(0.5)


def get_location(place):
    global my_project, root
    if my_project is None:
        place = root
    return "location: {}\n".format(place)


def warning(message):
    logger.warning(msg="{} {}".format(the_prompt(), message))
    return None


def done(message=None):
    if message is None:
        logger.info(msg="{} done.".format(the_prompt()))
    else:
        logger.info(msg="{} done. {}".format(the_prompt(), message))
    sleeper()
    return None


def ok(message=None):
    if message is None:
        message = ""
    logger.info(msg="{} OK. {}".format(the_prompt(), message))
    return None


def proceed(message=None):
    if message is None:
        return "{} proceed? (y/n): ".format(the_prompt())
    else:
        return "{} {} -- proceed? (y/n): ".format(the_prompt(), message)


def confirm(prefix_message=None):
    while True:
        str_confirm = input(proceed(message=prefix_message)).strip()
        if str_confirm in ["y", "n"]:
            break
        else:
            pass
    return str_confirm


def copy_file(src, dst):
    shutil.copy(src, dst)


def pick_folder(title="Select a folder"):
    root_tk = tk.Tk()
    root_tk.withdraw()  # Hide the main window

    folder_path = filedialog.askdirectory(title=title)

    if folder_path:
        return folder_path
    else:  # cancel
        return None


def func_a():
    print("ok")
    time.sleep(2)


def func_b():
    print("wohooo")
    time.sleep(2)


def func_c(p):
    dict_menu = {"Option A": [func_a, None], "Option B": [func_b, None]}

    m2 = Menu(dict_actions=dict_menu, name="project setup")
    m2.loop()


def new_project():
    global prompt_name, project_name, root, my_project

    def set_new_project():
        while True:
            str_name = input("{} enter new project name: ".format(the_prompt())).strip()
            if str_name in os.listdir(root):
                warning("project already exists")
                break
            elif any(char.isspace() for char in str_name):
                warning("blank spaces in name not allowed")
                break
            elif len(str_name) > 20:
                warning("name too long (max 20 characters)")
                break
            else:
                str_confirm = confirm(prefix_message="new name: {}".format(str_name))
                if str_confirm == "n":
                    pass
                else:
                    # create new project
                    ok(message="creating new project {}...".format(str_name))
                    # create project
                    my_project = project.Project(name=str_name, root=root)
                    # set up project
                    my_project.setup()
                    my_project = None
                    sleeper()
                    done()
                break
        return 0

    dict_menu = {
        "set project name": [set_new_project, None],
    }

    m2 = Menu(
        dict_actions=dict_menu, name="new project", message=get_location(place=root)
    )
    m2.loop()


def import_file():
    print("ihaa")


def data_mgmt_topo():
    global my_project

    def import_topo():

        dict_menu = {
            "dem.asc": [func_b, None],
            "slope.asc": [func_b, None],
            "twi.asc": [func_b, None],
        }

        submenu_name = "{} - datasets - [topo]".format(my_project.name)
        submenu = Menu(dict_actions=dict_menu, name=submenu_name, message=place)
        submenu.loop()

    place = my_project.folder_main + "/datasets/topo"

    dct_status = my_project.get_status(folder_name="datasets/topo")

    str_message = (
        dct_status["Folder"][["Folder", "File", "Format"]].to_string(index=False) + "\n"
    )

    dict_menu = {
        "import map": [func_b, None],
        "view map": [func_b, None],
        "run diagnostics": [func_b, None],
    }

    submenu_name = "{} - datasets - [topo]".format(my_project.name)
    submenu = Menu(dict_actions=dict_menu, name=submenu_name, message=str_message)
    submenu.loop()


def data_mgmt():
    global my_project

    dict_menu = {
        "topographic maps [topo]": [data_mgmt_topo, None],
        "soil and lithology [soils]": [func_b, None],
        "land use land cover [lulc]": [func_b, None],
        "rainfall data [rain]": [func_b, None],
        "basins and streamflow [basins]": [func_b, None],
        "remote sensing [rs]": [func_b, None],
        "model data [model]": [func_b, None],
    }
    place = my_project.folder_main + "/datasets"
    submenu_name = "{} - datasets".format(my_project.name)
    submenu = Menu(
        dict_actions=dict_menu, name=submenu_name, message=get_location(place)
    )
    submenu.loop()


def project_session():
    global my_project, project_name
    project_name = my_project.name

    dict_menu = {
        "data management": [data_mgmt, None],
        "simulation tools": [func_a, None],
        "assessment tools": [func_a, None],
        "model diagnostics": [func_a, None],
    }
    place = my_project.folder_main
    submenu = Menu(
        dict_actions=dict_menu, name=my_project.name, message=get_location(place)
    )
    submenu.loop()


def open_project():
    global root, my_project, prompt_name

    def set_project(params=None):
        global my_project, projet_name, root
        my_project = project.Project(name=params[:], root=root)
        projet_name = params[:]
        # start project session
        project_session()
        # reset global variables
        my_project = None
        projet_name = ""
        return 0

    list_projects = os.listdir(root)
    dict_menu = dict()
    for p in list_projects:
        dict_menu[p] = [set_project, p]
    place = root
    m2 = Menu(dict_actions=dict_menu, name="open project", message=get_location(place))
    m2.loop()


class Menu:
    """
    The Primitive Menu Object
    """

    def __init__(self, dict_actions, name="Menu", exit_key="e", message=None):
        """Instantiate the Menu object

        :param dict_actions: dictionary of actions (functions) and parameters (dict)
        :type dict_actions: dict
        :param name: menu title
        :type name: str
        :param exit_key: exite key
        :type exit_key: str
        """
        self.header_size = 80
        self.header_char = "*"
        self.name = name
        self.message = message
        self.exit = exit_key
        self.dict_actions = dict_actions
        self.dict_actions["exit menu"] = self.exit
        # get lists
        self.list_options = [o for o in self.dict_actions]
        self.list_keys = [str(i + 1) for i in range(len(self.list_options))]
        # set exit on keys
        self.list_keys[-1] = self.exit
        # actions by keys
        self.dict_keys = dict()
        for i in range(len(self.list_keys)):
            self.dict_keys[self.list_keys[i]] = dict_actions[self.list_options[i]]
        # labels dict
        self.dict_labels = dict()
        for i in range(len(self.list_keys)):
            self.dict_labels[self.list_keys[i]] = self.list_options[i]

    def get_table(self):
        """Get the menu table

        :return: table dataframe
        :rtype: :class:`pandas.DataFrame`
        """
        # set header line

        list_options = self.list_options.copy()
        list_keys = self.list_keys.copy()
        # header line
        list_lines_sizes = [len(str_line) for str_line in list_options]
        n_line_size = max(list_lines_sizes)

        list_options.insert(0, "-" * (n_line_size + 2))
        list_keys.insert(0, "-" * 10)
        df_table = pd.DataFrame({"options": list_options, "keys": list_keys})
        return df_table

    def header(self):
        n_name = len(self.name)
        n_aux = int((self.header_size - n_name) / 2)
        str_aux = self.header_char * n_aux
        return "\n\n{} {} {}\n".format(str_aux, self.name.upper(), str_aux)

    def ask(self):
        print(self.header())
        if self.message is None:
            pass
        else:
            print(self.message)
        print(self.get_table().to_string(index=False))
        print("\n")
        while True:
            str_ans = input("{} enter key: ".format(the_prompt())).strip()
            if str_ans == "":
                pass
            else:
                break
        return str_ans

    def validade(self, str_answer):
        if str_answer in self.list_keys:
            ok(
                message="selected: {} >>> {}".format(
                    str_answer, self.dict_labels[str_answer]
                )
            )
            sleeper()
            return True
        else:
            warning(
                message="<{}> key not found. options available: {}".format(
                    str_answer, self.list_keys
                )
            )
            sleeper()
            return False

    def loop(self, skip_confirmation=True):
        self.get_table()
        while True:
            str_answer = self.ask()
            b_valid = self.validade(str_answer=str_answer)
            if str_answer == self.exit:
                logger.info("exiting")
                sleeper()
                break
            else:
                if b_valid:
                    b_run = True
                    if skip_confirmation:
                        pass
                    else:
                        str_confirm = confirm(
                            prefix_message=self.dict_labels[str_answer]
                        )
                        if str_confirm == "y":
                            b_run = True
                        else:
                            b_run = False
                    if b_run:
                        # run function
                        if self.dict_keys[str_answer][1] is None:
                            output = self.dict_keys[str_answer][0]()
                        else:  # run with parameters
                            output = self.dict_keys[str_answer][0](
                                self.dict_keys[str_answer][1]
                            )
                        if output == 0:
                            break


def main():
    global root, logger
    # define root
    root_name = "plans"
    root = "C:/" + root_name
    # project
    my_project = None

    # handle root
    if os.path.isdir(root):
        pass
    else:
        os.mkdir(root)

    logger = logger_setup(streamhandler=True, filehandler=False)
    logger.info(msg="{} {}".format(the_prompt(), "starting new session"))
    sleeper()

    #
    dict_menu = {
        "open project": [open_project, None],
        "new project": [new_project, None],
    }
    # set menu
    m = Menu(
        dict_actions=dict_menu,
        name="plans - Home",
        message=get_location(place=root),
    )
    # loop
    m.loop()


if __name__ == "__main__":
    main()

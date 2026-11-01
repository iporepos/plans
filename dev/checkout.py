# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 The Project Authors
# See pyproject.toml for authors/maintainers.
# See LICENSE for license details.
"""
Master CLI tool for checkout after development sessions.

Runs Black formatting, Sphinx docs build, unit tests, and guided git
operations (commit, tag, push) in an interactive loop.
"""

# IMPORTS
# ***********************************************************************

# Native imports
# =======================================================================
import subprocess
import sys
import time


# FUNCTIONS
# =======================================================================
def _clear():
    """Clear the terminal screen on both Windows and Unix."""
    subprocess.run("cls" if sys.platform == "win32" else "clear", shell=True)


def _show_recent_tags(n=10):
    """Print the n most recent semver tags, newest first.

    Uses git's built-in version sort. If the repo has more than ``n`` tags,
    a count of hidden older tags is shown.

    :param n: Maximum number of tags to display.
    :type n: int
    """
    result = subprocess.run(
        ["git", "tag", "--sort=-version:refname"],
        capture_output=True,
        text=True,
    )
    tags = [t for t in result.stdout.splitlines() if t.strip()]
    for tag in tags[:n]:
        print(f"  {tag}")
    if len(tags) > n:
        print(f"  ... ({len(tags) - n} older tags not shown)")


def _heading(message, symbol="-"):
    """Print a section heading preceded by a separator line.

    :param message: Heading text.
    :type message: str
    :param symbol: Character used to build the separator (repeated 50 times).
    :type symbol: str
    """
    print("\n")
    print(50 * symbol)
    print(message)


def fork(message="Chose action", exit_option="exit", clear_option=True):
    """Prompt the user for a binary decision with optional extra choices.

    Loops until a valid key is entered.

    :param message: Prompt text shown to the user.
    :type message: str
    :param exit_option: Label for an optional exit/cancel key. Pass ``None`` to omit.
    :type exit_option: str or None
    :param clear_option: When ``True``, adds a ``[clear]`` key to the prompt.
    :type clear_option: bool
    :returns: The key entered by the user (``"y"``, ``"n"``, the exit label, or ``"clear"``).
    :rtype: str
    """
    s_prefix = f" >>> {message}"
    s_opt = "[y][n]"
    ls = ["y", "n"]

    if exit_option is not None:
        s_opt = s_opt + f"[{exit_option}]"
        ls = ls + [exit_option]

    if clear_option:
        s_opt = s_opt + f"[clear]"
        ls = ls + ["clear"]

    s = f"{s_prefix} {s_opt}: "

    s_inp = None
    while True:
        s_inp = input(s).strip().lower()
        if s_inp in ls:
            break

    return s_inp


def user_input(message="Enter input"):
    """Prompt for a free-text string with inline confirmation.

    Repeats until the user confirms or cancels.

    :param message: Prompt text shown to the user.
    :type message: str
    :returns: The confirmed string, or ``None`` if the user cancelled.
    :rtype: str or None
    """
    s_inp = None
    s = f" >>> {message}: "
    while True:
        print("\n")
        s_inp = input(s).strip()
        s_msg = f"Confirm input: '{s_inp}' ?"
        decision = fork(message=s_msg, exit_option="cancel", clear_option=False)

        if decision == "y":
            print(" >>> input confirmed.")
            break
        elif decision == "cancel":
            print(" >>> input cancelled.")
            s_inp = None
            break
        elif decision == "n":
            print(" >>> input restarted.")
            continue

    return s_inp


def run_style():
    """Run Black formatter on the current directory."""
    _heading("Black style", "=")
    subprocess.run(["black", "."])
    return None


def build_docs():
    """Build the Sphinx documentation via ``dev.docs``."""
    _heading("Sphinx docs", "=")
    subprocess.run([sys.executable, "-m", "dev.docs"])
    time.sleep(3)
    return None


def run_tests():
    """Run the unit test suite via ``dev.tests``."""
    _heading("Unit tests", "=")
    subprocess.run([sys.executable, "-m", "dev.tests"])
    time.sleep(3)
    return None


def handle_commit():
    """Show git status and interactively commit staged changes."""
    while True:
        _heading("", "-")
        subprocess.run(["git", "status"])
        s = fork(message="Commit changes?", exit_option=None, clear_option=False)

        if s == "y":
            git_msg = user_input("Enter commit message")
            if git_msg is None:
                print(" >>> Commit cancelled.")
                time.sleep(1)
            else:
                subprocess.run(["git", "commit", "-m", git_msg])
                print(f" >>> '{git_msg}' successfully commited.")
                time.sleep(3)
            break

        elif s == "n":
            break


def handle_tag():
    """Show existing tags and interactively create an annotated tag.

    :returns: The new tag string (e.g. ``"v1.2.3"``), or ``None`` if skipped.
    :rtype: str or None
    """
    while True:
        _heading("Current tags", "-")
        _show_recent_tags()

        s = fork(message="Enter new tag?", exit_option=None, clear_option=False)

        if s == "y":
            stag = user_input("Enter new tag in vX.Y.Z format")

            if stag is None:
                print(" >>> Tagging cancelled.")
                time.sleep(1)
                return None

            tag_msg = f"Release {stag[1:]}"
            subprocess.run(["git", "tag", "-a", stag, "-m", tag_msg])

            print(f" >>> '{stag}' successfully added")
            print("Updated tags:")
            _show_recent_tags()
            time.sleep(3)

            return stag

        elif s == "n":
            return None


def handle_push(stag=None):
    """Interactively push the main branch and an optional tag to remote.

    :param stag: Tag to push alongside main, or ``None`` to skip tag push.
    :type stag: str or None
    """
    while True:
        _heading("Publish", "-")
        s = fork(
            message="Publish main branch to remote?",
            exit_option=None,
            clear_option=True,
        )

        if s == "y":

            subprocess.run(["git", "push", "origin", "main"])
            print("\n")
            print(f" >>> main branch successfully published")
            time.sleep(2)

            if stag is not None:
                subprocess.run(["git", "push", "origin", stag])
                print("\n")
                print(f" >>> tag {stag} successfully published")
                time.sleep(2)

            break

        elif s == "n":
            print(f" >>> publishing cancelled")
            break

        elif s == "clear":
            _clear()
            continue


def exiting():
    """Print exit message and clear the screen."""
    print(" >>> exiting ...")
    time.sleep(1)
    _clear()


def main():
    """Run the interactive checkout loop: docs, tests, style, commit, tag, push."""
    while True:
        _clear()
        _heading("CHECK OUT", "#")
        print("\n")

        s = fork("Build Docs and Run Tests?", "exit", False)
        if s == "y":

            build_docs()
            run_tests()

        elif s == "exit":
            exiting()
            break

        run_style()

        _heading("Git Tags", "=")
        _show_recent_tags()

        _heading("Git Status", "=")
        subprocess.run(["git", "status"])
        print("\n\n")
        s = fork(
            message="Add/commit/push new changes?",
            exit_option="exit",
            clear_option=False,
        )

        if s == "exit":
            exiting()
            break

        elif s == "y":
            subprocess.run(["git", "add", "."])
            handle_commit()
            stag = handle_tag()
            handle_push(stag)

        elif s == "n":
            continue

        elif s == "clear":
            _clear()
            continue


# SCRIPT
# ***********************************************************************
if __name__ == "__main__":

    main()

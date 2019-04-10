"""
This module implements a simple CLI using prompt_toolkit
"""

from __future__ import unicode_literals
from core.Log import Log
from prompt_toolkit.application import Application
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window, VSplit, FloatContainer, Float
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea, SearchToolbar
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from core.Event import Event
from prettytable import PrettyTable
from termcolor import colored
import os


class CLI(object):
    """
    Simple CLI class using prompt_toolkit
    """
    prompt_to_execution = {}
    prompt_to_info = {}

    @staticmethod
    def add_command(name, funct, info, arguments = None):
        """
        Add a command to the cli
        :param name: command
        :param funct: function to be executed using the command
        :param info: info description for help command
        :param arguments: List of arguments
        :return:
        """
        CLI.prompt_to_execution[name.decode('unicode-escape')] = [funct, arguments] # decode name in unicode, needed for autocomplete
        CLI.prompt_to_info[name] = info

    @staticmethod
    def list_commands():
        """
        List all commands with info text for help output
        :return:
        """

        data = PrettyTable()

        data.field_names = ["Command", "Info"]

        for k, v in sorted(CLI.prompt_to_info.iteritems()):
            data.add_row([k, v])

        Log.echo(data)


    @staticmethod
    def start_cli():
        """
        Start cli loop and execute command
        :return:
        """
        CLI.add_command("help", CLI.list_commands, "Show commands")

        command_completer = WordCompleter(list(sorted(CLI.prompt_to_execution.keys())), ignore_case=True)

        welcome_text = TextArea(text="Type help for command overview. Quit with ctrl-c.", height=1, style='class:output-field')

        output_field = TextArea(style='class:output-field')

        input_output = TextArea(style='class:output-field', multiline=True, wrap_lines=True)

        input_field = TextArea(
            height=1,
            prompt='> ',
            style='class:input-field',
            wrap_lines=True,
            history=FileHistory('cli_history'),
            auto_suggest=AutoSuggestFromHistory(),
            completer=command_completer,
            complete_while_typing=True)

        container = FloatContainer(
            content=VSplit([
                HSplit([
                    welcome_text,
                    input_field,
                    Window(height=1, char='', style='class:line'),
                    input_output

                ]),
                Window(width=1, char='|', style='class:line'),
                output_field,
            ]),
            floats=[
                Float(xcursor=True,
                      ycursor=True,
                      content=CompletionsMenu(max_height=16, scroll_offset=1))
            ]
        )

        # Style.
        style = Style([
            ('output-field', 'bg:#ecf0f1 #000000'),
            ('input-field', 'bg:#ecf0f1 #000000'),
            ('line', 'bg:#ecf0f1 #000000'),
        ])

        kb = KeyBindings()

        @kb.add('c-c')
        @kb.add('c-q')
        def _(event):
            " Pressing Ctrl-Q or Ctrl-C will exit the user interface. "
            event.app.exit()
            os._exit(0)

        @kb.add('c-m')
        def accept(event=None):
            user_input = input_field.text

            user_input = user_input.split(" ")

            if user_input[0] in CLI.prompt_to_execution:
                command = CLI.prompt_to_execution.get(user_input[0], lambda: 'Invalid')[0]
                args = CLI.prompt_to_execution.get(user_input[0], lambda: 'Invalid')[1]

                if len(user_input) == 2:
                    command(user_input[1])
                elif len(user_input) == 3:
                    command(user_input[1], user_input[2])
                elif len(user_input) == 4:
                    command(user_input[1], user_input[2], user_input[3])
                elif len(user_input) == 5:
                    command(user_input[1], user_input[2], user_input[3], user_input[4])
                elif args is not None:
                    command(args)
                else:
                    command()
            else:
                Log.error("Command not found")


            input_field.text = ''


            #input_field.document = Document(text=new_text, cursor_position=len(new_text))

        def log_to_input(**kwargs):
            msg = kwargs.get("str")

            new_text = input_output.buffer.text + msg + "\n"

            input_output.buffer.document = Document(
                text=new_text, cursor_position=len(new_text)
            )

        def clear_input():
            new_text = ''

            input_output.buffer.document = Document(
                text=new_text, cursor_position=len(new_text)
            )

        def log_to_output(**kwargs):
            msg = kwargs.get('str')
            new_text = output_field.buffer.text + msg + "\n"

            output_field.buffer.document = Document(
                text=new_text, cursor_position=len(new_text))

        Event.on('log_to_input', log_to_input)
        Event.on('log_to_output', log_to_output)

        CLI.add_command("clear", clear_input, "Clears cli output")

        # Run application.
        application = Application(
            layout=Layout(container, focused_element=input_field),
            key_bindings=kb,
            style=style,
            mouse_support=True,
            full_screen=True)

        application.run()

        Log.info("Starting cli")

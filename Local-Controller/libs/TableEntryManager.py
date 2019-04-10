"""
This is a simplified version of the TableEntryManager used in the
global controller.

For further documentation see official docs of global controller implementation.
"""

from collections import defaultdict
from libs.core.Log import Log
from prettytable import PrettyTable
from libs.Exceptions import EntryNotFound, TableManagerNotFound, TableNotFound


class TableEntry:
    """
    This class represents a table entry, which can be written to a switch
    """

    def __init__(self, match_fields={}, action_name=None, action_params={}, priority=None):
        """
        A table entry consists of the match fields, action name and action parameters.
        In order to write to the correct switch, a table entry is associated to a switch
        :param switch: switch where this entry should be placed / is present
        :param match_fields:
        :param action_name:
        :param action_params:
        :param priority:
        """
        self.match_fields = match_fields
        self.action_name = action_name
        self.action_params = action_params
        self.priority = priority

    def __eq__(self, other):
        return self.match_fields == other.match_fields and \
            self.action_name == other.action_name and \
            self.action_params == other.action_params and \
            self.priority == other.priority

    def __str__(self):
        return str(self.match_fields) + "-" + str(self.action_name) \
            + "-" + str(self.action_params) + "-" + str(self.priority)


class TableEntryManager:
    Manager = {}

    def __init__(self, controller=None, name=None):
        self.tables = defaultdict(list)
        self.__controller = controller
        self.name = name

        # add this table manager to manager list to get access to
        # different controller manager
        TableEntryManager.Manager[name] = self

    def init_table(self, table_name=None):
        """
        Initialize storage for table
        :param table_name: table name
        :return:
        """
        self.tables[table_name] = []

    def add_table_entry(self, table_name=None, table_entry=None):
        """
        Adds a table entry for the given table_name
        :param table_name: name of the table
        :param table_entry: TableEntry object
        :return:
        """
        self.get_table_entries(table_name=table_name).append(table_entry)

        # add table entry
        self.__controller.add_table_entry(table_name=table_name,
                                          entry=table_entry)

    def __remove_table_entry(self, table_name=None, table_entry=None):
        """
        Removes a table entry for a given controller
        :param table_name: name of the table
        :param table_entry: TableEntry object
        :return:
        """

        # remove table entry based on match_fields
        for entry in self.get_table_entries(table_name=table_name):
            if entry.match_fields == table_entry.match_fields:
                self.tables.get(table_name).remove(entry)

                # delete old table entry
                self.__controller.delete_table_entry(table_name=table_name,
                                                     entry=table_entry)

                return

        raise EntryNotFound(table_entry)

    def get_table_entries(self, table_name=None):
        """
        Get the table with the given name
        :param table_name: name of the table
        :return:
        """
        table = self.tables.get(table_name, None)

        if table is None:
            raise TableNotFound(table_name)

        return table

    def entry_exists(self, table_name=None, table_entry=None):
        """
        Check if entry exists in table
        :param table_name: name of the table
        :param table_entry: TableEntry objects
        :return:
        """
        return table_entry in self.get_table_entries(table_name=table_name)

    def match_fields_exists(self, table_name=None, table_entry=None):
        """
        Check if a table entry with the given match fields exist
        :param table_name: table name where entry should be
        :param table_entry: table entry, which has certain match_fields
        :return:
        """
        for entry in self.get_table_entries(table_name=table_name):
            if entry.match_fields == table_entry.match_fields:
                return True

        return False

    def update_entry(self, table_name=None, table_entry=None):
        """
        Update a table entry
        :param table_name: table name
        :param table_entry: new table entry
        :return:
        """

        # remove the old entry from table storage
        self.__remove_table_entry(table_name=table_name, table_entry=table_entry)

        # add new entry
        self.add_table_entry(table_name=table_name, table_entry=table_entry)

    def remove_invalid_entries(self, table_name=None, valid_entries=None):
        """
        This method removes invalid entries from a switch based on a list of valid entries
        :param switch: switch where the entries should be removed
        :param table_name: table of the name where the rules should be removed
        :param valid_entries: a list of match fields of valid entries
        :return:
        """
        for entry in self.get_table_entries(table_name=table_name):
            # the current entry is not a valid entry anymore
            # so delete it
            if entry.match_fields not in valid_entries:
                self.__remove_table_entry(table_name=table_name, table_entry=entry)

    @staticmethod
    def handle_table_entry(manager=None, table_name=None, table_entry=None):
        """
        Handles a computed table entry
        This includes:
            - check if the current entry exists in this form -> do nothing
            - check if the current match fields exist but the params differ -> update the entry
            - check if the entry does not exist in any form -> create the entry
        :param manager: table manager object
        :param table_name: table name which manager should check
        :param table_entry: table entry which manager should check
        :return: True if a entry has been created / changed, False otherwise
        """
        if not manager.entry_exists(table_name=table_name, table_entry=table_entry):
            # the table entry match fields exists, but they differ in the actions parameters
            # so update the entry to the new parameters
            if manager.match_fields_exists(table_name=table_name, table_entry=table_entry):
                manager.update_entry(table_name=table_name, table_entry=table_entry)
            else:
                # the entry does not exist yet, so create it
                manager.add_table_entry(table_name=table_name, table_entry=table_entry)

            return True

        return False

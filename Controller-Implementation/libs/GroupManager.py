from libs.core.Log import Log
from scapy.contrib.igmp import IGMP
from libs.core.Event import Event
from libs.TopologyManager import TopologyManager
from prettytable import PrettyTable


class GroupManager:
    """
    This class handles all multicast group specific methods,
    i.e. add host to multicast group, subscribe / unsubscribe, etc.
    """

    # {bfr-name: {mc_addr: [host1, host2]}, bfr-name2: {mc_addr: []}, ...}
    group_to_member = {}

    @staticmethod
    def get_bfr_by_mc_addr(mc_addr):
        """
        Get all subscribed bfrs for given mc_addr
        :param mc_addr: multicast address
        :return: bfr list
        """
        bfr_list = []
        for bfrs in GroupManager.group_to_member:
            for group in GroupManager.group_to_member.get(bfrs, {}):
                if group == mc_addr and GroupManager.group_to_member.get(bfrs).get(group, []):
                    bfr_list.append(bfrs)

        return list(set(bfr_list))

    @staticmethod
    def get_mc_addresses_for_switch(switch=None):
        return [a for a in GroupManager.group_to_member.get(switch, {})
                if GroupManager.group_to_member.get(switch).get(a, [])]

    @staticmethod
    def get_mc_addresses():
        """
        Get all active multicast addresses
        :return: list of multicast addresses
        """
        mc_addr = []

        for bfrs in GroupManager.group_to_member:
            for group in GroupManager.group_to_member.get(bfrs, {}):
                if GroupManager.group_to_member.get(bfrs).get(group, []):
                    mc_addr.append(group)

        return list(set(mc_addr))

    @staticmethod
    def get_all_mc_addresses():
        """
        Get all multicast addreses
        this may include old (now) unused addresses
        :return:
        """
        mc_addr = []

        for bfrs in GroupManager.group_to_member:
            for group in GroupManager.group_to_member.get(bfrs, {}):
                mc_addr.append(group)

        return list(set(mc_addr))

    @staticmethod
    def add_to_group(switch, member, group):
        """
        Adds the given bfr (switch) with the member to a specifi mc_grp
        :param switch: bfr
        :param member: host which (actually) subscribes
        :param group: multicast group
        :return:
        """
        if switch not in GroupManager.group_to_member:
            GroupManager.group_to_member[switch] = {}

        if group not in GroupManager.group_to_member[switch]:
            GroupManager.group_to_member[switch][group] = []

        if member not in GroupManager.group_to_member[switch].get(group, []):
            GroupManager.group_to_member[switch].get(group).append(member)

    @staticmethod
    def remove_from_group(switch, member, group):
        """
        Removes a host from a given multicast group
        :param switch: switch which got the unsub message
        :param member: host which unsubscribes
        :param group: multicast group
        :return:
        """
        try:
            GroupManager.group_to_member.get(switch, {}).get(group, []).remove(member)
        except ValueError as e:
            Log.error("try to remove", member, "from", switch, "and group", group, e, GroupManager.group_to_member)
            pass

    @staticmethod
    def get_domains_for_mc_addr(mc_addr):
        """
        Get domains which have subscriptions on a given multicast address
        :param mc_addr: multicast address
        :return: list of domains
        """
        bfrs = GroupManager.get_bfr_by_mc_addr(mc_addr)

        domains = [0]

        for bfr in bfrs:
            domains.extend(TopologyManager.get_domain_for_device(bfr))

        domains = list(set(domains))

        return domains

    #############################################################
    #                   Event Listener                          #
    #############################################################

    @staticmethod
    def handle_packet_in(pkt):
        switch = pkt.switch.encode('utf-8')
        mc_addr = pkt.mc_address.encode('utf-8')
        src_ip = pkt.src_ip.encode('utf-8')

        

        if pkt.type == 0x16:
            GroupManager.add_to_group(switch, src_ip, mc_addr)
        elif pkt.type == 0x17:
            GroupManager.remove_from_group(switch, src_ip, mc_addr)

        Event.trigger("group_update")

        Log.event("Got igmp packet with type", hex(pkt.type), "and src", src_ip, "for group", mc_addr, "from", switch)

    @staticmethod
    def describe():
        data = PrettyTable()

        data.field_names = ["MC Address", "Subscribed BFRs", "Domains"]

        for mc_addr in GroupManager.get_mc_addresses():
            data.add_row([mc_addr, GroupManager.get_bfr_by_mc_addr(mc_addr), GroupManager.get_domains_for_mc_addr(mc_addr)])

        Log.echo(data)

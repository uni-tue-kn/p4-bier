#!/usr/bin/env python2

from core.CLI import CLI
from commands.Subscribe import Subscribe
from commands.Unsubscribe import Unsubscribe
from commands.Send import Send
from commands.Ping import Ping
from commands.Receive import Receive
from commands.DeviceInfo import DeviceInfo
import threading
from core.Event import Event


CLI.add_command("subscribe", Subscribe.sub, "Subscribe to given addr")
CLI.add_command("unsubscribe", Unsubscribe.sub, "Unsubscribe from given addr")
CLI.add_command("send", Send.main, "Send message to given addr")
CLI.add_command("info", DeviceInfo.info, "Get information about the host")
CLI.add_command("ping", Ping.main, "Send repeated message to given addr")

Event.activate()

threading.Thread(target=Receive.main).start()

CLI.start_cli()

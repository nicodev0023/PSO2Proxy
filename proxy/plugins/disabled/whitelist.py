import commands
from config import YAMLConfig
import json
import os
import packetFactory
from packetFactory import SystemMessagePacket
import plugins
whitelist = []

ircSettings = YAMLConfig("cfg/pso2proxy.whitelist.config.yml",
                         {'enabled': True}, True)

whitelistmode = ircSettings.get_key('enabled')


@plugins.on_start_hook
def load_whitelist():
    global whitelist
    if not os.path.exists("cfg/pso2proxy.whitelist.json"):
        f = open("cfg/pso2proxy.whitelist.json", "w")
        f.write(json.dumps(whitelist))
        f.close()
        print('[Whitelist] Blank whitelist created.')
    else:
        f = open("cfg/pso2proxy.whitelist.json", "r")
        whitelist = json.loads(f.read())
        f.close()
        print("[Whitelist] Loaded %i whitelisted SEGA IDs." % len(whitelist))


def save_whitelist():
    f = open("cfg/pso2proxy.whitelist.json", "w")
    f.write(json.dumps(whitelist))
    f.close()
    print('[Whitelist] Saved whitelist.')


@plugins.CommandHook("whitelistmode", "[Admin Only] Toggle whitelist mode", True)
class Whitelistmode(commands.Command):
    def call_from_client(self, client):
        global whitelistmode
        whitelistmode = not whitelistmode
        if whitelistmode:
            client.send_crypto_packet(packetFactory.SystemMessagePacket("[Whitelist] Whitelist turn on.", 0x3).build())
            return
        else:
            client.send_crypto_packet(packetFactory.SystemMessagePacket("[Whitelist] Whitelist turn off.", 0x3).build())
            return

    def call_from_console(self):
        global whitelistmode
        whitelistmode = not whitelistmode
        if whitelistmode:
            return "[Whitelist] Whitelist turn on."
        else:
            return "[Whitelist] Whitelist turn off."


@plugins.CommandHook("whitelist", "[Admin Only] Adds or removes someone to the connection whitelist.", True)
class Whitelist(commands.Command):
    def call_from_console(self):
        global whitelist
        params = self.args.split(" ")
        if len(params) < 3:
            return "[Whitelist] Invalid usage. (Usage: whitelist <add/del> <SegaID>)"
        if params[1] == "add" or params[1] == "ADD":
            if params[2] not in whitelist:
                whitelist.append(params[2])
                save_whitelist()
                return "[Whitelist] Added %s to the whitelist." % params[2]
            else:
                return "[Whitelist] %s is already in the whitelist." % params[2]
        elif params[1] == "del" or params[1] == "DEL":
            if params[2] in whitelist:
                whitelist.remove(params[2])
                save_whitelist()
                return "[Whitelist] Removed %s from whitelist." % params[2]
            else:
                return "[Whitelist] %s is not in the whitelist, can not delete!" % params[2]
        else:
            return "[Whitelist] Invalid usage. (Usage: whitelist <add/del> <SegaID>)"

    def call_from_client(self, client):
        """
        :param client: ShipProxy.ShipProxy
        """
        global whitelist
        params = self.args.split(" ")
        if len(params) < 3:
            client.send_crypto_packet(packetFactory.SystemMessagePacket("[Command] {red}Invalid usage. (Usage: whitelist <add/del> <SegaID>)", 0x3).build())
            return
        if params[1] == "add" or params[1] == "ADD":
            if params[2] not in whitelist:
                whitelist.append(params[2])
                save_whitelist()
                client.send_crypto_packet(packetFactory.SystemMessagePacket("[Command] {gre}Added %s to the whitelist." % params[2], 0x3).build())
                return
            else:
                client.send_crypto_packet(packetFactory.SystemMessagePacket("[Command] {red}%s is already in the whitelist." % params[2], 0x3).build())
                return
        elif params[1] == "del" or params[1] == "DEL":
            if params[2] in whitelist:
                whitelist.remove(params[2])
                save_whitelist()
                client.send_crypto_packet(packetFactory.SystemMessagePacket("[Command] {gre}Removed %s from whitelist." % params[2], 0x3).build())
                return
            else:
                client.send_crypto_packet(packetFactory.SystemMessagePacket("[Command] {red}%s is not in the whitelist, can not delete!" % params[2], 0x3).build())
                return
        else:
            client.send_crypto_packet(packetFactory.SystemMessagePacket("[Command] {red}Invalid usage. (Usage: whitelist <add/del> <SegaID>)", 0x3).build())
            return


@plugins.PacketHook(0x11, 0x0)
def whitelist_check(context, data):
    """

    :type context: ShipProxy.ShipProxy
    """
    global whitelist
    global whitelistmode
    if not whitelistmode:
        return data
    start = len(data) - 132  # Skip password
    username = data[start:start + 0x40].decode('utf-8')
    username = username.rstrip('\0')
    if username not in whitelist:
        print("[Whitelist] %s is not in the whitelist, disconnecting client." % username)
        context.send_crypto_packet(SystemMessagePacket("Oops sorry, you are not registered in the whitelist, doom might have missed your name from the last edit. Please contact doom or kasumi", 0x1).build())
        context.transport.loseConnection()
    return data

#! python3
# Copyright (C) 2015 - 2016 Hong Jen Yee (PCMan) <pcman.tw@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import json
import sys
import traceback

if __name__ == "__main__":
    sys.path.append('python3')
    sys.path.append('site-packages')


from serviceManager import textServiceMgr

import envive_helper_ui as ui
# import os
# import platform
# import subprocess
# from datetime import datetime
from envive_helper_python import HiddenWindow, SystemTrayIcon
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView
from PyQt5.QtWebChannel import QWebChannel


class Client(object):
    def __init__(self, server):
        self.server = server
        self.service = None

    def init(self, msg):
        self.guid = msg["id"]
        self.isWindows8Above = msg["isWindows8Above"]
        self.isMetroApp = msg["isMetroApp"]
        self.isUiLess = msg["isUiLess"]
        self.isUiLess = msg["isConsole"]
        # create the text service
        self.service = textServiceMgr.createService(self, self.guid)
        return (self.service is not None)

    def handleRequest(self, msg): # msg is a json object
        method = msg.get("method")
        seqNum = msg.get("seqNum", 0)
        # print("handle message: ", str(id(self)), method, seqNum)
        service = self.service
        if service:
            # let the text service handle the message
            reply = service.handleRequest(msg)
        else:  # the text service is not yet initialized
            reply = {"seqNum": seqNum}
            success = False
            if method == "init": # initialize the text service
                success = self.init(msg)
            reply["success"] = success
        # print(reply)
        print(f'reply aadsdasds: {reply}')
        return reply

class Server(QObject):
# class Server(object):
    value_changed = pyqtSignal(str)
    user_input_terminated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.clients = {}

    def run(self):
        while True:
            line = ""
            client_id = ""
            try:
                line = input().strip()
                if not line:
                    continue
                # parse PIME requests (one request per line):
                # request format: "<client_id>|<JSON string>\n"
                # response format: "PIME_MSG|<client_id>|<JSON string>\n"
                client_id, msg_text = line.split('|', maxsplit=1)
                msg = json.loads(msg_text)
                client = self.clients.get(client_id)
                if not client:
                    # create a Client instance for the client
                    client = Client(self)
                    self.clients[client_id] = client
                    print("new client:", client_id)
                if msg.get("method") == "close":  # special handling for closing a client
                    self.remove_client(client_id)
                else:
                    ret = client.handleRequest(msg)
                    # Send the response to the client via stdout
                    # one response per line in the format "PIME_MSG|<client_id>|<json reply>"
                    compositionString = ret.get('compositionString')
                    commitString = ret.get('commitString')
                    isInTerminated = ret.get('isInTerminated')

                    if compositionString:
                        print(f'User\'s compositionString: {compositionString}')
                        self.value_changed.emit(compositionString)
                    elif commitString:
                        print(f'User\'s commitString: {commitString}')
                        self.value_changed.emit(commitString)
                    elif isInTerminated:
                        print(f'User\'s isInTerminated: {isInTerminated}')
                        self.user_input_terminated.emit()

                    # reply_line = '|'.join(["PIME_MSG", client_id, json.dumps(ret, ensure_ascii=False)])
                    reply_line = '|'.join(["PIME_MSG", client_id, json.dumps(ret)])
                    print(reply_line)
            except EOFError:
                # stop the server
                break
            except Exception as e:
                print("ERROR:", e, line)
                # print the exception traceback for ease of debugging
                traceback.print_exc()
                # generate an empty output containing {success: False} to prevent the client from being blocked
                reply_line = '|'.join(["PIME_MSG", client_id, '{"success":false}'])
                print(reply_line)
                # Just terminate the python server process if any unknown error happens.
                # The python server will be restarted later by PIMELauncher.
                sys.exit(1)

    def remove_client(self, client_id):
        print("client disconnected:", client_id)
        try:
            del self.clients[client_id]
        except KeyError:
            pass


def main():
    try:
        app = QtWidgets.QApplication(sys.argv)

        window = HiddenWindow(Server())
        window.show()

        tray_widget = QtWidgets.QWidget()
        trayIcon = SystemTrayIcon(QIcon(r'icon.png'), tray_widget, window)
        trayIcon.show()

        sys.exit(app.exec_())
        # server = Server()
        # server.run()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()

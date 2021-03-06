# -*- coding: utf-8 -*-
#
# test_yarss_config.py
#
# Copyright (C) 2012 Bro
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

import smtplib
import base64

from twisted.trial import unittest

from deluge.log import LOG as log

from yarss2.torrent_handling import TorrentHandler
from yarss2.util.yarss_email import send_email, send_torrent_email
import yarss2.yarss_config
import common
import test_yarss_email

smtp = None
inbox = []

class Message(object):
    def __init__(self, from_address, to_address, message):
        self.from_address = from_address
        self.to_address = to_address
        self.message = message

class DummySMTP(object):
    def __init__(self, server_address, port):
        self.server_address = server_address
        self.port = port
        global smtp
        smtp = self
        self.ehlo_called = False
        self.starttls_called = False

    def login(self, username, password):
        self.username = username
        self.password = password

    def sendmail(self, from_address, to_address, fullmessage):
        global inbox
        inbox.append(Message(from_address,to_address,fullmessage))
        return []

    def quit(self):
        self.has_quit = True

    def ehlo(self):
        self.ehlo_called = True

    def starttls(self):
        self.starttls_called = True

    def get_emails(self):
        global inbox
        return inbox

smtplib.SMTP = DummySMTP

class YaRSS2EmailTestCase(unittest.TestCase):

    def setUp(self):
        self.config = common.get_test_config()

    def test_send_email(self):
        email_config = yarss2.yarss_config.get_fresh_email_config()
        email_config["from_address"] = "from@test.com"

        email = {}
        email["to_address"] = "test@address.com"
        email["subject"] = "Test Subject"
        email["message"] = "Test Message"

        global smtp
        global inbox
        self.assertTrue(send_email(email, email_config))
        self.assertEquals(inbox[0].from_address, email_config["from_address"])
        self.assertEquals(inbox[0].to_address, email["to_address"])
        self.assertEquals(smtp.server_address, email_config["smtp_server"])
        self.assertEquals(smtp.port, smtplib.SMTP_PORT)

    def test_send_email_with_auth(self):
        email_config = yarss2.yarss_config.get_fresh_email_config()
        email_config["from_address"] = "from@test.com"
        email_config["smtp_server"] = "server_address"
        email_config["smtp_port"] = "43353"
        email_config["smtp_authentication"] = True
        email_config["smtp_username"] = "testuser"
        email_config["smtp_password"] = "testpw"

        email = {}
        email["to_address"] = "test@address.com"
        email["subject"] = "Test Subject"
        email["message"] = "Test Message"

        global smtp
        global inbox
        self.assertTrue(send_email(email, email_config))
        self.assertEquals(inbox[0].from_address, email_config["from_address"])
        self.assertEquals(inbox[0].to_address, email["to_address"])
        self.assertEquals(smtp.server_address, email_config["smtp_server"])
        self.assertEquals(smtp.port, int(email_config["smtp_port"]))
        self.assertEquals(smtp.username, email_config["smtp_username"])
        self.assertEquals(smtp.password, email_config["smtp_password"])

        self.assertTrue(smtp.ehlo_called)
        self.assertTrue(smtp.starttls_called)


class YaRSS2TorrentEmailTestCase(unittest.TestCase):

    def setUp(self):
        self.log = log
        self.handler = TorrentHandler(self.log)
        smtplib.SMTP = test_yarss_email.DummySMTP
        self.email_config = yarss2.yarss_config.get_fresh_email_config()
        self.email_config["from_address"] = "from@test.com"
        self.email = {}
        self.email["to_address"] = "test@address.com"
        self.email["subject"] = "Test Subject"
        self.email["message"] = "Hi\n\nThis is a test message.\n\n\nRegards"
        self.email["name"] = "Test Message Name"

        self.expected_messsage = []
        self.expected_messsage.append('Content-Type: text/plain; charset="utf-8"')
        self.expected_messsage.append('MIME-Version: 1.0')
        self.expected_messsage.append('Content-Transfer-Encoding: base64')
        self.expected_messsage.append("Subject: %s")
        self.expected_messsage.append("From: %s")
        self.expected_messsage.append("To: %s")

        self.expected_messsage_multipart = []
        self.expected_messsage_multipart.append('Content-Type: multipart/alternative;')
        self.expected_messsage_multipart.append('MIME-Version: 1.0')
        self.expected_messsage_multipart.append("Subject: %s")
        self.expected_messsage_multipart.append("From: %s")
        self.expected_messsage_multipart.append("To: %s")
        self.expected_messsage_multipart.append('Content-Type: text/plain; charset="utf-8"')
        self.expected_messsage_multipart.append('MIME-Version: 1.0')
        self.expected_messsage_multipart.append('Content-Transfer-Encoding: base64')
        self.expected_messsage_multipart.append('Content-Type: text/html; charset="utf-8"')
        self.expected_messsage_multipart.append('MIME-Version: 1.0')
        self.expected_messsage_multipart.append('Content-Transfer-Encoding: base64')

    def verify_email_multipart(self, email_message, email, email_config, email_data):
        """
        email_message - a test_yarss_email.Message
        email - a dictionary with the email info
        email_config - a dictionary with the email configuration options
        """
        self.assertEquals(email_message.to_address, email["to_address"])
        lines = email_message.message.splitlines()

        # Content type - multipart
        self.assertEquals(lines[0], self.expected_messsage_multipart[0])
        # MIME version
        self.assertEquals(lines[2], self.expected_messsage_multipart[1])
        # Subject
        self.assertEquals(lines[3], self.expected_messsage_multipart[2] % email["subject"])
        # From address
        self.assertEquals(lines[4], self.expected_messsage_multipart[3] % email_config["from_address"])
        # To address
        self.assertEquals(lines[5], self.expected_messsage_multipart[4] % email["to_address"])
        # Content type text/plain
        self.assertEquals(lines[8], self.expected_messsage_multipart[5])
        # MIME version
        self.assertEquals(lines[9], self.expected_messsage_multipart[6])
        # Content transfer encoding
        self.assertEquals(lines[10], self.expected_messsage_multipart[7])

        # Message content
        index = 12
        message_base64 = ""
        # Get the whole message
        while lines[index].strip() != "":
            message_base64 += lines[index]
            index += 1

        msg_plain_base64 = base64.b64encode(email_data["message"])
        self.assertEquals(message_base64, msg_plain_base64)

        # Content type text/html
        self.assertEquals(lines[index + 2], self.expected_messsage_multipart[8])
        # MIME version
        self.assertEquals(lines[index + 3], self.expected_messsage_multipart[9])
        # Content transfer encoding
        self.assertEquals(lines[index + 4], self.expected_messsage_multipart[10])

        message_base64 = ""
        index  += 6
        # Get the whole message
        while lines[index].strip() != "":
            message_base64 += lines[index]
            index += 1

        msg_plain_base64 = base64.b64encode(email_data["message_html"])
        self.assertEquals(message_base64, msg_plain_base64)

    def verify_email(self, email_message, email, email_config):
        """
        email_message - a test_yarss_email.Message
        email - a dictionary with the email info
        email_config - a dictionary with the email configuration options
        """
        self.assertEquals(email_message.to_address, email["to_address"])
        lines = email_message.message.splitlines()
        # Content type
        self.assertEquals(lines[0], self.expected_messsage[0])
        # MIME version
        self.assertEquals(lines[1], self.expected_messsage[1])
        # Content transfer encoding
        self.assertEquals(lines[2], self.expected_messsage[2])
        # Subject
        self.assertEquals(lines[3], self.expected_messsage[3] % email["subject"])
        # From address
        self.assertEquals(lines[4], self.expected_messsage[4] % email_config["from_address"])
        # To address
        self.assertEquals(lines[5], self.expected_messsage[5] % email["to_address"])
        # Line 7 is the entire message content encoded in base64.
        self.assertEquals(lines[7], base64.b64encode(email["message"]))

    def test_send_torrent_email_with_deferred(self):
        def callback(args):
            self.verify_email(test_yarss_email.smtp.get_emails().pop(), self.email, self.email_config)
        # Send email in
        d = send_torrent_email(self.email_config, self.email, defered=True)
        d.addCallback(callback)
        return d

    def test_send_torrent_email_with_deferred_with_callback(self):
        """This test uses the callback keyword argument to add the callback
        function to the deferred"""
        def callback(args):
            self.verify_email(test_yarss_email.smtp.get_emails().pop(), self.email, self.email_config)
        # Send email in
        d = send_torrent_email(self.email_config, self.email, defered=True,
                                            callback_func=callback)
        return d

    def test_send_torrent_email_multipart_with_deferred(self):
        subscription = {"name": "Subscription name"}
        torrent_names = ["Torrent 1", "Torrent 2"]
        self.email["message"] = "Hi\n\nThis is a test message. \n\n$torrentlist\n\nRegards"
        email_data = {}

        def callback(args):
            message = test_yarss_email.smtp.get_emails().pop()
            self.verify_email_multipart(message, self.email, self.email_config, email_data)
            # Verify that the torrent names have been inserted into the message
            self.assertTrue(email_data["message"].find(torrent_names[0]) != -1)
            self.assertTrue(email_data["message"].find(torrent_names[1]) != -1)
            self.assertTrue(email_data["message_html"].find(torrent_names[0]) != -1)
            self.assertTrue(email_data["message_html"].find(torrent_names[1]) != -1)

        # Send email without deferred
        has_sent = send_torrent_email(self.email_config, self.email,
                                      torrent_name_list=torrent_names,
                                      subscription_data=subscription,
                                      defered=False, callback_func=callback,
                                      email_data=email_data)
        self.assertTrue(has_sent)
        # Send email in
        d = send_torrent_email(self.email_config, self.email, torrent_name_list=torrent_names,
                               defered=True, callback_func=callback, email_data=email_data)
        return d



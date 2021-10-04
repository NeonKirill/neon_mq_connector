# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
#
# Copyright 2008-2021 Neongecko.com Inc. | All Rights Reserved
#
# Notice of License - Duplicating this Notice of License near the start of any file containing
# a derivative of this software is a condition of license for this software.
# Friendly Licensing:
# No charge, open source royalty free use of the Neon AI software source and object is offered for
# educational users, noncommercial enthusiasts, Public Benefit Corporations (and LLCs) and
# Social Purpose Corporations (and LLCs). Developers can contact developers@neon.ai
# For commercial licensing, distribution of derivative works or redistribution please contact licenses@neon.ai
# Distributed on an "AS IS” basis without warranties or conditions of any kind, either express or implied.
# Trademarks of Neongecko: Neon AI(TM), Neon Assist (TM), Neon Communicator(TM), Klat(TM)
# Authors: Guy Daniels, Daniel McKnight, Elon Gasper, Richard Leeds, Kirill Hrymailo
#
# Specialized conversational reconveyance options from Conversation Processing Intelligence Corp.
# US Patents 2008-2021: US7424516, US20140161250, US20140177813, US8638908, US8068604, US8553852, US10530923, US10530924
# China Patent: CN102017585  -  Europe Patent: EU2156652  -  Patents Pending

import os
import sys
import time
import unittest
import pytest
import pika

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from neon_mq_connector.config import Configuration
from neon_mq_connector.connector import MQConnector, ConsumerThread
from neon_utils import LOG


class MQConnectorChild(MQConnector):

    def callback_func_1(self, channel, method, properties, body):
        self.func_1_ok = True
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def callback_func_2(self, channel, method, properties, body):
        self.func_2_ok = True
        # channel.basic_ack(delivery_tag=method.delivery_tag)

    def callback_func_after_message(self, channel, method, properties, body):
        self.callback_ok = True
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def callback_func_error(self, channel, method, properties, body):
        raise Exception("Exception to Handle")

    def handle_error(self, thread: ConsumerThread, exception: Exception):
        self.exception = exception

    def __init__(self, config: dict, service_name: str):
        super().__init__(config=config, service_name=service_name)
        self.vhost = '/test'
        self.func_1_ok = False
        self.func_2_ok = False
        self.callback_ok = False
        self.exception = None
        self.register_consumer(name="test1", vhost=self.vhost, queue='test', callback=self.callback_func_1,
                               auto_ack=False)
        self.register_consumer(name="test2", vhost=self.vhost, queue='test1', callback=self.callback_func_2,
                               auto_ack=False)
        self.register_consumer(name="error", vhost=self.vhost, queue="error", callback=self.callback_func_error,
                               on_error=self.handle_error, auto_ack=False)


class MQConnectorChildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        file_path = os.environ.get('CONNECTOR_CONFIG', "~/.local/share/neon/credentials.json")
        cls.connector_instance = MQConnectorChild(config=Configuration(file_path=file_path).config_data,
                                                  service_name='test')
        cls.connector_instance.run()

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.connector_instance.stop()
        except ChildProcessError as e:
            LOG.error(e)

    def test_not_null_service_id(self):
        self.assertIsNotNone(self.connector_instance.service_id)

    @pytest.mark.timeout(30)
    def test_connection_alive(self):
        self.assertIsInstance(self.connector_instance.consumers['test1'], ConsumerThread)

    @pytest.mark.timeout(30)
    def test_produce(self):
        with self.connector_instance.create_mq_connection(vhost=self.connector_instance.vhost) as mq_conn:
            self.connector_instance.emit_mq_message(mq_conn,
                                                    queue='test',
                                                    request_data={'data': 'Hello!'},
                                                    exchange='',
                                                    expiration=4000)
            self.connector_instance.emit_mq_message(mq_conn,
                                                    queue='test1',
                                                    request_data={'data': 'Hello 2!'},
                                                    exchange='',
                                                    expiration=4000)

        time.sleep(3)
        self.assertTrue(self.connector_instance.func_1_ok)
        self.assertTrue(self.connector_instance.func_2_ok)

    @pytest.mark.timeout(30)
    def test_error(self):
        with self.connector_instance.create_mq_connection(vhost=self.connector_instance.vhost) as mq_conn:
            self.connector_instance.emit_mq_message(mq_conn,
                                                    queue='error',
                                                    request_data={'data': 'test'},
                                                    exchange='',
                                                    expiration=4000)

        time.sleep(3)
        self.assertIsInstance(self.connector_instance.exception, Exception)
        self.assertEqual(str(self.connector_instance.exception), "Exception to Handle")

    def test_consumer_after_message(self):
        with self.connector_instance.create_mq_connection(vhost=self.connector_instance.vhost) as mq_conn:
            self.connector_instance.emit_mq_message(mq_conn,
                                                    queue='test3',
                                                    request_data={'data':'test'},
                                                    exchange='',
                                                    expiration=3000)

        self.connector_instance.register_consumer("test_consumer_after_message",
                                                  self.connector_instance.vhost, "test3",
                                                  self.connector_instance.callback_func_after_message, auto_ack=False)
        self.connector_instance.run_consumers(("test_consumer_after_message",))
        time.sleep(3)
        self.assertTrue(self.connector_instance.callback_ok)

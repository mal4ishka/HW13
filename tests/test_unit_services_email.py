import unittest
from unittest.mock import MagicMock
from address_book.services.email import send_email
from address_book.conf.config import settings

from fastapi import BackgroundTasks, Request
import logging
logging.basicConfig(level=logging.ERROR)


class TestServicesEmail(unittest.IsolatedAsyncioTestCase):

    async def test_send_email(self):
        background_tasks = BackgroundTasks()
        request = MagicMock(spec=Request)
        self.assertIsNone(background_tasks.add_task(send_email, settings.MAIL_USERNAME, settings.MAIL_USERNAME,
                                                    request.base_url))


if __name__ == '__main__':
    unittest.main()
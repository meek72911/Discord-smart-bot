import os
from unittest import mock
import config


def test_is_authorized_user():
    with mock.patch.object(config, "OWNER_ID", 111):
        with mock.patch.object(config, "TRUSTED_USER_IDS", {222, 333}):
            assert config.is_authorized_user(111) is True
            assert config.is_authorized_user(222) is True
            assert config.is_authorized_user(333) is True
            assert config.is_authorized_user(999) is False
            assert config.is_authorized_user(None) is False

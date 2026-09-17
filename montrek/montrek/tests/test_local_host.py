"""Tests for the DEBUG=1 guard's host classification in `montrek.settings`.

`_is_local_host` decides whether `DEBUG=1` is a development convenience or a
deployment mistake, so a false positive serves error pages full of settings,
SQL and local variables to the internet.
"""

from django.test import SimpleTestCase

from montrek.settings import _is_local_host


class IsLocalHostTest(SimpleTestCase):
    def assert_local(self, *hosts):
        for host in hosts:
            with self.subTest(host=host):
                self.assertIs(_is_local_host(host), True)

    def assert_not_local(self, *hosts):
        for host in hosts:
            with self.subTest(host=host):
                self.assertIs(_is_local_host(host), False)

    def test_loopback_and_empty(self):
        self.assert_local("", None, "  ", "localhost", "LocalHost", "127.0.0.1", "::1")

    def test_private_ipv4_ranges(self):
        self.assert_local(
            "10.0.0.3", "192.168.1.5", "172.16.0.1", "172.31.255.254", "169.254.1.1"
        )

    def test_private_ipv6(self):
        self.assert_local("fd00::1", "[::1]", "fe80::1")

    def test_reserved_local_suffixes_and_single_label_names(self):
        self.assert_local(
            "montrek-local.lan", "box.internal", "host.local", "dev.test", "ubuntu-vm"
        )

    def test_public_addresses_are_not_local(self):
        self.assert_not_local("8.8.8.8", "172.32.0.1", "2606:4700::1111")

    def test_public_names_are_not_local(self):
        self.assert_not_local("montrek.customer.de", "example.com")

    def test_a_public_name_that_merely_starts_like_a_private_range(self):
        """The bug this guard had: a routable name read as an RFC1918 address.

        `"10.attacker.example".startswith("10.")` is true, which was enough to
        classify a public host as local and wave DEBUG=1 through.
        """
        self.assert_not_local(
            "10.attacker.example",
            "192.168.evil.example",
            "172.20.phish.example",
            "169.254.evil.example",
            "127.0.0.1.attacker.example",
        )

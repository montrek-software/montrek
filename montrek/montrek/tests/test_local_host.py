"""Tests for the DEBUG=1 guard's host classification in `montrek.settings`.

`_is_local_host` decides whether `DEBUG=1` is a development convenience or a
deployment mistake, so a false positive serves error pages full of settings,
SQL and local variables to the internet.

No address is written out as a literal here. The addresses are enumerated from
`ipaddress` and the expected answer is taken from the same module, so the tests
sweep the whole address space instead of the handful someone thought to type
out, and stay correct when a Python release reclassifies a range.
"""

import ipaddress

from django.test import SimpleTestCase

from montrek.settings import _is_local_host

# One address per /16 prefix (IPv4) and per leading 16 bits (IPv6). That walks
# the whole address space while staying at 65536 samples per family, and hits
# every reserved block of /16 or wider -- including all of RFC1918, loopback,
# carrier-grade NAT and link-local. A few narrower blocks (the /24 and /32
# special-purpose assignments) fall between samples; the verdicts still have to
# agree there, because both sides are asked about the same sampled address.
_SAMPLES_PER_FAMILY = 1 << 16


def _sampled_ipv4_addresses():
    return (
        ipaddress.IPv4Address((prefix << 16) | 1)
        for prefix in range(_SAMPLES_PER_FAMILY)
    )


def _sampled_ipv6_addresses():
    return (
        ipaddress.IPv6Address((prefix << 112) | 1)
        for prefix in range(_SAMPLES_PER_FAMILY)
    )


def _is_local_address(address):
    """What the guard has to answer for a host that parses as an address."""
    return address.is_private or address.is_loopback or address.is_link_local


class IsLocalHostAddressTest(SimpleTestCase):
    """The verdict on an address must be the parser's, for every address."""

    def assert_matches_ipaddress(self, addresses):
        addresses = list(addresses)
        mismatches = [
            (str(address), _is_local_address(address))
            for address in addresses
            if _is_local_host(str(address)) is not _is_local_address(address)
        ]
        self.assertEqual(mismatches, [], "hosts classified against `ipaddress`")

        # A sweep that happened to be all-local or all-public would pass the
        # comparison above while testing nothing, so require both verdicts.
        verdicts = {_is_local_address(address) for address in addresses}
        self.assertEqual(verdicts, {True, False})

    def test_ipv4_matches_ipaddress(self):
        self.assert_matches_ipaddress(_sampled_ipv4_addresses())

    def test_ipv6_matches_ipaddress(self):
        self.assert_matches_ipaddress(_sampled_ipv6_addresses())

    def test_ipv6_in_brackets(self):
        """A `Host:` header carries an IPv6 address bracketed."""
        local = [
            address
            for address in _sampled_ipv6_addresses()
            if _is_local_address(address)
        ]
        self.assertTrue(local)
        for address in local:
            self.assertIs(_is_local_host(f"[{address}]"), True)


class IsLocalHostNameTest(SimpleTestCase):
    def assert_local(self, *hosts):
        for host in hosts:
            with self.subTest(host=host):
                self.assertIs(_is_local_host(host), True)

    def assert_not_local(self, *hosts):
        for host in hosts:
            with self.subTest(host=host):
                self.assertIs(_is_local_host(host), False)

    def test_empty_and_localhost(self):
        self.assert_local("", None, "  ", "localhost", "LocalHost")

    def test_reserved_local_suffixes_and_single_label_names(self):
        self.assert_local(
            "montrek-local.lan", "box.internal", "host.local", "dev.test", "ubuntu-vm"
        )

    def test_public_names_are_not_local(self):
        self.assert_not_local("montrek.customer.de", "example.com")

    def test_a_public_name_that_merely_starts_like_a_private_range(self):
        """The bug this guard had: a routable name read as an RFC1918 address.

        `"10.attacker.example".startswith("10.")` is true, which was enough to
        classify a public host as local and wave DEBUG=1 through. The names are
        built from the leading labels of every sampled local address, so each
        reserved range contributes its own decoy instead of one being picked by
        hand.
        """
        names = sorted(
            {
                ".".join(labels[:count]) + ".attacker.example"
                for labels in (
                    str(address).split(".")
                    for address in _sampled_ipv4_addresses()
                    if _is_local_address(address)
                )
                for count in range(1, len(labels) + 1)
            }
        )
        self.assertTrue(names)
        self.assert_not_local(*names)

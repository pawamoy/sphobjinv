r"""*Direct expect-fail API tests for* ``sphobjinv``.

``sphobjinv`` is a toolkit for manipulation and inspection of
Sphinx |objects.inv| files.

**Author**
    Brian Skinn (bskinn@alum.mit.edu)

**File Created**
    20 Mar 2019

**Copyright**
    \(c) Brian Skinn 2016-2020

**Source Repository**
    http://www.github.com/bskinn/sphobjinv

**Documentation**
    http://sphobjinv.readthedocs.io

**License**
    The MIT License; see |license_txt|_ for full license terms

**Members**

"""

from zlib import error as zlib_error

import pytest
from attr.exceptions import FrozenInstanceError
from jsonschema.exceptions import ValidationError

import sphobjinv as soi


pytestmark = [pytest.mark.api, pytest.mark.local]


def no_op(val):
    """No-op function to leave Path objects alone in tests."""
    return val


PATH_FXNS = (no_op, str)
PATH_FXN_IDS = ("no_op", "str")


class TestCore:
    """Tests for core sphobjinv functionality."""

    @pytest.mark.parametrize("path_fxn", PATH_FXNS, ids=PATH_FXN_IDS)
    def test_apifail_readbytes_missing_input_file(self, path_fxn, scratch_path):
        """Confirm that appropriate exception is raised w/no input file."""
        with pytest.raises(FileNotFoundError):
            soi.readbytes(path_fxn(scratch_path / "thisfilewillneverexist.foo"))

    @pytest.mark.parametrize("path_fxn", PATH_FXNS, ids=PATH_FXN_IDS)
    def test_apifail_writebytes_badoutputfile(self, path_fxn, scratch_path, misc_info):
        """Confirm OSError raised on bad filename (example of read error)."""
        b_str = b"This is a binary string!"

        with pytest.raises(OSError):
            soi.writebytes(path_fxn(scratch_path / misc_info.invalid_filename), b_str)


class TestDataObj:
    """Tests for the DataObj classes."""

    @pytest.mark.parametrize("dobj", [soi.DataObjBytes, soi.DataObjStr])
    def test_apifail_bad_dataobj_init_types(self, dobj):
        """Confirm error raised when init-ed w/wrong types."""
        with pytest.raises(TypeError):
            dobj(*range(6))

    def test_apifail_dataline_bothargstrue(self, misc_info):
        """Confirm error raised when both expand and contract are True."""
        dos = soi.DataObjStr(**soi.p_data.search(misc_info.str_lines[True]).groupdict())
        with pytest.raises(ValueError):
            dos.data_line(expand=True, contract=True)


class TestInventory:
    """Tests for the Inventory class."""

    @pytest.mark.parametrize("path_fxn", PATH_FXNS, ids=PATH_FXN_IDS)
    def test_apifail_error_decompressing_plaintext(self, path_fxn, res_dec):
        """Confirm error raised on attempt to decompress plaintext."""
        # OS-dependent. VersionError on Windows b/c bytes import of the
        # text-file objects_attrs.txt has the first line ending with b'2\r\n',
        # whereas *nix will pass the version check but choke in the zlib
        # decompression process
        with pytest.raises((zlib_error, soi.VersionError)):
            soi.Inventory(fname_zlib=path_fxn(res_dec))

    def test_apifail_inventory_invalidsource(self):
        """Confirm error raised when invalid source provided."""
        with pytest.raises(TypeError):
            soi.Inventory("abcdefg")

    def test_apifail_inventory_dictimport_noitems(self):
        """Confirm ValueError with no-items dict passed to json_dict."""
        d = {
            soi.HeaderFields.Project.value: "proj",
            soi.HeaderFields.Version.value: "v3.3",
            soi.HeaderFields.Count.value: 5,
        }

        with pytest.raises(ValueError):
            soi.Inventory()._import_json_dict(d)

    @pytest.mark.parametrize("path_fxn", PATH_FXNS, ids=PATH_FXN_IDS)
    def test_apifail_inventory_dictimport_toosmall(self, path_fxn, res_dec):
        """Confirm error raised when JSON dict passed w/too few objects."""
        inv = soi.Inventory(path_fxn(res_dec))
        d = inv.json_dict()
        d.pop("12")

        with pytest.raises(ValueError):
            soi.Inventory(d)

    @pytest.mark.parametrize("path_fxn", PATH_FXNS, ids=PATH_FXN_IDS)
    def test_apifail_inventory_dictimport_badobj(self, path_fxn, res_dec):
        """Confirm error raised when JSON dict passed w/an invalid object."""
        inv = soi.Inventory(path_fxn(res_dec))
        d = inv.json_dict()
        d.update({"112": "foobarbazquux"})

        with pytest.raises(ValidationError):
            soi.Inventory(dict_json=d)

    @pytest.mark.parametrize("path_fxn", PATH_FXNS, ids=PATH_FXN_IDS)
    def test_apifail_inventory_dictimport_toobig(self, path_fxn, res_dec):
        """Confirm error raised when JSON dict passed w/too many objects."""
        inv = soi.Inventory(path_fxn(res_dec))
        d = inv.json_dict()
        d.update({"57": d["23"]})

        with pytest.raises(ValueError):
            soi.Inventory(dict_json=d)

    @pytest.mark.parametrize("path_fxn", PATH_FXNS, ids=PATH_FXN_IDS)
    def test_apifail_inventory_dictimport_badrootobject(self, path_fxn, res_dec):
        """Confirm error raised when spurious extra root object present."""
        inv = soi.Inventory(path_fxn(res_dec))
        d = inv.json_dict()
        d.update({"bad_foo": "angry_bar"})

        with pytest.raises(ValidationError):
            soi.Inventory(dict_json=d)

    def test_apifail_inventory_dictimport_toomanysrcargs(
        self,
    ):
        """Confirm error if >1 sources passed."""
        with pytest.raises(RuntimeError):
            soi.Inventory(source="foo", plaintext="bar")

    def test_apifail_inventory_no_object_invs(self, subtests):
        """Confirm no-objects inventories don't import."""
        inv = soi.Inventory()

        with subtests.test(msg="plain"):
            with pytest.raises(TypeError):
                soi.Inventory(inv.data_file())

        with subtests.test(msg="zlib"):
            with pytest.raises((TypeError, ValueError)):
                soi.Inventory(soi.compress(inv.data_file()))

        d = {"project": "test", "version": "0.0", "count": 0}
        with subtests.test(msg="json"):
            with pytest.raises(ValueError):
                soi.Inventory(d)


@pytest.mark.xfail(reason="Made mutable to simplify Inventory revision by users")
class TestImmutable:
    """Tests for (now obsolete) DataObj immutability."""

    @pytest.mark.parametrize("path_fxn", PATH_FXNS, ids=PATH_FXN_IDS)
    @pytest.mark.parametrize("use_bytes", [True, False])
    def test_apifail_changing_immutable_dataobj(self, path_fxn, use_bytes, res_cmp):
        """Confirm DataObj's are immutable."""
        inv = soi.Inventory(path_fxn(res_cmp))

        with pytest.raises(FrozenInstanceError):  # pragma: no cover (XFAIL)
            if use_bytes:
                inv.objects[0].as_bytes.name = b"newname"
            else:
                inv.objects[0].name = "newname"

r"""*Direct, NONLOCAL expect-good API tests for* ``sphobjinv``.

``sphobjinv`` is a toolkit for manipulation and inspection of
Sphinx |objects.inv| files.

**Author**
    Brian Skinn (bskinn@alum.mit.edu)

**File Created**
    21 Mar 2019

**Copyright**
    \(c) Brian Skinn 2016-2019

**Source Repository**
    http://www.github.com/bskinn/sphobjinv

**Documentation**
    http://sphobjinv.readthedocs.io

**License**
    The MIT License; see |license_txt|_ for full license terms

**Members**

"""

from pathlib import Path

import pytest

import sphobjinv as soi


pytestmark = [pytest.mark.api, pytest.mark.good, pytest.mark.nonloc]


testall_inv_paths = (
    p
    for p in (Path(__file__).parent / "resource").iterdir()
    if p.name.startswith("objects_") and p.name.endswith(".inv")
)


@pytest.mark.parametrize("inv_path", list(testall_inv_paths), ids=(lambda p: p.name))
@pytest.mark.testall
@pytest.mark.timeout(20)
def test_api_inventory_many_url_imports(
    inv_path, res_path, scratch_path, misc_info, sphinx_load_test, pytestconfig
):
    """Confirm a plethora of .inv files downloads properly via url arg.

    This test is SLOW, and so does not run by default.  Invoke with `--nonloc`
    to run it; invoke with `--testall` to test over all .inv files in
    tests/resource.

    """
    fname = inv_path.name
    scr_fpath = scratch_path / fname

    # Drop unless nonlocal
    if not pytestconfig.getoption("--nonloc"):
        pytest.skip("'--nonloc' not specified")

    # Drop most unless testall
    if not pytestconfig.getoption("--testall") and fname != "objects_attrs.inv":
        pytest.skip("'--testall' not specified")

    # Construct inventories for comparison
    mch = misc_info.p_inv.match(fname)
    proj_name = mch.group(1)
    inv1 = soi.Inventory(str(res_path / fname))
    inv2 = soi.Inventory(url=misc_info.remote_url.format(proj_name))

    # Test the things
    assert inv1.project == inv2.project
    assert inv1.version == inv2.version
    assert inv1.count == inv2.count
    for objs in zip(inv1.objects, inv2.objects):
        assert objs[0].name == objs[1].name
        assert objs[0].domain == objs[1].domain
        assert objs[0].role == objs[1].role
        assert objs[0].uri == objs[1].uri
        assert objs[0].priority == objs[1].priority
        assert objs[0].dispname == objs[1].dispname

    # Ensure sphinx likes the regenerated inventory
    data = inv2.data_file()
    cmp_data = soi.compress(data)
    soi.writebytes(str(scr_fpath), cmp_data)
    sphinx_load_test(scr_fpath)


if __name__ == "__main__":
    print("Module not executable.")
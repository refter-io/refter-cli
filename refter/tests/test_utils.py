import pytest
from dbt.contracts.graph.manifest import WritableManifest

from refter.utils.validation import (
    _find_model_for_schema_and_table,
    _find_nodes_with_references,
    _get_ref_schema_and_table,
    _validate_column_references,
    _validate_references,
)


@pytest.fixture(scope="session")
def good_manifest():
    return WritableManifest.read_and_check_versions(
        "refter/tests/fixtures/manifest.json"
    )


@pytest.fixture(scope="session")
def bad_ref_manifest():
    return WritableManifest.read_and_check_versions(
        "refter/tests/fixtures/manifest_bad_refs.json"
    )


def test_get_ref_schema_and_table():
    schema, table = _get_ref_schema_and_table("my.schema")
    assert schema == "my" and table == "schema"

    with pytest.raises(ValueError):
        schema, table = _get_ref_schema_and_table("my.schema.v1")

    schema, table = _get_ref_schema_and_table("schema")
    assert schema is None and table == "schema"


def test_find_model_for_schema_and_table(good_manifest):
    nodes = good_manifest.nodes.values()

    node = _find_model_for_schema_and_table("hb_testdata", "categories", nodes)
    assert node.unique_id == "model.testdata.categories"

    node = _find_model_for_schema_and_table(None, "categories", nodes)
    assert node.unique_id == "model.testdata.categories"

    node = _find_model_for_schema_and_table(None, "i_dont_exist", nodes)
    assert node is None


def test_find_nodes_with_references(good_manifest):
    nodes = good_manifest.nodes.values()

    nodes = _find_nodes_with_references(nodes)
    assert len(nodes) == 2

    nodes = _find_nodes_with_references([])
    assert len(nodes) == 0


def test_validate_references(good_manifest):
    errors = _validate_references(good_manifest)
    assert len(errors.keys()) == 1

    errors = errors["hb_testdata.user_tasks"]
    assert len(errors) == 2
    assert errors[0].dict() == {
        "field": "disabled",
        "message": "value could not be parsed to a boolean",
        "column": None,
        "type": "type_error.bool",
    }


def test_validate_column_references(good_manifest):
    errors = _validate_column_references(good_manifest)
    assert len(errors.keys()) == 0


def test_validate_column_references_errors(bad_ref_manifest):
    errors = _validate_column_references(bad_ref_manifest)
    assert len(errors.keys()) == 1

    errors = errors["hb_testdata.user_tasks"]
    assert len(errors) == 4

    assert errors[0].dict() == {
        "column": "owner",
        "field": "relations.0.type",
        "message": "value is not a valid enumeration member; "
        + "permitted: 'one-to-one', "
        "'many-to-many', 'many-to-one', 'one-to-many'",
        "type": "type_error.enum",
    }

    assert errors[1].dict() == {
        "column": "title",
        "field": "deprecated",
        "message": "value is not a valid dict",
        "type": "type_error.dict",
    }

    assert errors[2].dict() == {
        "column": "title",
        "field": "relations.0.column",
        "message": "field required",
        "type": "value_error.missing",
    }

    assert errors[3].dict() == {
        "column": "title",
        "field": "relations.0.type",
        "message": "field required",
        "type": "value_error.missing",
    }


def test_validate_references_failure(bad_ref_manifest):
    errors = _validate_column_references(bad_ref_manifest)
    print(errors)
    assert len(errors) == 1

    table_errors = errors["hb_testdata.user_tasks"]
    assert len(table_errors) == 4
    assert table_errors[0].dict() == {
        "message": (
            "value is not a valid enumeration member; permitted:"
            + " 'one-to-one', 'many-to-many', 'many-to-one', 'one-to-many'"
        ),
        "column": "owner",
        "field": "relations.0.type",
        "type": "type_error.enum",
    }

    assert table_errors[1].dict() == {
        "column": "title",
        "field": "deprecated",
        "message": "value is not a valid dict",
        "type": "type_error.dict",
    }

    assert table_errors[2].dict() == {
        "column": "title",
        "field": "relations.0.column",
        "message": "field required",
        "type": "value_error.missing",
    }

    assert table_errors[3].dict() == {
        "column": "title",
        "field": "relations.0.type",
        "message": "field required",
        "type": "value_error.missing",
    }
